"""TTL-aware process-local cache for skills."""

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    """Cache entry with value and expiration."""

    value: Any
    expires_at: float | None  # Unix timestamp, None means no expiration


class TTLCache:
    """Thread-safe LRU cache with time-to-live support."""

    def __init__(self, max_size: int = 1000) -> None:
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        """Get a value from the cache.

        Returns None if the key doesn't exist or has expired.
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.expires_at is not None and time.time() > entry.expires_at:
                del self._cache[key]
                return None

            self._cache.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds. None means no expiration.
        """
        with self._lock:
            expires_at = time.time() + ttl if ttl is not None else None
            entry = CacheEntry(value=value, expires_at=expires_at)

            if key in self._cache:
                del self._cache[key]
            self._cache[key] = entry

            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def has(self, key: str) -> bool:
        """Check if a key exists in cache and is not expired."""
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """Delete a key from the cache.

        Returns True if key was found and deleted, False otherwise.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def prune_expired(self) -> int:
        """Remove expired entries from the cache.

        Returns the number of entries removed.
        """
        with self._lock:
            now = time.time()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry.expires_at is not None and now > entry.expires_at
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)
