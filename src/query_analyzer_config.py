"""Configuration management for the query analyzer."""

from dataclasses import dataclass, field
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class QueryAnalyzerConfig:
    """
    Configuration for the query analyzer node.
    
    Design Philosophy:
    ==================
    - Sensible defaults for development
    - Environment variables for production
    - Type-safe with dataclasses
    - Easy to test with different configs
    
    Usage:
    ======
    # Development (use defaults)
    config = QueryAnalyzerConfig()
    
    # Production (from environment)
    config = QueryAnalyzerConfig.from_env()
    
    # Testing (custom config)
    config = QueryAnalyzerConfig(cache_enabled=False)
    """
    
    # === LLM Settings ===
    llm_model: str = "anthropic/claude-3.5-sonnet"
    llm_fallback_model: str = "anthropic/claude-3-haiku"
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 10
    llm_max_retries: int = 3
    llm_retry_base_delay: float = 1.0  # seconds
    
    # === Caching ===
    cache_enabled: bool = True
    cache_backend: str = "redis"  # "redis", "memory", "sqlite"
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_max_size: int = 10000  # Max entries for in-memory cache
    
    # Redis-specific
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_key_prefix: str = "ai_research_agent:query_analyzer:"
    
    # === Validation ===
    max_query_length: int = 1000
    min_query_length: int = 2
    max_topics: int = 5
    max_categories: int = 4
    
    # === Fallback ===
    enable_fallback: bool = True
    fallback_categories: List[str] = field(
        default_factory=lambda: ["papers", "repositories", "documentation"]
    )
    
    # === Monitoring ===
    metrics_enabled: bool = True
    log_queries: bool = True  # Log all queries for analytics
    
    # === Cost Tracking ===
    # Approximate token costs per 1M tokens (USD)
    cost_per_1m_input_tokens: float = 3.0  # Claude 3.5 Sonnet
    cost_per_1m_output_tokens: float = 15.0
    
    @classmethod
    def from_env(cls) -> "QueryAnalyzerConfig":
        """
        Create config from environment variables.
        
        Environment Variables:
        =====================
        LLM_MODEL - Primary LLM model
        LLM_FALLBACK_MODEL - Fallback LLM model
        CACHE_ENABLED - Enable/disable caching (true/false)
        CACHE_TTL_SECONDS - Cache TTL in seconds
        REDIS_HOST - Redis host
        REDIS_PORT - Redis port
        REDIS_PASSWORD - Redis password
        MAX_QUERY_LENGTH - Maximum query length
        
        Returns:
            Config instance with values from environment
        """
        return cls(
            # LLM settings
            llm_model=os.getenv("LLM_MODEL", cls.llm_model),
            llm_fallback_model=os.getenv("LLM_FALLBACK_MODEL", cls.llm_fallback_model),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", str(cls.llm_temperature))),
            llm_timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", str(cls.llm_timeout_seconds))),
            
            # Caching
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            cache_backend=os.getenv("CACHE_BACKEND", cls.cache_backend),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", str(cls.cache_ttl_seconds))),
            
            # Redis
            redis_host=os.getenv("REDIS_HOST", cls.redis_host),
            redis_port=int(os.getenv("REDIS_PORT", str(cls.redis_port))),
            redis_password=os.getenv("REDIS_PASSWORD"),
            
            # Validation
            max_query_length=int(os.getenv("MAX_QUERY_LENGTH", str(cls.max_query_length))),
            min_query_length=int(os.getenv("MIN_QUERY_LENGTH", str(cls.min_query_length))),
        )
    
    def validate(self) -> List[str]:
        """
        Validate configuration values.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if self.llm_temperature < 0 or self.llm_temperature > 1:
            errors.append("llm_temperature must be between 0 and 1")
        
        if self.llm_timeout_seconds <= 0:
            errors.append("llm_timeout_seconds must be positive")
        
        if self.cache_ttl_seconds <= 0:
            errors.append("cache_ttl_seconds must be positive")
        
        if self.max_query_length <= self.min_query_length:
            errors.append("max_query_length must be greater than min_query_length")
        
        if self.cache_backend not in ["redis", "memory", "sqlite"]:
            errors.append(f"Invalid cache_backend: {self.cache_backend}")
        
        return errors


# Global default config instance
_default_config: Optional[QueryAnalyzerConfig] = None


def get_config() -> QueryAnalyzerConfig:
    """
    Get the global config instance.
    
    Usage:
    ======
    from query_analyzer_config import get_config
    
    config = get_config()
    if config.cache_enabled:
        # Use cache
        pass
    """
    global _default_config
    
    if _default_config is None:
        _default_config = QueryAnalyzerConfig.from_env()
        
        # Validate config
        errors = _default_config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
    
    return _default_config


def set_config(config: QueryAnalyzerConfig):
    """
    Set the global config instance (useful for testing).
    
    Usage:
    ======
    # In tests
    test_config = QueryAnalyzerConfig(cache_enabled=False)
    set_config(test_config)
    """
    global _default_config
    _default_config = config
