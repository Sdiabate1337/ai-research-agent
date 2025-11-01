"""Main graph definition for the AI research agent."""

from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import research_node, analysis_node, output_node


def create_research_graph() -> StateGraph:
    """
    Create and configure the research agent graph.
    
    Returns:
        Configured StateGraph instance
    """
    # Initialize the graph with the state schema
    workflow = StateGraph(AgentState)
    
    # Add nodes to the graph
    workflow.add_node("research", research_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("output", output_node)
    
    # Define the flow
    workflow.set_entry_point("research")
    workflow.add_edge("research", "analysis")
    workflow.add_edge("analysis", "output")
    workflow.add_edge("output", END)
    
    # Compile the graph
    return workflow.compile()


# Create the graph instance
research_graph = create_research_graph()
