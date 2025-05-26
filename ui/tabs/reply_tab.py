"""
Reply analysis tab.
Demonstrates analyzing customer replies and generating appropriate responses.
"""

import streamlit as st
from typing import Dict, Any, List
from unittest.mock import patch, Mock

from ui.state.session import get_memory_manager, store_demo_result
from ui.components.agent_visualizer import display_agent_timeline
from ui.components.email_display import display_email_output
from agents.models import ReplyAnalysisResult
from integrations.google.email_manager import EmailManager
from integrations.slack_manager import SlackManager


def render_reply_tab():
    """Render the reply analysis tab."""
    st.markdown("""
    ### 📧 Reply Analysis → Response Demo
    
    This demo shows how the AI agent analyzes customer replies, determines intent, 
    and generates appropriate follow-up responses.
    """)
    
    # Initialize sample data in session state if not exists
    if 'reply_sample_data' not in st.session_state:
        st.session_state.reply_sample_data = {}
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📨 Customer Reply Simulation")
        
        # Get current values (either from sample data or defaults)
        current_data = st.session_state.reply_sample_data
        
        # Lead context
        st.markdown("**Lead Context:**")
        lead_name = st.text_input(
            "Lead Name", 
            value=current_data.get("lead_name", "Sarah Chen"), 
            placeholder="e.g., John Smith"
        )
        lead_email = st.text_input(
            "Lead Email", 
            value=current_data.get("lead_email", "sarah.chen@techcorp.com"), 
            placeholder="e.g., john@company.com"
        )
        lead_company = st.text_input(
            "Company", 
            value=current_data.get("lead_company", "TechCorp Industries"), 
            placeholder="e.g., Acme Corp"
        )
        
        # Reply content
        st.markdown("**Customer Reply:**")
        reply_content = st.text_area(
            "Reply Content",
            value=current_data.get("reply_content", ""),
            height=150,
            placeholder="Enter the customer's reply here..."
        )
        
        # Sample reply buttons
        st.markdown("**Sample Replies:**")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Interested Reply", key="reply_interested_btn"):
                st.session_state.reply_sample_data = {
                    "lead_name": "Sarah Chen",
                    "lead_email": "sarah.chen@techcorp.com",
                    "lead_company": "TechCorp Industries",
                    "reply_content": """Hi Alex,

Thanks for reaching out! Your automation platform sounds exactly like what we need. We've been struggling with manual lead management and it's becoming a real bottleneck.

I'd love to see a demo. Are you available for a call next Tuesday or Wednesday afternoon? Also, could you send over that case study you mentioned?

Looking forward to hearing from you.

Best,
Sarah"""
                }
                st.rerun()
            
            if st.button("❓ Info Request", key="reply_info_request_btn"):
                st.session_state.reply_sample_data = {
                    "lead_name": "Sarah Chen",
                    "lead_email": "sarah.chen@techcorp.com",
                    "lead_company": "TechCorp Industries",
                    "reply_content": """Hi Alex,

Thanks for your email. The automation platform sounds interesting, but I need to understand more about the technical requirements and pricing.

Could you send me:
- Detailed feature list
- Integration requirements  
- Pricing information
- Implementation timeline

I'll need to review this with our IT team before we can move forward.

Thanks,
Sarah"""
                }
                st.rerun()
        
        with col_b:
            if st.button("📅 Meeting Request", key="reply_meeting_request_btn"):
                st.session_state.reply_sample_data = {
                    "lead_name": "Sarah Chen",
                    "lead_email": "sarah.chen@techcorp.com",
                    "lead_company": "TechCorp Industries",
                    "reply_content": """Hi Alex,

Perfect timing! We're actually in the middle of evaluating automation solutions for Q1 implementation.

Can we schedule a 30-minute demo for next week? I'd like to include our VP of Sales and IT Director in the call.

What's your availability Tuesday-Thursday between 2-4 PM EST?

Best regards,
Sarah Chen
CTO, TechCorp Industries"""
                }
                st.rerun()
            
            if st.button("🚫 Not Interested", key="reply_not_interested_btn"):
                st.session_state.reply_sample_data = {
                    "lead_name": "Sarah Chen",
                    "lead_email": "sarah.chen@techcorp.com",
                    "lead_company": "TechCorp Industries",
                    "reply_content": """Hi Alex,

Thank you for reaching out, but we're not looking for automation solutions at this time. We've recently implemented a new system and won't be making any changes for the foreseeable future.

Please remove me from your mailing list.

Thanks,
Sarah"""
                }
                st.rerun()
        
        # Submit button
        submitted = st.button("🔍 Analyze Reply", type="primary", key="reply_analyze_btn")
    
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
        # Clear sample data after submission
        st.session_state.reply_sample_data = {}
        # Create lead data
        lead_data = {
            "name": lead_name,
            "email": lead_email,
            "company": lead_company or "Unknown Company"
        }
        # Use DB-backed lead_id lookup/creation
        memory_manager = get_memory_manager()
        lead_id = memory_manager.get_or_create_lead_id(lead_email, lead_data)
        # Process the reply analysis
        with st.spinner("🤖 AI Agent is analyzing the reply..."):
            result = process_reply_analysis_demo(lead_id, lead_data, reply_content)
        # Store result for display (store as dict for consistency)
        store_demo_result("reply", lead_id, {
            "lead_data": lead_data,
            "reply_content": reply_content,
            "result": result
        })
        # --- EMAIL SENDING LOGIC ---
        send_reply_analysis_email(lead_data, reply_content, result)
        # --- SLACK NOTIFICATION LOGIC ---
        try:
            slack = SlackManager()
            response_email = generate_response_email(lead_data, reply_content, result)
            slack.send_message(
                channel_name="inbound-email-leads",
                title=response_email['subject'],
                body=response_email['body']
            )
        except Exception as e:
            print(f"Error sending Slack notification: {e}")
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
            
            # Handle both dict and ReplyAnalysisResult cases
            if isinstance(latest_result, dict):
                lead_data = latest_result.get('lead_data', {})
                reply_content = latest_result.get('reply_content', '')
                result_obj = latest_result.get('result', latest_result)
            else:
                # It's a ReplyAnalysisResult object
                lead_data = getattr(latest_result, 'lead_data', {})
                reply_content = getattr(latest_result, 'reply_content', '')
                result_obj = latest_result
            
            display_reply_analysis_results(latest_lead_id, lead_data, reply_content, result_obj)


