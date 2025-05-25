"""
Reply analysis tab.
Demonstrates analyzing customer replies and generating appropriate responses.
"""

import streamlit as st
from typing import Dict, Any, List
from unittest.mock import patch, Mock

from ui.state.session import get_memory_manager, get_next_lead_id, store_demo_result
from ui.components.agent_visualizer import display_agent_reasoning, display_agent_timeline
from ui.components.crm_viewer import display_crm_record
from ui.components.email_display import display_email_output


def render_reply_tab():
    """Render the reply analysis tab."""
    
    st.markdown("""
    ### 📧 Reply Analysis → Response Demo
    
    This demo shows how the AI agent analyzes customer replies, determines intent, 
    and generates appropriate follow-up responses.
    """)
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📨 Customer Reply Simulation")
        
        # Lead context
        st.markdown("**Lead Context:**")
        lead_name = st.text_input("Lead Name", value="Sarah Chen", placeholder="e.g., John Smith")
        lead_email = st.text_input("Lead Email", value="sarah.chen@techcorp.com", placeholder="e.g., john@company.com")
        lead_company = st.text_input("Company", value="TechCorp Industries", placeholder="e.g., Acme Corp")
        
        # Reply content
        st.markdown("**Customer Reply:**")
        reply_content = st.text_area(
            "Reply Content",
            height=150,
            placeholder="Enter the customer's reply here..."
        )
        
        # Sample reply buttons
        st.markdown("**Sample Replies:**")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Interested Reply"):
                st.session_state.sample_reply = """Hi Alex,

Thanks for reaching out! Your automation platform sounds exactly like what we need. We've been struggling with manual lead management and it's becoming a real bottleneck.

I'd love to see a demo. Are you available for a call next Tuesday or Wednesday afternoon? Also, could you send over that case study you mentioned?

Looking forward to hearing from you.

Best,
Sarah"""
                st.rerun()
            
            if st.button("❓ Info Request"):
                st.session_state.sample_reply = """Hi Alex,

Thanks for your email. The automation platform sounds interesting, but I need to understand more about the technical requirements and pricing.

Could you send me:
- Detailed feature list
- Integration requirements  
- Pricing information
- Implementation timeline

I'll need to review this with our IT team before we can move forward.

Thanks,
Sarah"""
                st.rerun()
        
        with col_b:
            if st.button("📅 Meeting Request"):
                st.session_state.sample_reply = """Hi Alex,

Perfect timing! We're actually in the middle of evaluating automation solutions for Q1 implementation.

Can we schedule a 30-minute demo for next week? I'd like to include our VP of Sales and IT Director in the call.

What's your availability Tuesday-Thursday between 2-4 PM EST?

Best regards,
Sarah Chen
CTO, TechCorp Industries"""
                st.rerun()
            
            if st.button("🚫 Not Interested"):
                st.session_state.sample_reply = """Hi Alex,

Thank you for reaching out, but we're not looking for automation solutions at this time. We've recently implemented a new system and won't be making any changes for the foreseeable future.

Please remove me from your mailing list.

Thanks,
Sarah"""
                st.rerun()
        
        # Auto-fill if sample reply exists
        if hasattr(st.session_state, 'sample_reply') and st.session_state.sample_reply:
            reply_content = st.session_state.sample_reply
        
        # Submit button
        submitted = st.button("🔍 Analyze Reply", type="primary")
    
    with col2:
        st.subheader("ℹ️ What This Demo Shows")
        st.info("""
        **Agent Workflow:**
        1. 📖 Parse reply content and context
        2. 🎯 Determine customer intent (interested, objection, info request, etc.)
        3. 📊 Assess engagement level and sentiment
        4. 🎭 Generate appropriate response strategy
        5. ✉️ Create personalized follow-up email
        6. 📋 Update CRM with interaction data
        
        **Intent Categories:**
        - 🟢 **Interested**: Ready to move forward
        - 🟡 **Info Request**: Needs more details
        - 🔵 **Meeting Request**: Wants to schedule
        - 🟠 **Objection**: Has concerns/barriers
        - 🔴 **Not Interested**: Declining offer
        """)
    
    # Process reply analysis
    if submitted and reply_content and lead_name and lead_email:
        # Clear sample reply
        if hasattr(st.session_state, 'sample_reply'):
            del st.session_state.sample_reply
        
        # Create lead data
        lead_data = {
            "name": lead_name,
            "email": lead_email,
            "company": lead_company or "Unknown Company"
        }
        
        # Generate unique lead ID
        lead_id = get_next_lead_id()
        
        # Process the reply analysis
        with st.spinner("🤖 AI Agent is analyzing the reply..."):
            result = process_reply_analysis_demo(lead_id, lead_data, reply_content)
        
        # Store result for display
        store_demo_result("reply", lead_id, result)
        
        # Display results
        display_reply_analysis_results(lead_id, lead_data, reply_content, result)
    
    # Show previous results if any
    elif hasattr(st.session_state, 'demo_results') and 'reply' in st.session_state.demo_results:
        st.markdown("---")
        st.subheader("📋 Previous Demo Results")
        
        results = st.session_state.demo_results['reply']
        if results:
            latest_lead_id = max(results.keys())
            latest_result = results[latest_lead_id]
            
            lead_data = latest_result.get('lead_data', {})
            reply_content = latest_result.get('reply_content', '')
            
            display_reply_analysis_results(latest_lead_id, lead_data, reply_content, latest_result)


