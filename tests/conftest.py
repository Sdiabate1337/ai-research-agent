"""Configuration partagée pour les tests pytest."""

import pytest
import sys
from pathlib import Path

# Ajouter le dossier src au path pour pouvoir importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_state():
    """
    Fixture qui crée un état de base pour les tests.
    
    Pourquoi une fixture?
    ====================
    - Réutilisable dans tous les tests
    - Évite la duplication de code
    - Facile à modifier en un seul endroit
    """
    from state import AgentState
    
    return {
        "query": "",  # Sera overridé par chaque test
        "search_categories": None,
        "date_range": "",
        "topic_filters": None,
        "papers": [],
        "repositories": [],
        "documentation": [],
        "discussions": [],
        "ranked_results": None,
        "summary_by_category": None,
        "key_insights": None,
        "action_items": None,
        "total_results_found": None,
        "search_errors": None
    }


@pytest.fixture
def mock_llm_response():
    """
    Fixture pour mocker les réponses LLM (éviter les vrais appels API en test).
    
    Pourquoi mocker?
    ===============
    - Tests rapides (pas d'appel réseau)
    - Tests déterministes (pas de variabilité)
    - Pas de coût API
    - Tests qui marchent offline
    """
    return {
        "search_categories": ["papers", "repositories"],
        "topic_filters": ["langgraph", "agents"],
        "reasoning": "Query concerne un framework spécifique"
    }