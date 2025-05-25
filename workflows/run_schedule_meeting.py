"""
Meeting Scheduling Agent Demo

This script demonstrates the MeetingScheduler agent's ability to:
1. Parse meeting requests from email content
2. Extract scheduling preferences and constraints
3. Generate appropriate meeting responses
4. Handle various scheduling scenarios (immediate, flexible, specific times)
"""

from datetime import datetime
import time
from typing import Dict, Any

from memory.memory_manager import memory_manager
from agents.agent_core import AgentCore
from agents.meeting_scheduler import MeetingScheduler
from lib.config_loader import get_config

# Mock meeting request data
mock_meeting_requests = {
    "meeting_001": {
        "lead_id": "lead_001",
        "request_id": "meeting_001",
        "message": "Can we schedule a demo for tomorrow morning? I'm available between 9-11 AM.",
        "timestamp": "2025-05-25 15:30:00",
        "urgency": "high"
    },
    "meeting_002": {
        "lead_id": "lead_002", 
        "request_id": "meeting_002",
        "message": "I'd like to schedule a call sometime next week to discuss your pricing.",
        "timestamp": "2025-05-25 14:20:00",
        "urgency": "medium"
    },
    "meeting_003": {
        "lead_id": "lead_003",
        "request_id": "meeting_003", 
        "message": "I'm flexible on timing. Any time this week or next week works for me.",
        "timestamp": "2025-05-25 16:45:00",
        "urgency": "low"
    },
    "meeting_004": {
        "lead_id": "lead_001",
        "request_id": "meeting_004",
        "message": "Actually, can we reschedule our meeting to Wednesday afternoon instead?",
        "timestamp": "2025-05-26 09:15:00", 
        "urgency": "medium"
    },
    "meeting_005": {
        "lead_id": "lead_004",
        "request_id": "meeting_005",
        "message": "Thanks for the offer but I'm not interested in a meeting right now.",
        "timestamp": "2025-05-25 11:30:00",
        "urgency": "none"
    }
}

# Mock CRM data
mock_crm_data = {
    "lead_001": {
        "name": "John Smith",
        "company": "TechCorp Inc",
        "email": "john.smith@techcorp.com",
        "status": "qualified",
        "meeting_status": "none",
        "last_interaction": "2025-05-24 10:00:00"
    },
    "lead_002": {
        "name": "Sarah Johnson",
        "company": "StartupXYZ", 
        "email": "sarah@startupxyz.com",
        "status": "qualified",
        "meeting_status": "none",
        "last_interaction": "2025-05-23 14:30:00"
    },
    "lead_003": {
        "name": "Mike Chen",
        "company": "Global Enterprises",
        "email": "m.chen@globalent.com",
        "status": "hot_lead",
        "meeting_status": "none", 
        "last_interaction": "2025-05-25 09:00:00"
    },
    "lead_004": {
        "name": "Lisa Wong",
        "company": "Innovation Labs",
        "email": "lisa.wong@innovlabs.com", 
        "status": "cold_lead",
        "meeting_status": "declined",
        "last_interaction": "2025-05-20 16:00:00"
    }
}

# Mock calendar availability (simulating Google Calendar)
mock_calendar_slots = {
    "2025-05-26": ["09:00", "10:00", "14:00", "15:00", "16:00"],
    "2025-05-27": ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00"],
    "2025-05-28": ["10:00", "11:00", "14:00", "15:00"],
    "2025-05-29": ["09:00", "10:00", "13:00", "14:00", "15:00", "16:00"],
    "2025-05-30": ["09:00", "11:00", "14:00", "15:00"]
}

def create_meeting_scheduler():
    """Create and return the MeetingScheduler agent."""
    llm_config = get_config()
    # Optionally override temperature/max_tokens for meeting scheduling if needed
    llm_config["temperature"] = 0.3
    llm_config["max_tokens"] = max(llm_config.get("max_tokens", 500), 800)
    agent_core = AgentCore(llm_config)
    return MeetingScheduler(agent_core, memory_manager)

def build_context_from_meeting_request(request_data, memory_mgr=None):
    """Build context for LLM from meeting request data."""
    # Use provided memory manager or global one
    mgr = memory_mgr or memory_manager
    
    lead_id = request_data["lead_id"]
    
    # Get lead info from mock CRM
    lead_info = mock_crm_data.get(lead_id, {})
    
    # Get previous qualification and meeting history from memory
    qualification = mgr.get_qualification_with_meeting_info(lead_id)
    meeting_history = "No previous meetings"
    
    if qualification:
        if qualification.get("meeting_status"):
            meeting_history = f"Previous meeting status: {qualification.get('meeting_status')}"
            if qualification.get("meeting_datetime"):
                meeting_history += f", Previous meeting time: {qualification.get('meeting_datetime')}"
    
    # Get available calendar slots
    available_slots = []
    for date, times in mock_calendar_slots.items():
        for available_time in times:
            available_slots.append(f"{date} {available_time}")
    
    context = {
        "lead_info": f"Name: {lead_info.get('name', 'Unknown')}, Company: {lead_info.get('company', 'Unknown')}, Status: {lead_info.get('status', 'unknown')}",
        "meeting_request": f"Message: {request_data['message']}, Timestamp: {request_data['timestamp']}, Urgency: {request_data['urgency']}",
        "meeting_history": meeting_history,
        "available_slots": ", ".join(available_slots[:10])  # Limit to first 10 slots
    }
    
    return context

