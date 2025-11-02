"""Configuration for LLM (OpenRouter)."""

from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def get_llm(model: str = "anthropic/claude-3.5-sonnet", temperature: float = 0):
    """
    Crée une instance du LLM via OpenRouter.
    
    Pourquoi OpenRouter?
    ===================
    - Accès à plusieurs modèles (Claude, GPT-4, Llama, etc.)
    - Un seul API key pour tous les modèles
    - Souvent moins cher que les APIs directes
    
    Args:
        model: Le modèle à utiliser (voir https://openrouter.ai/models)
        temperature: Contrôle la créativité (0 = déterministe, 1 = créatif)
        
    Returns:
        Instance ChatOpenAI configurée pour OpenRouter
        
    Explication des paramètres:
    ==========================
    - temperature=0: On veut des réponses consistantes et factuelles
    - base_url: Point d'entrée de l'API OpenRouter
    - api_key: Votre clé OpenRouter (à mettre dans .env)
    """
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY non trouvée! "
            "Ajoutez-la dans votre fichier .env: OPENROUTER_API_KEY=your_key_here"
        )
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=api_key,
        # Headers optionnels mais recommandés
        default_headers={
            "HTTP-Referer": "https://github.com/your-username/ai-research-agent",
            "X-Title": "AI Research Agent"
        }
    )