def process_reply_analysis_demo(lead_id: str, lead_data: Dict[str, Any], reply_content: str) -> ReplyAnalysisResult:
    """
    Process reply analysis using the actual reply analysis workflow.
    Args:
        lead_id: Unique identifier for the lead
        lead_data: Lead context data
        reply_content: The reply text
    Returns:
        ReplyAnalysisResult containing analysis results
    """
    memory_manager = get_memory_manager()
    from workflows.run_reply_intent import analyze_reply_intent
    from agents.models import ReplyAnalysisResult

    # Determine intent and generate a mock LLM response based on the reply content
    intent_category = determine_demo_intent(reply_content)
    mock_llm_response = generate_mock_intent_response(intent_category, reply_content, lead_data)

    # Patch the LLM chain to return our dynamic mock response
    with patch('agents.agent_core.AgentCore.create_llm_chain') as mock_chain, \
         patch('workflows.run_reply_intent.memory_manager', memory_manager):
        mock_llm = Mock()
        mock_llm.run.return_value = mock_llm_response
        mock_chain.return_value = mock_llm
        analysis = analyze_reply_intent({"lead_id": lead_id, **lead_data, "reply_text": reply_content})
    # Always return a ReplyAnalysisResult for UI safety
    if isinstance(analysis, dict):
        # Fill required fields with defaults if missing
        defaults = dict(
            disposition="maybe", confidence=50, sentiment="neutral", urgency="medium", reasoning="No reasoning provided", next_action="Manual review required", follow_up_timing="1-week", intent="neutral"
        )
        for k, v in defaults.items():
            analysis.setdefault(k, v)
        analysis = ReplyAnalysisResult(**analysis)
    return analysis


