"""
Streamlit UI for the AI Research Agent.
"""

import os
import sys
import json
import asyncio
import streamlit as st
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from graph import run_research_agent
from models import RankedResult

# Page Config
st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .report-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .result-card {
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        transition: transform 0.2s;
    }
    .result-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-right: 5px;
    }
    .tag-paper { background-color: #e3f2fd; color: #1565c0; }
    .tag-repo { background-color: #f3e5f5; color: #7b1fa2; }
    .tag-doc { background-color: #e8f5e9; color: #2e7d32; }
    .tag-discussion { background-color: #fff3e0; color: #ef6c00; }
</style>
""", unsafe_allow_html=True)

def render_result_card(res: RankedResult, index: int):
    """Render a single result card."""
    
    icon_map = {
        "paper": "📄",
        "repository": "💻",
        "documentation": "📚",
        "discussion": "💬"
    }
    
    color_map = {
        "paper": "tag-paper",
        "repository": "tag-repo",
        "documentation": "tag-doc",
        "discussion": "tag-discussion"
    }
    
    icon = icon_map.get(res.type, "🔗")
    tag_class = color_map.get(res.type, "tag-paper")
    
    with st.container():
        st.markdown(f"""
        <div class="result-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <span class="tag {tag_class}">{icon} {res.type.upper()}</span>
                    <span style="color: #666; font-size: 0.9em;">{res.date}</span>
                </div>
                <div style="background-color: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;">
                    Score: {res.relevance_score:.2f}
                </div>
            </div>
            <h4 style="margin: 10px 0 5px 0;"><a href="{res.url}" target="_blank" style="text-decoration: none; color: #1f77b4;">{res.title}</a></h4>
            <p style="font-size: 0.95em; color: #444; margin-bottom: 0;">{res.summary}</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    # Sidebar
    with st.sidebar:
        st.title("🤖 AI Research Agent")
        st.markdown("---")
        
        st.subheader("Settings")
        
        # API Keys (masked input)
        github_token = st.text_input("GitHub Token (Optional)", type="password", help="For higher rate limits")
        if github_token:
            os.environ["GITHUB_TOKEN"] = github_token
            
        openrouter_key = st.text_input("OpenRouter Key (Optional)", type="password", help="For LLM insights")
        if openrouter_key:
            os.environ["OPENROUTER_API_KEY"] = openrouter_key
            
        # Configuration
        st.markdown("### Configuration")
        cache_enabled = st.toggle("Enable Caching", value=True)
        if cache_enabled:
            os.environ["CACHE_ENABLED"] = "true"
            os.environ["CACHE_BACKEND"] = "memory"
        else:
            os.environ["CACHE_ENABLED"] = "false"
            
        st.markdown("---")
        st.markdown("### About")
        st.info(
            "This agent searches ArXiv, GitHub, Documentation, and Discussions "
            "to provide comprehensive research summaries."
        )

    # Main Content
    st.title("Research Assistant")
    st.markdown("Ask a technical question to get a multi-source research report.")
    
    # Search Input
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Research Query", placeholder="e.g., What are the latest developments in multi-agent systems?")
    with col2:
        date_range = st.selectbox("Date Range", ["week", "month", "24h"], index=0)
        
    search_button = st.button("Start Research", type="primary")
    
    if search_button and query:
        with st.status("🕵️‍♂️ Conducting Research...", expanded=True) as status:
            st.write("🧠 Analyzing query...")
            
            # Run the agent
            try:
                # Create a placeholder for logs/progress if we wanted to stream
                # For now, just run it
                result = run_research_agent(query, date_range)
                
                st.write("✅ Research complete!")
                status.update(label="Research Complete!", state="complete", expanded=False)
                
                # === RESULTS DISPLAY ===
                
                # 1. Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Results", result.get("total_results_found", 0))
                m2.metric("Papers", len(result.get("papers", [])))
                m3.metric("Repositories", len(result.get("repositories", [])))
                m4.metric("Discussions", len(result.get("discussions", []) + result.get("documentation", [])))
                
                st.markdown("---")
                
                # 2. Insights Section
                insights = result.get("key_insights", [])
                if insights and not (len(insights) == 1 and "Error" in str(insights[0])):
                    st.subheader("💡 Key Insights")
                    with st.container():
                        st.markdown('<div class="report-card">', unsafe_allow_html=True)
                        for insight in insights:
                            text = insight.get("text", str(insight)) if isinstance(insight, dict) else str(insight)
                            st.markdown(f"- {text}")
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # 3. Tabs for Results
                tab_all, tab_papers, tab_code, tab_web = st.tabs(["🏆 Top Results", "📄 Papers", "💻 Code", "🌐 Web"])
                
                ranked_results = result.get("ranked_results", [])
                
                with tab_all:
                    st.subheader("Top Ranked Results")
                    for i, res in enumerate(ranked_results):
                        render_result_card(res, i)
                        
                with tab_papers:
                    st.subheader("Academic Papers")
                    papers = [r for r in ranked_results if r.type == "paper"]
                    if not papers:
                        st.info("No papers found.")
                    for i, res in enumerate(papers):
                        render_result_card(res, i)
                        
                with tab_code:
                    st.subheader("Repositories")
                    repos = [r for r in ranked_results if r.type == "repository"]
                    if not repos:
                        st.info("No repositories found.")
                    for i, res in enumerate(repos):
                        render_result_card(res, i)
                        
                with tab_web:
                    st.subheader("Documentation & Discussions")
                    web_res = [r for r in ranked_results if r.type in ["documentation", "discussion"]]
                    if not web_res:
                        st.info("No web results found.")
                    for i, res in enumerate(web_res):
                        render_result_card(res, i)
                
                # 4. Action Items
                actions = result.get("action_items", [])
                if actions:
                    st.markdown("---")
                    st.subheader("✅ Recommended Actions")
                    for action in actions:
                        text = action.get("text", str(action)) if isinstance(action, dict) else str(action)
                        st.info(text)
                        
                # 5. JSON Debug
                with st.expander("View Raw JSON Response"):
                    # Helper to serialize
                    st.json(result)
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()
