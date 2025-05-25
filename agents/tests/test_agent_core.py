"""Unit tests for AgentCore class."""

import pytest
from unittest.mock import Mock, patch
from agents.agent_core import AgentCore


class TestAgentCore:
    """Test cases for AgentCore functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.llm_config = {
            "model": "gpt-4o-mini",
            "temperature": 0.0,
            "max_tokens": 500,
            "api_key": "test-key"
        }
        self.agent_core = AgentCore(self.llm_config)
    
    def test_init_with_valid_config(self):
        """Test AgentCore initialization with valid configuration."""
        agent = AgentCore(self.llm_config)
        assert agent is not None
    
    def test_init_with_invalid_config(self):
        """Test AgentCore initialization with invalid configuration."""
        with pytest.raises(ValueError):
            AgentCore({})
    
    def test_create_llm_chain_with_valid_inputs(self):
        """Test LLM chain creation with valid prompt template and variables."""
        template = "Analyze this: {text}"
        variables = ["text"]
        
        chain = self.agent_core.create_llm_chain(template, variables)
        
        assert chain is not None
        # Should return a LangChain LLMChain object
        from langchain.chains import LLMChain
        assert isinstance(chain, LLMChain)
    
    def test_create_llm_chain_with_invalid_template(self):
        """Test LLM chain creation with invalid prompt template."""
        with pytest.raises(ValueError):
            self.agent_core.create_llm_chain("", ["text"])
    
    def test_create_llm_chain_with_invalid_variables(self):
        """Test LLM chain creation with invalid input variables."""
        template = "Analyze this: {text}"
        
        with pytest.raises(ValueError):
            self.agent_core.create_llm_chain(template, [])
    
    def test_parse_structured_response_with_valid_input(self):
        """Test parsing structured response with valid LLM output."""
        response = """
        PRIORITY: high
        SCORE: 85
        REASONING: Strong interest signals
        """
        expected_fields = {
            "priority": "medium",
            "score": 50,
            "reasoning": ""
        }
        
        result = self.agent_core.parse_structured_response(response, expected_fields)
        
        assert result["priority"] == "high"
        assert result["score"] == 85
        assert "Strong interest signals" in result["reasoning"]
    
    def test_parse_structured_response_with_missing_fields(self):
        """Test parsing response with missing required fields uses defaults."""
        response = "PRIORITY: high"
        expected_fields = {
            "priority": "medium",
            "score": 50,
            "reasoning": "default reasoning"
        }
        
        result = self.agent_core.parse_structured_response(response, expected_fields)
        
        assert result["priority"] == "high"
        assert result["score"] == 50  # Should use default
        assert result["reasoning"] == "default reasoning"  # Should use default
    
    def test_parse_structured_response_with_invalid_format(self):
        """Test parsing response with completely invalid format."""
        response = "This is not a structured response"
        expected_fields = {"priority": "medium"}
        
        with pytest.raises(ValueError):
            self.agent_core.parse_structured_response(response, expected_fields)
    
    def test_configure_llm_with_valid_params(self):
        """Test LLM configuration with valid parameters."""
        # Should not raise any exceptions
        self.agent_core.configure_llm("gpt-3.5-turbo", 0.5, 1000)
    
    def test_configure_llm_with_invalid_temperature(self):
        """Test LLM configuration with invalid temperature."""
        with pytest.raises(ValueError):
            self.agent_core.configure_llm("gpt-4", 2.0, 1000)  # Temperature > 1.0
    
    def test_configure_llm_with_invalid_max_tokens(self):
        """Test LLM configuration with invalid max_tokens."""
        with pytest.raises(ValueError):
            self.agent_core.configure_llm("gpt-4", 0.5, -100)  # Negative tokens
    
    def test_configure_llm_with_invalid_model(self):
        """Test LLM configuration with invalid model name."""
        with pytest.raises(ValueError):
            self.agent_core.configure_llm("", 0.5, 1000)  # Empty model name
    
    def test_validate_response_format_with_valid_patterns(self):
        """Test response format validation with valid patterns."""
        response = """
        PRIORITY: high
        SCORE: 85
        REASONING: Detailed analysis here
        """
        patterns = [r"PRIORITY:\s*\w+", r"SCORE:\s*\d+", r"REASONING:\s*.+"]
        
        result = self.agent_core.validate_response_format(response, patterns)
        
        assert result is True
    
    def test_validate_response_format_with_missing_patterns(self):
        """Test response format validation with missing patterns."""
        response = "PRIORITY: high"
        patterns = [r"PRIORITY:\s*\w+", r"SCORE:\s*\d+"]  # SCORE pattern missing
        
        result = self.agent_core.validate_response_format(response, patterns)
        
        assert result is False
    
    def test_validate_response_format_with_empty_response(self):
        """Test response format validation with empty response."""
        response = ""
        patterns = [r"PRIORITY:\s*\w+"]
        
        result = self.agent_core.validate_response_format(response, patterns)
        
        assert result is False
    
    def test_validate_response_format_with_empty_patterns(self):
        """Test response format validation with empty patterns list."""
        response = "Some response text"
        patterns = []
        
        result = self.agent_core.validate_response_format(response, patterns)
        
        assert result is True  # Should return True if no patterns to validate 