"""Fallback analyzer for when LLM is unavailable."""

import re
from typing import List, Dict

class FallbackAnalyzer:
    """
    Rule-based query analyzer that works without LLM.
    
    Purpose:
    ========
    Provides reliable fallback when:
    - LLM API is down
    - Rate limits exceeded
    - Timeout errors
    - Cost constraints
    
    Strategy:
    =========
    - Keyword-based category detection
    - Named entity extraction (frameworks, libraries)
    - Simple topic extraction
    - Always succeeds (never throws)
    
    Limitations:
    ============
    - Less accurate than LLM
    - Doesn't understand context
    - May miss nuances
    - Limited to English primarily
    
    Usage:
    ======
    fallback = FallbackAnalyzer()
    result = fallback.analyze(
        query="What's new in LangGraph?",
        date_range="week"
    )
    # Returns: {"search_categories": [...], "topic_filters": [...], ...}
    """
    
    def __init__(self):
        # Category detection rules
        self.category_keywords = {
            "papers": [
                "paper", "research", "arxiv", "study", "publication",
                "academic", "conference", "journal", "thesis"
            ],
            "repositories": [
                "code", "github", "repo", "repository", "implementation",
                "library", "framework", "package", "source", "git"
            ],
            "documentation": [
                "documentation", "docs", "tutorial", "guide", "how to",
                "example", "api", "reference", "manual"
            ],
            "discussions": [
                "discussion", "news", "update", "new", "latest", "recent",
                "reddit", "twitter", "hackernews", "community", "forum"
            ]
        }
        
        # Known AI/ML entities to extract
        self.known_entities = {
            "langgraph", "langchain", "openai", "anthropic", "claude",
            "gpt", "llm", "rag", "agent", "transformer", "bert",
            "attention", "neural", "deep learning", "machine learning",
            "reinforcement learning", "multi-agent", "memory"
        }
        
        # Stop words to filter out
        self.stop_words = {
            "what", "how", "when", "where", "why", "who", "which",
            "the", "is", "in", "for", "new", "about", "with", "and",
            "or", "but", "to", "from", "at", "on", "a", "an", "this",
            "that", "these", "those", "of", "as", "by"
        }
    
    def detect_categories(self, query: str) -> List[str]:
        """
        Detect relevant categories from query.
        
        Rules:
        - Check for category keywords
        - Default to all categories if no match
        - Prioritize based on keyword strength
        
        Args:
            query: User query
            
        Returns:
            List of category names
        """
        query_lower = query.lower()
        detected = {}
        
        # Score each category
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            
            if score > 0:
                detected[category] = score
        
        # If nothing detected, return all categories
        if not detected:
            return ["papers", "repositories", "documentation"]
        
        # Always include papers and repositories as they're core research categories
        # Add detected categories on top
        categories = list(detected.keys())
        
        # Ensure core categories are always included
        if "papers" not in categories:
            categories.insert(0, "papers")
        if "repositories" not in categories:
            categories.insert(1, "repositories")
        if "documentation" not in categories:
            categories.insert(2, "documentation")
        
        # Take all 4 categories if we have them
        return categories[:4]
    
    def extract_topics(self, query: str) -> List[str]:
        """
        Extract topic keywords from query.
        
        Strategy:
        1. Check for known entities (LangGraph, Claude, etc.)
        2. Extract non-stop words
        3. Limit to 5 topics
        
        Args:
            query: User query
            
        Returns:
            List of topic keywords
        """
        topics = []
        query_lower = query.lower()
        
        # 1. Check for known entities
        for entity in self.known_entities:
            if entity in query_lower:
                topics.append(entity)
        
        # 2. Extract other significant words
        # Remove punctuation
        cleaned = re.sub(r'[^\w\s]', ' ', query_lower)
        words = cleaned.split()
        
        for word in words:
            if (
                word not in self.stop_words
                and len(word) > 3
                and word not in topics
                and word.isalpha()  # Only alphabetic
            ):
                topics.append(word)
        
        # 3. Limit to 5 topics
        return topics[:5]
    
    def analyze(self, query: str, date_range: str = "week") -> Dict:
        """
        Analyze query using rule-based approach.
        
        Args:
            query: User query
            date_range: Time range filter
            
        Returns:
            Analysis result dict with:
            - search_categories
            - topic_filters
            - reasoning
            - confidence_score (lower for fallback)
        """
        categories = self.detect_categories(query)
        topics = self.extract_topics(query)
        
        # If no topics found, use query words as fallback
        if not topics:
            topics = [word for word in query.lower().split()
                     if word not in self.stop_words and len(word) > 3][:5]
        
        return {
            "search_categories": categories,
            "topic_filters": topics,
            "reasoning": "Fallback analysis (LLM unavailable)",
            "confidence_score": 0.6,  # Lower confidence for fallback
            "method": "fallback"
        }


def get_fallback_analyzer() -> FallbackAnalyzer:
    """Get fallback analyzer instance."""
    return FallbackAnalyzer()
