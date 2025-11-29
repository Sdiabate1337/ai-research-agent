"""Caching layer for query analyzer results."""

import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CacheStats:
    """Statistics for cache performance."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate (0-1)."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.hit_rate
        }


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: int):
        """Set value in cache with TTL."""
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear all cache entries."""
        pass


class MemoryCacheBackend(CacheBackend):
    """
    In-memory cache backend using a dictionary.
    
    Pros:
    - No external dependencies
    - Fast
    - Simple to test
    
    Cons:
    - Lost on restart
    - Not shared across processes
    - No persistence
    """
    
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, tuple[str, datetime]] = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[str]:
        if key not in self.cache:
            return None
        
        value, expiry = self.cache[key]
        
        # Check if expired
        if datetime.now() > expiry:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: str, ttl_seconds: int):
        # Simple LRU: remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        expiry = datetime.now() + timedelta(seconds=ttl_seconds)
        self.cache[key] = (value, expiry)
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        self.cache.clear()


class RedisCacheBackend(CacheBackend):
    """
    Redis cache backend.
    
    Pros:
    - Persistent
    - Shared across processes
    - Built-in TTL support
    - Scalable
    
    Cons:
    - Requires Redis server
    - Network overhead
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "query_analyzer:"
    ):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Redis backend requires 'redis' package. "
                "Install with: pip install redis"
            )
        
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True  # Return strings instead of bytes
        )
        self.key_prefix = key_prefix
        
        # Test connection
        try:
            self.client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str) -> Optional[str]:
        return self.client.get(self._make_key(key))
    
    def set(self, key: str, value: str, ttl_seconds: int):
        self.client.setex(
            self._make_key(key),
            ttl_seconds,
            value
        )
    
    def delete(self, key: str):
        self.client.delete(self._make_key(key))
    
    def clear(self):
        """Clear all keys with our prefix."""
        pattern = f"{self.key_prefix}*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)


class QueryCache:
    """
    High-level cache for query analyzer results.
    
    Features:
    =========
    - Query normalization (consistent cache keys)
    - Multiple backend support (memory, Redis)
    - Automatic serialization/deserialization
    - Cache statistics
    
    Usage:
    ======
    from query_analyzer_config import get_config
    
    config = get_config()
    cache = QueryCache.from_config(config)
    
    # Check cache
    result = cache.get(query="What's new in AI?", date_range="week")
    if result is None:
        # Cache miss - call LLM
        result = call_llm(query)
        cache.set(query, date_range, result)
    """
    
    def __init__(self, backend: CacheBackend, ttl_seconds: int = 3600):
        self.backend = backend
        self.ttl_seconds = ttl_seconds
        self.stats = CacheStats()
    
    @classmethod
    def from_config(cls, config) -> "QueryCache":
        """
        Create cache from configuration.
        
        Args:
            config: QueryAnalyzerConfig instance
            
        Returns:
            QueryCache instance
        """
        if config.cache_backend == "redis":
            backend = RedisCacheBackend(
                host=config.redis_host,
                port=config.redis_port,
                db=config.redis_db,
                password=config.redis_password,
                key_prefix=config.redis_key_prefix
            )
        elif config.cache_backend == "memory":
            backend = MemoryCacheBackend(max_size=config.cache_max_size)
        else:
            raise ValueError(f"Unsupported cache backend: {config.cache_backend}")
        
        return cls(backend, ttl_seconds=config.cache_ttl_seconds)
    
    def normalize_query(self, query: str) -> str:
        """
        Normalize query for consistent cache keys.
        
        Normalization:
        - Lowercase
        - Strip whitespace
        - Remove extra spaces
        - Remove punctuation (optional)
        
        Examples:
        =========
        "What's NEW in AI?" → "whats new in ai"
        "  AI  agents  " → "ai agents"
        """
        normalized = query.lower().strip()
        # Collapse multiple spaces
        normalized = " ".join(normalized.split())
        return normalized
    
    def make_cache_key(self, query: str, date_range: str) -> str:
        """
        Create cache key from query and date_range.
        
        Uses hash to keep keys short and consistent.
        
        Args:
            query: User query
            date_range: Date range filter
            
        Returns:
            Cache key (hash)
        """
        normalized_query = self.normalize_query(query)
        key_string = f"{normalized_query}:{date_range}"
        
        # Use SHA256 hash for consistent, short keys
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return key_hash
    
    def get(self, query: str, date_range: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result for query.
        
        Args:
            query: User query
            date_range: Date range filter
            
        Returns:
            Cached result dict or None if not found
        """
        self.stats.total_requests += 1
        
        cache_key = self.make_cache_key(query, date_range)
        cached_value = self.backend.get(cache_key)
        
        if cached_value is None:
            self.stats.cache_misses += 1
            return None
        
        self.stats.cache_hits += 1
        
        # Deserialize from JSON
        try:
            return json.loads(cached_value)
        except json.JSONDecodeError:
            # Invalid cached data, treat as miss
            self.stats.cache_misses += 1
            return None
    
    def set(self, query: str, date_range: str, result: Dict[str, Any]):
        """
        Cache result for query.
        
        Args:
            query: User query
            date_range: Date range filter
            result: Analysis result to cache
        """
        cache_key = self.make_cache_key(query, date_range)
        
        # Serialize to JSON
        cached_value = json.dumps(result)
        
        self.backend.set(cache_key, cached_value, self.ttl_seconds)
    
    def invalidate(self, query: str, date_range: str):
        """
        Invalidate cache entry for query.
        
        Useful when you want to force a refresh.
        """
        cache_key = self.make_cache_key(query, date_range)
        self.backend.delete(cache_key)
    
    def clear(self):
        """Clear all cache entries."""
        self.backend.clear()
        self.stats = CacheStats()  # Reset stats
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats
