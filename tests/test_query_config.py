"""Tests for configuration module."""

import pytest
import os
from query_analyzer_config import QueryAnalyzerConfig, get_config, set_config


class TestQueryAnalyzerConfig:
    """Test configuration dataclass."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = QueryAnalyzerConfig()
        
        assert config.llm_model == "anthropic/claude-3.5-sonnet"
        assert config.llm_temperature == 0.0
        assert config.cache_enabled is True
        assert config.cache_backend == "redis"
        assert config.max_query_length == 1000
        assert config.min_query_length == 2
    
    def test_custom_values(self):
        """Test creating config with custom values."""
        config = QueryAnalyzerConfig(
            llm_model="anthropic/claude-3-haiku",
            cache_enabled=False,
            max_query_length=500
        )
        
        assert config.llm_model == "anthropic/claude-3-haiku"
        assert config.cache_enabled is False
        assert config.max_query_length == 500
    
    def test_validation_success(self):
        """Test validation succeeds for valid config."""
        config = QueryAnalyzerConfig()
        errors = config.validate()
        
        assert len(errors) == 0
    
    def test_validation_invalid_temperature(self):
        """Test validation fails for invalid temperature."""
        config = QueryAnalyzerConfig(llm_temperature=1.5)
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("temperature" in err.lower() for err in errors)
    
    def test_validation_invalid_length_bounds(self):
        """Test validation fails when max < min length."""
        config = QueryAnalyzerConfig(
            min_query_length=100,
            max_query_length=50
        )
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("max_query_length" in err.lower() for err in errors)
    
    def test_validation_invalid_cache_backend(self):
        """Test validation fails for invalid cache backend."""
        config = QueryAnalyzerConfig(cache_backend="invalid")
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("cache_backend" in err.lower() for err in errors)


class TestConfigFromEnv:
    """Test loading configuration from environment variables."""
    
    def test_from_env_with_defaults(self, monkeypatch):
        """Test loading from env with no env vars set."""
        # Clear relevant env vars
        for key in ["LLM_MODEL", "CACHE_ENABLED", "REDIS_HOST"]:
            monkeypatch.delenv(key, raising=False)
        
        config = QueryAnalyzerConfig.from_env()
        
        # Should use defaults
        assert config.llm_model == "anthropic/claude-3.5-sonnet"
        assert config.cache_enabled is True
    
    def test_from_env_custom_values(self, monkeypatch):
        """Test loading custom values from environment."""
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4")
        monkeypatch.setenv("CACHE_ENABLED", "false")
        monkeypatch.setenv("MAX_QUERY_LENGTH", "500")
        monkeypatch.setenv("REDIS_HOST", "redis.example.com")
        
        config = QueryAnalyzerConfig.from_env()
        
        assert config.llm_model == "openai/gpt-4"
        assert config.cache_enabled is False
        assert config.max_query_length == 500
        assert config.redis_host == "redis.example.com"


class TestGlobalConfig:
    """Test global config management."""
    
    def teardown_method(self):
        """Reset global config after each test."""
        from query_analyzer_config import _default_config
        import query_analyzer_config
        query_analyzer_config._default_config = None
    
    def test_get_config_singleton(self):
        """Test that get_config returns singleton instance."""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_set_config(self):
        """Test setting custom config."""
        custom_config = QueryAnalyzerConfig(cache_enabled=False)
        set_config(custom_config)
        
        retrieved_config = get_config()
        
        assert retrieved_config.cache_enabled is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
