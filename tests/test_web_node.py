"""Tests for the Web search node."""

import unittest
from unittest.mock import MagicMock, patch
from src.web_node import web_search_node
from src.state import AgentState

class TestWebNode(unittest.TestCase):
    
    def setUp(self):
        self.mock_state: AgentState = {
            "query": "test query",
            "query_normalized": "test query normalized",
            "search_categories": ["documentation", "discussions"],
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

    @patch("src.web_node.DDGS")
    def test_web_search_success(self, mock_ddgs_class):
        # Setup mock
        mock_ddgs_instance = MagicMock()
        mock_ddgs_class.return_value = mock_ddgs_instance
        
        # Mock results
        mock_ddgs_instance.text.side_effect = [
            # Documentation results
            [{"title": "Doc Title", "href": "https://docs.example.com", "body": "Doc Body"}],
            # Discussion results
            [{"title": "Reddit Thread", "href": "https://reddit.com/r/ai", "body": "Discussion Body"}]
        ]
        
        # Run node
        result = web_search_node(self.mock_state)
        
        # Verify Documentation
        self.assertIn("documentation", result)
        self.assertEqual(len(result["documentation"]), 1)
        doc = result["documentation"][0]
        self.assertEqual(doc.title, "Doc Title")
        self.assertEqual(doc.url, "https://docs.example.com")
        
        # Verify Discussions
        self.assertIn("discussions", result)
        self.assertEqual(len(result["discussions"]), 1)
        disc = result["discussions"][0]
        self.assertEqual(disc.title, "Reddit Thread")
        self.assertEqual(disc.platform, "reddit")

    @patch("src.web_node.DDGS")
    def test_skip_categories(self, mock_ddgs_class):
        self.mock_state["search_categories"] = ["papers"] # No web categories
        
        result = web_search_node(self.mock_state)
        
        self.assertEqual(result["documentation"], [])
        self.assertEqual(result["discussions"], [])
        mock_ddgs_class.assert_not_called()

    @patch("src.web_node.DDGS")
    def test_error_handling(self, mock_ddgs_class):
        mock_ddgs_instance = MagicMock()
        mock_ddgs_class.return_value = mock_ddgs_instance
        mock_ddgs_instance.text.side_effect = Exception("DDG Error")
        
        result = web_search_node(self.mock_state)
        
        # Should return empty lists but log error in search_errors
        self.assertEqual(result["documentation"], [])
        self.assertEqual(result["discussions"], [])
        
        # Check if error was captured (if implementation supports partial failure)
        # In our implementation, if docs fail, discussions might still run or fail.
        # But here we mocked side_effect for the first call.
        
        self.assertIn("search_errors", result)
        # Access attribute .source (Pydantic model)
        self.assertEqual(result["search_errors"][0].source, "web_docs")

if __name__ == "__main__":
    unittest.main()