def determine_demo_intent(reply_content: str) -> str:
    """Determine intent category based on reply content for demo purposes.
    Order of checks is important: check negative/edge cases before positive substrings to avoid misclassification."""
    reply_lower = reply_content.lower()
    # Check negative/edge cases first
    if any(word in reply_lower for word in ['not interested', 'remove me', 'unsubscribe', 'not looking']):
        return 'not_interested'
    elif any(word in reply_lower for word in ['concern', 'but', 'however', 'worry', 'issue']):
        return 'objection'
    elif any(word in reply_lower for word in ['pricing', 'cost', 'features', 'requirements', 'more information']):
        return 'info_request'
    elif any(word in reply_lower for word in ['schedule', 'meeting', 'call', 'demo', 'available']):
        return 'meeting_request'
    elif any(word in reply_lower for word in ['interested', 'sounds great', 'love to', 'perfect timing', 'exactly what we need']):
        return 'interested'
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
    
    urgency_levels = {
        'interested': 'high',
        'meeting_request': 'high',
        'info_request': 'medium',
        'neutral': 'medium',
        'objection': 'low',
        'not_interested': 'low'
    }
    
    next_actions = {
        'interested': 'Schedule demo call and send case study',
        'meeting_request': 'Coordinate meeting scheduling with calendar availability',
        'info_request': 'Send detailed information packet and follow up',
        'neutral': 'Send additional value proposition and nurture',
        'objection': 'Address concerns and provide reassurance',
        'not_interested': 'Respect decision and add to nurture campaign'
    }
    
    follow_up_timings = {
        'interested': 'immediate',
        'meeting_request': 'immediate',
        'info_request': '1-week',
        'neutral': '1-week',
        'objection': '1-month',
        'not_interested': '3-months'
    }
    
    # Map intent categories to disposition values expected by parser
    disposition_mapping = {
        'interested': 'engaged',
        'meeting_request': 'engaged',
        'info_request': 'maybe',
        'neutral': 'maybe',
        'objection': 'disinterested',
        'not_interested': 'disinterested'
    }
    
    score = intent_scores.get(intent_category, 50)
    engagement = engagement_levels.get(intent_category, 'medium')
    sentiment = sentiments.get(intent_category, 'neutral')
    urgency = urgency_levels.get(intent_category, 'medium')
    next_action = next_actions.get(intent_category, 'Follow up appropriately')
    follow_up_timing = follow_up_timings.get(intent_category, '1-week')
    disposition = disposition_mapping.get(intent_category, 'maybe')
    
    # Generate reasoning based on the reply content and intent
    reasoning_templates = {
        'interested': f"Customer from {lead_data.get('company', 'company')} explicitly expresses strong interest in the solution. Reply content shows clear buying signals and {engagement} engagement.",
        'meeting_request': f"Customer from {lead_data.get('company', 'company')} is actively requesting a meeting or demo, indicating {engagement} intent to move forward in the sales process.",
        'info_request': f"Customer from {lead_data.get('company', 'company')} is seeking additional information, showing {engagement} interest but needs more details before proceeding.",
        'neutral': f"Customer from {lead_data.get('company', 'company')} provides a neutral response with {engagement} engagement without clear buying signals or strong objections.",
        'objection': f"Customer from {lead_data.get('company', 'company')} raises concerns or objections that need to be addressed before moving forward, showing {engagement} engagement.",
        'not_interested': f"Customer from {lead_data.get('company', 'company')} clearly indicates lack of interest with {engagement} engagement and requests to be removed from follow-up."
    }
    
    reasoning = reasoning_templates.get(intent_category, f"Standard analysis for {intent_category} intent category.")
    
    # Format response to match what parse_reply_analysis_response expects
    return f"""DISPOSITION: {disposition}
CONFIDENCE: {score}
SENTIMENT: {sentiment}
URGENCY: {urgency}
REASONING: {reasoning}
NEXT_ACTION: {next_action}
FOLLOW_UP_TIMING: {follow_up_timing}"""


