"""Web search node for the AI research agent."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from duckduckgo_search import DDGS

from state import AgentState
from models import DocumentationResult, DiscussionResult, SearchError

# Configure logging
logger = logging.getLogger(__name__)


def web_search_node(state: AgentState) -> Dict[str, Any]:
    """
    Searches the web for documentation and discussions.
    
    Uses DuckDuckGo Search (free tier) to find:
    1. Documentation (official docs, guides)
    2. Discussions (Reddit, HackerNews, Twitter/X via Nitter/Google)
    
    Args:
        state: Current agent state
        
    Returns:
        Dict with 'documentation', 'discussions', and optional 'search_errors'
    """
    print(f"\n{'='*50}")
    print("🌐 WEB SEARCH NODE")
    print(f"{'='*50}")
    
    search_categories = state.get("search_categories", [])
    should_search_docs = "documentation" in search_categories
    should_search_discussions = "discussions" in search_categories
    
    if not should_search_docs and not should_search_discussions:
        print("⏭️  Web categories not requested, skipping...")
        return {"documentation": [], "discussions": []}
        
    documentation_results: List[DocumentationResult] = []
    discussion_results: List[DiscussionResult] = []
    errors: List[SearchError] = []
    
    # Use topic filters or query
    topics = state.get("topic_filters", [])
    base_query = " ".join(topics[:3]) if topics else state["query"]
    
    try:
        ddgs = DDGS()
        
        # === 1. DOCUMENTATION SEARCH ===
        if should_search_docs:
            print(f"🔍 Searching Documentation for: '{base_query}'")
            # Add terms to target docs
            doc_query = f"{base_query} documentation tutorial guide"
            
            try:
                results = ddgs.text(doc_query, max_results=5)
                for r in results:
                    doc = DocumentationResult(
                        title=r['title'],
                        url=r['href'],
                        content_snippet=r['body'],
                        source_framework="web"  # Generic source
                    )
                    documentation_results.append(doc)
                print(f"✅ Found {len(documentation_results)} doc pages")
            except Exception as e:
                print(f"❌ Doc Search Error: {e}")
                errors.append(SearchError(
                    source="web_docs",
                    error_message=str(e),
                    timestamp=datetime.now().isoformat()
                ))

        # === 2. DISCUSSIONS SEARCH ===
        if should_search_discussions:
            print(f"🔍 Searching Discussions for: '{base_query}'")
            # Target specific platforms
            # We can do multiple queries or one combined
            # "site:reddit.com OR site:news.ycombinator.com"
            
            # Remove site-specific filtering from the query to get broader results
            discussion_query = f"{base_query} discussion forum blog"
            
            try:
                results = ddgs.text(discussion_query, max_results=5)
                for r in results:
                    # Determine source from URL (for categorization only)
                    source = "web"
                    url = r.get('href', '')
                    if "reddit.com" in url:
                        source = "reddit"
                    elif "ycombinator.com" in url or "news.y" in url:
                        source = "hackernews"
                    
                    # Accept ALL results, not just reddit/HN
                    disc = DiscussionResult(
                        title=r.get('title', 'No title'),
                        url=url,
                        platform=source,
                        content=r.get('body', 'No preview available'),
                        date=datetime.now().strftime("%Y-%m-%d")
                    )
                    discussion_results.append(disc)
                print(f"✅ Found {len(discussion_results)} discussions")
            except Exception as e:
                print(f"❌ Discussion Search Error: {e}")
                errors.append(SearchError(
                    source="web_discussions",
                    error_message=str(e),
                    timestamp=datetime.now().isoformat()
                ))
                
        return {
            "documentation": documentation_results,
            "discussions": discussion_results,
            "search_errors": errors
        }
        
    except Exception as e:
        print(f"❌ Critical Web Search Error: {e}")
        return {
            "documentation": [],
            "discussions": [],
            "search_errors": [SearchError(
                source="web_critical",
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )]
        }
