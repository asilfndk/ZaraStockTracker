"""In-memory cache with TTL support for Zara Stock Tracker"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, TypeVar, Generic
import threading

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with expiration time"""
    value: T
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Check if the entry has expired"""
        return datetime.now() >= self.expires_at


class TTLCache:
    """Thread-safe in-memory cache with TTL support"""

    def __init__(self, default_ttl_seconds: int = 300):
        """
        Initialize cache with default TTL.

        Args:
            default_ttl_seconds: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict[str, CacheEntry[Any]] = {}
        self._lock = threading.RLock()
        self._default_ttl = timedelta(seconds=default_ttl_seconds)

    def get(self, key: str) -> Any | None:
        """
        Get value from cache if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired:
                del self._cache[key]
                return None

            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """
        Set value in cache with optional custom TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL in seconds
        """
        with self._lock:
            ttl = timedelta(
                seconds=ttl_seconds) if ttl_seconds else self._default_ttl
            expires_at = datetime.now() + ttl
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if key didn't exist
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cached entries"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        return self.get(key) is not None

    def __len__(self) -> int:
        """Return number of non-expired entries"""
        with self._lock:
            return sum(1 for entry in self._cache.values() if not entry.is_expired)


# Global cache instance for API responses (5 minute TTL)
api_cache = TTLCache(default_ttl_seconds=300)
