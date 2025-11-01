"""Node functions for the AI research agent graph."""

from typing import Dict, Any
from .state import AgentState
from .tools import search_papers, search_web


def research_node(state: AgentState) -> Dict[str, Any]:
    """
    Research node that gathers information about AI agents.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with research results
    """
    query = state["query"]
    messages = state.get("messages", [])
    
    # Perform research using available tools
    papers = search_papers(query)
    web_results = search_web(query)
    
    research_results = {
        "papers": papers,
        "web_results": web_results
    }
    
    messages.append(f"Completed research for query: {query}")
    
    return {
        "messages": messages,
        "research_results": [research_results]
    }


def analysis_node(state: AgentState) -> Dict[str, Any]:
    """
    Analysis node that processes and analyzes research results.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with analysis
    """
    research_results = state.get("research_results", [])
    messages = state.get("messages", [])
    
    # Placeholder analysis logic
    analysis = f"Analyzed {len(research_results)} research result(s)"
    
    messages.append("Completed analysis of research results")
    
    return {
        "messages": messages,
        "analysis": analysis
    }


def output_node(state: AgentState) -> Dict[str, Any]:
    """
    Output node that formats the final results.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with formatted output
    """
    query = state["query"]
    analysis = state.get("analysis", "No analysis available")
    messages = state.get("messages", [])
    
    # Format output
    output = f"""
Research Query: {query}

Analysis:
{analysis}

Status: Complete
"""
    
    messages.append("Generated final output")
    
    return {
        "messages": messages,
        "output": output
    }
