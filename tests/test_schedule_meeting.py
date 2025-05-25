"""
Test suite for meeting scheduling functionality.

This module tests the MeetingScheduler agent's ability to:
1. Parse meeting requests from email content
2. Extract scheduling preferences and constraints  
3. Generate appropriate meeting responses
4. Handle various scheduling scenarios
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from memory.memory_manager import MemoryManager
from memory.memory_store import SQLiteMemoryStore
from agents.agent_core import AgentCore
from agents.meeting_scheduler import MeetingScheduler
from experiments.run_schedule_meeting import (
    create_meeting_scheduler,
    analyze_meeting_request,
    handle_meeting_request,
    mock_meeting_requests,
    build_context_from_meeting_request,
    check_calendar_availability,
    book_meeting,
    generate_meeting_response,
    mock_calendar_slots
)

class TestMeetingSchedulingAnalysis(unittest.TestCase):
    """Test meeting scheduling analysis functions."""
    
    def setUp(self):
        """Set up test environment with temporary database."""
        # Reset mock meeting requests to match the structure in run_schedule_meeting.py
        mock_meeting_requests.clear()
        mock_meeting_requests.update({
            "meeting_001": {
                "lead_id": "lead_001",
                "request_id": "meeting_001",
                "message": "Can we schedule a demo for tomorrow morning? I'm available between 9-11 AM.",
                "timestamp": "2025-05-25 15:30:00",
                "urgency": "high"
            }
        })
        # Reset mock calendar slots to default state
        mock_calendar_slots.clear()
        mock_calendar_slots.update({
            "2025-05-26": ["09:00", "10:00", "14:00", "15:00", "16:00"],
            "2025-05-27": ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00"],
            "2025-05-28": ["10:00", "11:00", "14:00", "15:00"],
            "2025-05-29": ["09:00", "10:00", "13:00", "14:00", "15:00", "16:00"],
            "2025-05-30": ["09:00", "11:00", "14:00", "15:00"]
        })
        
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create memory store and manager with temporary database
        self.memory_store = SQLiteMemoryStore(self.temp_db.name)
        self.memory_manager = MemoryManager(self.memory_store)
        
        # Mock qualification data for testing
        self.memory_manager.save_qualification("lead_001", {
            "priority": "high",
            "lead_score": 85,
            "reasoning": "Strong interest",
            "next_action": "Schedule demo",
            "lead_disposition": "hot"
        })
        
        self.memory_manager.save_qualification("lead_002", {
            "priority": "medium", 
            "lead_score": 65,
            "reasoning": "Moderate interest",
            "next_action": "Follow up",
            "lead_disposition": "warm"
        })
    
    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_db.name)
    
    def test_meeting_scheduler_agent_initialization(self):
        """Test that MeetingScheduler agent can be initialized properly."""
        llm_config = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 500,
            "api_key": "test-key"
        }
        
        agent_core = AgentCore(llm_config=llm_config)
        meeting_scheduler = MeetingScheduler(agent_core, self.memory_manager)
        
        self.assertIsNotNone(meeting_scheduler)
        self.assertEqual(meeting_scheduler.agent_core, agent_core)
        self.assertEqual(meeting_scheduler.memory_manager, self.memory_manager)
    
    @patch('agents.agent_core.AgentCore.create_llm_chain')
    def test_meeting_scheduler_analyze_method(self, mock_create_chain):
        """Test the MeetingScheduler analyze_request method."""
        # Mock the LLM chain response in the expected format
        mock_chain = MagicMock()
        mock_chain.run.return_value = """
Intent: schedule_meeting
Urgency: high
Preferred Duration: 60
Time Preferences: tomorrow morning
Meeting Type: demo
Flexibility: medium
Next Action: Confirm the demo for either 9:00 AM or 10:00 AM
        """
        mock_create_chain.return_value = mock_chain

        llm_config = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 500,
            "api_key": "test-key"
        }

        agent_core = AgentCore(llm_config=llm_config)
        meeting_scheduler = MeetingScheduler(agent_core, self.memory_manager)

        # Build request_data with all required fields
        req = mock_meeting_requests["meeting_001"]
        request_data = {
            "request_text": req["message"],
            "sender_email": "test@example.com",
            "preferred_times": "2025-05-26 09:00,2025-05-26 10:00",
            "meeting_type": "demo",
            "lead_id": req["lead_id"]
        }

        lead_context = {
            "name": "Test User",
            "company": "Test Company",
            "available_slots": ["2025-05-26 09:00", "2025-05-26 10:00"]
        }

        result = meeting_scheduler.analyze_request(request_data, lead_context)

        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("intent", result)
        self.assertIn("urgency", result)
        self.assertIn("meeting_type", result)
        self.assertEqual(result["intent"], "schedule_meeting")
        self.assertEqual(result["urgency"], "high")
    
    def test_build_context_from_meeting_request(self):
        """Test building context from meeting request data."""
        request_data = mock_meeting_requests["meeting_001"]
        
        context = build_context_from_meeting_request(request_data, self.memory_manager)
        
        self.assertIn("lead_info", context)
        self.assertIn("meeting_request", context)
        self.assertIn("meeting_history", context)
        self.assertIn("available_slots", context)
        
        # Check that lead info is populated
        self.assertIn("Name:", context["lead_info"])
        self.assertIn("Company:", context["lead_info"])
        
        # Check that meeting request info is populated
        self.assertIn("Message:", context["meeting_request"])
        self.assertIn("Timestamp:", context["meeting_request"])
    
    def test_build_context_with_meeting_history(self):
        """Test building context when lead has meeting history."""
        # Save a meeting for lead_001
        self.memory_manager.save_meeting("lead_001", {
            "meeting_status": "requested",
            "meeting_datetime": "2025-05-26 14:00"
        })
        
        request_data = mock_meeting_requests["meeting_001"]
        context = build_context_from_meeting_request(request_data, self.memory_manager)
        
        # Should include previous meeting information
        self.assertIn("Previous meeting status", context["meeting_history"])
        self.assertIn("Previous meeting time", context["meeting_history"])
    
    def test_check_calendar_availability_valid_time(self):
        """Test checking calendar availability for a valid time slot."""
        # This should be available in mock_meeting_requests
        result = check_calendar_availability("2025-05-26 09:00")
        self.assertTrue(result)
    
    def test_check_calendar_availability_invalid_time(self):
        """Test checking calendar availability for an invalid time slot."""
        result = check_calendar_availability("2025-05-26 23:00")
        self.assertFalse(result)
    
    def test_book_meeting_success(self):
        """Test successful meeting booking."""
        event_id = book_meeting("lead_001", "2025-05-26 09:00", "demo", "60min")
        self.assertIsNotNone(event_id)
        self.assertIn("evt_lead_001", event_id)
        # Check that the slot was removed from available slots
        self.assertNotIn("09:00", mock_calendar_slots["2025-05-26"])
    
    def test_book_meeting_unavailable_slot(self):
        """Test booking a meeting for an unavailable slot."""
        event_id = book_meeting("lead_001", "2025-05-26 23:00", "demo", "60min")
        
        self.assertIsNone(event_id)
    
    def test_generate_meeting_response_schedule_new(self):
        """Test generating response for scheduling a new meeting."""
        analysis_result = {
            "intent": "schedule_meeting",
            "next_action": "propose_times"
        }
        
        response = generate_meeting_response(analysis_result)
        
        self.assertIn("scheduling", response.lower())
        self.assertIn("meeting", response.lower())

if __name__ == '__main__':
    unittest.main() 