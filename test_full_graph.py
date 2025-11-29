"""End-to-end test for the full research agent graph."""

import unittest
from unittest.mock import MagicMock, patch
from src.graph import create_research_agent_graph
from src.state import AgentState
from src.models import PaperResult, RepositoryResult, DocumentationResult, DiscussionResult

class TestFullGraph(unittest.TestCase):
    
    @patch("src.graph.query_analyzer_node_v2")
    @patch("src.graph.papers_search_node")
    @patch("src.graph.github_search_node")
    @patch("src.graph.web_search_node")
    @patch("src.graph.curator_node")
    @patch("src.graph.reporter_node")
    def test_graph_execution_flow(self, mock_reporter, mock_curator, mock_web, mock_github, mock_papers, mock_analyzer):
        # Setup mocks to return valid state updates
        
        # 1. Analyzer
        mock_analyzer.return_value = {
            "search_categories": ["papers", "repositories", "documentation"],
            "topic_filters": ["topic1"],
            "query_normalized": "normalized query"
        }
        
        # 2. Search Nodes
        mock_papers.return_value = {"papers": [MagicMock()]}
        mock_github.return_value = {"repositories": [MagicMock()]}
        mock_web.return_value = {"documentation": [MagicMock()], "discussions": []}
        
        # 3. Curator
        mock_curator.return_value = {
            "ranked_results": [MagicMock()],
            "total_results_found": 3
        }
        
        # 4. Reporter
        mock_reporter.return_value = {
            "key_insights": [],
            "summary_by_category": {},
            "action_items": []
        }
        
        # Create and run graph
        app = create_research_agent_graph()
        
        initial_state = {
            "query": "test query",
            "date_range": "week",
            "search_categories": [],
            "topic_filters": [],
            "papers": [],
            "repositories": [],
            "documentation": [],
            "discussions": [],
            "ranked_results": [],
            "summary_by_category": None,
            "key_insights": [],
            "action_items": [],
            "total_results_found": 0,
            "search_errors": []
        }
        
        result = app.invoke(initial_state)
        
        # Verify all nodes were called
        mock_analyzer.assert_called_once()
        mock_papers.assert_called_once()
        mock_github.assert_called_once()
        mock_web.assert_called_once()
        mock_curator.assert_called_once()
        mock_reporter.assert_called_once()
        
        # Verify result contains reporter output
        self.assertIn("key_insights", result)

if __name__ == "__main__":
    unittest.main()
