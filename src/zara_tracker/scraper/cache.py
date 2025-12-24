"""Thread-safe TTL cache for API responses."""

import threading
import time
from typing import Any, Dict, Optional


class ScrapeCache:
    """Thread-safe TTL cache for scraper responses."""

    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    return value
                del self._cache[key]
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self._default_ttl
        with self._lock:
            self._cache[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def cleanup(self) -> int:
        """Remove expired entries. Returns count of removed items."""
        now = time.time()
        removed = 0
        with self._lock:
            expired = [k for k, (_, exp) in self._cache.items() if now >= exp]
            for key in expired:
                del self._cache[key]
                removed += 1
        return removed


# Global cache instance
scrape_cache = ScrapeCache()
