"""Node functions for the AI research agent graph."""

from typing import Dict, Any, List
from state import AgentState
from llm_config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# === PAPERS SEARCH NODE ===

import arxiv
from datetime import datetime, timedelta
from typing import List

def score_paper_relevance(paper: dict, topic_filters: list) -> float:
    """
    Score la pertinence d'un paper par rapport aux topic_filters.
    
    Critères:
    - Présence des keywords dans le titre (poids: 3x)
    - Présence des keywords dans l'abstract (poids: 1x)
    - Récence (papers plus récents = score plus élevé)
    
    Args:
        paper: PaperResult dict
        topic_filters: Liste de keywords
        
    Returns:
        Score de pertinence (0-100)
    """
    if not topic_filters:
        return 50.0  # Score neutre
    
    score = 0.0
    title_lower = paper['title'].lower()
    abstract_lower = paper['abstract'].lower()
    
    # Compter les keywords présents
    for keyword in topic_filters:
        keyword_lower = keyword.lower()
        
        # Dans le titre (important)
        if keyword_lower in title_lower:
            score += 30.0
        
        # Dans l'abstract
        if keyword_lower in abstract_lower:
            score += 10.0
    
    # Bonus de récence (papers de cette semaine)
    from datetime import datetime, timedelta
    paper_date = datetime.strptime(paper['published_date'], "%Y-%m-%d")
    days_old = (datetime.now() - paper_date).days
    
    if days_old <= 7:
        score += 20.0
    elif days_old <= 30:
        score += 10.0
    
    # Normaliser à 0-100
    return min(score, 100.0)

def build_search_query(state: AgentState) -> str:
    """
    Construit la query de recherche pour ArXiv (VERSION AMÉLIORÉE).
    
    Améliorations:
    - Détecte les topics liés à l'IA et ajoute des catégories ArXiv
    - Construit une query structurée
    - Meilleure pertinence des résultats
    
    Args:
        state: État de l'agent
        
    Returns:
        Query de recherche optimisée avec catégories ArXiv
    """
    topic_filters = state.get("topic_filters", [])
    
    # 1. Construire la query de base
    if topic_filters and len(topic_filters) > 0:
        base_query = " ".join(topic_filters[:5])
        print(f"📝 Query de base depuis topic_filters: '{base_query}'")
    else:
        base_query = state["query"]
        print(f"📝 Query de base depuis query originale: '{base_query}'")
    
    # 2. Détecter les catégories ArXiv pertinentes
    arxiv_categories = detect_arxiv_categories(topic_filters or [state["query"]])
    
    # 3. Construire la query finale
    if arxiv_categories:
        # Utiliser les catégories pour une recherche plus ciblée
        category_query = " OR ".join([f"cat:{cat}" for cat in arxiv_categories])
        final_query = f"({base_query}) AND ({category_query})"
        print(f"🎯 Catégories ArXiv détectées: {arxiv_categories}")
        print(f"📝 Query finale: '{final_query}'")
    else:
        # Pas de catégorie spécifique, recherche large
        final_query = base_query
        print(f"📝 Query finale (sans catégorie): '{final_query}'")
    
    return final_query


def detect_arxiv_categories(keywords: list) -> list:
    """
    Détecte les catégories ArXiv pertinentes depuis les keywords.
    
    Mapping des topics IA vers catégories ArXiv:
    - AI/agents/intelligence → cs.AI
    - machine learning/deep learning → cs.LG
    - NLP/language/text → cs.CL
    - multi-agent → cs.MA
    - neural networks → cs.NE
    
    Args:
        keywords: Liste de mots-clés
        
    Returns:
        Liste de catégories ArXiv
    """
    categories = set()
    keywords_lower = [k.lower() for k in keywords]
    keywords_str = " ".join(keywords_lower)
    
    # Mapping des patterns vers catégories
    category_patterns = {
        "cs.AI": ["ai", "artificial intelligence", "agent", "intelligent", "reasoning"],
        "cs.LG": ["machine learning", "deep learning", "neural", "learning", "ml", "dl"],
        "cs.CL": ["nlp", "language", "text", "linguistic", "translation", "llm"],
        "cs.MA": ["multi-agent", "multiagent", "mas", "distributed"],
        "cs.NE": ["neural network", "evolutionary", "genetic"]
    }
    
    # Détecter les catégories
    for category, patterns in category_patterns.items():
        for pattern in patterns:
            if pattern in keywords_str:
                categories.add(category)
                break  # Une fois trouvée, pas besoin de chercher les autres patterns
    
    # Par défaut, si aucune catégorie détectée, utiliser cs.AI
    if not categories:
        categories.add("cs.AI")
    
    return list(categories)