def analyze_meeting_request(context):
    """Analyze a meeting request using MeetingScheduler agent."""
    print("\n=== Analyzing Meeting Request ===")
    
    # Get MeetingScheduler agent
    meeting_scheduler = create_meeting_scheduler()
    
    # Prepare request data for the agent
    request_data = {
        "request_text": context.get("meeting_request", ""),
        "sender_email": "unknown@example.com",  # Would be extracted from context in real scenario
        "preferred_times": context.get("available_slots", ""),
        "lead_id": "unknown"  # Would be extracted from context
    }
    
    # Prepare lead context for the agent
    lead_context = {
        "lead_info": context.get("lead_info", ""),
        "meeting_history": context.get("meeting_history", "No previous meetings")
    }
    
    try:
        # Run analysis using the agent
        analysis_result = meeting_scheduler.analyze_request(request_data, lead_context)
        
        print("\nAgent Analysis Result:")
        for key, value in analysis_result.items():
            print(f"  {key}: {value}")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ Error during meeting analysis: {str(e)}")
        # Return default analysis on error
        return {
            "intent": "schedule_meeting",
            "urgency": "medium",
            "preferred_duration": 60,
            "time_preferences": "flexible",
            "meeting_type": "consultation",
            "flexibility": "high",
            "next_action": "propose_times"
        }

def generate_meeting_response(analysis_result):
    """Generate appropriate response based on analysis."""
    intent = analysis_result.get("intent", "schedule_meeting")
    next_action = analysis_result.get("next_action", "propose_times")
    
    if intent == "cancel":
        return "Thank you for your message. I understand you're not interested in scheduling a meeting at this time. Please feel free to reach out if your needs change."
    
    elif next_action == "book_immediately":
        return "Perfect! I'll schedule our meeting and send you a calendar invitation shortly."
    
    elif next_action == "propose_times":
        return "Thank you for your interest in scheduling a meeting. I have several time slots available this week. Would any of these work for you: Monday 2pm, Tuesday 10am, or Wednesday 3pm?"
    
    elif next_action == "request_clarification":
        return "Thank you for reaching out. To better assist you, could you please let me know your preferred time and what specific topics you'd like to discuss?"
    
    else:
        return "Thank you for your message. I'll get back to you shortly about scheduling."

def check_calendar_availability(date_time_str):
    """Check if a specific date/time is available in the mock calendar."""
    try:
        # Parse the datetime string
        if " " in date_time_str:
            date_part, time_part = date_time_str.split(" ", 1)
            
            # Check if this date and time are in our mock calendar slots
            if date_part in mock_calendar_slots and time_part in mock_calendar_slots[date_part]:
                return True
        
        return False
    except Exception as e:
        print(f"❌ Error checking calendar availability: {str(e)}")
        return False

def book_meeting(lead_id, meeting_datetime, meeting_type="consultation", duration="60min"):
    """
    Book a meeting by creating calendar event and updating meeting record.
    Returns calendar event ID if successful, None if booking fails.
    """
    # Check if the slot is available first
    if not check_calendar_availability(meeting_datetime):
        return None
    
    # Generate unique meeting ID
    meeting_id = memory_manager.save_meeting(lead_id, {
        "meeting_status": "scheduled",
        "meeting_datetime": meeting_datetime,
        "meeting_type": meeting_type,
        "duration": duration
    })
    
    # Generate unique calendar event ID with timestamp to avoid duplicates
    timestamp = str(int(time.time()))
    calendar_event_id = f"evt_{lead_id}_{meeting_datetime.replace(' ', '_').replace(':', '')}_{timestamp}"
    
    # Save calendar event
    calendar_data = {
        "calendar_event_id": calendar_event_id,
        "event_datetime": meeting_datetime,
        "duration": duration,
        "status": "scheduled",
        "calendar_link": None
    }
    
    memory_manager.save_calendar_event(meeting_id, calendar_data)
    
    # Remove the booked slot from available slots
    # Handle both formats: list of full datetime strings and nested dict format
    if isinstance(mock_calendar_slots, list):
        if meeting_datetime in mock_calendar_slots:
            mock_calendar_slots.remove(meeting_datetime)
    elif isinstance(mock_calendar_slots, dict):
        try:
            date_part, time_part = meeting_datetime.split(" ", 1)
            if date_part in mock_calendar_slots and time_part in mock_calendar_slots[date_part]:
                mock_calendar_slots[date_part].remove(time_part)
        except (ValueError, KeyError):
            pass  # Invalid format or date not found
    
    return calendar_event_id

