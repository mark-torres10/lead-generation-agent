"""Meeting scheduling agent.

This module provides functionality for analyzing meeting requests, checking
availability, and booking meetings with leads.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from .agent_core import AgentCore


class MeetingScheduler:
    """Agent for handling meeting scheduling requests and availability.
    
    Analyzes meeting requests, checks availability, and manages the booking
    process for sales meetings with leads.
    """
    
    def __init__(self, agent_core: AgentCore, memory_manager: Any):
        """Initialize the MeetingScheduler with dependencies.
        
        Args:
            agent_core: Core agent infrastructure for LLM operations
            memory_manager: Memory manager for storing/retrieving meeting data
        """
        if agent_core is None:
            raise ValueError("agent_core cannot be None")
        if memory_manager is None:
            raise ValueError("memory_manager cannot be None")
        
        self.agent_core = agent_core
        self.memory_manager = memory_manager
        
        # Default business hours (9 AM to 5 PM)
        self.business_start_hour = 9
        self.business_end_hour = 17
        
        # Default meeting duration (30 minutes)
        self.default_duration = 30
    
    def analyze_request(self, request_data: Dict[str, Any], lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a meeting request to determine intent and scheduling approach.
        
        Analyzes the meeting request content to understand the lead's preferences,
        urgency, and specific requirements for scheduling.
        
        Args:
            request_data: Dictionary containing request information:
                         - request_text: Content of the meeting request
                         - sender_email: Email address of requester
                         - preferred_times: Any time preferences mentioned
                         - meeting_type: Type of meeting requested
                         - lead_id: ID of the requesting lead
            lead_context: Dictionary containing lead background information
        
        Returns:
            Dict containing analysis results:
                - intent: "schedule_meeting", "reschedule", "cancel", "inquiry"
                - urgency: "high", "medium", "low"
                - preferred_duration: Estimated meeting duration in minutes
                - time_preferences: Extracted time preferences
                - meeting_type: Type of meeting (demo, consultation, etc.)
                - flexibility: How flexible the lead is with timing
                - next_action: Recommended next step
        
        Raises:
            ValueError: If required request_data fields are missing
            RuntimeError: If LLM analysis fails
        """
        if not self._validate_request_data(request_data):
            raise ValueError("request_data is missing required fields")
        
        if not lead_context or not isinstance(lead_context, dict):
            raise ValueError("lead_context must be a valid dictionary")
        
        try:
            # Build context string from lead information
            context = self._build_context_string(lead_context)
            
            # Build prompt for analysis
            prompt = self._build_request_prompt(request_data, context)
            
            # Create LLM chain
            input_variables = ["request_text", "sender_email", "lead_context", "preferred_times"]
            chain = self.agent_core.create_llm_chain(prompt, input_variables)
            
            # Run analysis
            response = chain.run(
                request_text=request_data.get('request_text', ''),
                sender_email=request_data.get('sender_email', ''),
                lead_context=context,
                preferred_times=request_data.get('preferred_times', 'No specific preferences mentioned')
            )
            
            # Parse response
            result = self._parse_request_analysis(response)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Meeting request analysis failed: {str(e)}")
    
    def book(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book a meeting with a lead at the specified time.
        
        Creates a meeting booking with the provided details and updates
        the calendar system with the new appointment.
        
        Args:
            meeting_data: Dictionary containing meeting details:
                         - lead_id: ID of the lead
                         - start_time: Meeting start time (datetime)
                         - duration: Meeting duration in minutes
                         - meeting_type: Type of meeting
                         - attendees: List of attendee email addresses
                         - notes: Additional meeting notes
        
        Returns:
            Dict containing booking results:
                - booking_id: Unique identifier for the booking
                - confirmation_message: Message to send to lead
                - calendar_link: Link to calendar event
                - status: "confirmed", "pending", "failed"
        
        Raises:
            ValueError: If meeting_data is invalid
            RuntimeError: If booking fails
        """
        if not self._validate_meeting_data(meeting_data):
            raise ValueError("meeting_data is missing required fields")
        
        try:
            # Generate booking ID
            booking_id = f"meeting_{meeting_data['lead_id']}_{int(datetime.now().timestamp())}"
            
            # Check availability
            if not self.check_availability(meeting_data['start_time'], meeting_data.get('duration', self.default_duration)):
                return {
                    'booking_id': None,
                    'confirmation_message': 'The requested time slot is not available. Please choose a different time.',
                    'calendar_link': None,
                    'status': 'failed'
                }
            
            # Create meeting record
            meeting_record = {
                'booking_id': booking_id,
                'lead_id': meeting_data['lead_id'],
                'start_time': meeting_data['start_time'].isoformat(),
                'duration': meeting_data.get('duration', self.default_duration),
                'meeting_type': meeting_data.get('meeting_type', 'consultation'),
                'attendees': meeting_data.get('attendees', []),
                'notes': meeting_data.get('notes', ''),
                'status': 'confirmed',
                'created_at': datetime.now().isoformat()
            }
            
            # Store meeting (in real implementation, this would save to database)
            # For now, we'll simulate successful storage
            
            # Generate confirmation message
            confirmation_message = self._generate_confirmation_message(meeting_record)
            
            # Generate calendar link (placeholder)
            calendar_link = f"https://calendar.example.com/meeting/{booking_id}"
            
            return {
                'booking_id': booking_id,
                'confirmation_message': confirmation_message,
                'calendar_link': calendar_link,
                'status': 'confirmed'
            }
            
        except Exception as e:
            raise RuntimeError(f"Meeting booking failed: {str(e)}")
    
    def check_availability(self, start_time: datetime, duration: int = 30) -> bool:
        """Check if a specified time slot is available for booking.
        
        Verifies that the requested time slot is within business hours
        and doesn't conflict with existing meetings.
        
        Args:
            start_time: Proposed meeting start time
            duration: Meeting duration in minutes
        
        Returns:
            bool: True if time slot is available, False otherwise
        
        Raises:
            ValueError: If start_time is invalid
        """
        if not isinstance(start_time, datetime):
            raise ValueError("start_time must be a datetime object")
        
        if duration <= 0:
            raise ValueError("duration must be positive")
        
        # Check if time is in the past
        if start_time < datetime.now():
            return False
        
        # Check if time is within business hours
        if not self._is_business_hours(start_time, duration):
            return False
        
        # Check for conflicts with existing meetings
        # In real implementation, this would query the calendar system
        # For now, we'll simulate availability check
        return self._check_calendar_conflicts(start_time, duration)
    
    def get_available_slots(self, start_date: datetime, end_date: datetime, duration: int = 30) -> List[datetime]:
        """Get available meeting slots within a specified date range.
        
        Returns a list of available time slots for meetings within the
        specified date range, considering business hours and existing bookings.
        
        Args:
            start_date: Start of date range to search
            end_date: End of date range to search
            duration: Required meeting duration in minutes
        
        Returns:
            List[datetime]: List of available start times
        
        Raises:
            ValueError: If date range is invalid
        """
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            raise ValueError("start_date and end_date must be datetime objects")
        
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")
        
        if duration <= 0:
            raise ValueError("duration must be positive")
        
        available_slots = []
        current_date = start_date.replace(hour=self.business_start_hour, minute=0, second=0, microsecond=0)
        
        while current_date < end_date:
            # Skip weekends
            if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                current_date += timedelta(days=1)
                current_date = current_date.replace(hour=self.business_start_hour, minute=0, second=0, microsecond=0)
                continue
            
            # Check each 30-minute slot during business hours
            while current_date.hour < self.business_end_hour:
                if self.check_availability(current_date, duration):
                    available_slots.append(current_date)
                
                current_date += timedelta(minutes=30)
            
            # Move to next day
            current_date += timedelta(days=1)
            current_date = current_date.replace(hour=self.business_start_hour, minute=0, second=0, microsecond=0)
        
        return available_slots
    
    def propose_meeting_times(self, lead_preferences: Dict[str, Any], num_options: int = 3) -> List[Dict[str, Any]]:
        """Propose optimal meeting times based on lead preferences.
        
        Analyzes lead preferences and availability to suggest the best
        meeting times that accommodate both parties' schedules.
        
        Args:
            lead_preferences: Dictionary containing lead's preferences:
                             - preferred_days: List of preferred days
                             - preferred_times: List of preferred time ranges
                             - timezone: Lead's timezone
                             - urgency: How soon they want to meet
            num_options: Number of time options to propose
        
        Returns:
            List[Dict]: List of proposed meeting times with details
        
        Raises:
            ValueError: If lead_preferences is invalid or num_options is not positive
        """
        if not isinstance(lead_preferences, dict):
            raise ValueError("lead_preferences must be a valid dictionary")
        
        if num_options <= 0:
            raise ValueError("num_options must be positive")
        
        # Determine search range based on urgency
        urgency = lead_preferences.get('urgency', 'medium')
        if urgency == 'high':
            search_days = 3
        elif urgency == 'medium':
            search_days = 7
        else:
            search_days = 14
        
        start_date = datetime.now() + timedelta(hours=1)  # Start from next hour
        end_date = start_date + timedelta(days=search_days)
        
        # Get available slots
        available_slots = self.get_available_slots(start_date, end_date)
        
        # Filter and rank slots based on preferences
        ranked_slots = self._rank_slots_by_preferences(available_slots, lead_preferences)
        
        # Return top options
        proposals = []
        for i, slot in enumerate(ranked_slots[:num_options]):
            proposals.append({
                'option_number': i + 1,
                'start_time': slot,
                'end_time': slot + timedelta(minutes=self.default_duration),
                'day_of_week': slot.strftime('%A'),
                'formatted_time': slot.strftime('%Y-%m-%d %H:%M'),
                'score': self._calculate_slot_score(slot, lead_preferences)
            })
        
        return proposals
    
    def generate_meeting_response(self, analysis_result: Dict[str, Any], proposed_times: List[Dict[str, Any]]) -> str:
        """Generate a response message for meeting requests.
        
        Creates a professional response message based on the analysis
        results and proposed meeting times.
        
        Args:
            analysis_result: Results from analyze_request()
            proposed_times: List of proposed meeting times
        
        Returns:
            str: Formatted response message
        
        Raises:
            ValueError: If required parameters are missing
        """
        if not analysis_result or not isinstance(analysis_result, dict):
            raise ValueError("analysis_result must be a valid dictionary")
        
        intent = analysis_result.get('intent', 'schedule_meeting')
        meeting_type = analysis_result.get('meeting_type', 'consultation')
        
        if intent == 'schedule_meeting':
            response = f"Thank you for your interest in scheduling a {meeting_type}. "
            
            if proposed_times:
                response += "I have the following time slots available:\n\n"
                for time_option in proposed_times:
                    response += f"Option {time_option['option_number']}: {time_option['formatted_time']} ({time_option['day_of_week']})\n"
                
                response += "\nPlease let me know which time works best for you, and I'll send you a calendar invitation."
            else:
                response += "Unfortunately, I don't have any available slots in your preferred timeframe. Could you provide some alternative times that work for you?"
        
        elif intent == 'reschedule':
            response = "I understand you need to reschedule our meeting. "
            if proposed_times:
                response += "Here are some alternative times:\n\n"
                for time_option in proposed_times:
                    response += f"Option {time_option['option_number']}: {time_option['formatted_time']} ({time_option['day_of_week']})\n"
            else:
                response += "Please let me know what times work better for you."
        
        elif intent == 'cancel':
            response = "I understand you need to cancel our meeting. No problem at all. If you'd like to reschedule for a future date, please let me know."
        
        else:
            response = "Thank you for your message. I'd be happy to help you schedule a meeting. Please let me know your preferred times and I'll check my availability."
        
        return response
    
    def _parse_request_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM meeting request analysis response.
        
        Internal method to extract analysis fields from LLM response text
        and convert them to appropriate data types.
        
        Args:
            llm_response: Raw text response from LLM
        
        Returns:
            Dict containing parsed analysis data
        """
        expected_fields = {
            'intent': 'schedule_meeting',
            'urgency': 'medium',
            'preferred_duration': 30,
            'time_preferences': 'No specific preferences',
            'meeting_type': 'consultation',
            'flexibility': 'medium',
            'next_action': 'Propose meeting times'
        }
        
        return self.agent_core.parse_structured_response(llm_response, expected_fields)
    
    def _build_request_prompt(self, request_data: Dict[str, Any], context: str = "") -> str:
        """Build prompt template for meeting request analysis.
        
        Internal method to construct the prompt template used for LLM-based
        meeting request analysis.
        
        Args:
            request_data: Meeting request information
            context: Additional context about the lead
        
        Returns:
            str: Formatted prompt template for LLM analysis
        """
        template = """
You are an expert meeting scheduler. Analyze the following meeting request to understand the lead's intent and preferences.

Meeting Request:
- Request Text: {request_text}
- Sender: {sender_email}
- Preferred Times: {preferred_times}

Lead Context: {lead_context}

""" + context + """

Please provide your analysis in the following format:
Intent: [schedule_meeting/reschedule/cancel/inquiry]
Urgency: [high/medium/low]
Preferred Duration: [duration in minutes]
Time Preferences: [extracted time preferences]
Meeting Type: [demo/consultation/discovery/follow-up]
Flexibility: [high/medium/low]
Next Action: [specific recommended next step]

Consider these factors:
- Specific time mentions or constraints
- Urgency indicators in the language
- Type of meeting being requested
- Lead's flexibility with scheduling
- Any special requirements mentioned
"""
        
        return template
    
    def _validate_request_data(self, request_data: Dict[str, Any]) -> bool:
        """Validate that request data contains required fields.
        
        Args:
            request_data: Request data dictionary to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not request_data or not isinstance(request_data, dict):
            return False
        
        required_fields = ['request_text', 'sender_email']
        
        for field in required_fields:
            if field not in request_data or not request_data[field]:
                return False
        
        return True
    
    def _validate_meeting_data(self, meeting_data: Dict[str, Any]) -> bool:
        """Validate that meeting data contains required fields.
        
        Args:
            meeting_data: Meeting data dictionary to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not meeting_data or not isinstance(meeting_data, dict):
            return False
        
        required_fields = ['lead_id', 'start_time']
        
        for field in required_fields:
            if field not in meeting_data:
                return False
        
        if not isinstance(meeting_data['start_time'], datetime):
            return False
        
        return True
    
    def _is_business_hours(self, start_time: datetime, duration: int) -> bool:
        """Check if a time slot falls within business hours.
        
        Args:
            start_time: The start time to check
            duration: Duration of the meeting in minutes
            
        Returns:
            bool: True if the entire meeting is within business hours
        """
        # Check if it's a weekday (Monday = 0, Sunday = 6)
        if start_time.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Check if start time is within business hours
        if start_time.hour < self.business_start_hour or start_time.hour >= self.business_end_hour:
            return False
        
        # Check if meeting would end within business hours
        end_time = start_time + timedelta(minutes=duration)
        if end_time.hour > self.business_end_hour or (end_time.hour == self.business_end_hour and end_time.minute > 0):
            return False
        
        return True
    
    def _check_calendar_conflicts(self, start_time: datetime, duration: int) -> bool:
        """Check for conflicts with existing meetings.
        
        In a real implementation, this would query the calendar system.
        For now, we'll simulate some basic conflict checking.
        
        Args:
            start_time: Proposed meeting start time
            duration: Meeting duration in minutes
        
        Returns:
            bool: True if no conflicts, False if conflicts exist
        """
        # Simulate some existing meetings
        # In real implementation, this would query the database
        
        # For demo purposes, let's say we're busy on the hour every day from 2-3 PM
        if start_time.hour == 14:  # 2 PM
            return False
        
        return True
    
    def _rank_slots_by_preferences(self, available_slots: List[datetime], preferences: Dict[str, Any]) -> List[datetime]:
        """Rank available slots based on lead preferences.
        
        Args:
            available_slots: List of available time slots
            preferences: Lead's preferences
        
        Returns:
            List[datetime]: Slots ranked by preference score
        """
        scored_slots = []
        
        for slot in available_slots:
            score = self._calculate_slot_score(slot, preferences)
            scored_slots.append((slot, score))
        
        # Sort by score (highest first)
        scored_slots.sort(key=lambda x: x[1], reverse=True)
        
        return [slot for slot, score in scored_slots]
    
    def _calculate_slot_score(self, slot: datetime, preferences: Dict[str, Any]) -> int:
        """Calculate preference score for a time slot.
        
        Args:
            slot: Time slot to score
            preferences: Lead's preferences
        
        Returns:
            int: Preference score (higher is better)
        """
        score = 0
        
        # Preferred days bonus
        preferred_days = preferences.get('preferred_days', [])
        if preferred_days and slot.strftime('%A').lower() in [day.lower() for day in preferred_days]:
            score += 20
        
        # Preferred times bonus
        preferred_times = preferences.get('preferred_times', [])
        if preferred_times:
            for time_range in preferred_times:
                if self._time_in_range(slot, time_range):
                    score += 15
        
        # Morning vs afternoon preference
        if slot.hour < 12:
            score += 10  # Slight preference for morning meetings
        
        # Avoid very early or very late slots
        if slot.hour < 9 or slot.hour > 16:
            score -= 10
        
        return score
    
    def _time_in_range(self, slot: datetime, time_range: str) -> bool:
        """Check if slot falls within a time range.
        
        Args:
            slot: Time slot to check
            time_range: Time range string (e.g., "9:00-12:00")
        
        Returns:
            bool: True if slot is in range
        """
        try:
            if '-' in time_range:
                start_str, end_str = time_range.split('-')
                start_hour = int(start_str.split(':')[0])
                end_hour = int(end_str.split(':')[0])
                
                return start_hour <= slot.hour < end_hour
        except (ValueError, IndexError):
            pass
        
        return False
    
    def _generate_confirmation_message(self, meeting_record: Dict[str, Any]) -> str:
        """Generate confirmation message for booked meeting.
        
        Args:
            meeting_record: Meeting record with booking details
        
        Returns:
            str: Confirmation message
        """
        start_time = datetime.fromisoformat(meeting_record['start_time'])
        meeting_type = meeting_record.get('meeting_type', 'meeting')
        duration = meeting_record.get('duration', 30)
        
        message = f"Great! I've confirmed your {meeting_type} for {start_time.strftime('%A, %B %d at %I:%M %p')}. "
        message += f"The meeting is scheduled for {duration} minutes. "
        message += "You'll receive a calendar invitation shortly with all the details. "
        message += "Looking forward to speaking with you!"
        
        return message
    
    def _build_context_string(self, lead_context: Dict[str, Any]) -> str:
        """Build context string from lead information.
        
        Args:
            lead_context: Lead context dictionary
        
        Returns:
            str: Formatted context string
        """
        context_parts = []
        
        if lead_context.get('name'):
            context_parts.append(f"Lead Name: {lead_context['name']}")
        
        if lead_context.get('company'):
            context_parts.append(f"Company: {lead_context['company']}")
        
        if lead_context.get('previous_meetings'):
            context_parts.append(f"Previous Meetings: {lead_context['previous_meetings']}")
        
        return "\n".join(context_parts) if context_parts else "No additional context available"