def generate_response_email(lead_data: Dict[str, Any], reply_content: str, analysis: ReplyAnalysisResult) -> Dict[str, Any]:
    """Generate a response email based on the analysis results."""
    
    name = lead_data.get('name', 'there')
    company = lead_data.get('company', 'your company')
    disposition = analysis.disposition
    
    if disposition == 'engaged':
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

    elif disposition == 'maybe':
        # Check if it's an info request based on next_action
        next_action = analysis.next_action.lower()
        if 'information' in next_action or 'details' in next_action:
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
        elif 'meeting' in next_action.lower() or 'demo' in next_action.lower():
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
        else:
            # General nurture approach
            subject = f"Solutions for {company}'s automation needs"
            body = f"""Hi {name},

Thanks for your interest in our automation solutions. I appreciate you taking the time to reach out.

Based on your message, it sounds like {company} could benefit from streamlining your current processes. Our platform helps companies like yours automate repetitive tasks and improve efficiency.

I'd be happy to schedule a brief call to learn more about your specific needs and show you how our solution might help.

Would you prefer a quick 15-minute call or would you like me to send some information first?

Best regards,
Alex Thompson
Solutions Consultant
sales@yourcompany.com"""

    else:  # disinterested
        subject = "Thank you for your time"
        body = f"""Hi {name},

Thank you for letting me know. I completely understand that timing isn't right for {company} at the moment.

I've removed you from our immediate follow-up sequence as requested. 

If your automation needs change in the future, please don't hesitate to reach out. I'll be here to help.

Wishing you and {company} continued success!

Best regards,
Alex Thompson"""

    return {
        'subject': subject,
        'body': body,
        'recipient': lead_data.get('email'),
        'from': 'sales@yourcompany.com',
        'metadata': {
            'generated_at': '2024-01-10 11:15:00',
            'disposition': disposition,
            'confidence': analysis.confidence,
            'tone': 'professional',
            'template_used': f'reply_{disposition}'
        }
    }


