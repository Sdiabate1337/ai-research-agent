"""Tests pour le papers search node."""

import pytest
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nodes import papers_search_node, build_search_query, filter_papers_by_date
from datetime import datetime, timedelta


class TestBuildSearchQuery:
    """Tests pour la construction de la query."""
    
    def test_uses_topic_filters_when_available(self, sample_state):
        """Test: Utilise topic_filters quand disponibles."""
        sample_state["query"] = "What's new in AI?"
        sample_state["topic_filters"] = ["langgraph", "agents", "memory"]
        
        query = build_search_query(sample_state)
        
        assert query == "langgraph agents memory"
        print(f"✅ Query from filters: {query}")
    
    
    def test_falls_back_to_original_query(self, sample_state):
        """Test: Fallback sur query originale si pas de filters."""
        sample_state["query"] = "What's new in AI?"
        sample_state["topic_filters"] = []
        
        query = build_search_query(sample_state)
        
        assert query == "What's new in AI?"
        print(f"✅ Query from original: {query}")
    
    
    def test_limits_to_5_keywords(self, sample_state):
        """Test: Limite à 5 mots-clés max."""
        sample_state["topic_filters"] = ["one", "two", "three", "four", "five", "six", "seven"]
        
        query = build_search_query(sample_state)
        
        words = query.split()
        assert len(words) == 5
        assert query == "one two three four five"
        print(f"✅ Limited to 5 keywords: {query}")


class TestFilterPapersByDate:
    """Tests pour le filtrage par date."""
    
    def test_filters_24h_correctly(self):
        """Test: Filtre correctement sur 24h."""
        from unittest.mock import Mock
        
        # Créer des mock papers avec différentes dates
        now = datetime.now()
        
        paper_recent = Mock()
        paper_recent.published = now - timedelta(hours=12)
        
        paper_old = Mock()
        paper_old.published = now - timedelta(days=2)
        
        papers = [paper_recent, paper_old]
        
        filtered = filter_papers_by_date(papers, "24h")
        
        assert len(filtered) == 1
        assert filtered[0] == paper_recent
        print("✅ 24h filter works")
    
    
    def test_filters_week_correctly(self):
        """Test: Filtre correctement sur 1 semaine."""
        from unittest.mock import Mock
        
        now = datetime.now()
        
        paper_this_week = Mock()
        paper_this_week.published = now - timedelta(days=3)
        
        paper_last_month = Mock()
        paper_last_month.published = now - timedelta(days=20)
        
        papers = [paper_this_week, paper_last_month]
        
        filtered = filter_papers_by_date(papers, "week")
        
        assert len(filtered) == 1
        assert filtered[0] == paper_this_week
        print("✅ Week filter works")


class TestPapersSearchNode:
    """Tests pour le node complet."""
    
    def test_skips_when_papers_not_in_categories(self, sample_state):
        """Test: Skip si 'papers' n'est pas dans search_categories."""
        sample_state["search_categories"] = ["repositories", "discussions"]
        
        result = papers_search_node(sample_state)
        
        assert result["papers"] == []
        print("✅ Skips when papers not requested")
    
    
    def test_returns_papers_when_requested(self, sample_state):
        """Test: Retourne des papers quand demandé."""
        sample_state["query"] = "machine learning"
        sample_state["search_categories"] = ["papers"]
        sample_state["topic_filters"] = ["machine", "learning"]
        sample_state["date_range"] = "month"
        
        result = papers_search_node(sample_state)
        
        # Devrait avoir des résultats (ou au moins ne pas crasher)
        assert "papers" in result
        assert isinstance(result["papers"], list)
        
        # Si des papers sont trouvés, vérifier la structure
        if len(result["papers"]) > 0:
            paper = result["papers"][0]
            assert "title" in paper
            assert "authors" in paper
            assert "url" in paper
            assert "abstract" in paper
            assert "published_date" in paper
            assert "arxiv_id" in paper
            assert "category" in paper
            
            print(f"✅ Found {len(result['papers'])} papers")
            print(f"   First: {paper['title'][:50]}...")
        else:
            print("✅ No papers found (but didn't crash)")
    
    
    def test_handles_errors_gracefully(self, sample_state):
        """Test: Gère les erreurs sans crasher."""
        # Créer un état invalide qui devrait causer une erreur
        sample_state["search_categories"] = ["papers"]
        sample_state["topic_filters"] = [""]  # Query vide
        sample_state["query"] = ""
        
        # Ne devrait pas crasher
        result = papers_search_node(sample_state)
        
        assert "papers" in result
        # Soit des papers, soit une erreur, mais pas de crash
        assert isinstance(result["papers"], list)
        print("✅ Handles errors gracefully")
    
    
    @pytest.mark.slow
    def test_real_search_performance(self, sample_state):
        """Test de performance avec vraie recherche."""
        import time
        
        sample_state["query"] = "reinforcement learning"
        sample_state["search_categories"] = ["papers"]
        sample_state["topic_filters"] = ["reinforcement", "learning"]
        sample_state["date_range"] = "week"
        
        start = time.time()
        result = papers_search_node(sample_state)
        duration = time.time() - start
        
        # Ne devrait pas prendre plus de 10 secondes
        assert duration < 10.0, f"Search too slow: {duration}s"
        
        print(f"✅ Performance OK: {duration:.2f}s")
        print(f"   Found {len(result['papers'])} papers")