"""Tests for ReplyAnalyzer agent."""

import pytest
from unittest.mock import Mock, MagicMock
from agents.reply_analyzer import ReplyAnalyzer


class TestReplyAnalyzer:
    """Test suite for ReplyAnalyzer agent."""
    
    @pytest.fixture
    def mock_agent_core(self):
        """Mock AgentCore for testing."""
        mock_core = Mock()
        mock_core.create_llm_chain.return_value = Mock()
        mock_core.parse_structured_response.return_value = {
            'disposition': 'engaged',
            'confidence': 85,
            'sentiment': 'positive',
            'urgency': 'high',
            'reasoning': 'Lead shows strong interest',
            'next_action': 'Schedule meeting',
            'follow_up_timing': 'immediate',
            'intent': 'meeting_request'
        }
        return mock_core
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock MemoryManager for testing."""
        return Mock()
    
    @pytest.fixture
    def sample_reply_data(self):
        """Sample reply data for testing."""
        return {
            'reply_text': 'Yes, I am very interested in scheduling a demo. When can we meet?',
            'reply_subject': 'Re: Product Demo Request',
            'sender_email': 'john.doe@example.com',
            'timestamp': '2024-01-15T10:30:00Z',
            'lead_id': 'lead_123'
        }
    
    @pytest.fixture
    def sample_lead_context(self):
        """Sample lead context for testing."""
        return {
            'name': 'John Doe',
            'company': 'Example Corp',
            'previous_interest': 'Product demo',
            'interaction_history': 'Initial outreach, positive response'
        }
    
    def test_init_success(self, mock_agent_core, mock_memory_manager):
        """Test successful initialization."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        assert analyzer.agent_core == mock_agent_core
        assert analyzer.memory_manager == mock_memory_manager
    
    def test_init_none_agent_core(self, mock_memory_manager):
        """Test initialization with None agent_core."""
        with pytest.raises(ValueError, match="agent_core cannot be None"):
            ReplyAnalyzer(None, mock_memory_manager)
    
    def test_init_none_memory_manager(self, mock_agent_core):
        """Test initialization with None memory_manager."""
        with pytest.raises(ValueError, match="memory_manager cannot be None"):
            ReplyAnalyzer(mock_agent_core, None)
    
    def test_analyze_success(self, mock_agent_core, mock_memory_manager, sample_reply_data, sample_lead_context):
        """Test successful reply analysis."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        # Mock the chain
        mock_chain = Mock()
        mock_chain.run.return_value = "Disposition: engaged\nConfidence: 85\nSentiment: positive"
        mock_agent_core.create_llm_chain.return_value = mock_chain
        
        result = analyzer.analyze(sample_reply_data, sample_lead_context)
        
        assert result is not None
        assert result['disposition'] == 'engaged'
        assert result['confidence'] == 85
        assert result['sentiment'] == 'positive'
        
        # Verify chain was called with correct parameters
        mock_chain.run.assert_called_once()
        call_args = mock_chain.run.call_args.kwargs
        assert call_args['reply_text'] == sample_reply_data['reply_text']
        assert call_args['sender_email'] == sample_reply_data['sender_email']
    
    def test_analyze_invalid_reply_data(self, mock_agent_core, mock_memory_manager, sample_lead_context):
        """Test analysis with invalid reply data."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        invalid_data = {'reply_text': ''}  # Missing sender_email
        
        with pytest.raises(ValueError, match="reply_data is missing required fields"):
            analyzer.analyze(invalid_data, sample_lead_context)
    
    def test_analyze_invalid_lead_context(self, mock_agent_core, mock_memory_manager, sample_reply_data):
        """Test analysis with invalid lead context."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        with pytest.raises(ValueError, match="lead_context must be a valid dictionary"):
            analyzer.analyze(sample_reply_data, None)
    
    def test_analyze_llm_failure(self, mock_agent_core, mock_memory_manager, sample_reply_data, sample_lead_context):
        """Test analysis when LLM fails."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        # Mock chain to raise exception
        mock_chain = Mock()
        mock_chain.run.side_effect = Exception("LLM error")
        mock_agent_core.create_llm_chain.return_value = mock_chain
        
        with pytest.raises(RuntimeError, match="Reply analysis failed"):
            analyzer.analyze(sample_reply_data, sample_lead_context)
    
    def test_calculate_score_success(self, mock_agent_core, mock_memory_manager):
        """Test successful score calculation."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        analysis_result = {
            'disposition': 'engaged',
            'sentiment': 'positive',
            'urgency': 'high',
            'confidence': 90
        }
        
        score = analyzer.calculate_score(analysis_result)
        
        # engaged (40) + positive (25) + high (20) + confidence bonus (13) = 98
        assert score == 98
    
    def test_calculate_score_disinterested(self, mock_agent_core, mock_memory_manager):
        """Test score calculation for disinterested lead."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        analysis_result = {
            'disposition': 'disinterested',
            'sentiment': 'negative',
            'urgency': 'low',
            'confidence': 30
        }
        
        score = analyzer.calculate_score(analysis_result)
        
        # disinterested (0) + negative (0) + low (5) + confidence bonus (4) = 9
        assert score == 9
    
    def test_calculate_score_missing_fields(self, mock_agent_core, mock_memory_manager):
        """Test score calculation with missing fields."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        analysis_result = {'disposition': 'engaged'}  # Missing required fields
        
        with pytest.raises(ValueError, match="Missing required field"):
            analyzer.calculate_score(analysis_result)
    
    def test_determine_priority_high(self, mock_agent_core, mock_memory_manager):
        """Test priority determination for high priority cases."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        # Engaged + high urgency = high priority
        result1 = {
            'disposition': 'engaged',
            'urgency': 'high',
            'sentiment': 'positive'
        }
        assert analyzer.determine_priority(result1) == "high"
        
        # Maybe + high urgency + positive sentiment = high priority
        result2 = {
            'disposition': 'maybe',
            'urgency': 'high',
            'sentiment': 'positive'
        }
        assert analyzer.determine_priority(result2) == "high"
    
    def test_determine_priority_low(self, mock_agent_core, mock_memory_manager):
        """Test priority determination for low priority cases."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        # Disinterested = low priority
        result1 = {
            'disposition': 'disinterested',
            'urgency': 'medium',
            'sentiment': 'neutral'
        }
        assert analyzer.determine_priority(result1) == "low"
        
        # Negative sentiment + low urgency = low priority
        result2 = {
            'disposition': 'maybe',
            'urgency': 'low',
            'sentiment': 'negative'
        }
        assert analyzer.determine_priority(result2) == "low"
    
    def test_determine_priority_medium(self, mock_agent_core, mock_memory_manager):
        """Test priority determination for medium priority cases."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        result = {
            'disposition': 'maybe',
            'urgency': 'medium',
            'sentiment': 'neutral'
        }
        assert analyzer.determine_priority(result) == "medium"
    
    def test_determine_priority_invalid_input(self, mock_agent_core, mock_memory_manager):
        """Test priority determination with invalid input."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        with pytest.raises(ValueError, match="analysis_result must be a valid dictionary"):
            analyzer.determine_priority(None)
    
    def test_classify_intent_meeting_request(self, mock_agent_core, mock_memory_manager):
        """Test intent classification for meeting requests."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        texts = [
            "Can we schedule a meeting?",
            "I'd like to book a demo",
            "When are you available for a call?",
            "Let's set up an appointment"
        ]
        
        for text in texts:
            intent = analyzer.classify_intent(text, {})
            assert intent == "meeting_request"
    
    def test_classify_intent_info_request(self, mock_agent_core, mock_memory_manager):
        """Test intent classification for information requests."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        texts = [
            "Can you tell me more information about pricing?",
            "What are the key features?",
            "How does this work?",
            "I need more details"
        ]
        
        for text in texts:
            intent = analyzer.classify_intent(text, {})
            assert intent == "info_request"
    
    def test_classify_intent_not_interested(self, mock_agent_core, mock_memory_manager):
        """Test intent classification for not interested responses."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        texts = [
            "Not interested, thanks",
            "Please remove me from your list",
            "No thank you",
            "Not right now"
        ]
        
        for text in texts:
            intent = analyzer.classify_intent(text, {})
            assert intent == "not_interested"
    
    def test_classify_intent_objection(self, mock_agent_core, mock_memory_manager):
        """Test intent classification for objections."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        texts = [
            "This is too expensive for us",
            "We already have a solution",
            "I have some concerns about this",
            "Not sure if this fits our budget"
        ]
        
        for text in texts:
            intent = analyzer.classify_intent(text, {})
            assert intent == "objection"
    
    def test_classify_intent_interested(self, mock_agent_core, mock_memory_manager):
        """Test intent classification for interested responses."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        texts = [
            "Yes, I'm interested",
            "This sounds good",
            "Tell me more",
            "Definitely want to learn more"
        ]
        
        for text in texts:
            intent = analyzer.classify_intent(text, {})
            assert intent == "interested"
    
    def test_classify_intent_neutral(self, mock_agent_core, mock_memory_manager):
        """Test intent classification for neutral responses."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        text = "Thanks for reaching out"
        intent = analyzer.classify_intent(text, {})
        assert intent == "neutral"
    
    def test_classify_intent_empty_text(self, mock_agent_core, mock_memory_manager):
        """Test intent classification with empty text."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        with pytest.raises(ValueError, match="reply_text cannot be empty"):
            analyzer.classify_intent("", {})
    
    def test_extract_engagement_signals(self, mock_agent_core, mock_memory_manager):
        """Test extraction of engagement signals."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        text = """
        I'm very interested in this solution. How much does it cost? 
        We need to implement something ASAP as our CEO wants this done this quarter.
        Can you tell me more about the pricing? When can we schedule a demo?
        """
        
        signals = analyzer.extract_engagement_signals(text)
        
        assert signals['questions_asked'] == 3  # Three question marks
        assert len(signals['urgency_indicators']) > 0  # Should find "ASAP"
        assert signals['budget_mentions'] is True  # Should find "cost" and "pricing"
        assert len(signals['timeline_mentions']) > 0  # Should find "quarter"
        assert signals['decision_authority'] is True  # Should find "CEO"
    
    def test_extract_engagement_signals_minimal(self, mock_agent_core, mock_memory_manager):
        """Test extraction with minimal engagement signals."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        text = "Thanks for your email."
        
        signals = analyzer.extract_engagement_signals(text)
        
        assert signals['questions_asked'] == 0
        assert len(signals['urgency_indicators']) == 0
        assert signals['budget_mentions'] is False
        assert len(signals['timeline_mentions']) == 0
        assert signals['decision_authority'] is False
    
    def test_extract_engagement_signals_empty_text(self, mock_agent_core, mock_memory_manager):
        """Test extraction with empty text."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        with pytest.raises(ValueError, match="reply_text cannot be empty"):
            analyzer.extract_engagement_signals("")
    
    def test_validate_reply_data_valid(self, mock_agent_core, mock_memory_manager):
        """Test validation with valid reply data."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        valid_data = {
            'reply_text': 'Some reply text',
            'sender_email': 'test@example.com'
        }
        
        assert analyzer._validate_reply_data(valid_data) is True
    
    def test_validate_reply_data_invalid(self, mock_agent_core, mock_memory_manager):
        """Test validation with invalid reply data."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        # Missing required fields
        invalid_data1 = {'reply_text': 'Some text'}  # Missing sender_email
        assert analyzer._validate_reply_data(invalid_data1) is False
        
        # Empty required fields
        invalid_data2 = {'reply_text': '', 'sender_email': 'test@example.com'}
        assert analyzer._validate_reply_data(invalid_data2) is False
        
        # None input
        assert analyzer._validate_reply_data(None) is False
        
        # Non-dict input
        assert analyzer._validate_reply_data("not a dict") is False
    
    def test_calculate_engagement_score(self, mock_agent_core, mock_memory_manager):
        """Test engagement score calculation."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        # High engagement signals
        high_signals = {
            'questions_asked': 3,
            'urgency_indicators': ['asap', 'urgent'],
            'budget_mentions': True,
            'timeline_mentions': ['this quarter'],
            'decision_authority': True
        }
        
        score = analyzer._calculate_engagement_score(high_signals)
        # 15 (questions) + 16 (urgency) + 20 (budget) + 15 (timeline) + 20 (authority) = 86
        assert score == 86
        
        # Low engagement signals
        low_signals = {
            'questions_asked': 0,
            'urgency_indicators': [],
            'budget_mentions': False,
            'timeline_mentions': [],
            'decision_authority': False
        }
        
        score = analyzer._calculate_engagement_score(low_signals)
        assert score == 0
    
    def test_build_context_string(self, mock_agent_core, mock_memory_manager):
        """Test context string building."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        # Full context
        full_context = {
            'name': 'John Doe',
            'company': 'Example Corp',
            'previous_interest': 'Product demo'
        }
        
        context_str = analyzer._build_context_string(full_context)
        assert 'Lead Name: John Doe' in context_str
        assert 'Company: Example Corp' in context_str
        assert 'Previous Interest: Product demo' in context_str
        
        # Empty context
        empty_context = {}
        context_str = analyzer._build_context_string(empty_context)
        assert context_str == "No additional context available"
        
        # Partial context
        partial_context = {'name': 'John Doe'}
        context_str = analyzer._build_context_string(partial_context)
        assert 'Lead Name: John Doe' in context_str
        assert 'Company:' not in context_str
    
    def test_build_reply_prompt(self, mock_agent_core, mock_memory_manager, sample_reply_data):
        """Test reply prompt building."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        prompt = analyzer._build_reply_prompt(sample_reply_data, "Additional context")
        
        assert '{reply_text}' in prompt
        assert '{reply_subject}' in prompt
        assert '{sender_email}' in prompt
        assert '{lead_context}' in prompt
        assert '{interaction_history}' in prompt
        assert 'Additional context' in prompt
        assert 'Disposition:' in prompt
        assert 'Confidence:' in prompt
    
    def test_build_reply_prompt_invalid_data(self, mock_agent_core, mock_memory_manager):
        """Test reply prompt building with invalid data."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        invalid_data = {'reply_text': ''}  # Missing sender_email
        
        with pytest.raises(ValueError, match="reply_data is missing required fields"):
            analyzer._build_reply_prompt(invalid_data)
    
    def test_parse_analysis(self, mock_agent_core, mock_memory_manager):
        """Test analysis parsing."""
        analyzer = ReplyAnalyzer(mock_agent_core, mock_memory_manager)
        
        # Mock the parse_structured_response method
        expected_result = {
            'disposition': 'engaged',
            'confidence': 85,
            'sentiment': 'positive',
            'urgency': 'high',
            'reasoning': 'Strong interest shown',
            'next_action': 'Schedule meeting',
            'follow_up_timing': 'immediate',
            'intent': 'meeting_request'
        }
        mock_agent_core.parse_structured_response.return_value = expected_result
        
        result = analyzer._parse_analysis("Some LLM response")
        
        assert result == expected_result
        mock_agent_core.parse_structured_response.assert_called_once() 