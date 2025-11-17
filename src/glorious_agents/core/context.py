"""Event bus and skill context for inter-skill communication."""

import logging
import sqlite3
import threading
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Protocol

from glorious_agents.core.cache import TTLCache

logger = logging.getLogger(__name__)


class EventBus:
    """In-process publish-subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)
        self._lock = threading.Lock()

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
        """
        with self._lock:
            callbacks = self._subscribers.get(topic, [])

        # Execute callbacks outside lock to avoid deadlocks
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                # Log error but don't fail the publish
                logger.error(f"Error in event handler for {topic}: {e}", exc_info=True)


class SkillApp(Protocol):
    """Protocol for skill Typer apps."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the skill app."""
        ...


class SkillContext:
    """Shared context for all skills with TTL-aware cache."""

    def __init__(
        self, conn: sqlite3.Connection, event_bus: EventBus, cache_max_size: int = 1000
    ) -> None:
        self._conn = conn
        self._event_bus = event_bus
        self._skills: dict[str, SkillApp] = {}
        self._cache = TTLCache(max_size=cache_max_size)

    @property
    def conn(self) -> sqlite3.Connection:
        """Get the shared database connection."""
        return self._conn

    def publish(self, topic: str, data: dict[str, Any]) -> None:
        """Publish an event."""
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
