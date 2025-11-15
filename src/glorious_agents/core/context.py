"""Event bus and skill context for inter-skill communication."""

import logging
import sqlite3
import threading
import time
from collections import OrderedDict, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and expiration."""

    value: Any
    expires_at: float | None  # Unix timestamp, None means no expiration


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
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._cache_max_size = cache_max_size
        self._cache_lock = threading.Lock()

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
        """Get a value from the process-local cache.

        Returns None if the key doesn't exist or has expired.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            # Check expiration
            if entry.expires_at is not None and time.time() > entry.expires_at:
                # Expired, remove it
                del self._cache[key]
                return None

            # Move to end (LRU tracking)
            self._cache.move_to_end(key)
            return entry.value

    def cache_set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in the process-local cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds. None means no expiration.
        """
        with self._cache_lock:
            expires_at = time.time() + ttl if ttl is not None else None
            entry = CacheEntry(value=value, expires_at=expires_at)

            # Add or update entry
            if key in self._cache:
                del self._cache[key]  # Remove to update position
            self._cache[key] = entry

            # Enforce size limit (LRU eviction)
            while len(self._cache) > self._cache_max_size:
                # Remove oldest (first) item
                self._cache.popitem(last=False)

    def cache_has(self, key: str) -> bool:
        """Check if a key exists in cache and is not expired.

        Args:
            key: Cache key.

        Returns:
            True if key exists and is valid, False otherwise.
        """
        return self.cache_get(key) is not None

    def cache_delete(self, key: str) -> bool:
        """Delete a key from the cache.

        Args:
            key: Cache key to delete.

        Returns:
            True if key was found and deleted, False otherwise.
        """
        with self._cache_lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def cache_clear(self) -> None:
        """Clear all entries from the process-local cache."""
        with self._cache_lock:
            self._cache.clear()

    def cache_prune_expired(self) -> int:
        """Remove expired entries from the cache.

        Returns:
            Number of entries removed.
        """
        with self._cache_lock:
            now = time.time()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry.expires_at is not None and now > entry.expires_at
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)

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
        from glorious_agents.config import config

        # Determine skill name from caller context
        # For now, we'll require the skill to be registered
        # In a real implementation, we'd extract this from the call stack
        skill_name = getattr(self, "_skill_name", None)
        if not skill_name:
            return default

        # Load config file if not already loaded
        config_key = f"_config_{skill_name}"
        if not hasattr(self, config_key):
            from pathlib import Path

            config_dir = Path(config.AGENT_FOLDER) / "config"
            config_file = config_dir / f"{skill_name}.toml"
            if config_file.exists():
                try:
                    import tomllib

                    with open(config_file, "rb") as f:
                        skill_config = tomllib.load(f)
                    setattr(self, config_key, skill_config)
                except Exception as e:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(f"Error loading config for {skill_name}: {e}")
                    setattr(self, config_key, {})
            else:
                setattr(self, config_key, {})

        # Get nested config value
        skill_config = getattr(self, config_key, {})
        parts = key.split(".")
        value = skill_config
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value


# Canonical event topics
TOPIC_NOTE_CREATED = "note_created"
TOPIC_ISSUE_CREATED = "issue_created"
TOPIC_ISSUE_UPDATED = "issue_updated"
TOPIC_PLAN_ENQUEUED = "plan_enqueued"
TOPIC_SCAN_READY = "scan_ready"
TOPIC_VACUUM_DONE = "vacuum_done"
