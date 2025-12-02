"""Test manuel du papers search node."""
import sys
sys.path.insert(0, 'src')

from nodes import papers_search_node

# État de test
test_state = {
    "query": "What's new in LangGraph?",
    "search_categories": ["papers"],
    "date_range": "week",
    "topic_filters": ["langgraph", "agents"],
    "papers": [],
    "repositories": [],
    "documentation": [],
    "discussions": [],
    "ranked_results": None,
    "summary_by_category": None,
    "key_insights": None,
    "action_items": None,
    "total_results_found": None,
    "search_errors": None
}

print("🧪 Test du Papers Search Node\n")
result = papers_search_node(test_state)

print("\n📋 Résultats:")
print(f"Nombre de papers: {len(result['papers'])}")

if result['papers']:
    print("\n📄 Premier paper:")
    paper = result['papers'][0]
    print(f"   Titre: {paper['title']}")
    print(f"   Auteurs: {', '.join(paper['authors'][:3])}")
    print(f"   Date: {paper['published_date']}")
    print(f"   URL: {paper['url']}")
    print(f"   Abstract: {paper['abstract'][:200]}...")