"""Tests for metrics collection module."""

import pytest
from query_analyzer_metrics import MetricsCollector, MetricsSummary


class TestMetricsSummary:
    """Test MetricsSummary calculations."""
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        summary = MetricsSummary(
            total_queries=100,
            successful_queries=85,
            failed_queries=15
        )
        
        assert summary.success_rate == 0.85
    
    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        summary = MetricsSummary(
            cache_hits=70,
            cache_misses=30
        )
        
        assert summary.cache_hit_rate == 0.7
    
    def test_avg_processing_time(self):
        """Test average processing time calculation."""
        summary = MetricsSummary(
            total_queries=10,
            total_processing_time_ms=1000
        )
        
        assert summary.avg_processing_time_ms == 100
    
    def test_p50_calculation(self):
        """Test p50 (median) calculation."""
        summary = MetricsSummary(
            processing_times_ms=[100, 200, 300, 400, 500]
        )
        
        assert summary.p50_processing_time_ms == 300
    
    def test_p95_calculation(self):
        """Test p95 calculation."""
        times = [i * 10 for i in range(1, 101)]  # 10, 20, ..., 1000
        summary = MetricsSummary(processing_times_ms=times)
        
        p95 = summary.p95_processing_time_ms
        
        # p95 should be around 950
        assert 940 <= p95 <= 960
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        summary = MetricsSummary(
            total_queries=100,
            successful_queries=90,
            failed_queries=10,
            cache_hits=60,
            cache_misses=40
        )
        
        result = summary.to_dict()
        
        assert result["total_queries"] == 100
        assert result["success_rate"] == 0.9
        assert result["cache_hit_rate"] == 0.6
        assert "processing_time_ms" in result
        assert "llm_usage" in result


class TestMetricsCollector:
    """Test MetricsCollector functionality."""
    
    def test_record_successful_query(self):
        """Test recording a successful query."""
        metrics = MetricsCollector()
        
        metrics.record_query_analysis(
            duration_ms=150,
            success=True,
            cache_hit=False,
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001,
            language="en"
        )
        
        summary = metrics.get_summary()
        
        assert summary.total_queries == 1
        assert summary.successful_queries == 1
        assert summary.failed_queries == 0
        assert summary.cache_misses == 1
        assert summary.total_llm_calls == 1
        assert summary.total_input_tokens == 100
        assert summary.total_output_tokens == 50
        assert summary.language_counts["en"] == 1
    
    def test_record_cache_hit(self):
        """Test recording a cache hit."""
        metrics = MetricsCollector()
        
        metrics.record_query_analysis(
            duration_ms=5,
            success=True,
            cache_hit=True,
            language="en"
        )
        
        summary = metrics.get_summary()
        
        assert summary.cache_hits == 1
        assert summary.cache_misses == 0
        assert summary.total_llm_calls == 0  # No LLM call on cache hit
    
    def test_record_error(self):
        """Test recording errors."""
        metrics = MetricsCollector()
        
        metrics.record_error("ValueError", "Invalid input")
        metrics.record_error("ValueError", "Another error")
        metrics.record_error("TimeoutError", "Request timeout")
        
        summary = metrics.get_summary()
        
        assert summary.error_counts["ValueError"] == 2
        assert summary.error_counts["TimeoutError"] == 1
        assert summary.failed_queries == 3
    
    def test_processing_time_tracking(self):
        """Test processing time tracking."""
        metrics = MetricsCollector()
        
        times = [100, 200, 150, 300, 250]
        for time_ms in times:
            metrics.record_query_analysis(
                duration_ms=time_ms,
                success=True
            )
        
        summary = metrics.get_summary()
        
        assert summary.min_processing_time_ms == 100
        assert summary.max_processing_time_ms == 300
        assert summary.avg_processing_time_ms == 200  # (100+200+150+300+250)/5
    
    def test_language_distribution(self):
        """Test language distribution tracking."""
        metrics = MetricsCollector()
        
        metrics.record_query_analysis(duration_ms=100, success=True, language="en")
        metrics.record_query_analysis(duration_ms=100, success=True, language="en")
        metrics.record_query_analysis(duration_ms=100, success=True, language="fr")
        metrics.record_query_analysis(duration_ms=100, success=True, language="ar")
        
        summary = metrics.get_summary()
        
        assert summary.language_counts["en"] == 2
        assert summary.language_counts["fr"] == 1
        assert summary.language_counts["ar"] == 1
    
    def test_reset(self):
        """Test resetting metrics."""
        metrics = MetricsCollector()
        
        metrics.record_query_analysis(duration_ms=100, success=True)
        metrics.record_query_analysis(duration_ms=200, success=True)
        
        assert metrics.get_summary().total_queries == 2
        
        metrics.reset()
        
        assert metrics.get_summary().total_queries == 0
    
    def test_prometheus_export_format(self):
        """Test Prometheus export format."""
        metrics = MetricsCollector()
        
        metrics.record_query_analysis(duration_ms=100, success=True)
        metrics.record_query_analysis(duration_ms=200, success=True)
        
        summary = metrics.get_summary()
        prometheus_text = summary.to_prometheus()
        
        # Check for expected Prometheus format
        assert "# HELP" in prometheus_text
        assert "# TYPE" in prometheus_text
        assert "query_analyzer_total_queries" in prometheus_text
        assert "query_analyzer_success_rate" in prometheus_text
        assert "quantile=" in prometheus_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