def process_reply_analysis_demo(lead_id: str, lead_data: Dict[str, Any], reply_content: str) -> Dict[str, Any]:
    """
    Process reply analysis using the actual reply intent workflow.
    
    Args:
        lead_id: Unique identifier for the lead
        lead_data: Lead information
        reply_content: The customer's reply content
        
    Returns:
        Dictionary containing analysis results
    """
    memory_manager = get_memory_manager()
    
    # Import the reply analysis function
    from experiments.run_reply_intent import analyze_reply_intent
    
    # Determine intent based on reply content (for demo purposes)
    intent_category = determine_demo_intent(reply_content)
    
    # Mock the LLM response based on intent
    mock_response = generate_mock_intent_response(intent_category, reply_content, lead_data)
    
    # Patch the LLM chain to return our mock response
    with patch('experiments.run_reply_intent.get_intent_analysis_chain') as mock_chain, \
         patch('experiments.run_reply_intent.memory_manager', memory_manager):
        
        mock_llm = Mock()
        mock_llm.run.return_value = mock_response
        mock_chain.return_value = mock_llm
        
        # Run the actual analysis
        analysis = analyze_reply_intent(lead_id, lead_data, reply_content)
    
    # Generate response email
    response_email = generate_response_email(lead_data, reply_content, analysis)
    
    # Get interaction history
    interactions = memory_manager.get_interaction_history(lead_id)
    
    return {
        'lead_data': lead_data,
        'reply_content': reply_content,
        'analysis': analysis,
        'response_email': response_email,
        'interactions': interactions,
        'timeline': generate_reply_timeline(analysis)
    }


def determine_demo_intent(reply_content: str) -> str:
    """Determine intent category based on reply content for demo purposes."""
    
    reply_lower = reply_content.lower()
    
    if any(word in reply_lower for word in ['interested', 'sounds great', 'love to', 'perfect timing', 'exactly what we need']):
        return 'interested'
    elif any(word in reply_lower for word in ['schedule', 'meeting', 'call', 'demo', 'available']):
        return 'meeting_request'
    elif any(word in reply_lower for word in ['pricing', 'cost', 'features', 'requirements', 'more information']):
        return 'info_request'
    elif any(word in reply_lower for word in ['not interested', 'remove me', 'unsubscribe', 'not looking']):
        return 'not_interested'
    elif any(word in reply_lower for word in ['concern', 'but', 'however', 'worry', 'issue']):
        return 'objection'
    else:
        return 'neutral'


