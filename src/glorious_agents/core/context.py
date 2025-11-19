"""Event bus and skill context for inter-skill communication."""

import logging
import sqlite3
import threading
from collections import defaultdict
from collections.abc import Callable
from enum import Enum
from typing import Any, Protocol

from sqlalchemy import Engine

from glorious_agents.core.cache import TTLCache

logger = logging.getLogger(__name__)


class ErrorHandlingMode(Enum):
    """Error handling modes for event bus."""

    SILENT = "silent"  # Log errors but continue (default behavior)
    FAIL_FAST = "fail_fast"  # Raise first error
    COLLECT = "collect"  # Collect all errors and provide them


class EventBus:
    """In-process publish-subscribe event bus with configurable error handling.

    The event bus supports three error handling modes:
    - SILENT (default): Logs errors but continues processing other handlers
    - FAIL_FAST: Raises the first error encountered
    - COLLECT: Collects all errors and makes them available via get_last_errors()
    """

    def __init__(self, error_mode: ErrorHandlingMode = ErrorHandlingMode.SILENT) -> None:
        """Initialize EventBus with specified error handling mode.

        Args:
            error_mode: How to handle errors in event handlers (default: SILENT)
        """
        self._subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)
        self._lock = threading.Lock()
        self._error_mode = error_mode
        self._last_errors: list[tuple[str, Exception]] = []

    def subscribe(self, topic: str, callback: Callable[[dict[str, Any]], None]) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: Event topic name.
            callback: Function to call when event is published.
        """
        with self._lock:
            self._subscribers[topic].append(callback)

    def publish(self, topic: str, data: dict[str, Any]) -> None:
        """
        Publish an event to a topic.

        Args:
            topic: Event topic name.
            data: Event data payload.

        Raises:
            Exception: If error_mode is FAIL_FAST and a handler raises
        """
        with self._lock:
            callbacks = self._subscribers.get(topic, [])
            self._last_errors.clear()

        # Execute callbacks outside lock to avoid deadlocks
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                # Log error
                logger.error(f"Error in event handler for {topic}: {e}", exc_info=True)

                # Handle based on mode
                if self._error_mode == ErrorHandlingMode.FAIL_FAST:
                    raise
                elif self._error_mode == ErrorHandlingMode.COLLECT:
                    self._last_errors.append((topic, e))
                # SILENT mode: just log (default behavior)

    def get_last_errors(self) -> list[tuple[str, Exception]]:
        """Get errors from last publish operation (if error_mode is COLLECT).

        Returns:
            List of (topic, exception) tuples from the last publish call
        """
        return self._last_errors.copy()

    def get_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers for a topic.

        Args:
            topic: Topic name to query

        Returns:
            Number of subscribers for the topic
        """
        with self._lock:
            return len(self._subscribers.get(topic, []))

    def get_all_topics(self) -> list[str]:
        """Get list of all topics with subscribers.

        Returns:
            List of topic names that have at least one subscriber
        """
        with self._lock:
            return list(self._subscribers.keys())


class SkillApp(Protocol):
    """Protocol for skill Typer apps."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the skill app."""
        ...


