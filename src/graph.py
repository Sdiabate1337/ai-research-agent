"""LangGraph graph definition for the AI research agent."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import query_analyzer_node, papers_search_node


def create_research_agent_graph():
    """
    Crée le graph de l'agent de recherche.
    
    Flow actuel:
    START → analyze_query → search_papers → END
    
    Le graph:
    1. Analyse la query utilisateur
    2. Recherche des papers sur ArXiv
    3. Retourne les résultats
    
    Returns:
        Compiled graph prêt à être exécuté
    """
    
    # Créer le graph avec notre state
    graph = StateGraph(AgentState)
    
    # Ajouter les nodes
    # Note: Le nom du node (1er argument) peut être différent de la fonction
    graph.add_node("analyze_query", query_analyzer_node)
    graph.add_node("search_papers", papers_search_node)
    
    # Définir le point d'entrée
    graph.set_entry_point("analyze_query")
    
    # Définir les connexions (edges)
    # analyze_query → search_papers
    graph.add_edge("analyze_query", "search_papers")
    
    # search_papers → END
    graph.add_edge("search_papers", END)
    
    # Compiler le graph
    app = graph.compile()
    
    return app


# Fonction helper pour exécuter facilement
def run_research_agent(query: str, date_range: str = "week") -> Dict[str, Any]:
    """
    Exécute l'agent de recherche avec une query simple.
    
    Args:
        query: La question de recherche
        date_range: Période de recherche ("24h", "week", "month")
        
    Returns:
        State final avec les résultats
        
    Example:
        >>> results = run_research_agent("What's new in LangGraph?")
        >>> print(f"Found {len(results['papers'])} papers")
    """
    
    # Créer le graph
    app = create_research_agent_graph()
    
    # État initial (minimal)
    initial_state = {
        "query": query,
        "search_categories": None,  # L'analyzer décidera
        "date_range": date_range,
        "topic_filters": None,  # L'analyzer extraira
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
    
    # Exécuter le graph
    print("🚀 Démarrage de l'agent de recherche...\n")
    final_state = app.invoke(initial_state)
    
    return final_state