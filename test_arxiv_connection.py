"""Test simple de l'API ArXiv."""
import arxiv

# Recherche simple
search = arxiv.Search(
    query="artificial intelligence agents",
    max_results=3,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

print("🔍 Test ArXiv API:\n")
for result in search.results():
    print(f"📄 {result.title}")
    print(f"   Auteurs: {', '.join(author.name for author in result.authors[:3])}")
    print(f"   Date: {result.published.date()}")
    print(f"   URL: {result.entry_id}")
    print()