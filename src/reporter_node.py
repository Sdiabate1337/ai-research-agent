"""Reporter node for the AI research agent."""

import logging
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from state import AgentState
from models import RankedResult, CategorySummary, Insight, Action
from llm_config import get_llm

# Configure logging
logger = logging.getLogger(__name__)


class ReportOutput(BaseModel):
    """Structure de sortie du rapport généré par le LLM."""
    key_insights: List[Insight] = Field(description="Top 3-5 insights clés")
    summary_by_category: CategorySummary = Field(description="Résumé par catégorie")
    action_items: List[Action] = Field(description="Actions recommandées")


REPORTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Tu es un analyste de recherche technique senior.
    Ta mission est de synthétiser les résultats de recherche sur l'IA pour un ingénieur.
    
    Tu reçois une liste de résultats classés (Papers, Code, Docs, Discussions).
    
    Tu dois générer:
    1. **Key Insights**: 3 à 5 points clés qui résument les tendances ou découvertes majeures.
    2. **Category Summary**: Un paragraphe concis pour chaque catégorie (Papers, Repos, Docs, Discussions).
    3. **Action Items**: 3 liens ou actions concrètes à explorer en priorité.
    
    Règles:
    - Sois technique et précis.
    - Cite les sources (titres) dans tes résumés.
    - Si une catégorie est vide, indique "Aucun résultat pertinent".
    - Pour les "Action Items", choisis les ressources les plus impactantes (ex: le paper SOTA, le repo officiel).
    
    Format de sortie: JSON uniquement, respectant le schéma fourni.
    """),
    ("user", """Query: {query}
    
    Résultats (Top 20):
    {results_text}
    """)
])


def reporter_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesizes findings into a coherent report using LLM.
    
    Args:
        state: Current agent state
        
    Returns:
        Dict with 'key_insights', 'summary_by_category', 'action_items'
    """
    print(f"\n{'='*50}")
    print("📝 REPORTER NODE")
    print(f"{'='*50}")
    
    ranked_results = state.get("ranked_results", [])
    if not ranked_results:
        print("⚠️  No results to report on.")
        return {
            "key_insights": [],
            "summary_by_category": {
                "papers": "No papers found.",
                "repositories": "No repositories found.",
                "documentation": "No documentation found.",
                "discussions": "No discussions found."
            },
            "action_items": []
        }
    
    # Format results for LLM context
    results_text = ""
    for i, res in enumerate(ranked_results[:15]): # Limit context window
        # Handle Pydantic objects vs dicts (State usually has dicts if coming from curator)
        # But curator returns Pydantic objects in ranked_results list
        # Wait, curator returns List[RankedResult] which are Pydantic objects.
        
        # Let's assume they are objects
        r_type = res.type
        r_title = res.title
        r_summary = res.summary
        r_url = res.url
        
        results_text += f"{i+1}. [{r_type.upper()}] {r_title}\n   Summary: {r_summary}\n   URL: {r_url}\n\n"
        
    print("🤖 Generating report with LLM...")
    
    try:
        llm = get_llm(temperature=0.2) # Low temp for factual reporting
        parser = JsonOutputParser(pydantic_object=ReportOutput)
        chain = REPORTER_PROMPT | llm | parser
        
        report = chain.invoke({
            "query": state["query"],
            "results_text": results_text
        })
        
        print("✅ Report generated successfully")
        
        # Convert Pydantic models to dicts if needed, or keep as objects
        # The parser returns a dict matching ReportOutput structure
        # But ReportOutput fields are Pydantic models (Insight, etc.)
        # JsonOutputParser usually returns dicts if pydantic_object is used?
        # Actually JsonOutputParser returns a dict that matches the structure.
        
        return {
            "key_insights": report["key_insights"],
            "summary_by_category": report["summary_by_category"],
            "action_items": report["action_items"]
        }
        
    except Exception as e:
        print(f"❌ Report Generation Error: {e}")
        # Fallback: simple manual report
        return {
            "key_insights": [{"text": "Error generating insights", "confidence": 0.0, "related_sources": []}],
            "summary_by_category": {
                "papers": "Error generating summary",
                "repositories": "Error generating summary",
                "documentation": "Error generating summary",
                "discussions": "Error generating summary"
            },
            "action_items": []
        }
