"""
Agent reasoning visualization component.
Displays the AI agent's thought process and decision-making steps.
"""

import streamlit as st
from typing import Dict, Any, List


def display_agent_reasoning(reasoning_data: Dict[str, Any], title: str = "🧠 Agent's Thought Process"):
    """
    Display agent reasoning in a structured format.
    
    Args:
        reasoning_data: Dictionary containing reasoning information
        title: Title for the reasoning section
    """
    st.subheader(title)
    
    with st.container():
        # Create columns for better layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Main reasoning text
            if "reasoning" in reasoning_data:
                st.markdown("**Analysis:**")
                st.info(reasoning_data["reasoning"])
            
            # Extracted information
            if "extracted_info" in reasoning_data:
                st.markdown("**Extracted Information:**")
                extracted = reasoning_data["extracted_info"]
                for key, value in extracted.items():
                    st.write(f"• **{key.replace('_', ' ').title()}:** {value}")
        
        with col2:
            # Key metrics and scores
            if "lead_score" in reasoning_data:
                st.metric("Lead Score", f"{reasoning_data['lead_score']}/100")
            
            if "priority" in reasoning_data:
                priority_color = {
                    "high": "🔴",
                    "medium": "🟡", 
                    "low": "🟢"
                }.get(reasoning_data["priority"].lower(), "⚪")
                st.metric("Priority", f"{priority_color} {reasoning_data['priority'].title()}")
            
            if "confidence" in reasoning_data:
                st.metric("Confidence", f"{reasoning_data['confidence']}%")


def display_agent_timeline(steps: List[Dict[str, Any]], title: str = "📊 Agent Activity Timeline"):
    """
    Display a timeline of agent actions and decisions.
    
    Args:
        steps: List of step dictionaries with action information
        title: Title for the timeline section
    """
    st.subheader(title)
    
    for i, step in enumerate(steps, 1):
        with st.container():
            col1, col2, col3 = st.columns([1, 6, 2])
            
            with col1:
                st.write(f"**{i}.**")
            
            with col2:
                action = step.get("action", "Unknown action")
                st.write(f"**{action}**")
                
                if "details" in step:
                    st.caption(step["details"])
            
            with col3:
                if "duration" in step:
                    st.caption(f"⏱️ {step['duration']}")
                elif "timestamp" in step:
                    st.caption(f"🕐 {step['timestamp']}")
        
        # Add separator except for last item
        if i < len(steps):
            st.markdown("↓")


def display_confidence_meter(confidence: float, label: str = "Agent Confidence"):
    """
    Display a confidence meter for agent decisions.
    
    Args:
        confidence: Confidence score (0-100)
        label: Label for the confidence meter
    """
    # Determine color based on confidence level
    if confidence >= 80:
        color = "green"
    elif confidence >= 60:
        color = "orange"
    else:
        color = "red"
    
    # Create progress bar
    st.markdown(f"**{label}**")
    st.progress(confidence / 100)
    
    # Add confidence text with color
    confidence_text = f"<span style='color: {color}; font-weight: bold;'>{confidence:.1f}%</span>"
    st.markdown(f"Confidence: {confidence_text}", unsafe_allow_html=True)


def display_decision_factors(factors: Dict[str, Any], title: str = "🎯 Decision Factors"):
    """
    Display factors that influenced the agent's decision.
    
    Args:
        factors: Dictionary of factors and their weights/importance
        title: Title for the factors section
    """
    st.subheader(title)
    
    for factor, details in factors.items():
        with st.expander(f"📋 {factor.replace('_', ' ').title()}"):
            if isinstance(details, dict):
                if "weight" in details:
                    st.metric("Weight", f"{details['weight']}/10")
                if "description" in details:
                    st.write(details["description"])
                if "evidence" in details:
                    st.write("**Evidence:**")
                    for evidence in details["evidence"]:
                        st.write(f"• {evidence}")
            else:
                st.write(str(details)) 