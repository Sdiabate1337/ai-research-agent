"""Input validation and security for query analyzer."""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of query validation."""
    is_valid: bool
    error_message: Optional[str] = None
    normalized_query: Optional[str] = None
    detected_language: Optional[str] = None


def detect_language(query: str) -> str:
    """
    Detect the language of the query.
    
    Simple heuristic-based detection. For production, consider:
    - langdetect library
    - fasttext language identification
    
    Args:
        query: User query
        
    Returns:
        Language code ("en", "fr", "ar", "unknown")
    """
    # Arabic detection (simple: check for Arabic characters)
    if re.search(r'[\u0600-\u06FF]', query):
        return "ar"
    
    # French detection (simple: common French words)
    french_words = ['quoi', 'nouveau', 'dans', 'comment', 'pourquoi', 'recherche']
    query_lower = query.lower()
    if any(word in query_lower for word in french_words):
        return "fr"
    
    # Default to English
    return "en"


def normalize_query(query: str) -> str:
    """
    Normalize query text.
    
    Normalization steps:
    - Strip leading/trailing whitespace
    - Collapse multiple spaces into one
    - Remove excessive punctuation
    - Preserve meaning
    
    Args:
        query: Raw user query
        
    Returns:
        Normalized query
    """
    # Strip whitespace
    normalized = query.strip()
    
    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove excessive punctuation (but keep some for meaning)
    # e.g., "What?????" → "What?"
    normalized = re.sub(r'([!?.])\1+', r'\1', normalized)
    
    return normalized


def detect_prompt_injection(query: str) -> bool:
    """
    Detect potential prompt injection attempts.
    
    Red Flags:
    ==========
    - "Ignore previous instructions"
    - "Forget everything"
    - "You are now..."
    - "Act as..."
    - System prompts leaking attempts
    
    Args:
        query: User query
        
    Returns:
        True if potential injection detected
    """
    query_lower = query.lower()
    
    # Suspicious patterns
    injection_patterns = [
        r'ignore\s+(previous|all|your)\s+(instructions?|prompts?)',
        r'forget\s+(everything|all|what)',
        r'you\s+are\s+now',
        r'act\s+as\s+(?:a|an)',
        r'system\s*:',
        r'assistant\s*:',
        r'<\s*system\s*>',
        r'disregard',
        r'override',
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, query_lower):
            return True
    
    return False


def validate_and_sanitize_query(query: str, config) -> ValidationResult:
    """
    Validate and sanitize user query.
    
    Validation Steps:
    =================
    1. Check length (min/max)
    2. Detect prompt injection
    3. Normalize text
    4. Detect language
    5. Check for malicious patterns
    
    Args:
        query: Raw user query
        config: QueryAnalyzerConfig instance
        
    Returns:
        ValidationResult with is_valid and normalized_query
    """
    # Step 1: Check length
    if len(query) < config.min_query_length:
        return ValidationResult(
            is_valid=False,
            error_message=f"Query too short (min {config.min_query_length} characters)"
        )
    
    if len(query) > config.max_query_length:
        return ValidationResult(
            is_valid=False,
            error_message=f"Query too long (max {config.max_query_length} characters)"
        )
    
    # Step 2: Detect prompt injection
    if detect_prompt_injection(query):
        return ValidationResult(
            is_valid=False,
            error_message="Potential prompt injection detected"
        )
    
    # Step 3: Normalize
    normalized = normalize_query(query)
    
    # If normalization results in empty string
    if not normalized:
        return ValidationResult(
            is_valid=False,
            error_message="Query is empty after normalization"
        )
    
    # Step 4: Detect language
    language = detect_language(normalized)
    
    # Success!
    return ValidationResult(
        is_valid=True,
        error_message=None,
        normalized_query=normalized,
        detected_language=language
    )