def update_crm_with_meeting_info(lead_id: str, analysis_result: Dict[str, Any]) -> None:
    """Update CRM with meeting information from analysis result."""
    
    # Create meeting data from analysis result
    meeting_data = {
        "meeting_type": analysis_result.get("meeting_type", "consultation"),
        "urgency": analysis_result.get("urgency", "medium"),
        "preferred_duration": analysis_result.get("preferred_duration", 30),
        "next_action": analysis_result.get("next_action", "follow_up"),
        "time_preferences": str(analysis_result.get("time_preferences", [])),
        "status": "confirmed" if analysis_result.get("intent") == "schedule_meeting" else "pending"
    }
    
    # Check if lead has existing qualification
    existing_qualification = memory_manager.get_qualification(lead_id)
    
    if existing_qualification:
        # Update existing qualification with meeting info
        memory_manager.save_meeting(lead_id, meeting_data)
        # Update qualification with meeting flags only
        qualification_update = {
            "meeting_scheduled": True,
            "meeting_status": meeting_data.get("status", "scheduled")
        }
        # Merge with existing qualification to preserve required fields
        qualification_update.update(existing_qualification)
        memory_manager.save_qualification(lead_id, qualification_update)
    else:
        # Create a basic qualification with required fields if none exists
        basic_qualification = {
            "priority": "medium",
            "lead_score": 70,
            "reasoning": f"Meeting request analysis: {analysis_result.get('intent', 'unknown')}",
            "next_action": analysis_result.get("next_action", "follow_up"),
            "lead_disposition": "interested",
            "disposition_confidence": 80,
            "sentiment": "positive",
            "urgency": analysis_result.get("urgency", "medium"),
            "meeting_scheduled": True,
            "meeting_status": meeting_data.get("status", "scheduled")
        }
        memory_manager.save_qualification(lead_id, basic_qualification)
        memory_manager.save_meeting(lead_id, meeting_data)
    
    # Update mock CRM
    if lead_id in mock_crm_data:
        mock_crm_data[lead_id]["meeting_status"] = meeting_data.get("status")
        mock_crm_data[lead_id]["last_interaction"] = datetime.now().isoformat()
        mock_crm_data[lead_id]["notes"] = f"Meeting analysis: {analysis_result.get('intent', 'unknown')}"

def handle_meeting_request(request_id):
    """
    Main function to handle a meeting request end-to-end.
    """
    if request_id not in mock_meeting_requests:
        return f"Meeting request {request_id} not found"
    
    request_data = mock_meeting_requests[request_id]
    
    # Build context from the meeting request
    context = build_context_from_meeting_request(request_data, memory_manager)
    
    # Analyze the meeting request using MeetingScheduler agent
    analysis_result = analyze_meeting_request(context)
    
    # Generate appropriate response
    response = generate_meeting_response(analysis_result)
    
    # Try to book the meeting if needed
    if analysis_result.get("next_action") == "book_immediately":
        # For demo purposes, book at a default time
        default_time = "2025-05-27 10:00"
        if check_calendar_availability(default_time):
            book_meeting(request_data["lead_id"], default_time)
            response += f"\n\nMeeting booked for {default_time}"
        else:
            response += "\n\nUnable to book meeting at requested time."
    
    # Update CRM with meeting information
    update_crm_with_meeting_info(request_data["lead_id"], analysis_result)
    
    return response

def demo_meeting_scheduling():
    """Demo the meeting scheduling system."""
    print("MEETING SCHEDULING SYSTEM DEMO")
    print("=" * 60)
    
    # Process each meeting request
    results = {}
    for request_id in mock_meeting_requests.keys():
        result = handle_meeting_request(request_id)
        results[request_id] = result
    
    # Show final state
    print(f"\n{'='*60}")
    print("FINAL CRM STATE")
    print(f"{'='*60}")
    
    for lead_id, lead_data in mock_crm_data.items():
        print(f"\nLead: {lead_id}")
        print(f"  Name: {lead_data['name']}")
        print(f"  Company: {lead_data['company']}")
        print(f"  Status: {lead_data['status']}")
        print(f"  Meeting Status: {lead_data['meeting_status']}")
        print(f"  Last Interaction: {lead_data['last_interaction']}")
        
        # Show qualification with meeting info
        qualification = memory_manager.get_qualification_with_meeting_info(lead_id)
        if qualification:
            print(f"  Meeting Type: {qualification.get('meeting_type', 'N/A')}")
            print(f"  Meeting DateTime: {qualification.get('meeting_datetime', 'N/A')}")
    
    print(f"\n{'='*60}")
    print("REMAINING CALENDAR AVAILABILITY")
    print(f"{'='*60}")
    
    for date, times in mock_calendar_slots.items():
        if times:
            print(f"{date}: {', '.join(times)}")
        else:
            print(f"{date}: No slots available")

if __name__ == "__main__":
    demo_meeting_scheduling()
