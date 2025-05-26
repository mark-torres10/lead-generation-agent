"""
Contact form qualification tab.
Demonstrates the lead qualification workflow from contact form submission to follow-up email.
"""

import streamlit as st
from typing import Dict, Any
from unittest.mock import patch

from ui.state.session import get_memory_manager, get_next_lead_id, store_demo_result
from ui.components.agent_visualizer import display_agent_reasoning, display_agent_timeline
from ui.components.crm_viewer import display_crm_record
from ui.components.email_display import display_email_output
from agents.models import LeadQualificationResult


def render_qualify_tab():
    """Render the contact form qualification tab."""
    
    st.markdown("""
    ### 📝 Contact Us → Follow-up Demo
    
    This demo shows how the AI agent processes a contact form submission, qualifies the lead, 
    and generates a personalized follow-up email with CRM updates.
    """)
    
     # Initialize sample data in session state if not exists
    if 'qualify_sample_data' not in st.session_state:
        st.session_state.qualify_sample_data = {}
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎛️ Simulated Contact Us Form")
        
        # Sample data buttons (outside form)
        st.markdown("**Quick Fill Options:**")
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🏢 Enterprise Lead", key="qualify_enterprise_btn"):
                st.session_state.qualify_sample_data = {
                    "name": "Sarah Chen",
                    "email": "sarah.chen@techcorp.com",
                    "company": "TechCorp Industries",
                    "role": "Chief Technology Officer",
                    "message": "We're looking for automation solutions to streamline our sales process. We have a team of 200+ sales reps and need better lead management. Budget approved for Q1 implementation."
                }
                st.rerun()
        
        with col_b:
            if st.button("🏪 SMB Lead", key="qualify_smb_btn"):
                st.session_state.qualify_sample_data = {
                    "name": "Mike Rodriguez",
                    "email": "mike@localservices.com",
                    "company": "Local Services LLC",
                    "role": "Owner",
                    "message": "Small business owner here. Heard about your tools from a friend. Not sure if it's right for us but interested to learn more."
                }
                st.rerun()
        
        # Get current values (either from sample data or empty)
        current_data = st.session_state.qualify_sample_data
        
        # Contact form with pre-filled values
        with st.form("contact_form"):
            name = st.text_input(
                "Full Name", 
                value=current_data.get("name", ""),
                placeholder="e.g., Alice Johnson"
            )
            email = st.text_input(
                "Email Address", 
                value=current_data.get("email", ""),
                placeholder="e.g., alice@acmecorp.com"
            )
            company = st.text_input(
                "Company", 
                value=current_data.get("company", ""),
                placeholder="e.g., Acme Corp"
            )
            role = st.text_input(
                "Job Title", 
                value=current_data.get("role", ""),
                placeholder="e.g., VP of Sales"
            )
            message = st.text_area(
                "Message", 
                value=current_data.get("message", ""),
                height=100,
                placeholder="Tell us about your needs..."
            )
            
            submitted = st.form_submit_button("📤 Submit Contact Form", type="primary")
    
    with col2:
        st.subheader("ℹ️ What This Demo Shows")
        st.info("""
        **Agent Workflow:**
        1. 📝 Parse contact form data
        2. 🧠 Extract key information (company size, intent, urgency)
        3. 📊 Calculate lead score and priority
        4. ✉️ Generate personalized follow-up email
        5. 🗂️ Update CRM with qualification data
        
        **Key Features:**
        - Real-time agent reasoning display
        - Lead scoring and prioritization
        - Personalized email generation
        - CRM integration simulation
        """)
    
    # Process form submission
    if submitted and name and email and message:
        # Create form data
        form_data = {
            "name": name,
            "email": email,
            "company": company or "Unknown Company",
            "role": role or "Unknown Role",
            "message": message
        }
        
        # Generate unique lead ID
        lead_id = get_next_lead_id()
        
        # Process the qualification
        with st.spinner("🤖 AI Agent is processing the lead..."):
            result = process_qualification_demo(lead_id, form_data)
        
        # Store both result and form_data for display and testability
        store_demo_result("qualify", lead_id, {"result": result, "form_data": form_data})
        
        # Display results
        display_qualification_results(lead_id, form_data, result)
    
    # Show previous results if any
    elif hasattr(st.session_state, 'demo_results') and 'qualify' in st.session_state.demo_results:
        st.markdown("---")
        st.subheader("📋 Previous Demo Results")
        
        results = st.session_state.demo_results['qualify']
        if results:
            latest_lead_id = max(results.keys())
            latest_result = results[latest_lead_id]
            # If stored as {"result": ..., "form_data": ...}
            if isinstance(latest_result, dict) and "result" in latest_result and "form_data" in latest_result:
                display_qualification_results(latest_lead_id, latest_result["form_data"], latest_result["result"])
            else:
                # Fallback for legacy results
                if hasattr(latest_result, 'model_dump'):
                    form_data = {}
                elif isinstance(latest_result, dict):
                    form_data = latest_result.get('form_data', {})
                else:
                    form_data = {}
                display_qualification_results(latest_lead_id, form_data, latest_result)


