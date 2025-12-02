"""GitHub search node for the AI research agent."""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from github import Github, Auth
from github.Repository import Repository

from state import AgentState
from models import RepositoryResult, SearchError

# Configure logging
logger = logging.getLogger(__name__)


def github_search_node(state: AgentState) -> Dict[str, Any]:
    """
    Searches for relevant GitHub repositories based on the query and topics.
    
    Features:
    - Authenticated search (if GITHUB_TOKEN is present)
    - Topic-based filtering
    - Sorting by stars/recency
    - Metadata extraction (stars, contributors, description)
    
    Args:
        state: Current agent state
        
    Returns:
        Dict with 'repositories' and optional 'search_errors'
    """
    print(f"\n{'='*50}")
    print("🐙 GITHUB SEARCH NODE")
    print(f"{'='*50}")
    
    # 1. Check if we should search GitHub
    search_categories = state.get("search_categories", [])
    if "repositories" not in search_categories and "code" not in search_categories:
        print("⏭️  Repositories not in search_categories, skipping...")
        return {"repositories": [], "search_errors": []}
    
    # 2. Setup GitHub Client
    token = os.getenv("GITHUB_TOKEN")
    if token:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        print("🔐 Authenticated with GITHUB_TOKEN")
    else:
        g = Github()
        print("⚠️  No GITHUB_TOKEN found, using unauthenticated rate limits (60/hr)")
        
    try:
        # 3. Build Query
        # We use topic_filters if available, otherwise the normalized query
        topics = state.get("topic_filters", [])
        query_normalized = state.get("query_normalized", state["query"])
        
        # Construct a search query optimized for GitHub
        # Format: "topic1 topic2 in:readme in:description language:python"
        
        search_terms = []
        if topics:
            # Use top 2 topics only to avoid over-constraining
            search_terms.extend(topics[:2])
        else:
            # Use first 2-3 words from query
            query_words = query_normalized.split()[:2]
            search_terms.extend(query_words)
        
        # Relax quality filter even more (10 stars is still too high for new repos)
        search_terms.append("stars:>5")
        
        final_query = " ".join(search_terms)
        print(f"🔍 GitHub Query: '{final_query}'")
        
        # 4. Execute Search
        # Sort by stars by default, or updated if looking for "news"
        sort_by = "stars"
        if state.get("date_range") in ["24h", "week"]:
            sort_by = "updated"
            
        print(f"⏳ Searching GitHub (sort={sort_by})...")
        
        repos = g.search_repositories(
            query=final_query,
            sort=sort_by,
            order="desc"
        )
        
        # 5. Process Results
        results: List[RepositoryResult] = []
        max_results = 10
        
        # Iterate (this triggers the API call)
        count = 0
        for repo in repos:
            if count >= max_results:
                break
                
            # Filter by date if needed (client-side double check)
            if state.get("date_range") == "week":
                last_update = repo.updated_at
                # Make both timezone-aware for comparison
                from datetime import timezone
                now = datetime.now(timezone.utc)
                if now - last_update > timedelta(weeks=1):
                    continue
            
            # Convert to RepositoryResult
            repo_result: RepositoryResult = {
                "name": repo.full_name,
                "url": repo.html_url,
                "description": repo.description or "No description",
                "author": repo.owner.login,
                "contributors_count": 0, # Expensive to fetch, skip for now or fetch if critical
                "stars": repo.stargazers_count,
                "last_updated": repo.updated_at.strftime("%Y-%m-%d")
            }
            results.append(repo_result)
            count += 1
            
        print(f"✅ Found {len(results)} repositories")
        if results:
            print(f"   • Top repo: {results[0]['name']} ({results[0]['stars']} ⭐)")
            
        return {"repositories": results, "search_errors": []}
        
    except Exception as e:
        print(f"❌ GitHub Search Error: {e}")
        error = SearchError(
            source="github",
            error_message=str(e),
            timestamp=datetime.now().isoformat()
        )
        return {
            "repositories": [],
            "search_errors": [error]
        }
    finally:
        g.close()
