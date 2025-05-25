"""
Unit tests for meeting scheduling functionality.
"""
import unittest
import os
import sys
import tempfile
from datetime import datetime

# Add the parent directory to the path so we can import from memory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.memory_store import SQLiteMemoryStore
from memory.memory_manager import MemoryManager

# Import functions from the meeting scheduling experiment
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'experiments'))
from run_schedule_meeting import (
    parse_meeting_analysis_response,
    build_context_from_meeting_request,
    check_calendar_availability,
    book_meeting,
    generate_meeting_response,
    mock_meeting_requests,
    mock_calendar_slots
)

class TestMeetingSchedulingAnalysis(unittest.TestCase):
    """Test meeting scheduling analysis functions."""
    
    def setUp(self):
        """Set up test environment with temporary database."""
        # Reset mock calendar slots to ensure clean state for each test
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
    
    def test_parse_complete_meeting_analysis_response(self):
        """Test parsing a complete LLM response for meeting analysis."""
        llm_response = """
Meeting Intent: schedule_new
Meeting Type: demo
Urgency: high
Preferred Time: 2025-05-26 09:00
Duration: 60min
Analysis: Lead is very interested and wants immediate demo
Recommended Response: I'll schedule a demo for you right away
Booking Action: book_immediately
Suggested Datetime: 2025-05-26 09:00
"""
        
        result = parse_meeting_analysis_response(llm_response)
        
        self.assertEqual(result["meeting_intent"], "schedule_new")
        self.assertEqual(result["meeting_type"], "demo")
        self.assertEqual(result["urgency"], "high")
        self.assertEqual(result["preferred_time"], "2025-05-26 09:00")
        self.assertEqual(result["duration"], "60min")
        self.assertEqual(result["booking_action"], "book_immediately")
        self.assertEqual(result["suggested_datetime"], "2025-05-26 09:00")
    
    def test_parse_partial_meeting_analysis_response(self):
        """Test parsing a partial LLM response with missing fields."""
        llm_response = """
Meeting Intent: schedule_new
Meeting Type: consultation
Urgency: medium
"""
        
        result = parse_meeting_analysis_response(llm_response)
        
        self.assertEqual(result["meeting_intent"], "schedule_new")
        self.assertEqual(result["meeting_type"], "consultation")
        self.assertEqual(result["urgency"], "medium")
        # Check that defaults are applied for missing fields
        self.assertEqual(result["preferred_time"], "flexible")
        self.assertEqual(result["duration"], "60min")
        self.assertEqual(result["booking_action"], "propose_times")
    
    def test_parse_malformed_meeting_analysis_response(self):
        """Test parsing a malformed LLM response."""
        llm_response = "This is not a properly formatted response"
        
        result = parse_meeting_analysis_response(llm_response)
        
        # Should return defaults for all fields
        self.assertEqual(result["meeting_intent"], "schedule_new")
        self.assertEqual(result["meeting_type"], "consultation")
        self.assertEqual(result["urgency"], "medium")
        self.assertEqual(result["preferred_time"], "flexible")
    
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
        # This should be available in mock_calendar_slots
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
            "meeting_intent": "schedule_new",
            "booking_action": "propose_times"
        }
        
        response = generate_meeting_response(analysis_result)
        
        self.assertIn("scheduling", response.lower())
        self.assertIn("meeting", response.lower())
    
    def test_generate_meeting_response_decline(self):
        """Test generating response for declining a meeting."""
        analysis_result = {
            "meeting_intent": "decline",
            "booking_action": "decline_politely"
        }
        
        response = generate_meeting_response(analysis_result)
        
        self.assertIn("not interested", response.lower())
        self.assertIn("reach out", response.lower())
    
    def test_generate_meeting_response_book_immediately(self):
        """Test generating response for immediate booking."""
        analysis_result = {
            "meeting_intent": "schedule_new",
            "booking_action": "book_immediately",
            "suggested_datetime": "2025-05-26 14:00"
        }
        
        response = generate_meeting_response(analysis_result)
        
        self.assertIn("scheduled", response.lower())
        self.assertIn("2025-05-26 14:00", response)

