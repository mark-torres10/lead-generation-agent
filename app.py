"""
Main Streamlit application for the Leads AI Agent Demo.
"""

import streamlit as st

# Import tab components
from ui.tabs.qualify_tab import render_qualify_tab
from ui.tabs.reply_tab import render_reply_tab
from ui.tabs.meeting_tab import render_meeting_tab
from ui.tabs.discover_tab import render_discover_tab
from ui.tabs.metrics_evals_tab import render_metrics_evals_tab

# Import session state management
from ui.state.session import initialize_session_state


def main():
    """Main application entry point."""
    
    # Initialize session state
    initialize_session_state()
    
    # Page configuration
    st.set_page_config(
        page_title="Leads AI Agent Demo",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Main header
    st.title("🤖 Leads AI Agent Demo")
    st.markdown("""
    **Experience the power of AI-driven lead management**
    
    This interactive demo showcases how our AI agent handles the complete lead lifecycle - 
    from initial contact form submissions to meeting scheduling and follow-up communications.
    """)
    
    # Create tabs
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Contact Form → Follow-up",
        "📧 Reply Analysis → Response",
        "📅 Meeting Scheduling",
        "🔎 Discover New Leads",
        "📊 Metrics and Evaluations"
    ])
    
    with tab0:
        render_qualify_tab()
    
    with tab1:
        render_reply_tab()
    
    with tab2:
        render_meeting_tab()
    
    with tab3:
        render_discover_tab()
    
    with tab4:
        render_metrics_evals_tab()
    
    # Sidebar with additional information
    with st.sidebar:
        st.markdown("## 🎯 Demo Features")
        st.markdown("""
        **🔍 What You'll See:**
        - Real-time AI reasoning
        - Lead scoring & prioritization
        - Personalized email generation
        - CRM integration simulation
        - Meeting coordination
        
        **🛠️ Technologies:**
        - Large Language Models (LLM)
        - Natural Language Processing
        - Automated Workflow Engine
        - CRM Integration APIs
        - Calendar Management
        """)
        
        st.markdown("---")
        st.markdown("## 📊 Demo Statistics")
        
        # Show demo usage stats if available
        if hasattr(st.session_state, 'demo_results'):
            qualify_count = len(st.session_state.demo_results.get('qualify', {}))
            reply_count = len(st.session_state.demo_results.get('reply', {}))
            meeting_count = len(st.session_state.demo_results.get('meeting', {}))
            
            st.metric("Qualifications Run", qualify_count)
            st.metric("Replies Analyzed", reply_count)
            st.metric("Meetings Scheduled", meeting_count)
        else:
            st.metric("Qualifications Run", 0)
            st.metric("Replies Analyzed", 0)
            st.metric("Meetings Scheduled", 0)
        
        st.markdown("---")
        st.markdown("## 🔄 Reset Demo")
        if st.button("🗑️ Clear All Demo Data"):
            # Clear all demo results
            if hasattr(st.session_state, 'demo_results'):
                st.session_state.demo_results = {'qualify': {}, 'reply': {}, 'meeting': {}}
            if hasattr(st.session_state, 'lead_counter'):
                st.session_state.lead_counter = 0
            st.success("Demo data cleared!")
            st.rerun()


if __name__ == "__main__":
    main() 