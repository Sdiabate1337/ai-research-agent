"""Tests pour le query analyzer node."""

import pytest
import json
from pathlib import Path
from nodes import query_analyzer_node


def load_test_queries():
    """Charge les queries de test depuis le fichier JSON."""
    test_data_path = Path(__file__).parent / "data" / "sample_queries.json"
    with open(test_data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class TestQueryAnalyzerBasics:
    """Tests de base du query analyzer."""
    
    def test_default_date_range(self, sample_state):
        """
        Test: Si date_range n'est pas fourni, doit être 'week' par défaut.
        
        Pourquoi ce test?
        ================
        Assurer que l'agent fonctionne même sans tous les paramètres.
        """
        sample_state["query"] = "What's new in AI?"
        sample_state["date_range"] = ""
        
        result = query_analyzer_node(sample_state)
        
        assert result["date_range"] == "week"
        print("✅ Test passed: Default date_range is 'week'")
    
    
    def test_invalid_date_range_correction(self, sample_state):
        """
        Test: Si date_range est invalide, doit être corrigé à 'week'.
        """
        sample_state["query"] = "AI updates"
        sample_state["date_range"] = "yesterday"  # Invalide
        
        result = query_analyzer_node(sample_state)
        
        assert result["date_range"] == "week"
        print("✅ Test passed: Invalid date_range corrected")
    
    
    def test_valid_date_range_preserved(self, sample_state):
        """
        Test: Si date_range est valide, doit être préservé.
        """
        sample_state["query"] = "AI updates"
        sample_state["date_range"] = "24h"
        
        result = query_analyzer_node(sample_state)
        
        assert result["date_range"] == "24h"
        print("✅ Test passed: Valid date_range preserved")
    
    
    def test_returns_required_fields(self, sample_state):
        """
        Test: Le node doit toujours retourner les champs requis.
        """
        sample_state["query"] = "LangGraph updates"
        
        result = query_analyzer_node(sample_state)
        
        # Vérifier que tous les champs essentiels sont présents
        assert "date_range" in result
        assert "search_categories" in result
        assert "topic_filters" in result
        
        # Vérifier les types
        assert isinstance(result["search_categories"], list)
        assert isinstance(result["topic_filters"], list)
        assert len(result["search_categories"]) > 0
        
        print("✅ Test passed: All required fields present and valid")


class TestQueryAnalyzerMultilingual:
    """Tests multilingues du query analyzer."""
    
    @pytest.mark.parametrize("language", ["french_queries", "english_queries", "arabic_queries"])
    def test_multilingual_analysis(self, sample_state, language):
        """
        Test: Le LLM doit pouvoir analyser des queries en plusieurs langues.
        
        @pytest.mark.parametrize permet de lancer le même test avec différents paramètres.
        """
        queries = load_test_queries()[language]
        
        for query_data in queries:
            sample_state["query"] = query_data["query"]
            
            print(f"\n🧪 Testing {query_data['language']} query: {query_data['query']}")
            
            result = query_analyzer_node(sample_state)
            
            # Vérifications de base
            assert len(result["search_categories"]) > 0, "Should return at least one category"
            assert len(result["topic_filters"]) > 0, "Should extract at least one topic"
            
            # Vérifier que les catégories sont valides
            valid_categories = ["papers", "repositories", "documentation", "discussions"]
            for cat in result["search_categories"]:
                assert cat in valid_categories, f"Invalid category: {cat}"
            
            print(f"   ✅ Categories: {result['search_categories']}")
            print(f"   ✅ Topics: {result['topic_filters']}")


class TestQueryAnalyzerEdgeCases:
    """Tests des cas limites."""
    
    def test_very_short_query(self, sample_state):
        """Test: Query très courte (1-2 mots)."""
        sample_state["query"] = "AI"
        
        result = query_analyzer_node(sample_state)
        
        # Doit quand même retourner des résultats valides
        assert len(result["search_categories"]) > 0
        assert len(result["topic_filters"]) > 0
        
        print("✅ Test passed: Very short query handled")
    
    
    def test_very_long_query(self, sample_state):
        """Test: Query très longue et complexe."""
        sample_state["query"] = (
            "I want to learn everything about reinforcement learning, "
            "multi-agent systems, transformers, attention mechanisms, "
            "and how to build production-ready AI agents with memory"
        )
        
        result = query_analyzer_node(sample_state)
        
        # Doit extraire les topics principaux (pas tous les mots)
        assert len(result["topic_filters"]) <= 5, "Should limit to 5 main topics"
        
        print(f"✅ Test passed: Long query → {len(result['topic_filters'])} topics extracted")
    
    
    def test_query_with_special_characters(self, sample_state):
        """Test: Query avec emojis et caractères spéciaux."""
        sample_state["query"] = "🤖 What's new in AI agents? 🚀"
        
        result = query_analyzer_node(sample_state)
        
        # Doit gérer les emojis sans crasher
        assert len(result["search_categories"]) > 0
        
        print("✅ Test passed: Special characters handled")
    
    
    def test_user_provided_overrides(self, sample_state):
        """
        Test: Si l'utilisateur fournit déjà des catégories/filtres,
        ils doivent être préservés (pas overridés par le LLM).
        """
        sample_state["query"] = "AI updates"
        sample_state["search_categories"] = ["papers"]  # Utilisateur veut seulement papers
        sample_state["topic_filters"] = ["machine-learning"]
        
        result = query_analyzer_node(sample_state)
        
        # Les préférences utilisateur doivent être respectées
        assert result["search_categories"] == ["papers"]
        assert result["topic_filters"] == ["machine-learning"]
        
        print("✅ Test passed: User preferences preserved")


class TestQueryAnalyzerLLMFallback:
    """Tests du mécanisme de fallback."""
    
    @pytest.mark.skip(reason="Requires mocking LLM failure - advanced test")
    def test_llm_failure_fallback(self, sample_state):
        """
        Test: Si le LLM échoue, le fallback doit fonctionner.
        
        TODO: Implémenter le mocking du LLM pour simuler une erreur.
        """
        # Ce test nécessite de mocker le LLM pour simuler une erreur
        # On le skip pour l'instant
        pass


# === Test de performance (optionnel) ===

@pytest.mark.slow
def test_analyzer_performance(sample_state):
    """
    Test de performance: Le node ne doit pas être trop lent.
    
    Marqué @pytest.mark.slow pour pouvoir le skip en développement.
    Lance avec: pytest -m slow
    """
    import time
    
    sample_state["query"] = "What's new in LangGraph?"
    
    start = time.time()
    result = query_analyzer_node(sample_state)
    duration = time.time() - start
    
    # Ne devrait pas prendre plus de 5 secondes (appel LLM inclus)
    assert duration < 5.0, f"Analyzer too slow: {duration}s"
    
    print(f"✅ Performance test passed: {duration:.2f}s")