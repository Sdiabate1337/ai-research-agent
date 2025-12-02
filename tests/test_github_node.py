"""Tests for the GitHub search node."""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.github_node import github_search_node
from src.state import AgentState

class TestGithubNode(unittest.TestCase):
    
    def setUp(self):
        self.mock_state: AgentState = {
            "query": "test query",
            "query_normalized": "test query normalized",
            "search_categories": ["repositories"],
            "topic_filters": ["topic1", "topic2"],
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

    @patch("src.github_node.Github")
    def test_github_search_success(self, mock_github_class):
        # Setup mock
        mock_github_instance = MagicMock()
        mock_github_class.return_value = mock_github_instance
        
        mock_repo = MagicMock()
        mock_repo.full_name = "owner/repo"
        mock_repo.html_url = "https://github.com/owner/repo"
        mock_repo.description = "Test repo"
        mock_repo.owner.login = "owner"
        mock_repo.stargazers_count = 100
        mock_repo.updated_at = datetime.now()
        
        mock_github_instance.search_repositories.return_value = [mock_repo]
        
        # Run node
        result = github_search_node(self.mock_state)
        
        # Verify
        self.assertIn("repositories", result)
        self.assertEqual(len(result["repositories"]), 1)
        repo = result["repositories"][0]
        self.assertEqual(repo["name"], "owner/repo")
        self.assertEqual(repo["stars"], 100)
        
        # Verify query construction
        # Expected: "topic1 topic2 stars:>50"
        mock_github_instance.search_repositories.assert_called_once()
        call_args = mock_github_instance.search_repositories.call_args
        self.assertIn("topic1", call_args.kwargs['query'])
        self.assertIn("stars:>50", call_args.kwargs['query'])

    @patch("src.github_node.Github")
    def test_skip_if_category_missing(self, mock_github_class):
        self.mock_state["search_categories"] = ["papers"]
        
        result = github_search_node(self.mock_state)
        
        self.assertEqual(result["repositories"], [])
        mock_github_class.assert_not_called()

    @patch("src.github_node.Github")
    def test_error_handling(self, mock_github_class):
        mock_github_instance = MagicMock()
        mock_github_class.return_value = mock_github_instance
        mock_github_instance.search_repositories.side_effect = Exception("API Error")
        
        result = github_search_node(self.mock_state)
        
        self.assertEqual(result["repositories"], [])
        self.assertIn("search_errors", result)
        # SearchError is a Pydantic model, so we access attributes
        self.assertEqual(result["search_errors"][0].source, "github")
        self.assertIn("API Error", result["search_errors"][0].error_message)

if __name__ == "__main__":
    unittest.main()
