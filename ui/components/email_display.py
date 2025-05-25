"""
Email display component.
Formats and displays AI-generated emails in a professional email client style.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime


def display_email_output(
    email_data: Dict[str, Any], 
    title: str = "✉️ AI-Crafted Email",
    show_metadata: bool = True
):
    """
    Display an AI-generated email in email client format.
    
    Args:
        email_data: Dictionary containing email information
        title: Title for the email section
        show_metadata: Whether to show email metadata
    """
    st.subheader(title)
    
    # Email container with styling
    with st.container():
        # Email header
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px 10px 0 0; border: 1px solid #dee2e6;">
        """, unsafe_allow_html=True)
        
        # Email fields
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("**From:**")
            st.markdown("**To:**")
            st.markdown("**Subject:**")
        
        with col2:
            from_email = email_data.get('from', 'sales@yourcompany.com')
            to_email = email_data.get('recipient', email_data.get('to', 'N/A'))
            subject = email_data.get('subject', 'No Subject')
            
            st.markdown(f"`{from_email}`")
            st.markdown(f"`{to_email}`")
            st.markdown(f"**{subject}**")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Email body
        st.markdown("""
        <div style="background-color: white; padding: 20px; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 10px 10px;">
        """, unsafe_allow_html=True)
        
        body = email_data.get('body', email_data.get('content', 'No content'))
        
        # Format email body with proper line breaks
        formatted_body = body.replace('\n', '<br>')
        st.markdown(formatted_body, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Email metadata
        if show_metadata and 'metadata' in email_data:
            with st.expander("📊 Email Generation Details"):
                metadata = email_data['metadata']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'generated_at' in metadata:
                        st.write(f"**Generated:** {metadata['generated_at']}")
                    if 'template_used' in metadata:
                        st.write(f"**Template:** {metadata['template_used']}")
                
                with col2:
                    if 'lead_score' in metadata:
                        st.write(f"**Lead Score:** {metadata['lead_score']}/100")
                    if 'personalization_level' in metadata:
                        st.write(f"**Personalization:** {metadata['personalization_level']}")
                
                with col3:
                    if 'tone' in metadata:
                        st.write(f"**Tone:** {metadata['tone'].title()}")
                    if 'priority' in metadata:
                        st.write(f"**Priority:** {metadata['priority'].title()}")


def display_email_draft_options(
    email_variants: list[Dict[str, Any]], 
    title: str = "📝 Email Draft Options"
):
    """
    Display multiple email draft options for selection.
    
    Args:
        email_variants: List of email draft variants
        title: Title for the options section
    """
    st.subheader(title)
    
    if not email_variants:
        st.info("No email drafts available.")
        return
    
    # Create tabs for different variants
    if len(email_variants) > 1:
        tab_labels = [f"Draft {i+1}" for i in range(len(email_variants))]
        tabs = st.tabs(tab_labels)
        
        for i, (tab, email) in enumerate(zip(tabs, email_variants)):
            with tab:
                display_email_output(email, title=f"Draft {i+1}", show_metadata=False)
                
                # Add selection button
                if st.button(f"Select Draft {i+1}", key=f"select_draft_{i}"):
                    st.session_state.selected_email = email
                    st.success(f"Draft {i+1} selected!")
    else:
        display_email_output(email_variants[0], show_metadata=False)


def display_email_preview_with_actions(
    email_data: Dict[str, Any],
    title: str = "📧 Email Preview & Actions"
):
    """
    Display email with action buttons (send, edit, save as template).
    
    Args:
        email_data: Email data to display
        title: Title for the preview section
    """
    st.subheader(title)
    
    # Display the email
    display_email_output(email_data, title="", show_metadata=False)
    
    # Action buttons
    st.markdown("### Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📤 Send Email", type="primary"):
            st.success("Email sent successfully!")
            # Here you would integrate with actual email sending
    
    with col2:
        if st.button("✏️ Edit Draft"):
            st.info("Opening email editor...")
            # Here you would open an email editor
    
    with col3:
        if st.button("💾 Save as Template"):
            st.success("Email saved as template!")
            # Here you would save the email as a template
    
    with col4:
        if st.button("📋 Copy to Clipboard"):
            # In a real app, this would copy to clipboard
            st.info("Email copied to clipboard!")


def display_email_analytics(email_stats: Dict[str, Any]):
    """
    Display email performance analytics.
    
    Args:
        email_stats: Dictionary containing email statistics
    """
    st.subheader("📈 Email Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        open_rate = email_stats.get('open_rate', 0)
        st.metric("Open Rate", f"{open_rate}%", delta=f"+{open_rate-20}%")
    
    with col2:
        click_rate = email_stats.get('click_rate', 0)
        st.metric("Click Rate", f"{click_rate}%", delta=f"+{click_rate-5}%")
    
    with col3:
        response_rate = email_stats.get('response_rate', 0)
        st.metric("Response Rate", f"{response_rate}%", delta=f"+{response_rate-10}%")
    
    with col4:
        conversion_rate = email_stats.get('conversion_rate', 0)
        st.metric("Conversion Rate", f"{conversion_rate}%", delta=f"+{conversion_rate-3}%")


def create_email_composer(
    recipient_info: Dict[str, Any],
    template_suggestions: Optional[list[str]] = None
) -> Dict[str, Any]:
    """
    Create an interactive email composer interface.
    
    Args:
        recipient_info: Information about the email recipient
        template_suggestions: List of suggested email templates
        
    Returns:
        Dictionary containing the composed email data
    """
    st.subheader("✍️ Compose Email")
    
    # Recipient information display
    with st.expander("👤 Recipient Information"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {recipient_info.get('name', 'N/A')}")
            st.write(f"**Company:** {recipient_info.get('company', 'N/A')}")
        with col2:
            st.write(f"**Role:** {recipient_info.get('role', 'N/A')}")
            st.write(f"**Email:** {recipient_info.get('email', 'N/A')}")
    
    # Email composition form
    with st.form("email_composer"):
        # Template selection
        if template_suggestions:
            template = st.selectbox(
                "📋 Email Template",
                ["Custom"] + template_suggestions,
                help="Choose a template or write a custom email"
            )
        
        # Email fields
        subject = st.text_input(
            "📧 Subject Line",
            placeholder="Enter email subject...",
            help="Keep it concise and compelling"
        )
        
        body = st.text_area(
            "✍️ Email Body",
            height=200,
            placeholder="Write your email content here...",
            help="Personalize the message for better engagement"
        )
        
        # Email options
        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox("🎭 Tone", ["Professional", "Friendly", "Formal", "Casual"])
            priority = st.selectbox("⚡ Priority", ["Normal", "High", "Low"])
        
        with col2:
            include_signature = st.checkbox("✍️ Include Signature", value=True)
        
        # Submit button
        submitted = st.form_submit_button("📤 Generate Email", type="primary")
        
        if submitted and subject and body:
            email_data = {
                'subject': subject,
                'body': body,
                'recipient': recipient_info.get('email'),
                'tone': tone.lower(),
                'priority': priority.lower(),
                'include_signature': include_signature,
                'metadata': {
                    'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'tone': tone.lower(),
                    'priority': priority.lower(),
                    'template_used': template if template_suggestions else 'custom'
                }
            }
            
            return email_data
    
    return {} 