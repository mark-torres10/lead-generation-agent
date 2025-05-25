"""Tests for EmailQualifier agent."""

import pytest
from unittest.mock import Mock, MagicMock
from agents.email_qualifier import EmailQualifier
import pydantic


class TestEmailQualifier:
    """Test suite for EmailQualifier class."""
    
    @pytest.fixture
    def mock_agent_core(self):
        """Create mock AgentCore for testing."""
        mock_core = Mock()
        mock_core.create_llm_chain.return_value = Mock()
        mock_core.parse_structured_response.return_value = {
            'priority': 'high',
            'lead_score': 85,
            'reasoning': 'Strong enterprise lead with urgent need',
            'next_action': 'Schedule demo immediately',
            'disposition': 'hot',
            'confidence': 90
        }
        return mock_core
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Create mock memory manager for testing."""
        mock_memory = Mock()
        mock_memory.get_qualification.return_value = None
        return mock_memory
    
    @pytest.fixture
    def email_qualifier(self, mock_agent_core, mock_memory_manager):
        """Create EmailQualifier instance for testing."""
        return EmailQualifier(mock_agent_core, mock_memory_manager)
    
    @pytest.fixture
    def sample_lead_data(self):
        """Sample lead data for testing."""
        return {
            'name': 'John Smith',
            'company': 'TechCorp Inc',
            'email': 'john.smith@techcorp.com',
            'interest': 'Looking for enterprise AI solution for 500+ employees',
            'email_subject': 'Urgent: AI Implementation Needed',
            'email_body': 'We need to implement AI solution ASAP. Budget approved.'
        }
    
    def test_init_success(self, mock_agent_core, mock_memory_manager):
        """Test successful initialization."""
        qualifier = EmailQualifier(mock_agent_core, mock_memory_manager)
        assert qualifier.agent_core == mock_agent_core
        assert qualifier.memory_manager == mock_memory_manager
    
    def test_init_none_agent_core(self, mock_memory_manager):
        """Test initialization with None agent_core raises ValueError."""
        with pytest.raises(ValueError, match="agent_core cannot be None"):
            EmailQualifier(None, mock_memory_manager)
    
    def test_init_none_memory_manager(self, mock_agent_core):
        """Test initialization with None memory_manager raises ValueError."""
        with pytest.raises(ValueError, match="memory_manager cannot be None"):
            EmailQualifier(mock_agent_core, None)
    
    def test_qualify_success(self, email_qualifier, sample_lead_data, mock_agent_core):
        """Test successful lead qualification."""
        # Setup mock chain
        mock_chain = Mock()
        mock_chain.run.return_value = "Priority: high\nLead Score: 85\nReasoning: Strong lead"
        mock_agent_core.create_llm_chain.return_value = mock_chain
        
        result = email_qualifier.qualify(sample_lead_data)
        
        # Verify LLM chain was created and called
        mock_agent_core.create_llm_chain.assert_called_once()
        mock_chain.run.assert_called_once()
        
        # Verify result structure
        assert result.priority == 'high'
        assert result.lead_score == 85
        assert hasattr(result, 'reasoning')
        assert hasattr(result, 'next_action')
        assert hasattr(result, 'disposition')
        assert hasattr(result, 'confidence')
    
    def test_qualify_invalid_lead_data(self, email_qualifier):
        """Test qualification with invalid lead data."""
        invalid_data = {'name': 'John'}  # Missing required fields
        
        with pytest.raises(ValueError, match="lead_data is missing required fields"):
            email_qualifier.qualify(invalid_data)
    
    def test_qualify_llm_failure(self, email_qualifier, sample_lead_data, mock_agent_core):
        """Test qualification when LLM fails."""
        # Setup mock to raise exception
        mock_chain = Mock()
        mock_chain.run.side_effect = Exception("LLM error")
        mock_agent_core.create_llm_chain.return_value = mock_chain
        
        with pytest.raises(RuntimeError, match="LLM analysis failed"):
            email_qualifier.qualify(sample_lead_data)
    
    def test_qualify_with_previous_qualification(self, email_qualifier, sample_lead_data, mock_memory_manager):
        """Test qualification with previous qualification data."""
        # Setup memory manager to return previous qualification
        mock_memory_manager.get_qualification.return_value = {
            'priority': 'medium',
            'lead_score': 60
        }
        
        result = email_qualifier.qualify(sample_lead_data)
        
        # Verify memory manager was called
        mock_memory_manager.get_qualification.assert_called_once_with('john.smith@techcorp.com')
        assert result is not None
    
    def test_analyze_with_context_success(self, email_qualifier, sample_lead_data, mock_agent_core):
        """Test successful analysis with context."""
        previous_qual = {
            'priority': 'medium',
            'lead_score': 60,
            'reasoning': 'Initial assessment',
            'disposition': 'warm'
        }
        
        # Setup mock chain
        mock_chain = Mock()
        mock_chain.run.return_value = "Priority: high\nLead Score: 85"
        mock_agent_core.create_llm_chain.return_value = mock_chain
        
        result = email_qualifier.analyze_with_context(sample_lead_data, previous_qual)
        
        # Verify chain was called with context
        mock_agent_core.create_llm_chain.assert_called_once()
        mock_chain.run.assert_called_once()
        
        # Check that previous qualification context was included
        call_args = mock_chain.run.call_args[1]
        assert 'medium' in call_args['previous_qualification']
        assert '60' in call_args['previous_qualification']
        
        assert result is not None
    
    def test_analyze_with_context_invalid_data(self, email_qualifier):
        """Test analysis with context using invalid lead data."""
        invalid_data = {}
        
        with pytest.raises(ValueError, match="lead_data is invalid"):
            email_qualifier.analyze_with_context(invalid_data)
    
    def test_analyze_with_context_no_previous(self, email_qualifier, sample_lead_data, mock_agent_core):
        """Test analysis with context when no previous qualification exists."""
        # Setup mock chain
        mock_chain = Mock()
        mock_chain.run.return_value = "Priority: medium\nLead Score: 70"
        mock_agent_core.create_llm_chain.return_value = mock_chain
        
        result = email_qualifier.analyze_with_context(sample_lead_data, None)
        
        # Verify chain was called
        mock_chain.run.assert_called_once()
        call_args = mock_chain.run.call_args[1]
        assert call_args['previous_qualification'] == "None"
        
        assert result is not None
    
    def test_calculate_score_from_factors_success(self, email_qualifier):
        """Test successful score calculation from factors."""
        factors = {
            'company_size': 'enterprise',
            'urgency': 'high',
            'budget_signals': True,
            'authority': 'decision_maker',
            'need': 'urgent'
        }
        
        score = email_qualifier.calculate_score_from_factors(factors)
        
        # Expected: 25 (enterprise) + 20 (high urgency) + 20 (budget) + 15 (decision_maker) + 10 (urgent need) = 90
        assert score == 90
    
    def test_calculate_score_from_factors_minimum(self, email_qualifier):
        """Test score calculation with minimum values."""
        factors = {
            'company_size': 'small',
            'urgency': 'low',
            'budget_signals': False,
            'authority': 'none',
            'need': 'low'
        }
        
        score = email_qualifier.calculate_score_from_factors(factors)
        
        # Expected: 10 (small) + 5 (low urgency) + 0 (no budget) + 0 (no authority) + 2 (low need) = 17
        assert score == 17
    
    def test_calculate_score_from_factors_missing_factor(self, email_qualifier):
        """Test score calculation with missing required factor."""
        factors = {
            'company_size': 'large',
            'urgency': 'medium'
            # Missing other required factors
        }
        
        with pytest.raises(ValueError, match="Missing required factor"):
            email_qualifier.calculate_score_from_factors(factors)
    
    def test_calculate_score_from_factors_invalid_company_size(self, email_qualifier):
        """Test score calculation with invalid company size."""
        factors = {
            'company_size': 'invalid',
            'urgency': 'medium',
            'budget_signals': True,
            'authority': 'decision_maker',
            'need': 'high'
        }
        
        with pytest.raises(ValueError, match="Invalid company_size"):
            email_qualifier.calculate_score_from_factors(factors)
    
    def test_calculate_score_from_factors_invalid_budget_signals(self, email_qualifier):
        """Test score calculation with invalid budget signals type."""
        factors = {
            'company_size': 'large',
            'urgency': 'medium',
            'budget_signals': 'yes',  # Should be boolean
            'authority': 'decision_maker',
            'need': 'high'
        }
        
        with pytest.raises(ValueError, match="budget_signals must be boolean"):
            email_qualifier.calculate_score_from_factors(factors)
    
    def test_determine_priority_from_score_high(self, email_qualifier):
        """Test priority determination for high scores."""
        priority = email_qualifier.determine_priority_from_score(85, "medium")
        assert priority == "high"
    
    def test_determine_priority_from_score_medium(self, email_qualifier):
        """Test priority determination for medium scores."""
        priority = email_qualifier.determine_priority_from_score(65, "medium")
        assert priority == "medium"
    
    def test_determine_priority_from_score_low(self, email_qualifier):
        """Test priority determination for low scores."""
        priority = email_qualifier.determine_priority_from_score(30, "medium")
        assert priority == "low"
    
    def test_determine_priority_urgency_boost(self, email_qualifier):
        """Test priority boost from high urgency."""
        # Medium score with high urgency should become high priority
        priority = email_qualifier.determine_priority_from_score(65, "high")
        assert priority == "high"
    
    def test_determine_priority_urgency_reduction(self, email_qualifier):
        """Test priority reduction from low urgency."""
        # High score with low urgency should become medium priority
        priority = email_qualifier.determine_priority_from_score(85, "low")
        assert priority == "medium"
    
    def test_determine_priority_invalid_score(self, email_qualifier):
        """Test priority determination with invalid score."""
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            email_qualifier.determine_priority_from_score(150, "medium")
        
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            email_qualifier.determine_priority_from_score(-10, "medium")
    
    def test_determine_priority_invalid_urgency(self, email_qualifier):
        """Test priority determination with invalid urgency."""
        with pytest.raises(ValueError, match="Invalid urgency level"):
            email_qualifier.determine_priority_from_score(75, "invalid")
    
    def test_validate_lead_data_valid(self, email_qualifier, sample_lead_data):
        """Test validation of valid lead data."""
        assert email_qualifier._validate_lead_data(sample_lead_data) is True
    
    def test_validate_lead_data_missing_name(self, email_qualifier):
        """Test validation with missing name."""
        data = {
            'company': 'TechCorp',
            'email': 'test@techcorp.com',
            'interest': 'AI solution'
        }
        assert email_qualifier._validate_lead_data(data) is False
    
    def test_validate_lead_data_missing_company(self, email_qualifier):
        """Test validation with missing company."""
        data = {
            'name': 'John Smith',
            'email': 'test@techcorp.com',
            'interest': 'AI solution'
        }
        assert email_qualifier._validate_lead_data(data) is False
    
    def test_validate_lead_data_missing_email(self, email_qualifier):
        """Test validation with missing email."""
        data = {
            'name': 'John Smith',
            'company': 'TechCorp',
            'interest': 'AI solution'
        }
        assert email_qualifier._validate_lead_data(data) is False
    
    def test_validate_lead_data_missing_message_content(self, email_qualifier):
        """Test validation with missing message content."""
        data = {
            'name': 'John Smith',
            'company': 'TechCorp',
            'email': 'test@techcorp.com'
            # Missing both 'interest' and 'email_body'
        }
        assert email_qualifier._validate_lead_data(data) is False
    
    def test_validate_lead_data_with_email_body(self, email_qualifier):
        """Test validation with email_body instead of interest."""
        data = {
            'name': 'John Smith',
            'company': 'TechCorp',
            'email': 'test@techcorp.com',
            'email_body': 'We need AI solution'
        }
        assert email_qualifier._validate_lead_data(data) is True
    
    def test_validate_lead_data_none(self, email_qualifier):
        """Test validation with None data."""
        assert email_qualifier._validate_lead_data(None) is False
    
    def test_validate_lead_data_not_dict(self, email_qualifier):
        """Test validation with non-dictionary data."""
        assert email_qualifier._validate_lead_data("not a dict") is False
    
    def test_validate_lead_data_empty_fields(self, email_qualifier):
        """Test validation with empty required fields."""
        data = {
            'name': '',
            'company': 'TechCorp',
            'email': 'test@techcorp.com',
            'interest': 'AI solution'
        }
        assert email_qualifier._validate_lead_data(data) is False
    
    def test_build_qualification_prompt_success(self, email_qualifier, sample_lead_data):
        """Test successful prompt building."""
        prompt = email_qualifier._build_qualification_prompt(sample_lead_data)
        
        assert "lead qualification expert" in prompt.lower()
        assert "{lead_name}" in prompt
        assert "{lead_company}" in prompt
        assert "{lead_email}" in prompt
        assert "{lead_message}" in prompt
        assert "{previous_qualification}" in prompt
        assert "Priority:" in prompt
        assert "Lead Score:" in prompt
    
    def test_build_qualification_prompt_with_context(self, email_qualifier, sample_lead_data):
        """Test prompt building with additional context."""
        context = "Previous interaction: Called last week"
        prompt = email_qualifier._build_qualification_prompt(sample_lead_data, context)
        
        assert context in prompt
        assert "lead qualification expert" in prompt.lower()
    
    def test_build_qualification_prompt_invalid_data(self, email_qualifier):
        """Test prompt building with invalid lead data."""
        invalid_data = {'name': 'John'}  # Missing required fields
        
        with pytest.raises(ValueError, match="lead_data is missing required fields"):
            email_qualifier._build_qualification_prompt(invalid_data)
    
    def test_parse_qualification_success(self, email_qualifier, mock_agent_core):
        """Test successful qualification parsing."""
        llm_response = "Priority: high\nLead Score: 85\nReasoning: Strong lead"
        lead_data = {
            'lead_id': 'test_lead_id',
            'name': 'Test Name',
            'company': 'Test Company'
        }
        result = email_qualifier._parse_qualification(llm_response, lead_data)
        assert result.priority == 'high'
        assert result.lead_score == 85
        assert result.lead_name == 'Test Name'
        assert result.lead_company == 'Test Company'
    
    def test_parse_qualification_invalid_data(self, email_qualifier):
        """Test qualification parsing with invalid lead data."""
        invalid_data = {'name': 'John'}  # Missing required fields
        llm_response = "Priority: high\nLead Score: 85\nReasoning: Strong lead"
        with pytest.raises(ValueError, match="lead_data is missing required fields"):
            email_qualifier._parse_qualification(llm_response, invalid_data) 