def generate_mock_intent_response(intent_category: str, reply_content: str, lead_data: Dict[str, Any]) -> str:
    """Generate a mock LLM response based on the determined intent."""
    
    intent_scores = {
        'interested': 95,
        'meeting_request': 90,
        'info_request': 75,
        'neutral': 50,
        'objection': 30,
        'not_interested': 10
    }
    
    engagement_levels = {
        'interested': 'high',
        'meeting_request': 'high',
        'info_request': 'medium',
        'neutral': 'medium',
        'objection': 'low',
        'not_interested': 'very_low'
    }
    
    sentiments = {
        'interested': 'positive',
        'meeting_request': 'positive',
        'info_request': 'neutral',
        'neutral': 'neutral',
        'objection': 'negative',
        'not_interested': 'negative'
    }
    
    next_actions = {
        'interested': 'Schedule demo call and send case study',
        'meeting_request': 'Coordinate meeting scheduling with calendar availability',
        'info_request': 'Send detailed information packet and follow up',
        'neutral': 'Send additional value proposition and nurture',
        'objection': 'Address concerns and provide reassurance',
        'not_interested': 'Respect decision and add to nurture campaign'
    }
    
    score = intent_scores.get(intent_category, 50)
    engagement = engagement_levels.get(intent_category, 'medium')
    sentiment = sentiments.get(intent_category, 'neutral')
    next_action = next_actions.get(intent_category, 'Follow up appropriately')
    
    return f"""
    Intent: {intent_category}
    Confidence: {score}
    Engagement Level: {engagement}
    Sentiment: {sentiment}
    Urgency: medium
    Next Action: {next_action}
    Key Points: Customer from {lead_data.get('company', 'company')} showing {engagement} engagement with {sentiment} sentiment
    """