class SkillContext:
    """Shared context for all skills with TTL-aware cache.

    Supports both legacy SQLite connections and modern SQLAlchemy engines
    for backward compatibility during migration.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        event_bus: EventBus,
        cache_max_size: int = 1000,
        engine: Engine | None = None,
    ) -> None:
        """
        Initialize a SkillContext with a shared database connection, an event bus, and a TTL-backed in-process cache.

        Parameters:
                conn (sqlite3.Connection): Shared SQLite connection used by skills; accessing `conn` after the context is closed will raise a RuntimeError.
                event_bus (EventBus): In-process event bus for inter-skill publish/subscribe.
                cache_max_size (int): Maximum number of entries the internal TTL cache will hold (default 1000).
                engine (Engine | None): Optional SQLAlchemy engine for modern ORM-based skills.
        """
        self._conn = conn
        self._event_bus = event_bus
        self._engine = engine
        self._skills: dict[str, SkillApp] = {}
        self._cache = TTLCache(max_size=cache_max_size)
        self._closed = False

    def __enter__(self) -> "SkillContext":
        """
        Provide the SkillContext instance for use in a with statement.

        Returns:
            The same SkillContext instance.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """
        Clean up the context by closing resources when exiting a with block.

        Called by the context manager protocol; invokes `close()` to release any held resources.
        The exception type, value, and traceback passed by the protocol are accepted but ignored.
        Parameters:
            exc_type (Any): The exception type if an exception occurred, otherwise None.
            exc_val (Any): The exception instance if an exception occurred, otherwise None.
            exc_tb (Any): The traceback if an exception occurred, otherwise None.
        """
        self.close()

    def close(self) -> None:
        """
        Close the shared database connection and mark the context as closed.

        Any exceptions raised while closing the connection are ignored.
        """
        if not self._closed:
            try:
                self._conn.close()
            except Exception:
                pass  # Ignore errors during cleanup
            self._closed = True

    @property
    def conn(self) -> sqlite3.Connection:
        """
        Access the shared sqlite3 database connection for this context.

        Returns:
            sqlite3.Connection: The shared database connection.

        Raises:
            RuntimeError: If the context has been closed and the connection is no longer available.
        """
        if self._closed:
            raise RuntimeError("Cannot use connection after context is closed")
        return self._conn

    @property
    def engine(self) -> Engine | None:
        """
        Access the SQLAlchemy engine for ORM-based skills.

        Returns:
            Engine | None: The SQLAlchemy engine if configured, None otherwise.

        Raises:
            RuntimeError: If the context has been closed.
        """
        if self._closed:
            raise RuntimeError("Cannot use engine after context is closed")
        return self._engine

    def publish(self, topic: str, data: dict[str, Any]) -> None:
        """
        Publish an event to the shared in-process event bus for subscribers of the given topic.

        Parameters:
                topic (str): Topic name identifying the event channel.
                data (dict[str, Any]): Event payload passed to each subscriber callback.
        """
        self._event_bus.publish(topic, data)

    def subscribe(self, topic: str, callback: Callable[[dict[str, Any]], None]) -> None:
        """Subscribe to an event topic."""
        self._event_bus.subscribe(topic, callback)

    def register_skill(self, name: str, app: SkillApp) -> None:
        """Register a skill app."""
        self._skills[name] = app

    def get_skill(self, name: str) -> SkillApp | None:
        """Get a registered skill app by name."""
        return self._skills.get(name)

    def cache_get(self, key: str) -> Any:
        """Get a value from the process-local cache."""
        return self._cache.get(key)

    def cache_set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in the process-local cache."""
        self._cache.set(key, value, ttl)

    def cache_has(self, key: str) -> bool:
        """Check if a key exists in cache and is not expired."""
        return self._cache.has(key)

    def cache_delete(self, key: str) -> bool:
        """Delete a key from the cache."""
        return self._cache.delete(key)

    def cache_clear(self) -> None:
        """Clear all entries from the process-local cache."""
        self._cache.clear()

    def cache_prune_expired(self) -> int:
        """Remove expired entries from the cache."""
        return self._cache.prune_expired()

    def _load_skill_config(self, skill_name: str, config_key: str) -> None:
        """Load skill configuration from TOML file."""
        from pathlib import Path

        from glorious_agents.config import config

        config_dir = Path(config.DATA_FOLDER) / "config"
        config_file = config_dir / f"{skill_name}.toml"

        if config_file.exists():
            try:
                import tomllib

                with open(config_file, "rb") as f:
                    skill_config = tomllib.load(f)
                setattr(self, config_key, skill_config)
            except Exception as e:
                logger.error(f"Error loading config for {skill_name}: {e}")
                setattr(self, config_key, {})
        else:
            setattr(self, config_key, {})

    def _get_nested_value(self, data: dict[str, Any], key: str, default: Any) -> Any:
        """Get nested dictionary value using dot notation."""
        parts = key.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value for current skill.

        Loads configuration from ~/.agent/config/<skill_name>.toml on first access.
        Configuration values are validated against the skill's config_schema.

        Args:
            key: Configuration key (e.g., 'cache.ttl_default').
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        skill_name = getattr(self, "_skill_name", None)
        if not skill_name:
            return default

        config_key = f"_config_{skill_name}"
        if not hasattr(self, config_key):
            self._load_skill_config(skill_name, config_key)

        skill_config = getattr(self, config_key, {})
        return self._get_nested_value(skill_config, key, default)


# Canonical event topics
TOPIC_NOTE_CREATED = "note_created"
TOPIC_ISSUE_CREATED = "issue_created"
TOPIC_ISSUE_UPDATED = "issue_updated"
TOPIC_PLAN_ENQUEUED = "plan_enqueued"
TOPIC_SCAN_READY = "scan_ready"
TOPIC_VACUUM_DONE = "vacuum_done"
