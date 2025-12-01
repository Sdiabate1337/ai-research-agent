"""Configuration for LLM (OpenRouter)."""

from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def get_llm(
    model: str = "gpt-4o-mini",  # OpenAI's affordable model
    temperature: float = 0,
    timeout: int = 10,
    max_retries: int = 0
):
    """
    Create LLM instance using OpenAI API directly.
    
    Args:
        model: OpenAI model to use (gpt-4o-mini, gpt-4o, gpt-3.5-turbo)
        temperature: Controls creativity (0 = deterministic, 1 = creative)
        timeout: Timeout in seconds
        max_retries: Number of retries
        
    Returns:
        ChatOpenAI instance
    """
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found! "
            "Add it to your .env file: OPENAI_API_KEY=sk-..."
        )
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=api_key,
        request_timeout=timeout,
        max_retries=max_retries
    )


def get_llm_with_fallback(
    primary_model: str = "gpt-4o-mini",
    fallback_model: str = "gpt-3.5-turbo",
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
        primary_model: Main OpenAI model (gpt-4o-mini)
        fallback_model: Backup model (gpt-3.5-turbo)
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