def generate_response_email(lead_data: Dict[str, Any], reply_content: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a response email based on the analysis results."""
    
    name = lead_data.get('name', 'there')
    company = lead_data.get('company', 'your company')
    intent = analysis.get('intent', 'neutral')
    
    if intent == 'interested':
        subject = f"Next steps for {company}'s automation project"
        body = f"""Hi {name},

Fantastic! I'm excited to hear that our automation platform aligns with what {company} is looking for.

I've attached the case study I mentioned - it features a company very similar to yours that saw a 60% reduction in manual work within the first quarter.

For the demo, I can show you:
- How our platform would integrate with your current systems
- Specific automation workflows for your use case
- ROI projections based on your team size

I have availability Tuesday and Wednesday afternoon. Would 2:00 PM or 3:30 PM work better for you?

Looking forward to showing you what's possible!

Best regards,
Alex Thompson
Senior Solutions Consultant"""

    elif intent == 'meeting_request':
        subject = f"Demo scheduling for {company}"
        body = f"""Hi {name},

Perfect! I'd be happy to set up a demo for your team.

For a 30-minute session including your VP of Sales and IT Director, I'd recommend we cover:
- Platform overview and key features
- Integration requirements and technical setup
- Implementation timeline and support process
- Q&A session

I have the following slots available Tuesday-Thursday, 2-4 PM EST:
- Tuesday 2:00 PM
- Tuesday 3:30 PM  
- Wednesday 2:30 PM
- Thursday 2:00 PM

Please let me know which works best, and I'll send calendar invites to all attendees.

Best regards,
Alex Thompson"""

    elif intent == 'info_request':
        subject = f"Detailed information for {company}"
        body = f"""Hi {name},

Thank you for your interest! I've attached the information you requested:

📋 **Detailed Feature List**: Complete breakdown of automation capabilities
🔧 **Integration Requirements**: Technical specs and system compatibility  
💰 **Pricing Information**: Transparent pricing tiers and ROI calculator
📅 **Implementation Timeline**: Typical 30-60 day deployment process

I understand you'll need to review this with your IT team. I'm happy to join a technical call to answer any questions they might have about integration or security requirements.

Would it be helpful if I scheduled a brief technical overview call for next week?

Best regards,
Alex Thompson"""

    elif intent == 'not_interested':
        subject = "Thank you for your time"
        body = f"""Hi {name},

Thank you for letting me know. I completely understand that timing isn't right for {company} at the moment.

I've removed you from our immediate follow-up sequence as requested. 

If your automation needs change in the future, please don't hesitate to reach out. I'll be here to help.

Wishing you and {company} continued success!

Best regards,
Alex Thompson"""

    else:  # objection or neutral
        subject = "Addressing your questions about automation"
        body = f"""Hi {name},

Thank you for your thoughtful reply. I understand you may have some questions or concerns about implementing automation at {company}.

Many of our clients had similar considerations initially. I'd be happy to address any specific concerns you might have and share how other companies in your situation have successfully navigated the transition.

Would a brief 15-minute call be helpful to discuss your specific situation? No pressure - just an opportunity to provide clarity.

Best regards,
Alex Thompson"""

    return {
        'subject': subject,
        'body': body,
        'recipient': lead_data.get('email'),
        'from': 'sales@yourcompany.com',
        'metadata': {
            'generated_at': '2024-01-10 11:15:00',
            'intent': intent,
            'confidence': analysis.get('confidence', 50),
            'tone': 'professional',
            'template_used': f'reply_{intent}'
        }
    }


def generate_reply_timeline(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a timeline of agent actions for reply analysis."""
    
    intent = analysis.get('intent', 'neutral')
    confidence = analysis.get('confidence', 50)
    
    return [
        {
            "action": "Parse Reply Content",
            "details": "Extracted key phrases and context from customer reply",
            "duration": "0.3s"
        },
        {
            "action": "Analyze Intent",
            "details": f"Identified intent as '{intent}' with {confidence}% confidence",
            "duration": "1.2s"
        },
        {
            "action": "Assess Sentiment",
            "details": f"Determined sentiment: {analysis.get('sentiment', 'neutral')}",
            "duration": "0.8s"
        },
        {
            "action": "Evaluate Engagement",
            "details": f"Engagement level: {analysis.get('engagement_level', 'medium')}",
            "duration": "0.5s"
        },
        {
            "action": "Generate Response Strategy",
            "details": f"Selected appropriate response approach for {intent} intent",
            "duration": "0.7s"
        },
        {
            "action": "Create Response Email",
            "details": "Generated personalized response based on analysis",
            "duration": "2.3s"
        },
        {
            "action": "Update CRM",
            "details": "Logged interaction and updated lead status",
            "duration": "0.4s"
        }
    ]


def display_reply_analysis_results(lead_id: str, lead_data: Dict[str, Any], reply_content: str, result: Dict[str, Any]):
    """Display the reply analysis results in organized sections."""
    
    st.markdown("---")
    st.markdown("## 🎯 Reply Analysis Results")
    
    analysis = result.get('analysis', {})
    response_email = result.get('response_email', {})
    interactions = result.get('interactions', [])
    timeline = result.get('timeline', [])
    
    # Show original reply
    with st.expander("📨 Original Customer Reply", expanded=False):
        st.text_area("Reply Content", value=reply_content, height=120, disabled=True)
    
    # Agent reasoning section
    display_agent_reasoning(analysis)
    
    # Timeline section
    if timeline:
        display_agent_timeline(timeline)
    
    # Response email section
    if response_email:
        st.markdown("### 📧 Generated Response")
        display_email_output(response_email)
    
    # CRM update section
    st.markdown("### 🗂️ CRM Update")
    display_crm_record(lead_data, analysis, interactions, title="Updated Lead Record")
    
    # Clear results button
    if st.button("🗑️ Clear Results"):
        if hasattr(st.session_state, 'demo_results') and 'reply' in st.session_state.demo_results:
            st.session_state.demo_results['reply'] = {}
        st.rerun() 