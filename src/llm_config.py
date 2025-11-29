"""Configuration for LLM (OpenRouter)."""

from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def get_llm(
    model: str = "anthropic/claude-3.5-sonnet",
    temperature: float = 0,
    timeout: int = 10,
    max_retries: int = 0  # We handle retries ourselves
):
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
        timeout: Timeout en secondes pour les requêtes
        max_retries: Nombre de retries (0 = on gère nous-mêmes)
        
    Returns:
        Instance ChatOpenAI configurée pour OpenRouter
        
    Explication des paramètres:
    ==========================
    - temperature=0: On veut des réponses consistantes et factuelles
    - base_url: Point d'entrée de l'API OpenRouter
    - api_key: Votre clé OpenRouter (à mettre dans .env)
    - request_timeout: Timeout pour éviter les blocages
    - max_retries=0: On implémente notre propre logique de retry
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
        request_timeout=timeout,
        max_retries=max_retries,
        # Headers optionnels mais recommandés
        default_headers={
            "HTTP-Referer": "https://github.com/your-username/ai-research-agent",
            "X-Title": "AI Research Agent"
        }
    )


def get_llm_with_fallback(
    primary_model: str = "anthropic/claude-3.5-sonnet",
    fallback_model: str = "anthropic/claude-3-haiku",
    temperature: float = 0,
    timeout: int = 10
):
    """
    Get LLM with fallback model support.
    
    Strategy:
    =========
    1. Try primary model first (usually more capable)
    2. On error (rate limit, timeout, unavailable), use fallback
    3. Fallback is typically faster/cheaper
    
    Use Cases:
    ==========
    - Primary model rate limited → Use cheaper fallback
    - Primary model down → Use alternative
    - Cost optimization → Try fast model first
    
    Args:
        primary_model: Main model to use
        fallback_model: Backup model if primary fails
        temperature: LLM temperature
        timeout: Request timeout
        
    Returns:
        Tuple of (primary_llm, fallback_llm)
        
    Usage:
    ======
    primary, fallback = get_llm_with_fallback()
    
    try:
        result = primary.invoke(query)
    except Exception as e:
        print(f"Primary failed: {e}, using fallback")
        result = fallback.invoke(query)
    """
    primary = get_llm(primary_model, temperature, timeout)
    fallback = get_llm(fallback_model, temperature, timeout)
    
    return primary, fallback


def count_tokens(text: str, model: str = "anthropic/claude-3.5-sonnet") -> int:
    """
    Estimate token count for cost tracking.
    
    Approximation Rules:
    ====================
    - 1 token ≈ 4 characters (English)
    - 1 token ≈ 2-3 characters (code)
    - More accurate: use tiktoken library
    
    Args:
        text: Text to count tokens for
        model: Model name (for future token counter selection)
        
    Returns:
        Estimated token count
        
    Note:
    =====
    This is a rough estimate. For exact counts, use:
    - tiktoken (for OpenAI models)
    - Model-specific tokenizers
    """
    # Simple approximation: 1 token ≈ 4 characters
    return len(text) // 4


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "anthropic/claude-3.5-sonnet"
) -> float:
    """
    Calculate estimated cost in USD.
    
    Pricing (as of 2024):
    =====================
    Claude 3.5 Sonnet:
    - Input: $3 per 1M tokens
    - Output: $15 per 1M tokens
    
    Claude 3 Haiku:
    - Input: $0.25 per 1M tokens
    - Output: $1.25 per 1M tokens
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name
        
    Returns:
        Estimated cost in USD
    """
    # Model pricing (per 1M tokens)
    pricing = {
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
        "openai/gpt-4": {"input": 30.0, "output": 60.0},
        "openai/gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    }
    
    # Default to Claude 3.5 Sonnet if model not found
    model_pricing = pricing.get(model, pricing["anthropic/claude-3.5-sonnet"])
    
    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
    
    return input_cost + output_cost

