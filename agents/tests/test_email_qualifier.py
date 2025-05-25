"""Unit tests for EmailQualifier class."""

import pytest
from unittest.mock import Mock, patch
from agents.email_qualifier import EmailQualifier
from agents.agent_core import AgentCore


class TestEmailQualifier:
    """Test cases for EmailQualifier functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_agent_core = Mock(spec=AgentCore)
        self.mock_memory_manager = Mock()
        self.email_qualifier = EmailQualifier(self.mock_agent_core, self.mock_memory_manager)
        
        self.sample_lead_data = {
            "name": "John Smith",
            "company": "TechCorp Inc",
            "email": "john@techcorp.com",
            "interest": "Looking for automation tools",
            "email_subject": "Interested in your product",
            "email_body": "Hi, I'd like to learn more about your automation platform."
        }
    
    def test_init_with_valid_dependencies(self):
        """Test EmailQualifier initialization with valid dependencies."""
        qualifier = EmailQualifier(self.mock_agent_core, self.mock_memory_manager)
        assert qualifier is not None
    
    def test_init_with_none_dependencies(self):
        """Test EmailQualifier initialization with None dependencies."""
        with pytest.raises(ValueError):
            EmailQualifier(None, self.mock_memory_manager)
        
        with pytest.raises(ValueError):
            EmailQualifier(self.mock_agent_core, None)
    
    def test_qualify_with_valid_lead_data(self):
        """Test lead qualification with valid lead data."""
        expected_result = {
            "priority": "high",
            "lead_score": 85,
            "reasoning": "Strong interest signals",
            "next_action": "Schedule demo call",
            "disposition": "hot",
            "confidence": 90
        }
        
        result = self.email_qualifier.qualify(self.sample_lead_data)
        
        assert result is not None
        for key in expected_result:
            assert key in result
            assert result[key] == expected_result[key]
    
    def test_qualify_with_missing_required_fields(self):
        """Test qualification with missing required fields."""
        incomplete_data = {"name": "John Smith"}  # Missing required fields
        
        with pytest.raises(ValueError):
            self.email_qualifier.qualify(incomplete_data)
    
    def test_qualify_with_empty_lead_data(self):
        """Test qualification with empty lead data."""
        with pytest.raises(ValueError):
            self.email_qualifier.qualify({})
    
    def test_analyze_with_context_with_previous_qualification(self):
        """Test analysis with previous qualification context."""
        previous_qual = {
            "priority": "medium",
            "lead_score": 60,
            "reasoning": "Initial interest shown"
        }
        
        result = self.email_qualifier.analyze_with_context(
            self.sample_lead_data, 
            previous_qual
        )
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_analyze_with_context_without_previous_qualification(self):
        """Test analysis without previous qualification context."""
        result = self.email_qualifier.analyze_with_context(self.sample_lead_data, None)
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_calculate_score_from_factors_with_valid_factors(self):
        """Test score calculation with valid qualification factors."""
        factors = {
            "company_size": "large",
            "urgency": "high",
            "budget_signals": True,
            "authority": "decision_maker",
            "need": "urgent"
        }
        
        score = self.email_qualifier.calculate_score_from_factors(factors)
        
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    def test_calculate_score_from_factors_with_missing_factors(self):
        """Test score calculation with missing factors."""
        incomplete_factors = {"company_size": "small"}
        
        with pytest.raises(ValueError):
            self.email_qualifier.calculate_score_from_factors(incomplete_factors)
    
    def test_calculate_score_from_factors_with_invalid_factors(self):
        """Test score calculation with invalid factor values."""
        invalid_factors = {
            "company_size": "invalid_size",
            "urgency": "invalid_urgency",
            "budget_signals": "not_boolean",
            "authority": "",
            "need": None
        }
        
        with pytest.raises(ValueError):
            self.email_qualifier.calculate_score_from_factors(invalid_factors)
    
    def test_determine_priority_from_score_high_score(self):
        """Test priority determination with high score."""
        priority = self.email_qualifier.determine_priority_from_score(85, "high")
        assert priority == "high"
    
    def test_determine_priority_from_score_medium_score(self):
        """Test priority determination with medium score."""
        priority = self.email_qualifier.determine_priority_from_score(60, "medium")
        assert priority == "medium"
    
    def test_determine_priority_from_score_low_score(self):
        """Test priority determination with low score."""
        priority = self.email_qualifier.determine_priority_from_score(30, "low")
        assert priority == "low"
    
    def test_determine_priority_from_score_invalid_score(self):
        """Test priority determination with invalid score."""
        with pytest.raises(ValueError):
            self.email_qualifier.determine_priority_from_score(-10, "medium")
        
        with pytest.raises(ValueError):
            self.email_qualifier.determine_priority_from_score(150, "medium")
    
    def test_determine_priority_from_score_invalid_urgency(self):
        """Test priority determination with invalid urgency."""
        with pytest.raises(ValueError):
            self.email_qualifier.determine_priority_from_score(75, "invalid_urgency")
    
    def test_parse_qualification_with_valid_response(self):
        """Test parsing valid LLM qualification response."""
        llm_response = """
        PRIORITY: high
        SCORE: 85
        REASONING: Strong interest and budget signals
        NEXT_ACTION: Schedule demo call
        DISPOSITION: hot
        CONFIDENCE: 90
        """
        
        result = self.email_qualifier._parse_qualification(llm_response)
        
        assert result["priority"] == "high"
        assert result["lead_score"] == 85
        assert "Strong interest" in result["reasoning"]
        assert result["next_action"] == "Schedule demo call"
        assert result["disposition"] == "hot"
        assert result["confidence"] == 90
    
    def test_parse_qualification_with_invalid_response(self):
        """Test parsing invalid LLM response."""
        invalid_response = "This is not a structured response"
        
        with pytest.raises(ValueError):
            self.email_qualifier._parse_qualification(invalid_response)
    
    def test_build_qualification_prompt_with_valid_data(self):
        """Test building qualification prompt with valid data."""
        context = "Previous qualification: medium priority"
        
        prompt = self.email_qualifier._build_qualification_prompt(
            self.sample_lead_data, 
            context
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "John Smith" in prompt
        assert "TechCorp Inc" in prompt
    
    def test_build_qualification_prompt_with_missing_fields(self):
        """Test building prompt with missing required fields."""
        incomplete_data = {"name": "John"}  # Missing required fields
        
        with pytest.raises(ValueError):
            self.email_qualifier._build_qualification_prompt(incomplete_data)
    
    def test_validate_lead_data_with_valid_data(self):
        """Test lead data validation with valid data."""
        is_valid = self.email_qualifier._validate_lead_data(self.sample_lead_data)
        assert is_valid is True
    
    def test_validate_lead_data_with_missing_fields(self):
        """Test lead data validation with missing fields."""
        incomplete_data = {"name": "John Smith"}  # Missing required fields
        
        is_valid = self.email_qualifier._validate_lead_data(incomplete_data)
        assert is_valid is False
    
    def test_validate_lead_data_with_empty_data(self):
        """Test lead data validation with empty data."""
        is_valid = self.email_qualifier._validate_lead_data({})
        assert is_valid is False
    
    def test_validate_lead_data_with_none_data(self):
        """Test lead data validation with None data."""
        is_valid = self.email_qualifier._validate_lead_data(None)
        assert is_valid is False 