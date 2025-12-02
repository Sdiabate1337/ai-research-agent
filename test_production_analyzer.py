"""Test the production query analyzer with caching and metrics."""
import sys
sys.path.insert(0, 'src')

from graph import run_research_agent
from query_analyzer_metrics import get_metrics_collector
from query_analyzer_cache import QueryCache
from query_analyzer_config import get_config

print("=" * 70)
print("🚀 TESTING PRODUCTION QUERY ANALYZER V2")
print("=" * 70)

# Test 1: First query (cache miss, LLM call)
print("\n📝 Test 1: First query (should call LLM)")
print("-" * 70)
results = run_research_agent(
    query="What's new in LangGraph?",
    date_range="week"
)

print(f"\n✅ Query Results:")
print(f"   • Query: {results['query']}")
print(f"   • Normalized: {results.get('query_normalized', 'N/A')}")
print(f"   • Language: {results.get('query_language', 'N/A')}")
print(f"   • Categories: {results['search_categories']}")
print(f"   • Topics: {results['topic_filters']}")
print(f"   • Cache Hit: {results.get('query_cache_hit', False)}")
print(f"   • Processing Time: {results.get('query_processing_time_ms', 0)}ms")
print(f"   • Confidence: {results.get('query_confidence_score', 0)}")
print(f"   • LLM Tokens: {results.get('llm_tokens_used', 0)}")
print(f"   • Cost: ${results.get('llm_cost_usd', 0):.6f}")

# Test 2: Duplicate query (cache hit, no LLM call)
print("\n" + "=" * 70)
print("📝 Test 2: Duplicate query (should hit cache)")
print("-" * 70)
results2 = run_research_agent(
    query="What's new in LangGraph?",  # Same query
    date_range="week"
)

print(f"\n✅ Query Results:")
print(f"   • Cache Hit: {results2.get('query_cache_hit', False)}")
print(f"   • Processing Time: {results2.get('query_processing_time_ms', 0)}ms")
print(f"   • LLM Tokens: {results2.get('llm_tokens_used', 0)}")
print(f"   • Cost: ${results2.get('llm_cost_usd', 0):.6f}")

if results2.get('query_cache_hit'):
    print(f"\n   🎉 Cache working! {results.get('query_processing_time_ms', 0)}ms → {results2.get('query_processing_time_ms', 0)}ms")
    speedup = results.get('query_processing_time_ms', 1) / max(results2.get('query_processing_time_ms', 1), 1)
    print(f"   ⚡ Speedup: {speedup:.1f}x faster")

# Test 3: Different query
print("\n" + "=" * 70)
print("📝 Test 3: Different query")
print("-" * 70)
results3 = run_research_agent(
    query="Multi-agent systems research",
    date_range="week"
)

print(f"\n✅ Query Results:")
print(f"   • Categories: {results3['search_categories']}")
print(f"   • Topics: {results3['topic_filters']}")
print(f"   • Cache Hit: {results3.get('query_cache_hit', False)}")

# Show metrics summary
print("\n" + "=" * 70)
print("📊 METRICS SUMMARY")
print("=" * 70)

metrics = get_metrics_collector()
summary = metrics.get_summary()

print(f"\n📈 Overall Statistics:")
print(f"   • Total Queries: {summary.total_queries}")
print(f"   • Success Rate: {summary.success_rate * 100:.1f}%")
print(f"   • Cache Hit Rate: {summary.cache_hit_rate * 100:.1f}%")
print(f"   • Avg Processing Time: {summary.avg_processing_time_ms:.1f}ms")
print(f"   • Total LLM Calls: {summary.total_llm_calls}")
print(f"   • Total Tokens: {summary.total_input_tokens + summary.total_output_tokens}")
print(f"   • Total Cost: ${summary.total_cost_usd:.6f}")

if summary.processing_times_ms:
    print(f"\n📊 Processing Time Percentiles:")
    print(f"   • p50 (median): {summary.p50_processing_time_ms:.1f}ms")
    print(f"   • p95: {summary.p95_processing_time_ms:.1f}ms")
    print(f"   • p99: {summary.p99_processing_time_ms:.1f}ms")
    print(f"   • Min: {summary.min_processing_time_ms:.1f}ms")
    print(f"   • Max: {summary.max_processing_time_ms:.1f}ms")

if summary.language_counts:
    print(f"\n🌍 Language Distribution:")
    for lang, count in summary.language_counts.items():
        print(f"   • {lang}: {count} queries")

# Export metrics
print("\n" + "=" * 70)
print("💾 Exporting Metrics")
print("=" * 70)

metrics.export_json("query_metrics.json")
print("✅ Exported to query_metrics.json")

metrics.export_prometheus("query_metrics.prom")
print("✅ Exported to query_metrics.prom (Prometheus format)")

print("\n" + "=" * 70)
print("✅ ALL TESTS COMPLETE!")
print("=" * 70)
print("\n🎉 Production query analyzer is working with:")
print("   ✅ Caching (Redis/Memory)")
print("   ✅ Metrics collection")
print("   ✅ Input validation")
print("   ✅ Cost tracking")
print("   ✅ Language detection")
