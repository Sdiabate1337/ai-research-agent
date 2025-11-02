"""Node functions for the AI research agent graph."""

from typing import Dict, Any
from .state import AgentState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List


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


# Template de prompt pour l'analyse
QUERY_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Tu es un assistant expert en analyse de requêtes de recherche pour l'IA et le Machine Learning.

Ton rôle:
========
Analyser la requête utilisateur et déterminer:
1. Quelles catégories de sources chercher (papers, repositories, documentation, discussions)
2. Quels mots-clés/topics utiliser pour filtrer les résultats

Catégories disponibles:
======================
- papers: Articles académiques, recherche, arXiv, conférences (NeurIPS, ICML, etc.)
- repositories: Code GitHub/GitLab, frameworks, bibliothèques, implémentations
- documentation: Docs officielles, tutoriels, guides techniques
- discussions: Forums Reddit, HackerNews, Twitter/X, communautés

Instructions:
============
1. TOUJOURS suggérer au moins 2 catégories (sauf si très spécifique)
2. Extraire 2-5 mots-clés pertinents (en anglais de préférence)
3. Pour les requêtes générales, utiliser toutes les catégories
4. Pour les requêtes sur "nouveautés/updates", prioriser: discussions, repositories
5. Pour les requêtes théoriques, prioriser: papers, documentation

Exemples:
========
Query: "Quoi de neuf dans LangGraph cette semaine?"
→ categories: ["repositories", "discussions", "documentation"]
→ topics: ["langgraph", "updates", "features"]

Query: "Research papers on multi-agent systems"
→ categories: ["papers"]
→ topics: ["multi-agent", "systems", "coordination"]

Query: "Comment implémenter la mémoire dans un agent?"
→ categories: ["documentation", "repositories", "discussions"]
→ topics: ["agent", "memory", "implementation"]

Réponds UNIQUEMENT en JSON valide selon le schéma fourni."""),
    
    ("user", "Query: {query}\n\nDate range demandé: {date_range}")
])




def query_analyzer_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes the user query and sets default values.
    
    Tasks:
    1. Set default date_range if not provided
    2. Set default search_categories if not provided
    3. Extract topic_filters from query (if not provided)
    4. Log what we're about to search
    
    Args:
        state: Current agent state
        
    Returns:
        Dict with updated fields
    """
    qery = state["query"]
    print(f"\n{'='*50}")
    print(f"🔍 QUERY ANALYZER NODE (LLM-Powered)")
    print(f"{'='*50}")
    print(f"Query reçue: '{query}'")

    date_range = state["data_range"]
    if not data_range or data_range = "":
        data_range = "week"
        print(f"📅 Date range par défaut: '{date_range}'")
    else:
        valid_range = ["24h", "week", "month"]
        if date_range not in valid_range:
            print(f"⚠️  Date range invalide, utilisation de 'week'")
            data_range = "week"
        else:
            print(f"date range: '{date_range}' ")    


    
    # Vérifier si l'utilisateur a déjà fourni ces informations
    user_provided_categories = state.get("search_categories")
    user_provided_filters = state.get("topic_filters")

        # Si l'utilisateur a TOUT fourni, pas besoin du LLM

    if user_provided_categories and user_provided_filters:
        print(f"✅ Utilisateur a fourni catégories et filtres, skip LLM")
        search_categories = user_provided_categories
        topic_filters = user_provided_filters
        reasoning = "Fourni par l'utilisateur"

    else:
        print(f"🤖 Appel du LLM pour analyser la query...")
        try:
            # Créer la chaîne LLM
            llm = get_llm(temperature=0)
            parser = JsonOutputParser(pydantic_object = QueryAnalysis)

            # Créer la chaîne complète: prompt -> llm -> parser
            chain = QUERY_ANALYSIS_PROMPT | llm | parser

            analysis = chain.invoke([
                "query": query,
                "date_range", date_range
            ])

            # get the analisis results
            search_categories = analysis.get("search_categories", [])
            topic_filters = analysis("topic_filters", [])
            reasoning = analysis.get("raisoning", [])

            #s'assurer qu'il ya au moins une categorie
            if not search_categories:
                search_categories = ["papers", "repositories", "documentation", "discussions"]
    
            if user_provided_categories:
                search_categories = user_provided_categories

            if user_provided_filters:
                topic_filters = user_provided_filters

            print(f"\n🧠 Analyse LLM:")
            print(f"   • Raisonnement: {reasoning}")

        except exception as e:
            print(f"❌ Erreur lors de l'appel LLM: {e}")
            print(f"🔄 Fallback vers extraction simple...")

            search_categories = ["papers", "repositories", "documentation", "discussions"]
            topic_filters = extract_keyword(query)
            raisoning = f"Fallback (erreur LLM: {str(e)})"


        valid_categories = ["papers", "repositories", "documentation", "discussions"]
        search_categories = [cat for cat in search_categories if cat in valid_categories]

        if not search_categories:
            search_categories= valid_categories

        print(f"\n📊 Résumé de l'analyse:")
        print(f"   • Requête: {query}")
        print(f"   • Période: {date_range}")
        print(f"   • Sources: {', '.join(search_categories)}")
        print(f"   • Filtres: {', '.join(topic_filters) if topic_filters else 'Aucun'}")
        print(f"   • Méthode: {'LLM' if reasoning != 'Fourni par l'utilisateur' else 'Utilisateur'}")
        print(f"{'='*50}\n")

        return ([
            "date_range": date_range,
            "search_categories": search_categories,
            "topic_filters": topic_filters
        ])    


    print(f"Analyzing query: {query}")
    print(f"Date range: {date_range}")
    print(f"Categories: {search_categories}")

    return {
        "data_range": data_range,
        "search_categories": search_categories,
    }