"""LangGraph graph definition for the AI research agent."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state import AgentState

# Import nodes
from query_analyzer_node_v2 import query_analyzer_node_v2
from nodes import papers_search_node
from github_node import github_search_node
from web_node import web_search_node
from curator_node import curator_node
from reporter_node import reporter_node


def create_research_agent_graph():
    """
    Creates the research agent graph.
    
    Flow:
    1. analyze_query: Understand intent and select sources
    2. Parallel Search:
       - search_papers (ArXiv)
       - search_github (GitHub)
       - search_web (DuckDuckGo)
    3. curator: Deduplicate and rank results
    4. reporter: Synthesize findings
    """
    
    # Create graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("analyze_query", query_analyzer_node_v2)
    graph.add_node("search_papers", papers_search_node)
    graph.add_node("search_github", github_search_node)
    graph.add_node("search_web", web_search_node)
    graph.add_node("curator", curator_node)
    graph.add_node("reporter", reporter_node)
    
    # Define entry point
    graph.set_entry_point("analyze_query")
    
    # Define edges
    # From analyzer, we go to all search nodes in parallel
    # LangGraph executes parallel branches if they share the same start node
    graph.add_edge("analyze_query", "search_papers")
    graph.add_edge("analyze_query", "search_github")
    graph.add_edge("analyze_query", "search_web")
    
    # All search nodes go to curator
    graph.add_edge("search_papers", "curator")
    graph.add_edge("search_github", "curator")
    graph.add_edge("search_web", "curator")
    
    # Curator goes to reporter
    graph.add_edge("curator", "reporter")
    
    # Reporter ends the flow
    graph.add_edge("reporter", END)
    
    # Compile
    app = graph.compile()
    
    return app


def run_research_agent(query: str, date_range: str = "week") -> Dict[str, Any]:
    """
    Executes the research agent with a simple query.
    
    Args:
        query: Research question
        date_range: Time filter ("24h", "week", "month")
        
    Returns:
        Final state with results and report
    """
    
    app = create_research_agent_graph()
    
    initial_state = {
        "query": query,
        "date_range": date_range,
        # Initialize empty lists to avoid key errors if nodes skip
        "search_categories": [],
        "topic_filters": [],
        "papers": [],
        "repositories": [],
        "documentation": [],
        "discussions": [],
        "ranked_results": [],
        "summary_by_category": None,
        "key_insights": [],
        "action_items": [],
        "total_results_found": 0,
        "search_errors": []
    }
    
    print(f"🚀 Starting Research Agent: '{query}' ({date_range})\n")
    final_state = app.invoke(initial_state)
    
    return final_state