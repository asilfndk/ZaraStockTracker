"""Tests for cache module"""
from zara_tracker.core.cache import TTLCache, CacheEntry, api_cache
import pytest
import time
import sys
import os

# Add parent and src directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), 'src'))


class TestCacheEntry:
    """Tests for CacheEntry class"""

    def test_entry_not_expired(self):
        """Test that new entry is not expired"""
        from datetime import datetime, timedelta

        entry = CacheEntry(
            value="test",
            expires_at=datetime.now() + timedelta(seconds=60)
        )

        assert entry.is_expired is False

    def test_entry_expired(self):
        """Test that old entry is expired"""
        from datetime import datetime, timedelta

        entry = CacheEntry(
            value="test",
            expires_at=datetime.now() - timedelta(seconds=1)
        )

        assert entry.is_expired is True


class TestTTLCache:
    """Tests for TTLCache class"""

    def test_set_and_get(self):
        """Test basic set and get operations"""
        cache = TTLCache(default_ttl_seconds=60)

        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist"""
        cache = TTLCache()

        assert cache.get("nonexistent") is None

    def test_expiration(self):
        """Test that entries expire after TTL"""
        cache = TTLCache(default_ttl_seconds=1)

        cache.set("key", "value")
        assert cache.get("key") == "value"

        # Wait for expiration
        time.sleep(1.1)

        assert cache.get("key") is None

    def test_custom_ttl(self):
        """Test custom TTL for individual entries"""
        cache = TTLCache(default_ttl_seconds=60)

        cache.set("short", "value", ttl_seconds=1)
        cache.set("long", "value", ttl_seconds=60)

        time.sleep(1.1)

        assert cache.get("short") is None
        assert cache.get("long") == "value"

    def test_delete(self):
        """Test deleting a key"""
        cache = TTLCache()

        cache.set("key", "value")
        assert cache.delete("key") is True
        assert cache.get("key") is None

        # Deleting non-existent key
        assert cache.delete("nonexistent") is False

    def test_clear(self):
        """Test clearing the cache"""
        cache = TTLCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_contains(self):
        """Test __contains__ method"""
        cache = TTLCache()

        cache.set("key", "value")

        assert "key" in cache
        assert "nonexistent" not in cache

    def test_len(self):
        """Test __len__ method"""
        cache = TTLCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert len(cache) == 2

    def test_cleanup_expired(self):
        """Test cleanup_expired method"""
        cache = TTLCache(default_ttl_seconds=1)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Wait for expiration
        time.sleep(1.1)

        removed = cache.cleanup_expired()

        assert removed == 2


class TestAPICache:
    """Tests for global api_cache instance"""

    def test_api_cache_exists(self):
        """Test that api_cache is properly initialized"""
        assert api_cache is not None
        assert isinstance(api_cache, TTLCache)

    def test_api_cache_operations(self):
        """Test basic operations on api_cache"""
        # Clear any existing data
        api_cache.clear()

        api_cache.set("test_url", {"data": "test"})

        result = api_cache.get("test_url")
        assert result == {"data": "test"}

        # Cleanup
        api_cache.clear()
