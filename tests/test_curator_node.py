"""Tests for the Curator node."""

import unittest
from src.curator_node import curator_node
from src.state import AgentState
from models import PaperResult, RepositoryResult, DocumentationResult, DiscussionResult

class TestCuratorNode(unittest.TestCase):
    
    def setUp(self):
        self.mock_state: AgentState = {
            "query": "test query",
            "query_normalized": "test query normalized",
            "search_categories": ["papers", "repositories", "documentation"],
            "topic_filters": [],
            "date_range": "week",
            "papers": [],
            "repositories": [],
            "documentation": [],
            "discussions": [],
            "ranked_results": [],
            "summary_by_category": None,
            "key_insights": [],
            "action_items": [],
            "total_results_found": 0,
            "search_errors": [],
            "query_language": "en",
            "query_processing_time_ms": 100,
            "query_cache_hit": False,
            "query_confidence_score": 0.9,
            "llm_tokens_used": 0,
            "llm_cost_usd": 0.0
        }

    def test_curation_logic(self):
        # Setup mock data
        
        # 1. Paper
        paper = PaperResult(
            title="Paper 1",
            authors=["Author A"],
            summary="Summary 1",
            url="http://arxiv.org/1",
            published_date="2025-01-01",
            source="arxiv",
            relevance_score=0.9
        )
        self.mock_state["papers"] = [paper]
        
        # 2. Repo
        repo = RepositoryResult(
            name="Repo 1",
            description="Desc 1",
            language="Python",
            stars=1000,
            url="http://github.com/1",
            updated_at="2025-01-01"
        )
        self.mock_state["repositories"] = [repo]
        
        # 3. Duplicate URL (should be deduped)
        doc = DocumentationResult(
            title="Doc 1",
            content_snippet="Snippet 1",
            url="http://github.com/1", # Same URL as repo
            source_framework="web"
        )
        self.mock_state["documentation"] = [doc]
        
        # Run node
        result = curator_node(self.mock_state)
        
        # Verify
        ranked = result["ranked_results"]
        self.assertEqual(len(ranked), 2) # Should be 2 because Doc 1 is duplicate URL of Repo 1
        
        # Check ranking (Paper 0.9 vs Repo ~0.6)
        self.assertEqual(ranked[0].type, "paper")
        self.assertEqual(ranked[1].type, "repository")
        
        self.assertEqual(result["total_results_found"], 3)

    def test_empty_input(self):
        result = curator_node(self.mock_state)
        self.assertEqual(len(result["ranked_results"]), 0)
        self.assertEqual(result["total_results_found"], 0)

if __name__ == "__main__":
    unittest.main()
