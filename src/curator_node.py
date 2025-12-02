"""Curator node for the AI research agent."""

import logging
from typing import Dict, Any, List, Set
from datetime import datetime

from state import AgentState
from models import RankedResult, PaperResult, RepositoryResult, DocumentationResult, DiscussionResult

# Configure logging
logger = logging.getLogger(__name__)


def curator_node(state: AgentState) -> Dict[str, Any]:
    """
    Curates, deduplicates, and ranks results from all sources.
    
    Tasks:
    1. Deduplicate results (by URL/Title)
    2. Convert all results to unified RankedResult format
    3. Calculate relevance scores
    4. Sort by relevance and date
    5. Limit total results
    
    Args:
        state: Current agent state
        
    Returns:
        Dict with 'ranked_results' and 'total_results_found'
    """
    print(f"\n{'='*50}")
    print("🧐 CURATOR NODE")
    print(f"{'='*50}")
    
    # Collect all results
    papers = state.get("papers", [])
    repos = state.get("repositories", [])
    docs = state.get("documentation", [])
    discussions = state.get("discussions", [])
    
    total_raw = len(papers) + len(repos) + len(docs) + len(discussions)
    print(f"📥 Processing {total_raw} raw results...")
    
    ranked_results: List[RankedResult] = []
    seen_urls: Set[str] = set()
    
    # Helper to add result if unique
    def add_result(source_type: str, item: Any, title: str, url: str, date: str, summary: str, score: float):
        if url in seen_urls:
            return
        seen_urls.add(url)
        
        ranked_results.append(RankedResult(
            type=source_type,
            title=title,
            url=url,
            date=date,
            summary=summary,
            relevance_score=score,
            source_metadata=item if isinstance(item, dict) else item.model_dump()
        ))

    # 1. Process Papers
    for p in papers:
        # Papers: Normalize relevance_score to 0.7-0.95 range
        # (to not always dominate other sources)
        raw_score = p.get('relevance_score', 0.8) if isinstance(p, dict) else getattr(p, 'relevance_score', 0.8)
        if raw_score > 1.0:
            raw_score = raw_score / 100.0  # Normalize if 0-100
        # Scale to 0.5-0.85 to allow other sources to compete
        # (Docs are 0.85, High-star repos can go up to 0.95)
        score = 0.5 + (raw_score * 0.35)
        
        if isinstance(p, dict):
            title = p['title']
            url = p['url']
            date = p['published_date']
            summary = p.get('abstract', '')[:200] + "..."
        else:
            title = p.title
            url = p.url
            date = p.published_date
            summary = p.summary[:200] + "..."
            
        add_result("paper", p, title, url, date, summary, score)

    # 2. Process Repositories
    for r in repos:
        # Repos: Score based on stars with better scaling
        stars = r['stars'] if isinstance(r, dict) else r.stars
        # Logarithmic scale: 10 stars = 0.5, 100 = 0.7, 1000 = 0.85, 10k+ = 0.95
        import math
        if stars > 0:
            score = min(0.5 + (math.log10(stars) / 4.0) * 0.45, 0.95)
        else:
            score = 0.5
        
        if isinstance(r, dict):
            title = r['name']
            url = r['url']
            date = r['last_updated']
            summary = r['description']
        else:
            title = r.name
            url = r.url
            date = r.updated_at
            summary = r.description
            
        add_result("repository", r, title, url, date, summary, score)

    # 3. Process Documentation
    for d in docs:
        score = 0.85 # Docs are usually relevant if found
        
        if isinstance(d, dict):
            title = d['name']
            url = d['url']
            summary = d.get('description', '')
            date = datetime.now().strftime("%Y-%m-%d") # Docs often lack date
        else:
            title = d.title
            url = d.url
            summary = d.content_snippet
            date = datetime.now().strftime("%Y-%m-%d")
            
        add_result("documentation", d, title, url, date, summary, score)

    # 4. Process Discussions
    for d in discussions:
        score = 0.6 # Discussions are noisy
        
        if isinstance(d, dict):
            title = d['title']
            url = d['url']
            summary = d.get('source', 'web')
            date = d['date']
        else:
            title = d.title
            url = d.url
            summary = f"Discussion on {d.platform}"
            date = d.date
            
        add_result("discussion", d, title, url, date, summary, score)

    # Sort by score (desc)
    ranked_results.sort(key=lambda x: x.relevance_score, reverse=True)
    
    # Diversity Guarantee: Ensure we have at least 2 results from each category if available
    final_selection = []
    categories = ["paper", "repository", "documentation", "discussion"]
    selected_indices = set()
    
    # 1. Pick top 2 from each category
    for cat in categories:
        count = 0
        for i, res in enumerate(ranked_results):
            if res.type == cat and i not in selected_indices:
                final_selection.append(res)
                selected_indices.add(i)
                count += 1
                if count >= 2:  # Guarantee 2 per category
                    break
    
    # 2. Fill the rest up to 20 with highest scoring remaining
    for i, res in enumerate(ranked_results):
        if len(final_selection) >= 20:
            break
        if i not in selected_indices:
            final_selection.append(res)
            selected_indices.add(i)
            
    # Re-sort final selection by score for display
    final_selection.sort(key=lambda x: x.relevance_score, reverse=True)
    
    ranked_results = final_selection
    
    print(f"✅ Curated {len(ranked_results)} unique results")
    if ranked_results:
        print(f"   • Top result: [{ranked_results[0].type}] {ranked_results[0].title}")
        
    return {
        "ranked_results": ranked_results,
        "total_results_found": total_raw
    }
