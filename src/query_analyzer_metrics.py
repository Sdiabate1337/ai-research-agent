"""Metrics collection and monitoring for query analyzer."""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class MetricsSummary:
    """Summary of collected metrics."""
    
    # Query processing
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    
    # Caching
    cache_hits: int = 0
    cache_misses: int = 0
    
    # Performance (milliseconds)
    total_processing_time_ms: float = 0
    min_processing_time_ms: float = float('inf')
    max_processing_time_ms: float = 0
    processing_times_ms: List[float] = field(default_factory=list)
    
    # LLM usage
    total_llm_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0
    
    # Errors
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Language distribution
    language_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (0-1)."""
        if self.total_queries == 0:
            return 0.0
        return self.successful_queries / self.total_queries
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate (0-1)."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total
    
    @property
    def avg_processing_time_ms(self) -> float:
        """Calculate average processing time."""
        if self.total_queries == 0:
            return 0.0
        return self.total_processing_time_ms / self.total_queries
    
    @property
    def p50_processing_time_ms(self) -> float:
        """Calculate p50 (median) processing time."""
        if not self.processing_times_ms:
            return 0.0
        sorted_times = sorted(self.processing_times_ms)
        return sorted_times[len(sorted_times) // 2]
    
    @property
    def p95_processing_time_ms(self) -> float:
        """Calculate p95 processing time."""
        if not self.processing_times_ms:
            return 0.0
        sorted_times = sorted(self.processing_times_ms)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx]
    
    @property
    def p99_processing_time_ms(self) -> float:
        """Calculate p99 processing time."""
        if not self.processing_times_ms:
            return 0.0
        sorted_times = sorted(self.processing_times_ms)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[idx]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": self.success_rate,
            
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
            
            "processing_time_ms": {
                "avg": self.avg_processing_time_ms,
                "min": self.min_processing_time_ms if self.min_processing_time_ms != float('inf') else 0,
                "max": self.max_processing_time_ms,
                "p50": self.p50_processing_time_ms,
                "p95": self.p95_processing_time_ms,
                "p99": self.p99_processing_time_ms,
            },
            
            "llm_usage": {
                "total_calls": self.total_llm_calls,
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_cost_usd": self.total_cost_usd,
            },
            
            "errors": dict(self.error_counts),
            "languages": dict(self.language_counts),
        }
    
    def to_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Prometheus Format:
        ==================
        # HELP metric_name Description
        # TYPE metric_name metric_type
        metric_name{label="value"} value
        
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        # Query metrics
        lines.append("# HELP query_analyzer_total_queries Total number of queries processed")
        lines.append("# TYPE query_analyzer_total_queries counter")
        lines.append(f"query_analyzer_total_queries {self.total_queries}")
        
        lines.append("# HELP query_analyzer_success_rate Query success rate")
        lines.append("# TYPE query_analyzer_success_rate gauge")
        lines.append(f"query_analyzer_success_rate {self.success_rate}")
        
        # Cache metrics
        lines.append("# HELP query_analyzer_cache_hit_rate Cache hit rate")
        lines.append("# TYPE query_analyzer_cache_hit_rate gauge")
        lines.append(f"query_analyzer_cache_hit_rate {self.cache_hit_rate}")
        
        # Processing time metrics
        lines.append("# HELP query_analyzer_processing_time_ms Query processing time in milliseconds")
        lines.append("# TYPE query_analyzer_processing_time_ms summary")
        lines.append(f'query_analyzer_processing_time_ms{{quantile="0.5"}} {self.p50_processing_time_ms}')
        lines.append(f'query_analyzer_processing_time_ms{{quantile="0.95"}} {self.p95_processing_time_ms}')
        lines.append(f'query_analyzer_processing_time_ms{{quantile="0.99"}} {self.p99_processing_time_ms}')
        
        # LLM metrics
        lines.append("# HELP query_analyzer_llm_tokens Total LLM tokens used")
        lines.append("# TYPE query_analyzer_llm_tokens counter")
        lines.append(f'query_analyzer_llm_tokens{{type="input"}} {self.total_input_tokens}')
        lines.append(f'query_analyzer_llm_tokens{{type="output"}} {self.total_output_tokens}')
        
        lines.append("# HELP query_analyzer_llm_cost_usd Total LLM cost in USD")
        lines.append("# TYPE query_analyzer_llm_cost_usd counter")
        lines.append(f"query_analyzer_llm_cost_usd {self.total_cost_usd}")
        
        return "\n".join(lines)


class MetricsCollector:
    """
    Collect and track metrics for the query analyzer.
    
    Features:
    =========
    - Query processing metrics (success/failure, timing)
    - Cache performance metrics
    - LLM usage and cost tracking
    - Error tracking
    - Language distribution
    
    Thread Safety:
    ==============
    This implementation is NOT thread-safe. For production with multiple
    workers, use a proper metrics backend (Prometheus, StatsD, etc.)
    
    Usage:
    ======
    metrics = MetricsCollector()
    
    # Record a query
    start = time.time()
    try:
        result = analyze_query(query)
        duration_ms = (time.time() - start) * 1000
        
        metrics.record_query_analysis(
            duration_ms=duration_ms,
            success=True,
            cache_hit=False,
            llm_tokens_used=1000,
            language="en"
        )
    except Exception as e:
        metrics.record_error(type(e).__name__, str(e))
    
    # Get summary
    summary = metrics.get_summary()
    print(summary.to_dict())
    """
    
    def __init__(self):
        self.summary = MetricsSummary()
        self.start_time = datetime.now()
    
    def record_query_analysis(
        self,
        duration_ms: float,
        success: bool = True,
        cache_hit: bool = False,
        llm_tokens_used: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        language: Optional[str] = None
    ):
        """
        Record a query analysis event.
        
        Args:
            duration_ms: Processing time in milliseconds
            success: Whether the query was successful
            cache_hit: Whether the result came from cache
            llm_tokens_used: Total tokens used (deprecated, use input/output)
            input_tokens: Input tokens used
            output_tokens: Output tokens used
            cost_usd: Estimated cost in USD
            language: Detected query language
        """
        self.summary.total_queries += 1
        
        if success:
            self.summary.successful_queries += 1
        else:
            self.summary.failed_queries += 1
        
        # Cache metrics
        if cache_hit:
            self.summary.cache_hits += 1
        else:
            self.summary.cache_misses += 1
        
        # Performance metrics
        self.summary.total_processing_time_ms += duration_ms
        self.summary.processing_times_ms.append(duration_ms)
        self.summary.min_processing_time_ms = min(
            self.summary.min_processing_time_ms,
            duration_ms
        )
        self.summary.max_processing_time_ms = max(
            self.summary.max_processing_time_ms,
            duration_ms
        )
        
        # LLM metrics
        if not cache_hit:
            self.summary.total_llm_calls += 1
            self.summary.total_input_tokens += input_tokens
            self.summary.total_output_tokens += output_tokens
            self.summary.total_cost_usd += cost_usd
        
        # Language tracking
        if language:
            self.summary.language_counts[language] += 1
    
    def record_error(self, error_type: str, error_message: str):
        """
        Record an error.
        
        Args:
            error_type: Type of error (e.g., "ValueError", "OpenAIError")
            error_message: Error message
        """
        self.summary.error_counts[error_type] += 1
        self.summary.failed_queries += 1
    
    def get_summary(self) -> MetricsSummary:
        """Get current metrics summary."""
        return self.summary
    
    def reset(self):
        """Reset all metrics."""
        self.summary = MetricsSummary()
        self.start_time = datetime.now()
    
    def export_json(self, filepath: str):
        """
        Export metrics to JSON file.
        
        Args:
            filepath: Path to save JSON file
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "metrics": self.summary.to_dict()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_prometheus(self, filepath: str):
        """
        Export metrics in Prometheus format.
        
        Args:
            filepath: Path to save Prometheus metrics
        """
        prometheus_text = self.summary.to_prometheus()
        
        with open(filepath, 'w') as f:
            f.write(prometheus_text)


# Global metrics collector instance
_global_metrics: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get the global metrics collector instance.
    
    Usage:
    ======
    from query_analyzer_metrics import get_metrics_collector
    
    metrics = get_metrics_collector()
    metrics.record_query_analysis(...)
    """
    global _global_metrics
    
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    
    return _global_metrics


def reset_metrics():
    """Reset the global metrics collector."""
    global _global_metrics
    if _global_metrics is not None:
        _global_metrics.reset()
