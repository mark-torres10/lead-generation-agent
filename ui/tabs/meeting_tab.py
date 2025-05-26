"""
Meeting scheduling tab.
Demonstrates the meeting scheduling workflow and calendar coordination.
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from ui.state.session import get_memory_manager, store_demo_result
from ui.components.agent_visualizer import display_agent_reasoning, display_agent_timeline
from ui.components.crm_viewer import display_crm_record
from ui.components.email_display import display_email_output


def render_meeting_tab():
    """Render the meeting scheduling tab."""
    
    st.markdown("""
    ### 📅 Meeting Scheduling Demo
    
    This demo shows how the AI agent handles meeting requests, coordinates schedules, 
    and sends calendar invitations with meeting details.
    """)
    
    # Initialize sample data in session state if not exists
    if 'meeting_sample_data' not in st.session_state:
        st.session_state.meeting_sample_data = {}
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📅 Meeting Request Simulation")
        
        # Get current values (either from sample data or defaults)
        current_data = st.session_state.meeting_sample_data
        
        # Lead context
        st.markdown("**Lead Information:**")
        lead_name = st.text_input(
            "Lead Name", 
            value=current_data.get("lead_name", "David Kim"), 
            placeholder="e.g., John Smith",
            key="meeting_lead_name"
        )
        lead_email = st.text_input(
            "Lead Email", 
            value=current_data.get("lead_email", "david.kim@innovatetech.com"), 
            placeholder="e.g., john@company.com",
            key="meeting_lead_email"
        )
        lead_company = st.text_input(
            "Company", 
            value=current_data.get("lead_company", "InnovateTech Solutions"), 
            placeholder="e.g., Acme Corp",
            key="meeting_lead_company"
        )
        lead_role = st.text_input(
            "Role", 
            value=current_data.get("lead_role", "VP of Operations"), 
            placeholder="e.g., CEO",
            key="meeting_lead_role"
        )
        
        # Meeting request details
        st.markdown("**Meeting Request:**")
        
        # Get the index for selectbox values
        meeting_types = ["Product Demo", "Discovery Call", "Technical Discussion", "Pricing Review", "Follow-up Meeting"]
        durations = ["15 minutes", "30 minutes", "45 minutes", "60 minutes"]
        urgencies = ["Low", "Medium", "High", "Urgent"]
        
        current_meeting_type = current_data.get("meeting_type", "Product Demo")
        current_duration = current_data.get("duration", "30 minutes")
        current_urgency = current_data.get("urgency", "Medium")
        
        meeting_type_index = meeting_types.index(current_meeting_type) if current_meeting_type in meeting_types else 0
        duration_index = durations.index(current_duration) if current_duration in durations else 1
        urgency_index = urgencies.index(current_urgency) if current_urgency in urgencies else 1
        
        meeting_type = st.selectbox(
            "Meeting Type",
            meeting_types,
            index=meeting_type_index,
            key="meeting_type_select"
        )
        
        duration = st.selectbox(
            "Duration",
            durations,
            index=duration_index,
            key="meeting_duration_select"
        )
        
        urgency = st.selectbox(
            "Urgency",
            urgencies,
            index=urgency_index,
            key="meeting_urgency_select"
        )
        
        # Additional attendees
        attendees = st.text_area(
            "Additional Attendees (optional)",
            value=current_data.get("attendees", ""),
            placeholder="e.g., CTO John Doe (john@company.com), Sales Director Jane Smith (jane@company.com)",
            height=80,
            key="meeting_attendees_text"
        )
        
        # Meeting notes/context
        meeting_context = st.text_area(
            "Meeting Context/Notes",
            value=current_data.get("context", ""),
            height=120,
            placeholder="Any specific topics, requirements, or context for the meeting...",
            key="meeting_context_text"
        )
        
        # Sample scenarios
        st.markdown("**Quick Scenarios:**")
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🚀 Product Demo"):
                st.session_state.meeting_sample_data = {
                    "lead_name": "David Kim",
                    "lead_email": "david.kim@innovatetech.com",
                    "lead_company": "InnovateTech Solutions",
                    "lead_role": "VP of Operations",
                    "meeting_type": "Product Demo",
                    "duration": "30 minutes",
                    "urgency": "Medium",
                    "attendees": "CTO Sarah Johnson (sarah@innovatetech.com)",
                    "context": "Interested in seeing how the automation platform can help streamline our sales processes. Want to understand integration capabilities and see a live demo of key features."
                }
                st.rerun()
            
            if st.button("🔧 Technical Discussion"):
                st.session_state.meeting_sample_data = {
                    "lead_name": "David Kim",
                    "lead_email": "david.kim@innovatetech.com",
                    "lead_company": "InnovateTech Solutions",
                    "lead_role": "VP of Operations",
                    "meeting_type": "Technical Discussion",
                    "duration": "45 minutes",
                    "urgency": "High",
                    "attendees": "IT Director Mike Chen (mike@innovatetech.com), Security Lead Alex Rodriguez (alex@innovatetech.com)",
                    "context": "Need to discuss technical requirements, security protocols, and integration architecture before moving forward with implementation."
                }
                st.rerun()
        
        with col_b:
            if st.button("💰 Pricing Review"):
                st.session_state.meeting_sample_data = {
                    "lead_name": "David Kim",
                    "lead_email": "david.kim@innovatetech.com",
                    "lead_company": "InnovateTech Solutions",
                    "lead_role": "VP of Operations",
                    "meeting_type": "Pricing Review",
                    "duration": "30 minutes",
                    "urgency": "Medium",
                    "attendees": "CFO Lisa Wang (lisa@innovatetech.com)",
                    "context": "Ready to discuss pricing options and contract terms. Looking for enterprise pricing and implementation timeline for Q2 rollout."
                }
                st.rerun()
            
            if st.button("⚡ Urgent Follow-up"):
                st.session_state.meeting_sample_data = {
                    "lead_name": "David Kim",
                    "lead_email": "david.kim@innovatetech.com",
                    "lead_company": "InnovateTech Solutions",
                    "lead_role": "VP of Operations",
                    "meeting_type": "Follow-up Meeting",
                    "duration": "15 minutes",
                    "urgency": "Urgent",
                    "attendees": "",
                    "context": "Quick follow-up needed to address concerns raised by the board. Need immediate clarification on data security and compliance features."
                }
                st.rerun()
        
        # Submit button
        submitted = st.button("📅 Schedule Meeting", type="primary")
    
    with col2:
        st.subheader("ℹ️ What This Demo Shows")
        st.info("""
        **Agent Workflow:**
        1. 📋 Parse meeting request details
        2. 🗓️ Check calendar availability
        3. 👥 Coordinate with multiple attendees
        4. ⏰ Suggest optimal time slots
        5. 📧 Send calendar invitations
        6. 🔄 Handle scheduling conflicts
        7. 📝 Prepare meeting agenda
        
        **Features Demonstrated:**
        - Smart scheduling based on urgency
        - Multi-attendee coordination
        - Automated calendar invitations
        - Meeting preparation materials
        - CRM integration and tracking
        """)
        
        # Show sample calendar
        st.markdown("**📅 Sample Calendar Availability:**")
        display_sample_calendar()
    
    # Process meeting scheduling
    if submitted and lead_name and lead_email and meeting_type:
        # Clear sample data after submission
        st.session_state.meeting_sample_data = {}
        
        # Create meeting request data
        meeting_request = {
            "lead_name": lead_name,
            "lead_email": lead_email,
            "lead_company": lead_company,
            "lead_role": lead_role,
            "meeting_type": meeting_type,
            "duration": duration,
            "urgency": urgency,
            "attendees": attendees,
            "context": meeting_context
        }
        
        # Use DB-backed lead_id lookup/creation (robust, email-based)
        memory_manager = get_memory_manager()
        lead_data = {
            "name": lead_name,
            "email": lead_email,
            "company": lead_company,
            "role": lead_role
        }
        lead_id = memory_manager.get_or_create_lead_id(lead_email, lead_data)
        
        # Process the meeting scheduling
        with st.spinner("🤖 AI Agent is scheduling the meeting..."):
            result = process_meeting_scheduling_demo(lead_id, meeting_request)
        
        # Store result for display
        store_demo_result("meeting", lead_id, result)
        
        # Display results
        display_meeting_results(lead_id, meeting_request, result)
    
    # Show previous results if any
    elif hasattr(st.session_state, 'demo_results') and 'meeting' in st.session_state.demo_results:
        st.markdown("---")
        st.subheader("📋 Previous Demo Results")
        
        results = st.session_state.demo_results['meeting']
        if results:
            latest_lead_id = max(results.keys())
            latest_result = results[latest_lead_id]
            
            meeting_request = latest_result.get('meeting_request', {})
            
            display_meeting_results(latest_lead_id, meeting_request, latest_result)


def display_sample_calendar():
    """Display a sample calendar showing availability."""
    
    # Generate next 5 business days
    today = datetime.now()
    business_days = []
    current_date = today
    
    while len(business_days) < 5:
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            business_days.append(current_date)
        current_date += timedelta(days=1)
    
    # Create a simple calendar view
    for day in business_days:
        day_name = day.strftime("%A")
        day_date = day.strftime("%m/%d")
        
        # Mock availability (some slots busy, some free)
        if day.weekday() == 0:  # Monday
            availability = "🟢 9:00 AM, 🔴 10:30 AM, 🟢 2:00 PM, 🟢 3:30 PM"
        elif day.weekday() == 1:  # Tuesday  
            availability = "🟢 10:00 AM, 🟢 11:30 AM, 🔴 2:00 PM, 🟢 4:00 PM"
        elif day.weekday() == 2:  # Wednesday
            availability = "🔴 9:00 AM, 🟢 10:30 AM, 🟢 1:00 PM, 🟢 3:00 PM"
        elif day.weekday() == 3:  # Thursday
            availability = "🟢 9:30 AM, 🟢 11:00 AM, 🟢 2:30 PM, 🔴 4:00 PM"
        else:  # Friday
            availability = "🟢 9:00 AM, 🔴 10:00 AM, 🟢 1:30 PM, 🟢 3:00 PM"
        
        st.text(f"{day_name} {day_date}: {availability}")
    
    st.caption("🟢 Available  🔴 Busy")


def process_meeting_scheduling_demo(lead_id: str, meeting_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process meeting scheduling using the actual scheduling workflow.
    
    Args:
        lead_id: Unique identifier for the lead
        meeting_request: Meeting request details
        
    Returns:
        Dictionary containing scheduling results
    """
    memory_manager = get_memory_manager()

    # Import the scheduling function
    from workflows.run_schedule_meeting import analyze_meeting_request, build_context_from_meeting_request

    # Create a mock request data structure that matches what the experiments module expects
    mock_request_data = {
        "lead_id": lead_id,
        "request_id": f"ui_meeting_{lead_id}",
        "message": f"Meeting request: {meeting_request.get('meeting_type', 'Meeting')} for {meeting_request.get('duration', '30 minutes')}. Urgency: {meeting_request.get('urgency', 'Medium')}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "urgency": meeting_request.get('urgency', 'Medium').lower()
    }

    # Automatically qualify the lead when they schedule a meeting
    # This is a strong buying signal and should result in a high lead score
    lead_qualification = calculate_meeting_qualification(meeting_request)

    # Ensure lead has a qualification before scheduling meeting
    if not memory_manager.has_qualification(lead_id):
        # Create initial qualification for new leads
        memory_manager.save_qualification(lead_id, lead_qualification)
    else:
        # Update existing qualification with meeting-based scoring
        existing_qualification = memory_manager.get_qualification(lead_id)
        updated_qualification = existing_qualification.copy() if existing_qualification else {}
        updated_qualification.update(lead_qualification)
        memory_manager.save_qualification(lead_id, updated_qualification)

    # Generate mock scheduling response
    mock_response = generate_mock_scheduling_response(meeting_request)

    # Patch the LLM chain to return our mock response
    with patch('agents.agent_core.AgentCore.create_llm_chain') as mock_chain, \
         patch('workflows.run_schedule_meeting.memory_manager', memory_manager):
        # Add lead to mock CRM so build_context_from_meeting_request can find it
        from workflows.run_schedule_meeting import mock_crm_data
        mock_crm_data[lead_id] = {
            "name": meeting_request["lead_name"],
            "company": meeting_request["lead_company"],
            "email": meeting_request["lead_email"],
            "status": "qualified",
            "meeting_status": "none",
            "last_interaction": "2024-01-10 12:00:00"
        }

        mock_llm = Mock()
        mock_llm.run.return_value = mock_response
        mock_chain.return_value = mock_llm

        # Build context and analyze the meeting request
        context = build_context_from_meeting_request(mock_request_data, memory_manager)
        scheduling_result = analyze_meeting_request(context)

    # Add lead score to scheduling result for display
    final_qualification = memory_manager.get_qualification(lead_id)
    if final_qualification:
        scheduling_result.update({
            'lead_score': final_qualification.get('lead_score', 0),
            'priority': final_qualification.get('priority', 'medium'),
            'reasoning': final_qualification.get('reasoning', 'Meeting scheduled')
        })

    # Log the meeting as an interaction
    memory_manager.add_interaction(
        lead_id,
        "meeting_scheduled",
        {
            "meeting_type": meeting_request.get("meeting_type"),
            "duration": meeting_request.get("duration"),
            "urgency": meeting_request.get("urgency"),
            "context": meeting_request.get("context"),
            "timestamp": datetime.now().isoformat()
        }
    )

    # Generate calendar invitation
    calendar_invite = generate_calendar_invitation(meeting_request, scheduling_result)

    # Generate confirmation email
    confirmation_email = generate_confirmation_email(meeting_request, scheduling_result)

    # Get interaction history
    interactions = memory_manager.get_interaction_history(lead_id)

    return {
        'lead_id': lead_id,
        'meeting_request': meeting_request,
        'scheduling_result': scheduling_result,
        'calendar_invite': calendar_invite,
        'confirmation_email': confirmation_email,
        'interactions': interactions,
        'timeline': generate_scheduling_timeline(meeting_request, scheduling_result)
    }


