"""Tests for MeetingScheduler agent."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from agents.meeting_scheduler import MeetingScheduler


class TestMeetingScheduler:
    """Test suite for MeetingScheduler agent."""
    
    @pytest.fixture
    def mock_agent_core(self):
        """Mock AgentCore for testing."""
        mock_core = Mock()
        mock_core.create_llm_chain.return_value = Mock()
        mock_core.parse_structured_response.return_value = {
            'intent': 'schedule_meeting',
            'urgency': 'high',
            'preferred_duration': 60,
            'time_preferences': 'Morning preferred',
            'meeting_type': 'demo',
            'flexibility': 'medium',
            'next_action': 'Propose meeting times'
        }
        return mock_core
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock MemoryManager for testing."""
        return Mock()
    
    @pytest.fixture
    def sample_request_data(self):
        """Sample meeting request data for testing."""
        return {
            'request_text': 'I would like to schedule a demo for next week. Mornings work best for me.',
            'sender_email': 'john.doe@example.com',
            'preferred_times': 'Morning preferred',
            'meeting_type': 'demo',
            'lead_id': 'lead_123'
        }
    
    @pytest.fixture
    def sample_lead_context(self):
        """Sample lead context for testing."""
        return {
            'name': 'John Doe',
            'company': 'Example Corp',
            'previous_meetings': 'None',
            'timezone': 'EST'
        }
    
    @pytest.fixture
    def sample_meeting_data(self):
        """Sample meeting data for testing."""
        # Create a time that's guaranteed to be in business hours (10 AM on a weekday)
        future_time = datetime.now() + timedelta(days=1)
        while future_time.weekday() >= 5:  # Ensure it's a weekday
            future_time += timedelta(days=1)
        future_time = future_time.replace(hour=10, minute=0, second=0, microsecond=0)
        
        return {
            'lead_id': 'lead_123',
            'start_time': future_time,
            'duration': 30,
            'meeting_type': 'demo',
            'attendees': ['john.doe@example.com'],
            'notes': 'Product demo meeting'
        }
    
    def test_init_success(self, mock_agent_core, mock_memory_manager):
        """Test successful initialization."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        assert scheduler.agent_core == mock_agent_core
        assert scheduler.memory_manager == mock_memory_manager
        assert scheduler.business_start_hour == 9
        assert scheduler.business_end_hour == 17
        assert scheduler.default_duration == 30
    
    def test_init_none_agent_core(self, mock_memory_manager):
        """Test initialization with None agent_core."""
        with pytest.raises(ValueError, match="agent_core cannot be None"):
            MeetingScheduler(None, mock_memory_manager)
    
    def test_init_none_memory_manager(self, mock_agent_core):
        """Test initialization with None memory_manager."""
        with pytest.raises(ValueError, match="memory_manager cannot be None"):
            MeetingScheduler(mock_agent_core, None)
    
    def test_analyze_request_success(self, mock_agent_core, mock_memory_manager, sample_request_data, sample_lead_context):
        """Test successful request analysis."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Mock the chain
        mock_chain = Mock()
        mock_chain.run.return_value = "Intent: schedule_meeting\nUrgency: high\nMeeting Type: demo"
        mock_agent_core.create_llm_chain.return_value = mock_chain
        
        result = scheduler.analyze_request(sample_request_data, sample_lead_context)
        
        assert result is not None
        assert result['intent'] == 'schedule_meeting'
        assert result['urgency'] == 'high'
        assert result['meeting_type'] == 'demo'
        
        # Verify chain was called with correct parameters
        mock_chain.run.assert_called_once()
        call_args = mock_chain.run.call_args.kwargs
        assert call_args['request_text'] == sample_request_data['request_text']
        assert call_args['sender_email'] == sample_request_data['sender_email']
    
    def test_analyze_request_invalid_data(self, mock_agent_core, mock_memory_manager, sample_lead_context):
        """Test analysis with invalid request data."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        invalid_data = {'request_text': ''}  # Missing sender_email
        
        with pytest.raises(ValueError, match="request_data is missing required fields"):
            scheduler.analyze_request(invalid_data, sample_lead_context)
    
    def test_analyze_request_invalid_context(self, mock_agent_core, mock_memory_manager, sample_request_data):
        """Test analysis with invalid lead context."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        with pytest.raises(ValueError, match="lead_context must be a valid dictionary"):
            scheduler.analyze_request(sample_request_data, None)
    
    def test_analyze_request_llm_failure(self, mock_agent_core, mock_memory_manager, sample_request_data, sample_lead_context):
        """Test analysis when LLM fails."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Mock chain to raise exception
        mock_chain = Mock()
        mock_chain.run.side_effect = Exception("LLM error")
        mock_agent_core.create_llm_chain.return_value = mock_chain
        
        with pytest.raises(RuntimeError, match="Meeting request analysis failed"):
            scheduler.analyze_request(sample_request_data, sample_lead_context)
    
    def test_book_success(self, mock_agent_core, mock_memory_manager, sample_meeting_data):
        """Test successful meeting booking."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        result = scheduler.book(sample_meeting_data)
        
        assert result['status'] == 'confirmed'
        assert result['booking_id'] is not None
        assert result['confirmation_message'] is not None
        assert result['calendar_link'] is not None
        assert 'meeting_' in result['booking_id']
    
    def test_book_invalid_data(self, mock_agent_core, mock_memory_manager):
        """Test booking with invalid meeting data."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        invalid_data = {'lead_id': 'test'}  # Missing start_time
        
        with pytest.raises(ValueError, match="meeting_data is missing required fields"):
            scheduler.book(invalid_data)
    
    def test_book_unavailable_time(self, mock_agent_core, mock_memory_manager):
        """Test booking when time is unavailable."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Create meeting data for 2 PM (which is blocked in our mock)
        unavailable_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=1)
        meeting_data = {
            'lead_id': 'lead_123',
            'start_time': unavailable_time,
            'duration': 30
        }
        
        result = scheduler.book(meeting_data)
        
        assert result['status'] == 'failed'
        assert result['booking_id'] is None
        assert 'not available' in result['confirmation_message']
    
    def test_check_availability_valid_time(self, mock_agent_core, mock_memory_manager):
        """Test availability check for valid business hours."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # 10 AM tomorrow (valid business hours)
        valid_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        assert scheduler.check_availability(valid_time, 30) is True
    
    def test_check_availability_past_time(self, mock_agent_core, mock_memory_manager):
        """Test availability check for past time."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        past_time = datetime.now() - timedelta(hours=1)
        
        assert scheduler.check_availability(past_time, 30) is False
    
    def test_check_availability_weekend(self, mock_agent_core, mock_memory_manager):
        """Test availability check for weekend."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Find next Saturday
        today = datetime.now()
        days_ahead = 5 - today.weekday()  # Saturday = 5
        if days_ahead <= 0:
            days_ahead += 7
        saturday = today + timedelta(days=days_ahead)
        saturday = saturday.replace(hour=10, minute=0, second=0, microsecond=0)
        
        assert scheduler.check_availability(saturday, 30) is False
    
    def test_check_availability_outside_business_hours(self, mock_agent_core, mock_memory_manager):
        """Test availability check outside business hours."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # 8 AM (before business hours)
        early_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
        assert scheduler.check_availability(early_time, 30) is False
        
        # 6 PM (after business hours)
        late_time = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0) + timedelta(days=1)
        assert scheduler.check_availability(late_time, 30) is False
    
    def test_check_availability_blocked_time(self, mock_agent_core, mock_memory_manager):
        """Test availability check for blocked time (2 PM)."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # 2 PM tomorrow (blocked in our mock)
        blocked_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        assert scheduler.check_availability(blocked_time, 30) is False
    
    def test_check_availability_invalid_input(self, mock_agent_core, mock_memory_manager):
        """Test availability check with invalid input."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        with pytest.raises(ValueError, match="start_time must be a datetime object"):
            scheduler.check_availability("not a datetime", 30)
        
        valid_time = datetime.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="duration must be positive"):
            scheduler.check_availability(valid_time, -30)
    
    def test_get_available_slots(self, mock_agent_core, mock_memory_manager):
        """Test getting available slots."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        start_date = datetime.now() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)
        
        slots = scheduler.get_available_slots(start_date, end_date, 30)
        
        assert isinstance(slots, list)
        # Should have some slots (exact number depends on current time and mock conflicts)
        assert len(slots) > 0
        
        # All slots should be datetime objects
        for slot in slots:
            assert isinstance(slot, datetime)
            # Should be within business hours
            assert 9 <= slot.hour < 17
            # Should be weekday
            assert slot.weekday() < 5
    
    def test_get_available_slots_invalid_range(self, mock_agent_core, mock_memory_manager):
        """Test getting available slots with invalid date range."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        start_date = datetime.now() + timedelta(days=2)
        end_date = datetime.now() + timedelta(days=1)  # End before start
        
        with pytest.raises(ValueError, match="start_date must be before end_date"):
            scheduler.get_available_slots(start_date, end_date, 30)
    
    def test_get_available_slots_invalid_input(self, mock_agent_core, mock_memory_manager):
        """Test getting available slots with invalid input."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        with pytest.raises(ValueError, match="start_date and end_date must be datetime objects"):
            scheduler.get_available_slots("not datetime", datetime.now(), 30)
        
        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="duration must be positive"):
            scheduler.get_available_slots(start_date, end_date, -30)
    
    def test_propose_meeting_times(self, mock_agent_core, mock_memory_manager):
        """Test proposing meeting times."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        preferences = {
            'preferred_days': ['Monday', 'Tuesday'],
            'preferred_times': ['9:00-12:00'],
            'urgency': 'high'
        }
        
        proposals = scheduler.propose_meeting_times(preferences, 3)
        
        assert isinstance(proposals, list)
        assert len(proposals) <= 3  # Should return at most 3 options
        
        for proposal in proposals:
            assert 'option_number' in proposal
            assert 'start_time' in proposal
            assert 'end_time' in proposal
            assert 'formatted_time' in proposal
            assert 'score' in proposal
            assert isinstance(proposal['start_time'], datetime)
    
    def test_propose_meeting_times_invalid_preferences(self, mock_agent_core, mock_memory_manager):
        """Test proposing meeting times with invalid preferences."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        with pytest.raises(ValueError, match="lead_preferences must be a valid dictionary"):
            scheduler.propose_meeting_times(None, 3)
        
        with pytest.raises(ValueError, match="num_options must be positive"):
            scheduler.propose_meeting_times({}, -1)
    
    def test_generate_meeting_response_schedule(self, mock_agent_core, mock_memory_manager):
        """Test generating response for schedule meeting intent."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        analysis_result = {
            'intent': 'schedule_meeting',
            'meeting_type': 'demo'
        }
        
        proposed_times = [
            {
                'option_number': 1,
                'formatted_time': '2024-01-15 10:00',
                'day_of_week': 'Monday'
            },
            {
                'option_number': 2,
                'formatted_time': '2024-01-15 14:00',
                'day_of_week': 'Monday'
            }
        ]
        
        response = scheduler.generate_meeting_response(analysis_result, proposed_times)
        
        assert 'demo' in response
        assert 'Option 1:' in response
        assert 'Option 2:' in response
        assert '2024-01-15 10:00' in response
        assert 'calendar invitation' in response
    
    def test_generate_meeting_response_reschedule(self, mock_agent_core, mock_memory_manager):
        """Test generating response for reschedule intent."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        analysis_result = {
            'intent': 'reschedule',
            'meeting_type': 'consultation'
        }
        
        proposed_times = [
            {
                'option_number': 1,
                'formatted_time': '2024-01-16 11:00',
                'day_of_week': 'Tuesday'
            }
        ]
        
        response = scheduler.generate_meeting_response(analysis_result, proposed_times)
        
        assert 'reschedule' in response
        assert 'alternative times' in response
        assert 'Option 1:' in response
    
    def test_generate_meeting_response_cancel(self, mock_agent_core, mock_memory_manager):
        """Test generating response for cancel intent."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        analysis_result = {
            'intent': 'cancel',
            'meeting_type': 'demo'
        }
        
        response = scheduler.generate_meeting_response(analysis_result, [])
        
        assert 'cancel' in response
        assert 'No problem' in response
        assert 'reschedule for a future date' in response
    
    def test_generate_meeting_response_no_times(self, mock_agent_core, mock_memory_manager):
        """Test generating response when no times are available."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        analysis_result = {
            'intent': 'schedule_meeting',
            'meeting_type': 'demo'
        }
        
        response = scheduler.generate_meeting_response(analysis_result, [])
        
        assert 'Unfortunately' in response
        assert 'alternative times' in response
    
    def test_generate_meeting_response_invalid_input(self, mock_agent_core, mock_memory_manager):
        """Test generating response with invalid input."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        with pytest.raises(ValueError, match="analysis_result must be a valid dictionary"):
            scheduler.generate_meeting_response(None, [])
    
    def test_validate_request_data_valid(self, mock_agent_core, mock_memory_manager):
        """Test validation with valid request data."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        valid_data = {
            'request_text': 'I want to schedule a meeting',
            'sender_email': 'test@example.com'
        }
        
        assert scheduler._validate_request_data(valid_data) is True
    
    def test_validate_request_data_invalid(self, mock_agent_core, mock_memory_manager):
        """Test validation with invalid request data."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Missing required fields
        invalid_data1 = {'request_text': 'Some text'}  # Missing sender_email
        assert scheduler._validate_request_data(invalid_data1) is False
        
        # Empty required fields
        invalid_data2 = {'request_text': '', 'sender_email': 'test@example.com'}
        assert scheduler._validate_request_data(invalid_data2) is False
        
        # None input
        assert scheduler._validate_request_data(None) is False
        
        # Non-dict input
        assert scheduler._validate_request_data("not a dict") is False
    
    def test_validate_meeting_data_valid(self, mock_agent_core, mock_memory_manager):
        """Test validation with valid meeting data."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        valid_data = {
            'lead_id': 'lead_123',
            'start_time': datetime.now() + timedelta(days=1)
        }
        
        assert scheduler._validate_meeting_data(valid_data) is True
    
    def test_validate_meeting_data_invalid(self, mock_agent_core, mock_memory_manager):
        """Test validation with invalid meeting data."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Missing required fields
        invalid_data1 = {'lead_id': 'test'}  # Missing start_time
        assert scheduler._validate_meeting_data(invalid_data1) is False
        
        # Invalid start_time type
        invalid_data2 = {'lead_id': 'test', 'start_time': 'not a datetime'}
        assert scheduler._validate_meeting_data(invalid_data2) is False
        
        # None input
        assert scheduler._validate_meeting_data(None) is False
    
    def test_is_business_hours(self, mock_agent_core, mock_memory_manager):
        """Test business hours checking."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Valid business hours (10 AM on a weekday)
        weekday_morning = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        while weekday_morning.weekday() >= 5:  # Ensure it's a weekday
            weekday_morning += timedelta(days=1)
        
        assert scheduler._is_business_hours(weekday_morning, 30) is True
        
        # Weekend
        saturday = datetime.now()
        while saturday.weekday() != 5:  # Find a Saturday
            saturday += timedelta(days=1)
        saturday = saturday.replace(hour=10, minute=0, second=0, microsecond=0)
        
        assert scheduler._is_business_hours(saturday, 30) is False
        
        # Too early (8 AM)
        early_time = weekday_morning.replace(hour=8)
        assert scheduler._is_business_hours(early_time, 30) is False
        
        # Too late (6 PM)
        late_time = weekday_morning.replace(hour=18)
        assert scheduler._is_business_hours(late_time, 30) is False
        
        # Meeting runs past business hours
        late_meeting = weekday_morning.replace(hour=16, minute=45)  # 4:45 PM
        assert scheduler._is_business_hours(late_meeting, 30) is False  # Would end at 5:15 PM
    
    def test_calculate_slot_score(self, mock_agent_core, mock_memory_manager):
        """Test slot scoring based on preferences."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Monday 10 AM
        monday_morning = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        while monday_morning.weekday() != 0:  # Find a Monday
            monday_morning += timedelta(days=1)
        
        preferences = {
            'preferred_days': ['Monday'],
            'preferred_times': ['9:00-12:00']
        }
        
        score = scheduler._calculate_slot_score(monday_morning, preferences)
        
        # Should get bonus for preferred day (20) + preferred time (15) + morning (10) = 45
        assert score >= 35  # Allow some flexibility in scoring
    
    def test_time_in_range(self, mock_agent_core, mock_memory_manager):
        """Test time range checking."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # 10 AM slot
        slot = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Should be in 9:00-12:00 range
        assert scheduler._time_in_range(slot, "9:00-12:00") is True
        
        # Should not be in 13:00-16:00 range
        assert scheduler._time_in_range(slot, "13:00-16:00") is False
        
        # Invalid range format
        assert scheduler._time_in_range(slot, "invalid") is False
    
    def test_generate_confirmation_message(self, mock_agent_core, mock_memory_manager):
        """Test confirmation message generation."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        meeting_record = {
            'start_time': '2024-01-15T10:00:00',
            'meeting_type': 'demo',
            'duration': 30
        }
        
        message = scheduler._generate_confirmation_message(meeting_record)
        
        assert 'confirmed' in message
        assert 'demo' in message
        assert '30 minutes' in message
        assert 'calendar invitation' in message
        assert 'Looking forward' in message
    
    def test_build_context_string(self, mock_agent_core, mock_memory_manager):
        """Test context string building."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Full context
        full_context = {
            'name': 'John Doe',
            'company': 'Example Corp',
            'previous_meetings': 'Initial consultation'
        }
        
        context_str = scheduler._build_context_string(full_context)
        assert 'Lead Name: John Doe' in context_str
        assert 'Company: Example Corp' in context_str
        assert 'Previous Meetings: Initial consultation' in context_str
        
        # Empty context
        empty_context = {}
        context_str = scheduler._build_context_string(empty_context)
        assert context_str == "No additional context available"
    
    def test_build_request_prompt(self, mock_agent_core, mock_memory_manager, sample_request_data):
        """Test request prompt building."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        prompt = scheduler._build_request_prompt(sample_request_data, "Additional context")
        
        assert '{request_text}' in prompt
        assert '{sender_email}' in prompt
        assert '{lead_context}' in prompt
        assert '{preferred_times}' in prompt
        assert 'Additional context' in prompt
        assert 'Intent:' in prompt
        assert 'Urgency:' in prompt
        assert 'Meeting Type:' in prompt
    
    def test_parse_request_analysis(self, mock_agent_core, mock_memory_manager):
        """Test request analysis parsing."""
        scheduler = MeetingScheduler(mock_agent_core, mock_memory_manager)
        
        # Mock the parse_structured_response method
        expected_result = {
            'intent': 'schedule_meeting',
            'urgency': 'high',
            'preferred_duration': 60,
            'time_preferences': 'Morning preferred',
            'meeting_type': 'demo',
            'flexibility': 'medium',
            'next_action': 'Propose meeting times'
        }
        mock_agent_core.parse_structured_response.return_value = expected_result
        
        result = scheduler._parse_request_analysis("Some LLM response")
        
        assert result == expected_result
        mock_agent_core.parse_structured_response.assert_called_once() 