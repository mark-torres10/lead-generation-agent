"""Unit tests for MeetingScheduler class."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from agents.meeting_scheduler import MeetingScheduler
from agents.agent_core import AgentCore


class TestMeetingScheduler:
    """Test cases for MeetingScheduler functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_agent_core = Mock(spec=AgentCore)
        self.mock_memory_manager = Mock()
        self.mock_calendar_service = Mock()
        self.meeting_scheduler = MeetingScheduler(
            self.mock_agent_core, 
            self.mock_memory_manager, 
            self.mock_calendar_service
        )
        
        self.sample_meeting_request = {
            "lead_name": "John Smith",
            "lead_email": "john@techcorp.com",
            "company": "TechCorp Inc",
            "request_content": "Could we schedule a demo call next week? I'm available Tuesday or Wednesday afternoon.",
            "original_email": "Hi John, I wanted to follow up on your interest...",
            "timestamp": "2024-01-15T10:30:00Z",
            "lead_score": 85
        }
    
    def test_init_with_valid_dependencies(self):
        """Test MeetingScheduler initialization with valid dependencies."""
        scheduler = MeetingScheduler(
            self.mock_agent_core, 
            self.mock_memory_manager, 
            self.mock_calendar_service
        )
        assert scheduler is not None
    
    def test_init_with_none_dependencies(self):
        """Test MeetingScheduler initialization with None dependencies."""
        with pytest.raises(ValueError):
            MeetingScheduler(None, self.mock_memory_manager, self.mock_calendar_service)
        
        with pytest.raises(ValueError):
            MeetingScheduler(self.mock_agent_core, None, self.mock_calendar_service)
        
        with pytest.raises(ValueError):
            MeetingScheduler(self.mock_agent_core, self.mock_memory_manager, None)
    
    def test_analyze_request_with_valid_meeting_request(self):
        """Test meeting request analysis with valid request data."""
        result = self.meeting_scheduler.analyze_request(self.sample_meeting_request)
        
        assert result is not None
        assert "meeting_intent" in result
        assert "meeting_type" in result
        assert "urgency" in result
        assert "preferred_time" in result
        assert "duration" in result
        assert "analysis" in result
        assert "recommended_response" in result
        assert "booking_action" in result
        assert "suggested_datetime" in result
    
    def test_analyze_request_with_missing_required_fields(self):
        """Test analysis with missing required fields."""
        incomplete_data = {"lead_name": "John Smith"}  # Missing required fields
        
        with pytest.raises(ValueError):
            self.meeting_scheduler.analyze_request(incomplete_data)
    
    def test_analyze_request_with_empty_request_data(self):
        """Test analysis with empty request data."""
        with pytest.raises(ValueError):
            self.meeting_scheduler.analyze_request({})
    
    def test_book_with_valid_meeting_details(self):
        """Test meeting booking with valid details."""
        meeting_details = {
            "lead_name": "John Smith",
            "lead_email": "john@techcorp.com",
            "datetime": "2024-01-22T14:00:00Z",
            "duration": 30,
            "meeting_type": "demo",
            "notes": "Product demo call"
        }
        
        result = self.meeting_scheduler.book(meeting_details)
        
        assert result is not None
        assert "booking_id" in result
        assert "calendar_event_id" in result
        assert "confirmation_sent" in result
        assert "meeting_details" in result
        assert "updated_lead_score" in result
    
    def test_book_with_invalid_datetime(self):
        """Test booking with invalid datetime."""
        invalid_meeting_details = {
            "lead_name": "John Smith",
            "lead_email": "john@techcorp.com",
            "datetime": "invalid-datetime",
            "duration": 30,
            "meeting_type": "demo"
        }
        
        with pytest.raises(ValueError):
            self.meeting_scheduler.book(invalid_meeting_details)
    
    def test_book_with_past_datetime(self):
        """Test booking with past datetime."""
        past_datetime = (datetime.now() - timedelta(days=1)).isoformat()
        past_meeting_details = {
            "lead_name": "John Smith",
            "lead_email": "john@techcorp.com",
            "datetime": past_datetime,
            "duration": 30,
            "meeting_type": "demo"
        }
        
        with pytest.raises(ValueError):
            self.meeting_scheduler.book(past_meeting_details)
    
    def test_check_availability_with_valid_datetime(self):
        """Test availability check with valid datetime."""
        test_datetime = "2024-01-22T14:00:00Z"
        duration = 30
        
        is_available = self.meeting_scheduler.check_availability(test_datetime, duration)
        
        assert isinstance(is_available, bool)
    
    def test_check_availability_with_invalid_datetime(self):
        """Test availability check with invalid datetime."""
        with pytest.raises(ValueError):
            self.meeting_scheduler.check_availability("invalid-datetime", 30)
    
    def test_check_availability_with_invalid_duration(self):
        """Test availability check with invalid duration."""
        test_datetime = "2024-01-22T14:00:00Z"
        
        with pytest.raises(ValueError):
            self.meeting_scheduler.check_availability(test_datetime, 0)
        
        with pytest.raises(ValueError):
            self.meeting_scheduler.check_availability(test_datetime, -30)
    
    def test_get_available_slots_with_valid_date_range(self):
        """Test getting available slots with valid date range."""
        start_date = "2024-01-22"
        end_date = "2024-01-26"
        duration = 30
        
        slots = self.meeting_scheduler.get_available_slots(start_date, end_date, duration)
        
        assert isinstance(slots, list)
        # Each slot should have datetime and duration
        for slot in slots:
            assert "datetime" in slot
            assert "duration" in slot
    
    def test_get_available_slots_with_invalid_date_range(self):
        """Test getting available slots with invalid date range."""
        # End date before start date
        with pytest.raises(ValueError):
            self.meeting_scheduler.get_available_slots("2024-01-26", "2024-01-22", 30)
    
    def test_get_available_slots_with_invalid_duration(self):
        """Test getting available slots with invalid duration."""
        with pytest.raises(ValueError):
            self.meeting_scheduler.get_available_slots("2024-01-22", "2024-01-26", 0)
    
    def test_propose_meeting_times_with_valid_preferences(self):
        """Test proposing meeting times with valid preferences."""
        preferences = {
            "preferred_days": ["Tuesday", "Wednesday"],
            "preferred_times": ["afternoon"],
            "duration": 30,
            "urgency": "high",
            "timezone": "UTC"
        }
        
        proposals = self.meeting_scheduler.propose_meeting_times(preferences)
        
        assert isinstance(proposals, list)
        assert len(proposals) > 0
        # Each proposal should have datetime and reasoning
        for proposal in proposals:
            assert "datetime" in proposal
            assert "reasoning" in proposal
    
    def test_propose_meeting_times_with_missing_preferences(self):
        """Test proposing meeting times with missing preferences."""
        incomplete_preferences = {"duration": 30}  # Missing required preferences
        
        with pytest.raises(ValueError):
            self.meeting_scheduler.propose_meeting_times(incomplete_preferences)
    
    def test_generate_meeting_response_with_booking_confirmation(self):
        """Test generating response for successful booking."""
        booking_result = {
            "booking_id": "book_123",
            "calendar_event_id": "cal_456",
            "confirmation_sent": True,
            "meeting_details": {
                "datetime": "2024-01-22T14:00:00Z",
                "duration": 30,
                "meeting_type": "demo"
            }
        }
        
        response = self.meeting_scheduler.generate_meeting_response(
            self.sample_meeting_request, 
            booking_result
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "confirmed" in response.lower() or "scheduled" in response.lower()
    
    def test_generate_meeting_response_with_booking_failure(self):
        """Test generating response for failed booking."""
        booking_result = {
            "booking_id": None,
            "calendar_event_id": None,
            "confirmation_sent": False,
            "error": "Time slot not available"
        }
        
        response = self.meeting_scheduler.generate_meeting_response(
            self.sample_meeting_request, 
            booking_result
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "sorry" in response.lower() or "unable" in response.lower()
    
    def test_update_lead_qualification_after_booking(self):
        """Test updating lead qualification after successful booking."""
        booking_result = {
            "booking_id": "book_123",
            "calendar_event_id": "cal_456",
            "confirmation_sent": True,
            "meeting_details": {
                "datetime": "2024-01-22T14:00:00Z",
                "duration": 30,
                "meeting_type": "demo"
            }
        }
        current_score = 85
        
        updated_qualification = self.meeting_scheduler.update_lead_qualification(
            booking_result, 
            current_score
        )
        
        assert isinstance(updated_qualification, dict)
        assert "lead_score" in updated_qualification
        assert "priority" in updated_qualification
        assert "next_action" in updated_qualification
        assert "reasoning" in updated_qualification
    
    def test_update_lead_qualification_after_failed_booking(self):
        """Test updating lead qualification after failed booking."""
        booking_result = {
            "booking_id": None,
            "calendar_event_id": None,
            "confirmation_sent": False,
            "error": "Time slot not available"
        }
        current_score = 85
        
        updated_qualification = self.meeting_scheduler.update_lead_qualification(
            booking_result, 
            current_score
        )
        
        assert isinstance(updated_qualification, dict)
        assert updated_qualification["lead_score"] <= current_score  # Should not increase
    
    def test_parse_meeting_analysis_with_valid_response(self):
        """Test parsing valid LLM meeting analysis response."""
        llm_response = """
        MEETING_INTENT: demo_request
        MEETING_TYPE: product_demo
        URGENCY: high
        PREFERRED_TIME: next_week_afternoon
        DURATION: 30
        ANALYSIS: Strong interest in product demo
        RECOMMENDED_RESPONSE: Confirm availability and schedule
        BOOKING_ACTION: schedule_immediately
        SUGGESTED_DATETIME: 2024-01-22T14:00:00Z
        """
        
        result = self.meeting_scheduler._parse_meeting_analysis(llm_response)
        
        assert result["meeting_intent"] == "demo_request"
        assert result["meeting_type"] == "product_demo"
        assert result["urgency"] == "high"
        assert result["preferred_time"] == "next_week_afternoon"
        assert result["duration"] == 30
        assert "Strong interest" in result["analysis"]
        assert result["recommended_response"] == "Confirm availability and schedule"
        assert result["booking_action"] == "schedule_immediately"
        assert result["suggested_datetime"] == "2024-01-22T14:00:00Z"
    
    def test_parse_meeting_analysis_with_invalid_response(self):
        """Test parsing invalid LLM response."""
        invalid_response = "This is not a structured response"
        
        with pytest.raises(ValueError):
            self.meeting_scheduler._parse_meeting_analysis(invalid_response)
    
    def test_build_meeting_prompt_with_valid_data(self):
        """Test building meeting analysis prompt with valid data."""
        context = "Previous qualification: high priority lead"
        
        prompt = self.meeting_scheduler._build_meeting_prompt(
            self.sample_meeting_request, 
            context
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "John Smith" in prompt
        assert "TechCorp Inc" in prompt
        assert "demo call next week" in prompt
    
    def test_build_meeting_prompt_with_missing_fields(self):
        """Test building prompt with missing required fields."""
        incomplete_data = {"lead_name": "John"}  # Missing required fields
        
        with pytest.raises(ValueError):
            self.meeting_scheduler._build_meeting_prompt(incomplete_data)
    
    def test_validate_meeting_request_with_valid_data(self):
        """Test meeting request validation with valid data."""
        is_valid = self.meeting_scheduler._validate_meeting_request(self.sample_meeting_request)
        assert is_valid is True
    
    def test_validate_meeting_request_with_missing_fields(self):
        """Test meeting request validation with missing fields."""
        incomplete_data = {"lead_name": "John Smith"}  # Missing required fields
        
        is_valid = self.meeting_scheduler._validate_meeting_request(incomplete_data)
        assert is_valid is False
    
    def test_validate_meeting_request_with_empty_data(self):
        """Test meeting request validation with empty data."""
        is_valid = self.meeting_scheduler._validate_meeting_request({})
        assert is_valid is False
    
    def test_validate_meeting_request_with_none_data(self):
        """Test meeting request validation with None data."""
        is_valid = self.meeting_scheduler._validate_meeting_request(None)
        assert is_valid is False
    
    def test_parse_datetime_with_valid_iso_format(self):
        """Test datetime parsing with valid ISO format."""
        iso_datetime = "2024-01-22T14:00:00Z"
        
        parsed_dt = self.meeting_scheduler._parse_datetime(iso_datetime)
        
        assert isinstance(parsed_dt, datetime)
        assert parsed_dt.year == 2024
        assert parsed_dt.month == 1
        assert parsed_dt.day == 22
        assert parsed_dt.hour == 14
    
    def test_parse_datetime_with_invalid_format(self):
        """Test datetime parsing with invalid format."""
        with pytest.raises(ValueError):
            self.meeting_scheduler._parse_datetime("invalid-datetime")
    
    def test_parse_datetime_with_empty_string(self):
        """Test datetime parsing with empty string."""
        with pytest.raises(ValueError):
            self.meeting_scheduler._parse_datetime("")
    
    def test_parse_datetime_with_none(self):
        """Test datetime parsing with None."""
        with pytest.raises(ValueError):
            self.meeting_scheduler._parse_datetime(None) 