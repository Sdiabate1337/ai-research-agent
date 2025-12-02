"""Tests for query analyzer cache module."""

import pytest
import time
from query_analyzer_cache import (
    QueryCache,
    MemoryCacheBackend,
    CacheStats
)


class TestMemoryCacheBackend:
    """Test in-memory cache backend."""
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = MemoryCacheBackend()
        
        cache.set("key1", "value1", ttl_seconds=60)
        result = cache.get("key1")
        
        assert result == "value1"
    
    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = MemoryCacheBackend()
        
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = MemoryCacheBackend()
        
        cache.set("key1", "value1", ttl_seconds=1)
        
        # Should exist immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be None after expiration
        assert cache.get("key1") is None
    
    def test_delete(self):
        """Test deleting a cache entry."""
        cache = MemoryCacheBackend()
        
        cache.set("key1", "value1", ttl_seconds=60)
        assert cache.get("key1") == "value1"
        
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_clear(self):
        """Test clearing all cache entries."""
        cache = MemoryCacheBackend()
        
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_max_size_eviction(self):
        """Test that oldest entries are evicted when max size reached."""
        cache = MemoryCacheBackend(max_size=2)
        
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        cache.set("key3", "value3", ttl_seconds=60)  # Should evict key1
        
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"


class TestQueryCache:
    """Test high-level QueryCache functionality."""
    
    def test_query_normalization(self):
        """Test that queries are normalized consistently."""
        backend = MemoryCacheBackend()
        cache = QueryCache(backend, ttl_seconds=60)
        
        # Different formatting, same query
        norm1 = cache.normalize_query("What's NEW in AI?")
        norm2 = cache.normalize_query("  what's new in ai  ")
        norm3 = cache.normalize_query("WHAT'S  NEW  IN  AI")
        
        assert norm1 == norm2 == norm3
    
    def test_cache_key_consistency(self):
        """Test that same queries produce same cache keys."""
        backend = MemoryCacheBackend()
        cache = QueryCache(backend, ttl_seconds=60)
        
        key1 = cache.make_cache_key("What's new in AI?", "week")
        key2 = cache.make_cache_key("what's new in ai", "week")
        
        assert key1 == key2
    
    def test_cache_hit(self):
        """Test cache hit scenario."""
        backend = MemoryCacheBackend()
        cache = QueryCache(backend, ttl_seconds=60)
        
        # Set a value
        result = {"categories": ["papers"], "topics": ["ai"]}
        cache.set("What's new in AI?", "week", result)
        
        # Get it back
        cached = cache.get("What's new in AI?", "week")
        
        assert cached == result
        assert cache.stats.cache_hits == 1
        assert cache.stats.cache_misses == 0
    
    def test_cache_miss(self):
        """Test cache miss scenario."""
        backend = MemoryCacheBackend()
        cache = QueryCache(backend, ttl_seconds=60)
        
        # Try to get non-existent value
        result = cache.get("Nonexistent query", "week")
        
        assert result is None
        assert cache.stats.cache_hits == 0
        assert cache.stats.cache_misses == 1
    
    def test_cache_stats(self):
        """Test cache statistics tracking."""
        backend = MemoryCacheBackend()
        cache = QueryCache(backend, ttl_seconds=60)
        
        # Set some values
        cache.set("query1", "week", {"test": 1})
        cache.set("query2", "week", {"test": 2})
        
        # Hit and miss
        cache.get("query1", "week")  # Hit
        cache.get("query2", "week")  # Hit
        cache.get("query3", "week")  # Miss
        
        stats = cache.get_stats()
        
        assert stats.total_requests == 3
        assert stats.cache_hits == 2
        assert stats.cache_misses == 1
        assert stats.hit_rate == 2/3
    
    def test_invalidate(self):
        """Test cache invalidation."""
        backend = MemoryCacheBackend()
        cache = QueryCache(backend, ttl_seconds=60)
        
        # Set a value
        cache.set("query1", "week", {"test": 1})
        assert cache.get("query1", "week") is not None
        
        # Invalidate
        cache.invalidate("query1", "week")
        
        # Should be None now
        assert cache.get("query1", "week") is None
    
    def test_different_date_ranges_separate_cache(self):
        """Test that different date ranges use separate cache entries."""
        backend = MemoryCacheBackend()
        cache = QueryCache(backend, ttl_seconds=60)
        
        # Same query, different date ranges
        cache.set("AI updates", "24h", {"result": "24h"})
        cache.set("AI updates", "week", {"result": "week"})
        
        result_24h = cache.get("AI updates", "24h")
        result_week = cache.get("AI updates", "week")
        
        assert result_24h["result"] == "24h"
        assert result_week["result"] == "week"


class TestCacheStats:
    """Test CacheStats functionality."""
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(total_requests=10, cache_hits=7, cache_misses=3)
        
        assert stats.hit_rate == 0.7
    
    def test_hit_rate_zero_requests(self):
        """Test hit rate with zero requests."""
        stats = CacheStats()
        
        assert stats.hit_rate == 0.0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = CacheStats(total_requests=10, cache_hits=6, cache_misses=4)
        
        result = stats.to_dict()
        
        assert result["total_requests"] == 10
        assert result["cache_hits"] == 6
        assert result["cache_misses"] == 4
        assert result["hit_rate"] == 0.6


@pytest.mark.skipif(
    not pytest.importorskip("redis", minversion=None),
    reason="Redis not installed"
)
class TestRedisCacheBackend:
    """Test Redis cache backend (requires Redis server)."""
    
    @pytest.fixture
    def redis_cache(self):
        """Create Redis cache for testing."""
        try:
            from query_analyzer_cache import RedisCacheBackend
            cache = RedisCacheBackend(
                host="localhost",
                port=6379,
                key_prefix="test:"
            )
            cache.clear()  # Clean before test
            yield cache
            cache.clear()  # Clean after test
        except Exception:
            pytest.skip("Redis server not available")
    
    def test_redis_set_and_get(self, redis_cache):
        """Test Redis set and get."""
        redis_cache.set("key1", "value1", ttl_seconds=60)
        result = redis_cache.get("key1")
        
        assert result == "value1"
    
    def test_redis_ttl(self, redis_cache):
        """Test Redis TTL expiration."""
        redis_cache.set("key1", "value1", ttl_seconds=1)
        
        # Should exist immediately
        assert redis_cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be None after expiration
        assert redis_cache.get("key1") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