def calculate_meeting_qualification(meeting_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate lead qualification based on meeting scheduling request.
    Reuses logic from existing qualification functions.
    """
    meeting_type = meeting_request.get('meeting_type', 'Product Demo')
    urgency = meeting_request.get('urgency', 'Medium')
    company = meeting_request.get('lead_company', 'Unknown Company')
    role = meeting_request.get('lead_role', 'Unknown Role')
    
    # Base score for scheduling a meeting (strong buying signal)
    base_score = 75
    
    # Adjust score based on meeting type
    meeting_type_scores = {
        'Product Demo': 85,           # High intent - wants to see the product
        'Technical Discussion': 90,   # Very high intent - technical evaluation
        'Pricing Review': 95,         # Highest intent - ready to discuss pricing
        'Discovery Call': 80,         # Good intent - exploring solutions
        'Follow-up Meeting': 70       # Medium intent - continuing conversation
    }
    
    lead_score = meeting_type_scores.get(meeting_type, base_score)
    
    # Adjust based on urgency
    urgency_adjustments = {
        'Urgent': 10,
        'High': 5,
        'Medium': 0,
        'Low': -5
    }
    
    lead_score += urgency_adjustments.get(urgency, 0)
    
    # Determine priority based on final score
    if lead_score >= 90:
        priority = "high"
    elif lead_score >= 75:
        priority = "medium"
    else:
        priority = "low"
    
    # Generate reasoning based on meeting details
    reasoning_parts = [
        f"Lead from {company} has scheduled a {meeting_type.lower()}",
        f"with {urgency.lower()} urgency priority.",
        "Meeting scheduling indicates strong buying intent and active evaluation process.",
        f"Role: {role} suggests decision-making capability."
    ]
    
    if meeting_type == 'Pricing Review':
        reasoning_parts.append("Pricing discussion indicates readiness to purchase.")
    elif meeting_type == 'Technical Discussion':
        reasoning_parts.append("Technical evaluation suggests serious consideration.")
    elif meeting_type == 'Product Demo':
        reasoning_parts.append("Demo request shows active interest in solution capabilities.")
    
    reasoning = " ".join(reasoning_parts)
    
    # Determine next action
    next_action_map = {
        'Product Demo': f"Conduct {meeting_type.lower()} and showcase key features relevant to {company}",
        'Technical Discussion': f"Prepare technical documentation and conduct {meeting_type.lower()}",
        'Pricing Review': f"Present pricing options and negotiate terms during {meeting_type.lower()}",
        'Discovery Call': f"Conduct discovery session to understand {company}'s specific needs",
        'Follow-up Meeting': "Continue conversation and address any remaining questions"
    }
    
    next_action = next_action_map.get(meeting_type, f"Conduct {meeting_type.lower()} as scheduled")
    
    # Ensure score is within valid range
    lead_score = max(0, min(100, lead_score))
    
    return {
        "priority": priority,
        "lead_score": lead_score,
        "reasoning": reasoning,
        "next_action": next_action,
        "lead_disposition": "meeting_scheduled",
        "sentiment": "positive",
        "urgency": urgency.lower()
    }


def generate_mock_scheduling_response(meeting_request: Dict[str, Any]) -> str:
    """Generate a mock LLM response for meeting scheduling."""
    
    urgency = meeting_request.get('urgency', 'Medium')
    duration = meeting_request.get('duration', '30 minutes')
    meeting_type = meeting_request.get('meeting_type', 'Product Demo')
    
    # Determine suggested time based on urgency
    if urgency == 'Urgent':
        suggested_time = "Tomorrow 2:00 PM EST"
        priority = "high"
    elif urgency == 'High':
        suggested_time = "Wednesday 10:30 AM EST"
        priority = "high"
    elif urgency == 'Medium':
        suggested_time = "Thursday 2:30 PM EST"
        priority = "medium"
    else:
        suggested_time = "Friday 1:30 PM EST"
        priority = "low"
    
    return f"""
    Meeting Type: {meeting_type}
    Suggested Time: {suggested_time}
    Duration: {duration}
    Priority: {priority}
    Status: confirmed
    Meeting Link: https://meet.company.com/demo-{meeting_request.get('lead_name', 'lead').lower().replace(' ', '-')}
    Agenda: Prepared based on {meeting_type.lower()} requirements
    """


def generate_calendar_invitation(meeting_request: Dict[str, Any], scheduling_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate calendar invitation details."""
    
    meeting_type = meeting_request.get('meeting_type', 'Meeting')
    company = meeting_request.get('lead_company', 'Company')
    duration = meeting_request.get('duration', '30 minutes')
    suggested_time = scheduling_result.get('suggested_time', 'TBD')
    meeting_link = scheduling_result.get('meeting_link', 'https://meet.company.com/demo')
    
    # Generate agenda based on meeting type
    if meeting_type == "Product Demo":
        agenda = """
        📋 **Meeting Agenda:**
        1. Welcome & Introductions (5 min)
        2. Platform Overview (10 min)
        3. Live Demo - Key Features (10 min)
        4. Q&A Session (5 min)
        5. Next Steps Discussion (5 min)
        
        🎯 **Demo Focus:**
        - Automation workflows
        - Integration capabilities
        - ROI projections
        """
    elif meeting_type == "Technical Discussion":
        agenda = """
        📋 **Meeting Agenda:**
        1. Technical Requirements Review (15 min)
        2. Security & Compliance Discussion (15 min)
        3. Integration Architecture (10 min)
        4. Implementation Timeline (5 min)
        
        🔧 **Technical Topics:**
        - API documentation
        - Security protocols
        - Data handling
        """
    elif meeting_type == "Pricing Review":
        agenda = """
        📋 **Meeting Agenda:**
        1. Pricing Tiers Overview (10 min)
        2. Enterprise Options (10 min)
        3. Contract Terms Discussion (5 min)
        4. Implementation Timeline (5 min)
        
        💰 **Pricing Topics:**
        - Volume discounts
        - Payment terms
        - Support packages
        """
    else:
        agenda = f"""
        📋 **Meeting Agenda:**
        1. Welcome & Objectives (5 min)
        2. {meeting_type} Discussion (20 min)
        3. Action Items & Next Steps (5 min)
        """
    
    return {
        'subject': f"{meeting_type} - {company}",
        'start_time': suggested_time,
        'duration': duration,
        'attendees': [
            meeting_request.get('lead_email'),
            'alex.thompson@yourcompany.com'
        ],
        'meeting_link': meeting_link,
        'agenda': agenda,
        'location': 'Video Conference',
        'description': f"""
        {meeting_type} with {company}
        
        {agenda}
        
        📞 **Meeting Details:**
        - Join Link: {meeting_link}
        - Duration: {duration}
        - Host: Alex Thompson, Solutions Consultant
        
        📧 **Contact Information:**
        - Email: alex.thompson@yourcompany.com
        - Phone: (555) 123-4567
        
        Looking forward to our discussion!
        """
    }


def generate_confirmation_email(meeting_request: Dict[str, Any], scheduling_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate meeting confirmation email."""
    
    name = meeting_request.get('lead_name', 'there')
    company = meeting_request.get('lead_company', 'your company')
    meeting_type = meeting_request.get('meeting_type', 'meeting')
    suggested_time = scheduling_result.get('suggested_time', 'TBD')
    duration = meeting_request.get('duration', '30 minutes')
    meeting_link = scheduling_result.get('meeting_link', 'https://meet.company.com/demo')
    
    subject = f"Meeting Confirmed: {meeting_type} - {suggested_time}"
    
    body = f"""Hi {name},

Perfect! I've scheduled our {meeting_type.lower()} for {suggested_time} ({duration}).

📅 **Meeting Details:**
- Date & Time: {suggested_time}
- Duration: {duration}
- Meeting Link: {meeting_link}
- Host: Alex Thompson, Solutions Consultant

🎯 **What to Expect:**
I've prepared a customized session focused on {company}'s specific needs. We'll cover the key areas you mentioned and ensure you have all the information needed to move forward.

📋 **Before Our Meeting:**
- I'll send a calendar invitation with all the details
- Please test the meeting link beforehand
- Feel free to prepare any specific questions

📞 **Need to Reschedule?**
If this time doesn't work, just reply to this email and I'll find an alternative that works better for your schedule.

Looking forward to our conversation!

Best regards,
Alex Thompson
Senior Solutions Consultant
alex.thompson@yourcompany.com
(555) 123-4567"""

    return {
        'subject': subject,
        'body': body,
        'recipient': meeting_request.get('lead_email'),
        'from': 'alex.thompson@yourcompany.com',
        'metadata': {
            'generated_at': '2024-01-10 12:00:00',
            'meeting_type': meeting_type,
            'urgency': meeting_request.get('urgency', 'Medium'),
            'tone': 'professional',
            'template_used': 'meeting_confirmation'
        }
    }


def generate_scheduling_timeline(meeting_request: Dict[str, Any], scheduling_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a timeline of scheduling actions."""
    
    meeting_type = meeting_request.get('meeting_type', 'meeting')
    urgency = meeting_request.get('urgency', 'Medium')
    
    return [
        {
            "action": "Parse Meeting Request",
            "details": f"Extracted {meeting_type.lower()} requirements and preferences",
            "duration": "0.2s"
        },
        {
            "action": "Check Calendar Availability",
            "details": f"Scanned calendar for {urgency.lower()} priority slots",
            "duration": "0.8s"
        },
        {
            "action": "Coordinate Attendees",
            "details": "Checked availability for all requested participants",
            "duration": "1.1s"
        },
        {
            "action": "Select Optimal Time",
            "details": f"Chose {scheduling_result.get('suggested_time', 'optimal')} slot based on preferences",
            "duration": "0.5s"
        },
        {
            "action": "Generate Meeting Link",
            "details": "Created secure video conference room",
            "duration": "0.3s"
        },
        {
            "action": "Prepare Agenda",
            "details": f"Customized agenda for {meeting_type.lower()} format",
            "duration": "1.2s"
        },
        {
            "action": "Send Invitations",
            "details": "Dispatched calendar invites and confirmation emails",
            "duration": "0.7s"
        },
        {
            "action": "Update CRM",
            "details": "Logged meeting details and set follow-up reminders",
            "duration": "0.4s"
        }
    ]


def display_meeting_results(lead_id: str, meeting_request: Dict[str, Any], result: Dict[str, Any]):
    """Display the meeting scheduling results in organized sections."""
    
    st.markdown("---")
    st.markdown("## 📅 Meeting Scheduling Results")
    
    scheduling_result = result.get('scheduling_result', {})
    calendar_invite = result.get('calendar_invite', {})
    confirmation_email = result.get('confirmation_email', {})
    interactions = result.get('interactions', [])
    timeline = result.get('timeline', [])
    
    # Agent reasoning section
    display_agent_reasoning(scheduling_result)
    
    # Timeline section
    if timeline:
        display_agent_timeline(timeline)
    
    # Calendar invitation section
    if calendar_invite:
        st.markdown("### 📅 Calendar Invitation")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**📋 Meeting Details:**")
            st.info(f"""
            **Subject:** {calendar_invite.get('subject', 'Meeting')}
            **Date & Time:** {calendar_invite.get('start_time', 'TBD')}
            **Duration:** {calendar_invite.get('duration', '30 minutes')}
            **Location:** {calendar_invite.get('location', 'Video Conference')}
            **Meeting Link:** {calendar_invite.get('meeting_link', 'TBD')}
            """)
        
        with col2:
            st.markdown("**👥 Attendees:**")
            attendees = calendar_invite.get('attendees', [])
            for attendee in attendees:
                st.write(f"• {attendee}")
        
        # Show agenda
        with st.expander("📋 Meeting Agenda", expanded=True):
            st.markdown(calendar_invite.get('agenda', 'Agenda to be determined'))
    
    # Confirmation email section
    if confirmation_email:
        st.markdown("### 📧 Confirmation Email")
        display_email_output(confirmation_email)
    
    # CRM update section
    st.markdown("### 🗂️ CRM Update")
    lead_data = {
        'name': meeting_request.get('lead_name'),
        'email': meeting_request.get('lead_email'),
        'company': meeting_request.get('lead_company'),
        'role': meeting_request.get('lead_role')
    }
    
    # Add meeting info to scheduling result for CRM display
    crm_data = dict(scheduling_result)
    crm_data.update({
        'next_action': f"Attend {meeting_request.get('meeting_type', 'meeting')} on {scheduling_result.get('suggested_time', 'TBD')}",
        'lead_disposition': 'meeting_scheduled',
        'priority': scheduling_result.get('priority', 'medium'),
        'lead_score': scheduling_result.get('lead_score', 0),
        'reasoning': scheduling_result.get('reasoning', 'Meeting scheduled - strong buying signal')
    })
    
    display_crm_record(lead_data, crm_data, interactions, title="Updated Lead Record")
    
    # Clear results button
    if st.button("🗑️ Clear Results", key="meeting_clear_results_btn"):
        if hasattr(st.session_state, 'demo_results') and 'meeting' in st.session_state.demo_results:
            st.session_state.demo_results['meeting'] = {}
        st.rerun() 