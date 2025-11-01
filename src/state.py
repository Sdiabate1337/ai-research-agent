"""State schema for the AI research agent graph."""

from typing import TypedDict, List, Optional

class PaperResult(TypedDict):
    title: str
    authors: List[str]
    url: str
    abstract: str
    published_date: str
    arxiv_id: str
    category: List[str]


class RepositoryResult(TypedDict):
    name: str
    url: str
    description: str
    author: str
    contributors_count: int
    stars: int
    last_updated: str

class DocumentationResult(TypedDict):
    name: str
    url: str
    sources: str
    description: str
    language: str

class DiscussionResult(TypedDict):
    title: str
    url: str
    source: str  # "reddit", "hackernews", "twitter"
    author: str
    comment_count: str
    date: str   

class CategorySummary(TypedDict):
    papers: str
    repositories: str
    documentation: str
    discussions: str     

class RankedResult(TypedDict):
    source_type: str  # "paper", "repository", etc.
    title: str
    url: str
    confidence_score: float
    published_date: str
    summary: str

class Insight(TypedDict):
    text: str
    confidence: float
    related_sources: List[str]    

class Action(TypedDict):
    text: str

class SearchError(TypedDict):
    """Track errors during search operations."""
    source: str  # Which search failed?
    error_message: str
    timestamp: str    


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
    """

    # === INPUT FIELDS (always present) ===
    query: str
    search_categories: Optional[List[str]]  # ["papers", "code", "docs", "news"]
    date_range: str  # "24h", "week", "month"
    topic_filters: Optional[List[str]] # ["langgraph", "memory", "tools"]
    
    # === RAW RESULTS (replaced on each search) ===
    papers: List[PaperResult]  # NOT List[dict]!
    repositories: List[RepositoryResult]
    documentation: List[DocumentationResult]
    discussions: List[DiscussionResult]
    
    # === PROCESSED RESULTS (computed later) ===
    ranked_results: Optional[List[RankedResult]]
    summary_by_category: Optional[CategorySummary]
    key_insights: Optional[List[Insight]]
    action_items: Optional[List[Action]]  # "Read paper X", "Try tool Y"

    # === METADATA ===
    total_results_found: Optional[int]
    search_errors: Optional[List[SearchError]]

