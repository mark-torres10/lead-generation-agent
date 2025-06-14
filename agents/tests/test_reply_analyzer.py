"""Unit tests for ReplyAnalyzer class."""

import pytest
from unittest.mock import Mock, patch
from agents.reply_analyzer import ReplyAnalyzer
from agents.agent_core import AgentCore


class TestReplyAnalyzer:
    """Test cases for ReplyAnalyzer functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_agent_core = Mock(spec=AgentCore)
        self.mock_memory_manager = Mock()
        self.reply_analyzer = ReplyAnalyzer(self.mock_agent_core, self.mock_memory_manager)
        
        self.sample_reply_data = {
            "reply_content": "Thanks for reaching out! I'm very interested in learning more about your automation platform. Could we schedule a demo call next week?",
            "original_email": "Hi John, I wanted to follow up on your interest in our automation tools...",
            "lead_name": "John Smith",
            "lead_email": "john@techcorp.com",
            "company": "TechCorp Inc",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    def test_init_with_valid_dependencies(self):
        """Test ReplyAnalyzer initialization with valid dependencies."""
        analyzer = ReplyAnalyzer(self.mock_agent_core, self.mock_memory_manager)
        assert analyzer is not None
    
    def test_init_with_none_dependencies(self):
        """Test ReplyAnalyzer initialization with None dependencies."""
        with pytest.raises(ValueError):
            ReplyAnalyzer(None, self.mock_memory_manager)
        
        with pytest.raises(ValueError):
            ReplyAnalyzer(self.mock_agent_core, None)
    
    def test_analyze_with_valid_reply_data(self):
        """Test reply analysis with valid reply data."""
        lead_context = {"name": "John Smith", "company": "TechCorp Inc", "previous_interest": "Interested in automation", "interaction_history": "No previous interactions"}
        reply_data = {"reply_text": "Thanks for reaching out!", "sender_email": "john@techcorp.com"}
        self.reply_analyzer.agent_core.parse_structured_response = lambda resp, fields: {
            "disposition": "engaged",
            "confidence": 85,
            "sentiment": "positive",
            "urgency": "high",
            "reasoning": "Strong interest signals and meeting request",
            "next_action": "Schedule demo call",
            "follow_up_timing": "within_24_hours",
            "intent": "meeting_request"
        }
        result = self.reply_analyzer.analyze(reply_data, lead_context)
        assert result is not None
        assert "disposition" in result
        assert "confidence" in result
        assert "sentiment" in result
        assert "urgency" in result
        assert "reasoning" in result
        assert "next_action" in result
        assert "follow_up_timing" in result
        assert "intent" in result
    
    def test_analyze_with_missing_required_fields(self):
        """Test analysis with missing required fields."""
        incomplete_data = {"reply_content": "Thanks for reaching out!"}  # Missing required fields
        lead_context = {"name": "John Smith", "company": "TechCorp Inc", "previous_interest": "Interested in automation", "interaction_history": "No previous interactions"}
        with pytest.raises(ValueError):
            self.reply_analyzer.analyze(incomplete_data, lead_context)
    
    def test_analyze_with_empty_reply_data(self):
        """Test analysis with empty reply data."""
        lead_context = {"name": "John Smith", "company": "TechCorp Inc", "previous_interest": "Interested in automation", "interaction_history": "No previous interactions"}
        with pytest.raises(ValueError):
            self.reply_analyzer.analyze({}, lead_context)
    
    def test_analyze_with_none_reply_data(self):
        """Test analysis with None reply data."""
        lead_context = {"name": "John Smith", "company": "TechCorp Inc", "previous_interest": "Interested in automation", "interaction_history": "No previous interactions"}
        with pytest.raises(ValueError):
            self.reply_analyzer.analyze(None, lead_context)
    
    def test_calculate_score_with_valid_analysis(self):
        """Test score calculation with valid analysis results."""
        analysis_result = {
            "disposition": "interested",
            "sentiment": "positive",
            "urgency": "high",
            "intent": "meeting_request",
            "confidence": 85
        }
        new_score = self.reply_analyzer.calculate_score(analysis_result)
        assert isinstance(new_score, int)
        assert 0 <= new_score <= 100
    
    def test_calculate_score_with_negative_sentiment(self):
        """Test score calculation with negative sentiment."""
        analysis_result = {
            "disposition": "not_interested",
            "sentiment": "negative",
            "urgency": "low",
            "intent": "rejection",
            "confidence": 90
        }
        new_score = self.reply_analyzer.calculate_score(analysis_result)
        assert isinstance(new_score, int)
        assert 0 <= new_score <= 100
    
    def test_calculate_score_with_invalid_current_score(self):
        """Test score calculation with invalid current score."""
        analysis_result = {
            "disposition": "interested",
            "sentiment": "positive",
            "urgency": "medium",
            "intent": "information_request",
            "confidence": 80
        }
        with pytest.raises(ValueError):
            self.reply_analyzer.calculate_score({})
    
    def test_determine_priority_with_high_engagement(self):
        """Test priority determination with high engagement analysis."""
        analysis_result = {
            "disposition": "very_interested",
            "urgency": "high",
            "sentiment": "positive",
            "intent": "meeting_request",
            "confidence": 95
        }
        priority = self.reply_analyzer.determine_priority(analysis_result)
        assert priority == "medium"
    
    def test_determine_priority_with_low_engagement(self):
        """Test priority determination with low engagement analysis."""
        analysis_result = {
            "disposition": "not_interested",
            "urgency": "low",
            "sentiment": "neutral",
            "intent": "polite_decline",
            "confidence": 85
        }
        priority = self.reply_analyzer.determine_priority(analysis_result)
        assert priority == "medium"
    
    def test_determine_priority_with_missing_fields(self):
        """Test priority determination with missing analysis fields."""
        incomplete_analysis = {"disposition": "interested"}  # Missing required fields
        priority = self.reply_analyzer.determine_priority(incomplete_analysis)
        assert priority in ["medium", "low", "high"]
    
    def test_classify_intent_meeting_request(self):
        """Test intent classification for meeting request."""
        reply_content = "Could we schedule a demo call next week? I'm very interested in seeing how this works."
        context = {"name": "John Smith", "company": "TechCorp Inc"}
        intent = self.reply_analyzer.classify_intent(reply_content, context)
        assert intent == "meeting_request"
    
    def test_classify_intent_information_request(self):
        """Test intent classification for information request."""
        reply_content = "Thanks for reaching out. Could you send me more details about pricing and features?"
        context = {"name": "John Smith", "company": "TechCorp Inc"}
        intent = self.reply_analyzer.classify_intent(reply_content, context)
        assert intent == "info_request"
    
    def test_classify_intent_rejection(self):
        """Test intent classification for rejection."""
        reply_content = "Thanks but we're not interested at this time. Please remove me from your list."
        context = {"name": "John Smith", "company": "TechCorp Inc"}
        intent = self.reply_analyzer.classify_intent(reply_content, context)
        assert intent == "not_interested"
    
    def test_classify_intent_with_empty_content(self):
        """Test intent classification with empty content."""
        context = {"name": "John Smith", "company": "TechCorp Inc"}
        with pytest.raises(ValueError):
            self.reply_analyzer.classify_intent("", context)
    
    def test_extract_engagement_signals_positive(self):
        """Test extraction of positive engagement signals."""
        reply_content = "This looks very promising! I'm excited to learn more. When can we schedule a demo?"
        signals = self.reply_analyzer.extract_engagement_signals(reply_content)
        assert isinstance(signals, dict)
        assert "questions_asked" in signals
        assert "urgency_indicators" in signals
        assert "budget_mentions" in signals
        assert "timeline_mentions" in signals
        assert "decision_authority" in signals
    
    def test_extract_engagement_signals_negative(self):
        """Test extraction of negative engagement signals."""
        reply_content = "Not interested. Please don't contact me again."
        signals = self.reply_analyzer.extract_engagement_signals(reply_content)
        assert isinstance(signals, dict)
        assert "questions_asked" in signals
        assert "urgency_indicators" in signals
        assert "budget_mentions" in signals
        assert "timeline_mentions" in signals
        assert "decision_authority" in signals
    
    def test_extract_engagement_signals_with_empty_content(self):
        """Test engagement signal extraction with empty content."""
        with pytest.raises(ValueError):
            self.reply_analyzer.extract_engagement_signals("")
    
    def test_parse_analysis_with_valid_response(self):
        """Test parsing valid LLM analysis response."""
        llm_response = """
        DISPOSITION: interested
        CONFIDENCE: 85
        SENTIMENT: positive
        URGENCY: high
        REASONING: Strong interest signals and meeting request
        NEXT_ACTION: Schedule demo call
        FOLLOW_UP_TIMING: within_24_hours
        INTENT: meeting_request
        """
        self.reply_analyzer.agent_core.parse_structured_response = lambda resp, fields: {
            "disposition": "interested",
            "confidence": 85,
            "sentiment": "positive",
            "urgency": "high",
            "reasoning": "Strong interest signals and meeting request",
            "next_action": "Schedule demo call",
            "follow_up_timing": "within_24_hours",
            "intent": "meeting_request"
        }
        result = self.reply_analyzer._parse_analysis(llm_response)
        assert result["disposition"] == "interested"
        assert result["confidence"] == 85
        assert result["sentiment"] == "positive"
        assert result["urgency"] == "high"
        assert "Strong interest" in result["reasoning"]
        assert result["next_action"] == "Schedule demo call"
        assert result["follow_up_timing"] == "within_24_hours"
        assert result["intent"] == "meeting_request"
    
    def test_parse_analysis_with_invalid_response(self):
        """Test parsing invalid LLM response."""
        invalid_response = "This is not a structured response"
        self.reply_analyzer.agent_core.parse_structured_response = lambda resp, fields: (_ for _ in ()).throw(ValueError("No structured data found in response"))
        with pytest.raises(ValueError):
            self.reply_analyzer._parse_analysis(invalid_response)
    
    def test_build_reply_prompt_with_valid_data(self):
        """Test building reply analysis prompt with valid data."""
        context = "Previous qualification: high priority lead"
        reply_data = {"reply_text": "Thanks for reaching out!", "sender_email": "john@techcorp.com"}
        prompt = self.reply_analyzer._build_reply_prompt(reply_data, context)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_build_reply_prompt_with_missing_fields(self):
        """Test building prompt with missing required fields."""
        incomplete_data = {"reply_content": "Thanks!"}  # Missing required fields
        
        with pytest.raises(ValueError):
            self.reply_analyzer._build_reply_prompt(incomplete_data)
    
    def test_validate_reply_data_with_valid_data(self):
        """Test reply data validation with valid data."""
        valid_data = {"reply_text": "Thanks for reaching out!", "sender_email": "john@techcorp.com"}
        is_valid = self.reply_analyzer._validate_reply_data(valid_data)
        assert is_valid is True
    
    def test_validate_reply_data_with_missing_fields(self):
        """Test reply data validation with missing fields."""
        incomplete_data = {"reply_content": "Thanks!"}  # Missing required fields
        
        is_valid = self.reply_analyzer._validate_reply_data(incomplete_data)
        assert is_valid is False
    
    def test_validate_reply_data_with_empty_data(self):
        """Test reply data validation with empty data."""
        is_valid = self.reply_analyzer._validate_reply_data({})
        assert is_valid is False
    
    def test_validate_reply_data_with_none_data(self):
        """Test reply data validation with None data."""
        is_valid = self.reply_analyzer._validate_reply_data(None)
        assert is_valid is False
    
    def test_calculate_engagement_score_high_engagement(self):
        """Test engagement score calculation with high engagement signals."""
        signals = {
            "questions_asked": 3,
            "urgency_indicators": ["asap", "urgent", "soon"],
            "budget_mentions": True,
            "timeline_mentions": ["this quarter"],
            "decision_authority": True
        }
        score = self.reply_analyzer._calculate_engagement_score(signals)
        assert isinstance(score, int)
        assert 70 <= score <= 100  # High engagement should yield high score
    
    def test_calculate_engagement_score_low_engagement(self):
        """Test engagement score calculation with low engagement signals."""
        signals = {
            "positive_keywords": [],
            "urgency_indicators": [],
            "meeting_requests": [],
            "question_count": 0,
            "negative_keywords": ["not interested", "remove"],
            "rejection_indicators": ["decline", "pass"]
        }
        
        score = self.reply_analyzer._calculate_engagement_score(signals)
        
        assert isinstance(score, int)
        assert 0 <= score <= 30  # Low engagement should yield low score
    
    def test_calculate_engagement_score_with_invalid_signals(self):
        """Test engagement score calculation with invalid signals."""
        with pytest.raises(Exception):
            self.reply_analyzer._calculate_engagement_score(None) 