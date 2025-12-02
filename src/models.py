"""Shared Pydantic models for the AI research agent."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryAnalysis(BaseModel):
    """
    Structure de sortie pour l'analyse de query par le LLM.
    
    Pourquoi Pydantic?
    =================
    - Validation automatique des types
    - Documentation claire des champs attendus
    - LangChain peut automatiquement parser vers ce format
    """
    
    search_categories: List[str] = Field(
        description="Catégories de recherche pertinentes parmi: papers, repositories, documentation, discussions"
    )
    
    topic_filters: List[str] = Field(
        description="Mots-clés et topics principaux à rechercher (2-5 mots-clés)"
    )
    
    reasoning: str = Field(
        description="Brève explication du raisonnement (pour debugging)"
    )
    
    confidence_score: float = Field(
        description="Confidence in this analysis from 0.0 (low) to 1.0 (high)",
        ge=0.0,
        le=1.0
    )


class PaperResult(BaseModel):
    """Structure d'un résultat de recherche de papier."""
    title: str
    authors: List[str]
    summary: str
    url: str
    published_date: str
    source: str = "arxiv"
    relevance_score: Optional[float] = None


class RepositoryResult(BaseModel):
    """Structure d'un résultat de repository."""
    name: str
    description: str
    language: str
    stars: int
    url: str
    updated_at: str


class DocumentationResult(BaseModel):
    """Structure d'un résultat de documentation."""
    title: str
    content_snippet: str
    url: str
    source_framework: str


class DiscussionResult(BaseModel):
    """Structure d'un résultat de discussion."""
    title: str
    content: str
    url: str
    platform: str  # twitter, reddit, etc.
    date: str


class RankedResult(BaseModel):
    """Résultat unifié et classé."""
    type: str  # paper, repo, doc, discussion
    title: str
    url: str
    summary: str
    date: str
    relevance_score: float
    source_metadata: Dict[str, Any]


class CategorySummary(BaseModel):
    """Résumé par catégorie."""
    papers_summary: str
    code_summary: str
    community_summary: str


class Insight(BaseModel):
    """Insight clé extrait."""
    title: str
    description: str
    importance: str  # high, medium, low


class Action(BaseModel):
    """Action recommandée."""
    description: str
    priority: str
    url: Optional[str] = None


class SearchError(BaseModel):
    """Erreur de recherche."""
    source: str
    error_message: str
    timestamp: str
