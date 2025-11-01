"""State schema for the AI research agent graph."""

from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    """
    State schema for the research agent workflow.
    
    Attributes:
        query: The research query or topic
        messages: List of messages exchanged during the workflow
        research_results: Collected research findings
        analysis: Analysis of the research results
        output: Final formatted output
    """
    query: str
    messages: List[str]
    research_results: Optional[List[dict]]
    analysis: Optional[str]
    output: Optional[str]
