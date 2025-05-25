"""
CRM data visualization component.
Displays lead information and interaction history in a CRM-like format.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime


def display_crm_record(
    lead_data: Dict[str, Any], 
    qualification: Optional[Dict[str, Any]] = None,
    interactions: Optional[List[Dict[str, Any]]] = None,
    title: str = "🗂 CRM Record"
):
    """
    Display a complete CRM record for a lead.
    
    Args:
        lead_data: Basic lead information
        qualification: Lead qualification data
        interactions: List of interactions with the lead
        title: Title for the CRM section
    """
    st.subheader(title)
    
    # Lead Information Section
    with st.container():
        st.markdown("### 👤 Lead Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {lead_data.get('name', 'N/A')}")
            st.write(f"**Email:** {lead_data.get('email', 'N/A')}")
            st.write(f"**Company:** {lead_data.get('company', 'N/A')}")
        
        with col2:
            st.write(f"**Role:** {lead_data.get('role', 'N/A')}")
            st.write(f"**Phone:** {lead_data.get('phone', 'N/A')}")
            st.write(f"**Source:** {lead_data.get('source', 'Contact Form')}")
    
    # Qualification Section
    if qualification:
        st.markdown("### 📊 Qualification Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            score = qualification.get('lead_score', 0)
            score_color = "green" if score >= 70 else "orange" if score >= 50 else "red"
            st.markdown(f"**Lead Score:** <span style='color: {score_color}; font-weight: bold;'>{score}/100</span>", 
                       unsafe_allow_html=True)
        
        with col2:
            priority = qualification.get('priority', 'unknown').title()
            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
            st.write(f"**Priority:** {priority_emoji} {priority}")
        
        with col3:
            disposition = qualification.get('lead_disposition', 'unknown').title()
            st.write(f"**Status:** {disposition}")
        
        # Additional qualification details
        if qualification.get('reasoning'):
            with st.expander("📝 Qualification Notes"):
                st.write(qualification['reasoning'])
        
        if qualification.get('next_action'):
            st.info(f"**Next Action:** {qualification['next_action']}")
    
    # Interactions Section
    if interactions:
        st.markdown("### 📞 Interaction History")
        display_interaction_timeline(interactions)


def display_before_after_crm(
    before_data: Dict[str, Any], 
    after_data: Dict[str, Any],
    title: str = "🔄 CRM Update Comparison"
):
    """
    Display before and after CRM states side by side.
    
    Args:
        before_data: CRM state before agent action
        after_data: CRM state after agent action
        title: Title for the comparison section
    """
    st.subheader(title)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Before")
        with st.container():
            _display_crm_summary(before_data, border_color="lightgray")
    
    with col2:
        st.markdown("#### After")
        with st.container():
            _display_crm_summary(after_data, border_color="lightgreen")


def _display_crm_summary(data: Dict[str, Any], border_color: str = "lightgray"):
    """Display a summary view of CRM data."""
    
    # Create a styled container
    st.markdown(f"""
    <div style="border: 2px solid {border_color}; padding: 15px; border-radius: 10px; margin: 10px 0;">
    """, unsafe_allow_html=True)
    
    # Basic info
    if 'name' in data:
        st.write(f"**Contact:** {data['name']}")
    if 'company' in data:
        st.write(f"**Company:** {data['company']}")
    
    # Status info
    if 'lead_score' in data:
        st.write(f"**Score:** {data['lead_score']}/100")
    if 'priority' in data:
        st.write(f"**Priority:** {data['priority'].title()}")
    if 'lead_disposition' in data:
        st.write(f"**Status:** {data['lead_disposition'].title()}")
    if 'next_action' in data:
        st.write(f"**Next Action:** {data['next_action']}")
    
    st.markdown("</div>", unsafe_allow_html=True)


def display_interaction_timeline(interactions: List[Dict[str, Any]]):
    """
    Display interaction history in a timeline format.
    
    Args:
        interactions: List of interaction records
    """
    if not interactions:
        st.info("No interactions recorded yet.")
        return
    
    for interaction in interactions:
        event_type = interaction.get('event_type', 'unknown')
        timestamp = interaction.get('timestamp', 'Unknown time')
        event_data = interaction.get('event_data', {})
        
        # Format timestamp if it's a datetime string
        try:
            if isinstance(timestamp, str):
                # Try to parse ISO format timestamp
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_time = str(timestamp)
        except (ValueError, TypeError, AttributeError):
            formatted_time = str(timestamp)
        
        # Choose emoji based on event type
        event_emoji = {
            'email_sent': '📧',
            'email_received': '📨',
            'call_made': '📞',
            'meeting_scheduled': '📅',
            'qualification_updated': '📊',
            'reply_received': '💬',
            'follow_up_scheduled': '⏰'
        }.get(event_type, '📝')
        
        with st.container():
            col1, col2, col3 = st.columns([1, 6, 2])
            
            with col1:
                st.write(event_emoji)
            
            with col2:
                st.write(f"**{event_type.replace('_', ' ').title()}**")
                
                # Display relevant event data
                if event_type == 'email_sent' and 'subject' in event_data:
                    st.caption(f"Subject: {event_data['subject']}")
                elif event_type == 'meeting_scheduled' and 'datetime' in event_data:
                    st.caption(f"Scheduled for: {event_data['datetime']}")
                elif event_type == 'qualification_updated' and 'lead_score' in event_data:
                    st.caption(f"New score: {event_data['lead_score']}/100")
                elif 'description' in event_data:
                    st.caption(event_data['description'])
            
            with col3:
                st.caption(formatted_time)
        
        st.markdown("---")


def display_lead_metrics(qualification: Dict[str, Any]):
    """
    Display key lead metrics in a dashboard format.
    
    Args:
        qualification: Lead qualification data
    """
    st.markdown("### 📈 Lead Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = qualification.get('lead_score', 0)
        st.metric("Lead Score", f"{score}/100", delta=None)
    
    with col2:
        priority = qualification.get('priority', 'unknown').title()
        st.metric("Priority", priority)
    
    with col3:
        sentiment = qualification.get('sentiment', 'neutral').title()
        st.metric("Sentiment", sentiment)
    
    with col4:
        urgency = qualification.get('urgency', 'low').title()
        st.metric("Urgency", urgency) 