def filter_papers_by_date(papers: List[arxiv.Result], date_range: str) -> List[arxiv.Result]:
    """
    Filtre les papers par date.
    
    Args:
        papers: Liste de résultats ArXiv
        date_range: "24h", "week", ou "month"
        
    Returns:
        Papers filtrés
    """
    now = datetime.now()
    
    if date_range == "24h":
        cutoff = now - timedelta(days=1)
    elif date_range == "week":
        cutoff = now - timedelta(weeks=1)
    elif date_range == "month":
        cutoff = now - timedelta(days=30)
    else:
        # Par défaut: 1 semaine
        cutoff = now - timedelta(weeks=1)
    
    # Filtrer les papers
    filtered = []
    for paper in papers:
        # paper.published est un datetime avec timezone
        paper_date = paper.published.replace(tzinfo=None)
        if paper_date >= cutoff:
            filtered.append(paper)
    
    print(f"📅 Filtrage par date ({date_range}): {len(papers)} → {len(filtered)} papers")
    return filtered


def convert_arxiv_to_paper_result(arxiv_paper: arxiv.Result) -> dict:
    """
    Convertit un résultat ArXiv en PaperResult.
    
    Args:
        arxiv_paper: Résultat de l'API ArXiv
        
    Returns:
        Dict au format PaperResult
    """
    return {
        "title": arxiv_paper.title,
        "authors": [author.name for author in arxiv_paper.authors],
        "url": arxiv_paper.entry_id,
        "abstract": arxiv_paper.summary.replace("\n", " "),  # Nettoyer les retours ligne
        "published_date": arxiv_paper.published.strftime("%Y-%m-%d"),
        "arxiv_id": arxiv_paper.get_short_id(),
        "category": [cat for cat in arxiv_paper.categories]
    }


def extract_keywords(query: str) -> List[str]:
    """
    Extrait les mots-clés potentiels d'une requête.
    
    Fallback simple sans LLM pour extraction de keywords.
    """
    stop_words = {
        "what", "how", "when", "where", "why", "who",
        "the", "is", "in", "for", "new", "about", "with",
        "and", "or", "but", "to", "from", "at", "on"
    }
    
    query_lower = query.lower()
    for char in "?!.,;:":
        query_lower = query_lower.replace(char, "")
    
    words = query_lower.split()
    keywords = [
        word for word in words
        if word not in stop_words
        and len(word) > 3
        and word.isalpha()
    ]
    
    return keywords[:5]


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
    query = state["query"]
    print(f"\n{'='*50}")
    print("🔍 QUERY ANALYZER NODE (LLM-Powered)")
    print(f"{'='*50}")
    print(f"Query reçue: '{query}'")

    # === ÉTAPE 1: Gérer date_range ===
    date_range = state.get("date_range", "")
    if not date_range or date_range == "":
        date_range = "week"
        print(f"📅 Date range par défaut: '{date_range}'")
    else:
        valid_ranges = ["24h", "week", "month"]
        if date_range not in valid_ranges:
            print("⚠️  Date range invalide, utilisation de 'week'")
            date_range = "week"
        else:
            print(f"📅 Date range: '{date_range}'")

    # === ÉTAPE 2: Vérifier si l'utilisateur a fourni les infos ===
    user_provided_categories = state.get("search_categories")
    user_provided_filters = state.get("topic_filters")

    # === ÉTAPE 3: Analyser avec LLM ou utiliser les valeurs fournies ===
    if user_provided_categories and user_provided_filters:
        print("✅ Utilisateur a fourni catégories et filtres, skip LLM")
        search_categories = user_provided_categories
        topic_filters = user_provided_filters
        reasoning = "Fourni par l'utilisateur"
    else:
        # Appeler le LLM pour l'analyse
        print("🤖 Appel du LLM pour analyser la query...")
        try:
            # Créer la chaîne LLM
            llm = get_llm(temperature=0)
            parser = JsonOutputParser(pydantic_object=QueryAnalysis)

            # Créer la chaîne complète: prompt -> llm -> parser
            chain = QUERY_ANALYSIS_PROMPT | llm | parser

            # Invoquer le LLM
            analysis = chain.invoke({
                "query": query,
                "date_range": date_range
            })

            # AJOUTEZ CETTE LIGNE DE DEBUG:
            print(f"🔍 DEBUG - Réponse brute du LLM: {analysis}")
            print(f"🔍 DEBUG - Type: {type(analysis)}")

            # Extraire les résultats
            search_categories = analysis.get("categories", [])
            topic_filters = analysis.get("topics", [])
            reasoning = analysis.get("reasoning", "")

            # Validation: s'assurer qu'on a au moins une catégorie
            if not search_categories:
                print("⚠️  LLM n'a retourné aucune catégorie, utilisation de toutes")
                search_categories = ["papers", "repositories", "documentation", "discussions"]

            # Merger avec les préférences utilisateur si partielles
            if user_provided_categories:
                search_categories = user_provided_categories
                print("✅ Utilisation des catégories fournies par l'utilisateur")

            if user_provided_filters:
                topic_filters = user_provided_filters
                print("✅ Utilisation des filtres fournis par l'utilisateur")

            print("\n🧠 Analyse LLM:")
            print(f"   • Raisonnement: {reasoning}")

        except Exception as e:
            # Fallback en cas d'erreur LLM
            print(f"❌ Erreur lors de l'appel LLM: {e}")
            print("🔄 Fallback vers extraction simple...")

            search_categories = ["papers", "repositories", "documentation", "discussions"]
            topic_filters = extract_keywords(query)
            reasoning = f"Fallback (erreur LLM: {str(e)})"

    # === ÉTAPE 4: Validation finale ===
    valid_categories = ["papers", "repositories", "documentation", "discussions"]
    search_categories = [cat for cat in search_categories if cat in valid_categories]

    if not search_categories:
        search_categories = valid_categories

    # === ÉTAPE 5: Logging final ===
    print(f"\n📊 Résumé de l'analyse:")
    print(f"   • Requête: {query}")
    print(f"   • Période: {date_range}")
    print(f"   • Sources: {', '.join(search_categories)}")
    print(f"   • Filtres: {', '.join(topic_filters) if topic_filters else 'Aucun'}")
    method = "LLM" if reasoning != "Fourni par l'utilisateur" else "Utilisateur"
    print(f"   • Méthode: {method}")
    print(f"{'='*50}\n")

    # === ÉTAPE 6: Retourner les updates ===
    return {
        "date_range": date_range,
        "search_categories": search_categories,
        "topic_filters": topic_filters,
    }


