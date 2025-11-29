"""State schema for the AI research agent graph."""

from typing import TypedDict, List, Optional
from typing_extensions import Annotated
import operator
from models import (
    PaperResult,
    RepositoryResult,
    DocumentationResult,
    DiscussionResult,
    RankedResult,
    CategorySummary,
    Insight,
    Action,
    SearchError
)


class AgentState(TypedDict):
    """
    State schema for the research agent workflow.
    
    Attributes:
        query: The user's research question
        search_categories: Which sources to search (optional)
        date_range: Time filter for results (default: "week")
        topic_filters: Keywords to filter by (optional)
        
        papers/repositories/documentation/discussions: Raw search results
        
        ranked_results: All results ranked by relevance and date
        summary_by_category: Summarized findings per category
        key_insights: Main takeaways
        action_items: Recommended next steps
        
        total_results_found: Count of all results across sources
        search_errors: Any errors encountered during search
        
        Query Analyzer Metadata (NEW):
        query_normalized: Normalized version of query
        query_language: Detected language code (en, fr, ar)
        query_processing_time_ms: Time taken to analyze query
        query_cache_hit: Whether result came from cache
        query_confidence_score: Confidence in analysis (0-1)
        llm_tokens_used: Total LLM tokens consumed
        llm_cost_usd: Estimated cost in USD
    """
    
    # === INPUT FIELDS (always present) ===
    query: str
    search_categories: Optional[List[str]]  # ["papers", "code", "docs", "news"]
    date_range: str  # "24h", "week", "month"
    topic_filters: Optional[List[str]]  # ["langgraph", "memory", "tools"]
    
    # === RAW RESULTS (replaced on each search) ===
    papers: List[PaperResult]
    repositories: List[RepositoryResult]
    documentation: List[DocumentationResult]
    discussions: List[DiscussionResult]
    
    # === PROCESSED RESULTS (computed later) ===
    ranked_results: Optional[List[RankedResult]]
    summary_by_category: Optional[CategorySummary]
    key_insights: Optional[List[Insight]]
    action_items: Optional[List[Action]]
    
    # === OUTPUT FIELDS (updated during workflow) ===
    total_results_found: Optional[int]
    
    # Using typing.Annotated with operator.add to combine lists from parallel nodes
    search_errors: Annotated[Optional[List[SearchError]], operator.add]
    
    # === QUERY ANALYZER METADATA (NEW) ===
    query_normalized: Optional[str]
    query_language: Optional[str]  # "en", "fr", "ar"
    query_processing_time_ms: Optional[int]
    query_cache_hit: Optional[bool]
    query_confidence_score: Optional[float]
    llm_tokens_used: Optional[int]
    llm_cost_usd: Optional[float]