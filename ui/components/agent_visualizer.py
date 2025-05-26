"""
Agent reasoning visualization component.
Displays the AI agent's thought process and decision-making steps.
"""

import streamlit as st
from typing import Dict, Any, List


def display_agent_reasoning(reasoning_data: Dict[str, Any], title: str = "🧠 Agent's Thought Process"):
    """
    Display agent reasoning in a structured, visually appealing format for both qualification and reply analysis.
    Args:
        reasoning_data: Dictionary or model containing reasoning information
        title: Title for the reasoning section
    """
    st.subheader(title)

    # Try to support both dict and pydantic model
    if hasattr(reasoning_data, 'model_dump'):
        data = reasoning_data.model_dump()
    elif hasattr(reasoning_data, 'dict'):
        data = reasoning_data.dict()
    else:
        data = dict(reasoning_data)

    # Main summary card
    st.markdown("""
    <div style='background: #f8f9fa; border-radius: 10px; padding: 18px 20px; margin-bottom: 12px; box-shadow: 0 1px 4px #e9ecef;'>
    <b>Summary:</b> {summary}
    </div>
    """.format(summary=data.get('reasoning', 'No reasoning provided.')), unsafe_allow_html=True)

    # Key metrics in columns
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    score = data.get('lead_score', None)
    score_color = "green" if score is not None and score >= 80 else "orange" if score is not None and score >= 50 else "red"
    priority_val = data.get('priority', None)
    priority = str(priority_val).title() if priority_val else "Unknown"
    priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
    disposition_val = data.get('disposition', None)
    disposition = str(disposition_val).title() if disposition_val else "Unknown"
    confidence = data.get('confidence', None)
    sentiment_val = data.get('sentiment', None)
    sentiment = str(sentiment_val).title() if sentiment_val else "Unknown"
    urgency_val = data.get('urgency', None)
    valid_urgencies = ["Low", "Medium", "High", "Urgent"]
    if not urgency_val or str(urgency_val).strip().lower() == "not specified" or str(urgency_val).title() not in valid_urgencies:
        urgency = "Not specified"
    else:
        urgency = str(urgency_val).title()
    intent_val = data.get('intent', None)
    intent = str(intent_val).replace("_", " ").title() if intent_val else "Unknown"
    next_action = data.get('next_action', None)
    follow_up = data.get('follow_up_timing', None)

    with col1:
        if score is not None:
            st.metric("Lead Score", f"{score}/100")
            st.markdown(f"<span style='color:{score_color}; font-weight:bold;'>{score}/100</span>", unsafe_allow_html=True)
        st.metric("Priority", f"{priority_emoji} {priority}")
    with col2:
        st.metric("Disposition", disposition)
        if confidence is not None:
            st.metric("Confidence", f"{confidence}%")
    with col3:
        st.metric("Sentiment", sentiment)
        st.metric("Urgency", urgency)
    with col4:
        st.metric("Intent", intent)
        if next_action:
            st.markdown(f"<b>Next Action:</b> {next_action}", unsafe_allow_html=True)
        if follow_up:
            st.markdown(f"<b>Follow-up Timing:</b> {follow_up}", unsafe_allow_html=True)

    # Progressive disclosure for full details
    with st.expander("Show all agent analysis fields"):
        for k, v in data.items():
            st.write(f"**{k.replace('_', ' ').title()}:** {v}")


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