class TestMeetingSchedulingIntegration(unittest.TestCase):
    """Integration tests for meeting scheduling system."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create memory store and manager with temporary database
        self.memory_store = SQLiteMemoryStore(self.temp_db.name)
        self.memory_manager = MemoryManager(self.memory_store)
    
    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_db.name)
    
    def test_handle_immediate_meeting_request(self):
        """Test handling an immediate meeting request."""
        request_data = mock_meeting_requests["meeting_001"]
        context = build_context_from_meeting_request(request_data, self.memory_manager)
        
        self.assertIn("lead_info", context)
        self.assertIn("meeting_request", context)
    
    def test_handle_specific_time_request(self):
        """Test handling a specific time meeting request."""
        request_data = mock_meeting_requests["meeting_002"]
        context = build_context_from_meeting_request(request_data, self.memory_manager)
        
        self.assertIn("lead_info", context)
        self.assertIn("meeting_request", context)
    
    def test_handle_flexible_timing_request(self):
        """Test handling a flexible timing meeting request."""
        request_data = mock_meeting_requests["meeting_003"]
        context = build_context_from_meeting_request(request_data, self.memory_manager)
        
        self.assertIn("lead_info", context)
        self.assertIn("meeting_request", context)
    
    def test_handle_reschedule_request(self):
        """Test handling a reschedule request."""
        request_data = mock_meeting_requests["meeting_004"]
        context = build_context_from_meeting_request(request_data, self.memory_manager)
        
        self.assertIn("lead_info", context)
        self.assertIn("meeting_request", context)
    
    def test_handle_meeting_decline(self):
        """Test handling a meeting decline."""
        request_data = mock_meeting_requests["meeting_005"]
        context = build_context_from_meeting_request(request_data, self.memory_manager)
        
        self.assertIn("lead_info", context)
        self.assertIn("meeting_request", context)

class TestMeetingSchedulingEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset mock calendar slots to ensure clean state for each test
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
        
        # Initialize memory manager with temporary database
        store = SQLiteMemoryStore(self.temp_db.name)
        self.memory_manager = MemoryManager(store)
        
        # Save mock qualification data
        self.memory_manager.save_qualification("lead_001", {
            "priority": "high",
            "lead_score": 85,
            "reasoning": "Strong interest in product demo",
            "next_action": "Schedule demo call"
        })
        
        self.memory_manager.save_qualification("lead_002", {
            "priority": "medium", 
            "lead_score": 65,
            "reasoning": "Needs more information",
            "next_action": "Send product brochure"
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_db.name)
    
    def test_parse_llm_response_with_special_characters(self):
        """Test parsing LLM response with special characters."""
        llm_response = """
Meeting Intent: schedule_new
Meeting Type: demo/consultation
Urgency: high!!!
Preferred Time: flexible (any time works)
Duration: 60min
Analysis: Lead is very interested & wants immediate demo!!!
"""
        
        result = parse_meeting_analysis_response(llm_response)
        
        self.assertEqual(result["meeting_intent"], "schedule_new")
        self.assertEqual(result["meeting_type"], "demo/consultation")
        self.assertEqual(result["urgency"], "high!!!")
    
    def test_check_calendar_availability_various_formats(self):
        """Test calendar availability with various datetime formats."""
        # Valid format
        self.assertTrue(check_calendar_availability("2025-05-26 09:00"))
        
        # Invalid formats
        self.assertFalse(check_calendar_availability("invalid-date"))
        self.assertFalse(check_calendar_availability("2025-05-26"))
        self.assertFalse(check_calendar_availability("09:00"))
    
    def test_book_meeting_invalid_datetime(self):
        """Test booking meeting with invalid datetime format."""
        event_id = book_meeting("lead_001", "invalid-datetime", "demo", "60min")
        self.assertIsNone(event_id)
    
    def test_build_context_missing_lead(self):
        """Test building context for non-existent lead."""
        request_data = {
            "lead_id": "nonexistent_lead",
            "request_id": "test_001",
            "message": "Test message",
            "timestamp": "2025-05-25 10:00:00",
            "urgency": "medium"
        }
        
        context = build_context_from_meeting_request(request_data, self.memory_manager)
        
        # Should handle gracefully with default values
        self.assertIn("Unknown", context["lead_info"])
        self.assertIn("No previous meetings", context["meeting_history"])

if __name__ == "__main__":
    unittest.main() 