def process_qualification_demo(lead_id: str, form_data: Dict[str, Any]) -> LeadQualificationResult:
    """
    Process lead qualification using the actual qualification workflow.
    Args:
        lead_id: Unique identifier for the lead
        form_data: Contact form data
    Returns:
        LeadQualificationResult containing qualification results
    """
    memory_manager = get_memory_manager()
    from workflows.run_qualification import qualify_lead
    # Only patch memory_manager for test/demo isolation
    with patch('workflows.run_qualification.memory_manager', memory_manager):
        qualification = qualify_lead(lead_id, form_data)
    return qualification


def generate_follow_up_email(form_data: Dict[str, Any], qualification: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a follow-up email based on qualification results."""
    
    name = form_data.get('name', 'there')
    company = form_data.get('company', 'your company')
    role = form_data.get('role', 'your role')
    
    # Customize email based on lead score
    lead_score = qualification.get('lead_score', 50)
    
    if lead_score >= 80:
        # High-value lead
        subject = f"Perfect timing for {company}'s automation goals"
        body = f"""Hi {name},

Thank you for reaching out about automation solutions for {company}. Based on your message, it sounds like you're facing exactly the challenges our platform was designed to solve.

As {role}, you're likely seeing firsthand how manual processes can slow down your team's productivity. Our automation platform has helped similar companies reduce manual work by 60% while improving lead conversion rates.

I'd love to show you a personalized demo of how this could work specifically for {company}. Would you be available for a brief 30-minute call this week?

I can also send over a case study from a similar company that saw immediate results.

Best regards,
Alex Thompson
Senior Solutions Consultant
sales@yourcompany.com
(555) 123-4567"""
    
    elif lead_score >= 60:
        # Medium-value lead
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
    
    else:
        # Lower-value lead - nurture approach
        subject = "Resources for your automation journey"
        body = f"""Hi {name},

Thank you for your interest in automation solutions. It's great to see {company} exploring ways to improve efficiency.

I've attached a helpful guide on "Getting Started with Sales Automation" that many companies find valuable when beginning their automation journey.

If you'd like to discuss your specific needs, I'm here to help. Feel free to reply to this email or schedule a call at your convenience.

Best regards,
Alex Thompson
Solutions Consultant
sales@yourcompany.com"""
    
    return {
        'subject': subject,
        'body': body,
        'recipient': form_data.get('email'),
        'from': 'sales@yourcompany.com',
        'metadata': {
            'generated_at': '2024-01-10 10:30:00',
            'lead_score': lead_score,
            'priority': qualification.get('priority', 'medium'),
            'tone': 'professional',
            'template_used': 'qualification_follow_up'
        }
    }


def generate_demo_timeline(form_data: Dict[str, Any], qualification: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Generate a timeline of agent actions for visualization."""
    
    return [
        {
            "action": "Parse Contact Form",
            "details": f"Extracted information from {form_data.get('name', 'contact')}'s submission",
            "duration": "0.2s"
        },
        {
            "action": "Analyze Company & Role",
            "details": f"Researched {form_data.get('company', 'company')} and {form_data.get('role', 'role')} context",
            "duration": "1.1s"
        },
        {
            "action": "Calculate Lead Score",
            "details": f"Scored lead as {qualification.get('lead_score', 0)}/100 based on multiple factors",
            "duration": "0.8s"
        },
        {
            "action": "Determine Priority",
            "details": f"Set priority to {qualification.get('priority', 'medium')} based on score and urgency",
            "duration": "0.3s"
        },
        {
            "action": "Generate Follow-up Email",
            "details": "Created personalized email based on lead profile and score",
            "duration": "2.1s"
        },
        {
            "action": "Update CRM",
            "details": "Saved qualification data and scheduled follow-up actions",
            "duration": "0.5s"
        }
    ]


def display_qualification_results(lead_id: str, form_data: dict, result):
    # Header Card
    st.markdown(f"""
    <div style="background: #f8f9fa; border-radius: 12px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 8px #e9ecef;">
      <div style="display: flex; align-items: center;">
        <div style="font-size: 2.2em; font-weight: bold; margin-right: 16px;">{form_data.get('name', 'Lead')}</div>
        <div style="font-size: 1.2em; color: #6c757d;">{form_data.get('company', '')}</div>
        <span style="margin-left: auto; background: #e0f7fa; color: #00796b; border-radius: 8px; padding: 4px 12px; font-size: 0.9em;">Qualified by AI</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Key Metrics
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    score = result.lead_score
    score_color = "green" if score >= 80 else "orange" if score >= 50 else "red"
    priority_val = getattr(result, "priority", None)
    priority = str(priority_val).title() if priority_val else "Unknown"
    priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
    disposition_val = getattr(result, "disposition", None)
    disposition = str(disposition_val).title() if disposition_val else "Unknown"
    confidence = getattr(result, "confidence", 0)
    urgency_val = getattr(result, "urgency", None)
    valid_urgencies = ["Low", "Medium", "High", "Urgent"]
    if not urgency_val or str(urgency_val).strip().lower() == "not specified" or str(urgency_val).title() not in valid_urgencies:
        urgency = "Not specified"
    else:
        urgency = str(urgency_val).title()
    next_action = getattr(result, "next_action", "N/A")

    with col1:
        st.metric("Lead Score", f"{score}/100")
        st.markdown(f"<span style='color:{score_color}; font-weight:bold;'>{score}/100</span>", unsafe_allow_html=True)
    with col2:
        st.metric("Priority", f"{priority_emoji} {priority}")
    with col3:
        st.metric("Status", disposition)
    with col4:
        st.metric("Confidence", f"{confidence}%")
        if confidence < 60:
            st.warning("AI is less certain about this lead.")

    # Action Row
    st.markdown(f"""
    <div style="margin: 16px 0; padding: 12px; background: #e3f2fd; border-radius: 8px;">
      <b>Next Action:</b> <span style="font-size:1.1em;">{next_action}</span>
      <span style="margin-left: 16px; background: #fff3e0; color: #ef6c00; border-radius: 6px; padding: 2px 10px;">Urgency: {urgency}</span>
    </div>
    """, unsafe_allow_html=True)

    if urgency == "Not specified":
        st.info("To improve AI confidence, provide more details about the lead's timeline or urgency in the message.")

    # Value-Add Statement
    st.info("This lead was automatically qualified by AI, saving your team manual review time and surfacing the most promising opportunities first.")

    # Explainability Section
    with st.expander("🧠 Why did the AI qualify this lead this way?"):
        st.write(result.reasoning)
        # Show signals/factors as chips if available
        signals = getattr(result, "signals", None)
        if signals:
            st.markdown("**Key Signals / Factors:**", unsafe_allow_html=True)
            chip_html = "".join([
                f"<span style='display:inline-block;background:#e0f2f1;color:#00695c;border-radius:16px;padding:4px 14px;margin:2px 6px 2px 0;font-size:0.98em;font-weight:500;box-shadow:0 1px 3px #e0e0e0;'>{s}</span>"
                for s in signals if s
            ])
            st.markdown(f"<div style='margin-bottom:8px'>{chip_html}</div>", unsafe_allow_html=True)
        # Show confidence improvements if confidence is low
        confidence = getattr(result, "confidence", 0)
        conf_impr = getattr(result, "confidence_improvements", None)
        if confidence < 60 and conf_impr:
            st.markdown(
                f"<div style='margin-top:8px;padding:10px 16px;background:#fff3e0;border-radius:8px;color:#ef6c00;'><b>What would improve AI confidence?</b><br>{conf_impr if isinstance(conf_impr, str) else ', '.join(conf_impr)}</div>",
                unsafe_allow_html=True
            )

    # Optionally, show what would improve confidence
    # if confidence < 60:
    #     st.info("To improve confidence, provide more details about the lead's company size or decision process.")

    # CRM and timeline sections (reuse your existing components)
    # ... (existing CRM/timeline/email display code) ...
    
    # Agent reasoning section
    qualification = getattr(result, "qualification", None)
    if qualification is not None:
        display_agent_reasoning(qualification)
    
    # Timeline section (persisted)
    memory_manager = get_memory_manager()
    interactions = memory_manager.get_interaction_history(lead_id)
    if interactions:
        # Convert interaction records to timeline steps for display_agent_timeline
        timeline_steps = []
        for interaction in interactions:
            event_type = interaction.get("event_type", "event")
            event_data = interaction.get("event_data", {})
            timestamp = interaction.get("timestamp", "")
            # Compose a readable step
            step = {
                "action": event_type.replace("_", " ").title(),
                "details": event_data.get("reasoning") or event_data.get("next_action") or str(event_data),
                "timestamp": timestamp
            }
            # Add key fields if present
            if "lead_score" in event_data:
                step["lead_score"] = event_data["lead_score"]
            if "priority" in event_data:
                step["priority"] = event_data["priority"]
            timeline_steps.append(step)
        display_agent_timeline(timeline_steps)
    else:
        st.info("No interaction history yet for this lead.")
    
    # Email output section
    email = getattr(result, "email", None)
    if email is not None:
        display_email_output(email)
    
    # CRM sections
    col1, col2 = st.columns(2)
    
    with col1:
        # Before state (just form data)
        before_data = {
            'name': form_data.get('name'),
            'company': form_data.get('company'),
            'lead_score': 0,
            'priority': 'unqualified',
            'lead_disposition': 'new',
            'next_action': 'Needs qualification'
        }
        
        st.subheader("🗂️ CRM Record - Before")
        display_crm_record(form_data, before_data, title="")
    
    with col2:
        # After state (with qualification)
        st.subheader("🗂️ CRM Record - After")
        after_qualification = qualification if qualification is not None else result.model_dump()
        interactions = getattr(result, "interactions", None)
        display_crm_record(form_data, after_qualification, interactions, title="")
    
    # Clear results button
    if st.button("🗑️ Clear Results", key="qualify_clear_results_btn"):
        if hasattr(st.session_state, 'demo_results') and 'qualify' in st.session_state.demo_results:
            st.session_state.demo_results['qualify'] = {}
        st.rerun() 