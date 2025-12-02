"""Test manuel du graph complet."""
import sys
sys.path.insert(0, 'src')

from graph import run_research_agent

print("="*60)
print("🤖 TEST DU GRAPH COMPLET")
print("="*60)

# Test 1: Query simple
print("\n📝 Test 1: Query simple\n")
results = run_research_agent(
    query="What's new in RAG architecture?",
    date_range="week"
)

print("\n" + "="*60)
print("📊 RÉSULTATS FINAUX")
print("="*60)
print(f"Query: {results['query']}")
print(f"Date range: {results['date_range']}")
print(f"Categories: {results['search_categories']}")
print(f"Topics: {results['topic_filters']}")
print(f"\n📚 Papers trouvés: {len(results['papers'])}")

if results['papers']:
    print("\n📄 Top 3 papers:")
    for i, paper in enumerate(results['papers'][:3], 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Auteurs: {', '.join(paper['authors'][:2])}")
        print(f"   Date: {paper['published_date']}")
        print(f"   URL: {paper['url']}")
        print(f"   Abstract: {paper['abstract'][:150]}...")

print("\n" + "="*60)
print("✅ Test terminé!")
print("="*60)