def generate_reply_timeline(analysis: ReplyAnalysisResult) -> List[Dict[str, Any]]:
    """Generate a timeline of agent actions for reply analysis."""
    
    disposition = analysis.disposition
    confidence = analysis.confidence
    
    return [
        {
            "action": "Parse Reply Content",
            "details": "Extracted key phrases and context from customer reply",
            "duration": "0.3s"
        },
        {
            "action": "Analyze Intent",
            "details": f"Identified disposition as '{disposition}' with {confidence}% confidence",
            "duration": "1.2s"
        },
        {
            "action": "Assess Sentiment",
            "details": f"Determined sentiment: {analysis.sentiment}",
            "duration": "0.8s"
        },
        {
            "action": "Evaluate Urgency",
            "details": f"Urgency level: {analysis.urgency}",
            "duration": "0.5s"
        },
        {
            "action": "Calculate Lead Score",
            "details": f"Updated lead score to {analysis.lead_score}/100 based on analysis",
            "duration": "0.4s"
        },
        {
            "action": "Generate Response Strategy",
            "details": f"Selected appropriate response approach for {disposition} disposition",
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


def display_reply_analysis_results(lead_id: str, lead_data: Dict[str, Any], reply_content: str, result: ReplyAnalysisResult):
    """
    Display the reply analysis results in the UI (modern, actionable, visually appealing).
    """
    # Header Card
    st.markdown(f"""
    <div style="background: #f8f9fa; border-radius: 12px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 8px #e9ecef;">
      <div style="display: flex; align-items: center;">
        <div style="font-size: 2.2em; font-weight: bold; margin-right: 16px;">{lead_data.get('name', 'Lead')}</div>
        <div style="font-size: 1.2em; color: #6c757d;">{lead_data.get('company', '')}</div>
        <span style="margin-left: auto; background: #e0f7fa; color: #00796b; border-radius: 8px; padding: 4px 12px; font-size: 0.9em;">Reply Analyzed by AI</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Key Metrics
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    score = result.lead_score if result.lead_score is not None else 0
    score_color = "green" if score >= 80 else "orange" if score >= 50 else "red"
    priority_val = getattr(result, "priority", None)
    priority = str(priority_val).title() if priority_val else "Unknown"
    priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
    disposition_val = getattr(result, "disposition", None)
    disposition = str(disposition_val).title() if disposition_val else "Unknown"
    confidence = getattr(result, "confidence", 0)
    sentiment_val = getattr(result, "sentiment", None)
    sentiment = str(sentiment_val).title() if sentiment_val else "Unknown"
    urgency_val = getattr(result, "urgency", None)
    valid_urgencies = ["Low", "Medium", "High", "Urgent"]
    if not urgency_val or str(urgency_val).strip().lower() == "not specified" or str(urgency_val).title() not in valid_urgencies:
        urgency = "Not specified"
    else:
        urgency = str(urgency_val).title()
    intent_val = getattr(result, "intent", None)
    intent = str(intent_val).replace("_", " ").title() if intent_val else "Unknown"
    next_action = getattr(result, "next_action", "N/A")
    follow_up = getattr(result, "follow_up_timing", "N/A")

    with col1:
        st.metric("Lead Score", f"{score}/100")
        st.markdown(f"<span style='color:{score_color}; font-weight:bold;'>{score}/100</span>", unsafe_allow_html=True)
    with col2:
        st.metric("Priority", f"{priority_emoji} {priority}")
        st.metric("Disposition", disposition)
    with col3:
        st.metric("Confidence", f"{confidence}%")
        st.metric("Sentiment", sentiment)
    with col4:
        st.metric("Urgency", urgency)
        st.metric("Intent", intent)

    # Action Row
    st.markdown(f"""
    <div style="margin: 16px 0; padding: 12px; background: #e3f2fd; border-radius: 8px;">
      <b>Next Action:</b> <span style="font-size:1.1em;">{next_action}</span>
      <span style="margin-left: 16px; background: #fff3e0; color: #ef6c00; border-radius: 6px; padding: 2px 10px;">Follow-up: {follow_up}</span>
    </div>
    """, unsafe_allow_html=True)

    # Value-Add Statement
    st.info("This reply was automatically analyzed by AI, surfacing actionable next steps and updating the CRM in real time.")

    # Explainability Section
    with st.expander("🧠 Why did the AI analyze this reply this way?"):
        st.write(result.reasoning)
        # Show reasoning and details
        # (Add more chips or details if available in the future)

    # Show original reply
    with st.expander("📨 Original Customer Reply", expanded=False):
        st.text_area("Reply Content", value=reply_content, height=120, disabled=True)

    # Timeline section
    timeline = getattr(result, 'timeline', None)
    if timeline:
        display_agent_timeline(timeline)

    # Response email section
    response_email = getattr(result, 'response_email', None)
    if response_email:
        st.markdown("###  Generated Response")
        display_email_output(response_email)

    memory_manager = get_memory_manager()
    qual_history = memory_manager.get_qualification_history(lead_id)
    # Sort descending by created_at or updated_at
    def get_sort_key(qual):
        return qual.get('updated_at') or qual.get('created_at') or ''
    qual_history = sorted(qual_history, key=get_sort_key, reverse=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 👤 Lead Information")
        st.markdown(f"**Name:** {lead_data.get('name', 'N/A')}")
        st.markdown(f"**Email:** {lead_data.get('email', 'N/A')}")
        st.markdown(f"**Company:** {lead_data.get('company', 'N/A')}")
        st.markdown(f"**Role:** {lead_data.get('role', 'N/A')}")
        st.markdown(f"**Phone:** {lead_data.get('phone', 'N/A')}")
        st.markdown(f"**Source:** {lead_data.get('source', 'Contact Form')}")

    with col2:
        st.markdown("### 🕑 Qualification History")
        if not qual_history:
            st.info("No qualification history for this lead yet.")
        else:
            container_height = min(400, 120 * len(qual_history))
            with st.container():
                st.markdown(f"<div style='max-height:{container_height}px;overflow-y:auto;'>", unsafe_allow_html=True)
                for idx, qual in enumerate(qual_history):
                    score = qual.get('lead_score', 0)
                    score_color = 'green' if score >= 80 else 'orange' if score >= 50 else 'red'
                    priority = str(qual.get('priority', 'Unknown')).title()
                    priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
                    status = str(qual.get('lead_disposition', 'Unknown')).title()
                    next_action = qual.get('next_action', 'N/A')
                    # Expander label: show score and next action
                    expander_label = f"Score: {score}/100 | Next: {next_action}"
                    with st.expander(expander_label, expanded=False):
                        st.markdown(f"<div style='display:flex;align-items:center;gap:16px;padding:8px 0;'>"
                                    f"<span style='font-weight:bold;color:{score_color};font-size:1.1em;'>Score: {score}/100</span>"
                                    f"<span style='font-size:1.1em;'>{priority_emoji} {priority}</span>"
                                    f"<span style='font-size:1.1em;'>Status: {status}</span>"
                                    f"</div>", unsafe_allow_html=True)
                        # Only show the reply analysis for this qualification/history item
                        if qual.get('reasoning'):
                            st.markdown(f"**Reasoning:** {qual['reasoning']}")
                        if qual.get('next_action'):
                            st.info(f"**Next Action:** {qual['next_action']}")
                        if qual.get('urgency'):
                            st.markdown(f"**Urgency:** {qual['urgency']}")
                        if qual.get('sentiment'):
                            st.markdown(f"**Sentiment:** {qual['sentiment']}")
                        if qual.get('follow_up_timing'):
                            st.markdown(f"**Follow-up Timing:** {qual['follow_up_timing']}")
                        if qual.get('created_at'):
                            st.caption(f"Created: {qual['created_at']}")
                        if qual.get('updated_at'):
                            st.caption(f"Updated: {qual['updated_at']}")
                st.markdown("</div>", unsafe_allow_html=True)

    # Clear results button
    if st.button("🗑️ Clear Results", key="reply_clear_results_btn"):
        if hasattr(st.session_state, 'demo_results') and 'reply' in st.session_state.demo_results:
            st.session_state.demo_results['reply'] = {}
        st.rerun()


def send_reply_analysis_email(lead_data: Dict[str, Any], reply_content: str, analysis: ReplyAnalysisResult, sandbox_email: str = "mtorres.sandbox@gmail.com") -> None:
    """Send the reply analysis email using EmailManager. Extracted for testability."""
    email_manager = EmailManager()
    subject = f"Reply analysis for lead {lead_data['name']}"
    response_email = generate_response_email(lead_data, reply_content, analysis)
    llm_message = response_email['body']
    lead_info = (
        "\n\n[Lead Information]\n"
        f"Name: {lead_data['name']}\n"
        f"Email: {lead_data['email']}\n"
        f"Company: {lead_data['company']}\n"
        f"Original Reply: {reply_content}\n"
    )
    full_message = llm_message + lead_info
    try:
        email_manager.send_email(
            subject=subject,
            message=full_message,
            recipients=[sandbox_email],
            sender=sandbox_email
        )
    except Exception as e:
        # In UI, this is shown as st.error; here, just raise or log
        print(f"Error sending reply analysis email: {e}")
        raise
