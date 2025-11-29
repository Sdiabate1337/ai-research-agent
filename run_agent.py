#!/usr/bin/env python3
"""Demo script to run the AI Research Agent."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from graph import run_research_agent


def main():
    """Run the research agent with a sample query."""
    
    print("=" * 60)
    print("AI RESEARCH AGENT - Multi-Source Search Demo")
    print("=" * 60)
    print()
    
    # Example query
    query = "What are the latest developments in multi-agent systems?"
    date_range = "week"
    
    print(f"Query: {query}")
    print(f"Date Range: {date_range}")
    print()
    
    # Run the agent
    try:
        result = run_research_agent(query, date_range)
        
        print("\n" + "=" * 60)
        print("RESULTS SUMMARY")
        print("=" * 60)
        
        # Display results
        print(f"\n📊 Total Results: {result.get('total_results_found', 0)}")
        print(f"📝 Papers: {len(result.get('papers', []))}")
        print(f"💻 Repositories: {len(result.get('repositories', []))}")
        print(f"📚 Documentation: {len(result.get('documentation', []))}")
        print(f"💬 Discussions: {len(result.get('discussions', []))}")
        print(f"⭐ Ranked Results: {len(result.get('ranked_results', []))}")
        
        # Display top insights
        insights = result.get('key_insights', [])
        if insights:
            print("\n🔍 KEY INSIGHTS:")
            for i, insight in enumerate(insights[:3], 1):
                if isinstance(insight, dict):
                    print(f"   {i}. {insight.get('text', 'N/A')}")
                else:
                    print(f"   {i}. {insight}")
        
        # Display action items
        actions = result.get('action_items', [])
        if actions:
            print("\n✅ RECOMMENDED ACTIONS:")
            for i, action in enumerate(actions[:3], 1):
                if isinstance(action, dict):
                    print(f"   {i}. {action.get('text', 'N/A')}")
                else:
                    print(f"   {i}. {action}")
        
        # Display top ranked results
        ranked = result.get('ranked_results', [])
        if ranked:
            print("\n🏆 TOP RESULTS:")
            for i, res in enumerate(ranked[:5], 1):
                if hasattr(res, 'title'):
                    print(f"   {i}. [{res.type.upper()}] {res.title}")
                    print(f"      Score: {res.relevance_score:.2f} | {res.url}")
                elif isinstance(res, dict):
                    print(f"   {i}. [{res.get('type', 'N/A').upper()}] {res.get('title', 'N/A')}")
                    print(f"      Score: {res.get('relevance_score', 0):.2f} | {res.get('url', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✨ Agent execution completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
