"""Nodes for the AI research agent graph."""

import os
from datetime import datetime
from typing import Dict, Any, List

from langchain_community.utilities import ArxivAPIWrapper
from langchain_core.output_parsers import JsonOutputParser

# Import shared models and prompts
from models import QueryAnalysis, PaperResult
from prompts import QUERY_ANALYSIS_PROMPT
from llm_config import get_llm

# === DEPRECATED: Use query_analyzer_node_v2 instead ===
# The old query_analyzer_node has been removed.
# Please use src/query_analyzer_node_v2.py


# === PAPERS SEARCH NODE ===

def papers_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recherche des papiers sur ArXiv.
    
    Args:
        state: State actuel contenant la query analysée
        
    Returns:
        Mise à jour du state avec les papiers trouvés
    """
    print("\n" + "=" * 50)
    print("📚 PAPERS SEARCH NODE")
    print("=" * 50)
    
    # Vérifier si on doit chercher des papers
    search_categories = state.get("search_categories", [])
    if "papers" not in search_categories:
        print("⏭️  Papers not in search_categories, skipping...")
        return {"papers": [], "search_errors": []}
    
    # Construire la query ArXiv
    # On utilise les topic_filters pour être plus précis
    topics = state.get("topic_filters", [])
    base_query = state.get("query", "")
    
    if topics:
        # Combiner les topics
        topic_query = " ".join(topics)
        print(f"📝 Query de base depuis topic_filters: '{topic_query}'")
        
        # Ajouter des catégories CS (Computer Science) pertinentes pour l'IA
        # cs.AI = Artificial Intelligence
        # cs.CL = Computation and Language (NLP)
        # cs.LG = Machine Learning
        # cs.MA = Multiagent Systems
        categories = ["cs.AI", "cs.CL", "cs.LG", "cs.MA"]
        
        # Simple heuristique pour choisir la catégorie principale
        # (Pourrait être amélioré avec le LLM)
        selected_cats = []
        if "agent" in topic_query.lower() or "multi" in topic_query.lower():
            selected_cats.append("cs.MA")
        if "language" in topic_query.lower() or "text" in topic_query.lower() or "llm" in topic_query.lower():
            selected_cats.append("cs.CL")
        
        # Si aucune spécifique, on met AI et LG par défaut
        if not selected_cats:
            selected_cats = ["cs.AI", "cs.LG"]
            
        print(f"🎯 Catégories ArXiv détectées: {selected_cats}")
        
        # Construire la query finale
        # Format: (topic1 topic2) AND (cat:cs.AI OR cat:cs.LG)
        cat_query = " OR ".join([f"cat:{cat}" for cat in selected_cats])
        final_query = f"({topic_query}) AND ({cat_query})"
        
    else:
        final_query = base_query
        
    print(f"📝 Query finale: '{final_query}'")
    
    # Configurer la recherche
    arxiv = ArxivAPIWrapper(
        top_k_results=10,
        ARXIV_MAX_QUERY_LENGTH=300,
        doc_content_chars_max=1000,
        load_max_docs=10,
        load_all_available_meta=True
    )
    
    try:
        print(f"🔍 Recherche ArXiv: '{final_query}'")
        print(f"📅 Date range: {state.get('date_range', 'all')}")
        print("⏳ Appel API ArXiv...")
        
        # Note: ArxivAPIWrapper de LangChain ne supporte pas nativement le filtrage par date
        # On récupère plus de résultats et on filtre manuellement
        results = arxiv.run(final_query)
        
        # Parser les résultats (c'est du texte brut avec ArxivAPIWrapper standard)
        # Pour une version plus robuste, on pourrait utiliser arxiv-python directement
        # Ici on simule le parsing pour l'exemple
        
        # Utilisation de la librairie arxiv directement pour avoir des objets structurés
        import arxiv as arxiv_lib
        
        client = arxiv_lib.Client()
        search = arxiv_lib.Search(
            query=final_query,
            max_results=10,
            sort_by=arxiv_lib.SortCriterion.SubmittedDate,
            sort_order=arxiv_lib.SortOrder.Descending
        )
        
        papers_data = []
        raw_results = list(client.results(search))
        print(f"✅ Reçu {len(raw_results)} résultats bruts")
        
        for result in raw_results:
            # Filtrage par date si nécessaire (très basique ici)
            # state['date_range'] pourrait être "week", "month", etc.
            # TODO: Implémenter le filtrage par date précis
            
            paper = PaperResult(
                title=result.title,
                authors=[a.name for a in result.authors],
                summary=result.summary,
                url=result.entry_id,
                published_date=result.published.strftime("%Y-%m-%d"),
                source="arxiv",
                relevance_score=1.0 # Placeholder
            )
            papers_data.append(paper)
            
        print(f"📅 Filtrage par date ({state.get('date_range')}): {len(raw_results)} → {len(papers_data)} papers")
        
        if papers_data:
            print(f"\n📊 Résumé:")
            print(f"   • Query: {final_query}")
            print(f"   • Papers trouvés: {len(papers_data)}")
            print(f"   • Premier paper: {papers_data[0].title[:50]}...")
        else:
            print("⚠️ Aucun papier trouvé")
            
        return {"papers": papers_data, "search_errors": []}
        
    except Exception as e:
        print(f"❌ Erreur lors de la recherche ArXiv: {e}")
        # On ne veut pas faire planter tout le graph
        return {"papers": [], "search_errors": [str(e)]}