def papers_search_node(state: AgentState) -> Dict[str, Any]:
    """
    Recherche des papers académiques sur ArXiv.
    
    Workflow:
    1. Vérifier si "papers" est dans search_categories
    2. Construire la query de recherche
    3. Appeler l'API ArXiv
    4. Filtrer par date
    5. Convertir au format PaperResult
    6. Gérer les erreurs
    
    Args:
        state: État actuel de l'agent
        
    Returns:
        Dict avec le champ "papers" mis à jour
    """
    print(f"\n{'='*50}")
    print("📚 PAPERS SEARCH NODE")
    print(f"{'='*50}")
    
    # Vérifier si on doit chercher des papers
    search_categories = state.get("search_categories", [])
    if "papers" not in search_categories:
        print("⏭️  Papers not in search_categories, skipping...")
        return {"papers": []}
    
    try:
        # 1. Construire la query
        search_query = build_search_query(state)
        date_range = state.get("date_range", "week")
        
        print(f"🔍 Recherche ArXiv: '{search_query}'")
        print(f"📅 Date range: {date_range}")
        
        # 2. Configurer la recherche ArXiv
        search = arxiv.Search(
            query=search_query,
            max_results=10,  # Option A: fixe à 10
            sort_by=arxiv.SortCriterion.SubmittedDate,  # Plus récents en premier
            sort_order=arxiv.SortOrder.Descending
        )
        
        # 3. Récupérer les résultats
        print("⏳ Appel API ArXiv...")
        results = list(search.results())
        print(f"✅ Reçu {len(results)} résultats bruts")
        
        # 4. Filtrer par date
        filtered_results = filter_papers_by_date(results, date_range)
        
        # 5. Convertir au format PaperResult
        papers = [convert_arxiv_to_paper_result(paper) for paper in filtered_results]

        # 5.5. NOUVEAU: Scorer et trier par pertinence
        topic_filters = state.get("topic_filters", [])
        for paper in papers:
            paper['relevance_score'] = score_paper_relevance(paper, topic_filters)

        # Trier par score de pertinence (plus haut en premier)
        papers.sort(key=lambda p: p['relevance_score'], reverse=True)

        
        # 6. Logging final
        print(f"\n📊 Résumé:")
        print(f"   • Query: {search_query}")
        print(f"   • Papers trouvés: {len(papers)}")
        if papers:
            print(f"   • Premier paper: {papers[0]['title'][:60]}...")
        print(f"{'='*50}\n")
        
        return {"papers": papers}
        
    except Exception as e:
        # Gestion des erreurs
        print(f"❌ Erreur lors de la recherche ArXiv: {e}")
        
        error = {
            "source": "papers",
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "papers": [],
            "search_errors": [error]
        }    