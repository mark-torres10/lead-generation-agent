"""Core agent infrastructure for LLM chain creation and configuration.

This module provides shared functionality for all agents including LLM initialization,
prompt template management, and response parsing utilities.
"""

import os
import re
from typing import Dict, List, Any
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAI


class AgentCore:
    """Core infrastructure for agent LLM operations.
    
    Provides shared functionality for LLM chain creation, configuration,
    and response parsing that can be used by all specialized agents.
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """Initialize the AgentCore with LLM configuration.
        
        Args:
            llm_config: Dictionary containing LLM configuration parameters
                       including model, temperature, max_tokens, api_key, etc.
        """
        if not llm_config:
            raise ValueError("llm_config cannot be empty")
        
        self.llm_config = llm_config
        self.llm = None
        self._configure_llm_from_config(llm_config)
    
    def create_llm_chain(self, prompt_template: str, input_variables: List[str]) -> LLMChain:
        """Create an LLM chain with the given prompt template.
        
        Args:
            prompt_template: The prompt template string with placeholders
            input_variables: List of variable names used in the template
            
        Returns:
            LLMChain: Configured LangChain LLM chain ready for execution
            
        Raises:
            ValueError: If prompt_template or input_variables are invalid
            RuntimeError: If LLM initialization fails
        """
        if not prompt_template or not prompt_template.strip():
            raise ValueError("prompt_template cannot be empty")
        
        if not input_variables:
            raise ValueError("input_variables cannot be empty")
        
        if self.llm is None:
            raise RuntimeError("LLM not properly initialized")
        
        try:
            prompt = PromptTemplate(
                input_variables=input_variables,
                template=prompt_template
            )
            return LLMChain(llm=self.llm, prompt=prompt)
        except Exception as e:
            raise RuntimeError(f"Failed to create LLM chain: {str(e)}")
    
    def parse_structured_response(self, response: str, expected_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured LLM response into a dictionary.
        
        Extracts key-value pairs from LLM response text and validates against
        expected fields with type conversion and default values.
        
        Args:
            response: Raw LLM response text
            expected_fields: Dictionary mapping field names to their expected types/defaults
                           e.g., {"priority": "medium", "score": 50, "reasoning": ""}
            
        Returns:
            Dict containing parsed and validated response data
            
        Raises:
            ValueError: If response format is invalid or required fields are missing
        """
        if not response or not response.strip():
            raise ValueError("Response cannot be empty")
        
        if not expected_fields:
            raise ValueError("expected_fields cannot be empty")
        
        try:
            lines = response.strip().split('\n')
            result = {}
            found_any_structured_data = False
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    # Clean up markdown formatting from key and value
                    key = key.strip().replace('*', '').replace('#', '').lower().replace(' ', '_').replace('-', '_')
                    value = value.strip().replace('*', '').strip()
                    
                    # Convert to appropriate types based on expected fields
                    if key in expected_fields:
                        found_any_structured_data = True
                        expected_type = type(expected_fields[key])
                        if expected_type is int:
                            try:
                                result[key] = int(value)
                            except ValueError:
                                result[key] = expected_fields[key]  # Use default
                        elif expected_type is float:
                            try:
                                result[key] = float(value)
                            except ValueError:
                                result[key] = expected_fields[key]  # Use default
                        else:
                            result[key] = value
            
            # If no structured data was found, raise an error
            if not found_any_structured_data:
                raise ValueError("No structured data found in response")
            
            # Fill in missing fields with defaults
            for key, default_value in expected_fields.items():
                if key not in result:
                    result[key] = default_value
            
            return result
            
        except ValueError:
            # Re-raise ValueError as is
            raise
        except Exception as e:
            raise ValueError(f"Failed to parse structured response: {str(e)}")
    
    def configure_llm(self, model: str, temperature: float, max_tokens: int, **kwargs) -> None:
        """Configure the LLM with specified parameters.
        
        Args:
            model: Model name (e.g., "gpt-4o-mini", "gpt-3.5-turbo")
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional LLM configuration parameters
            
        Raises:
            ValueError: If parameters are out of valid ranges
            RuntimeError: If LLM reconfiguration fails
        """
        if not model or not model.strip():
            raise ValueError("Model name cannot be empty")
        
        if not (0.0 <= temperature <= 1.0):
            raise ValueError("Temperature must be between 0.0 and 1.0")
        
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        try:
            config = {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            self.llm_config.update(config)
            self._configure_llm_from_config(self.llm_config)
        except Exception as e:
            raise RuntimeError(f"Failed to configure LLM: {str(e)}")
    
    def validate_response_format(self, response: str, required_patterns: List[str]) -> bool:
        """Validate that response contains required patterns.
        
        Args:
            response: LLM response text to validate
            required_patterns: List of regex patterns that must be present
            
        Returns:
            bool: True if all patterns are found, False otherwise
        """
        if not response:
            return False
        
        if not required_patterns:
            return True  # No patterns to validate
        
        try:
            for pattern in required_patterns:
                if not re.search(pattern, response, re.IGNORECASE):
                    return False
            return True
        except Exception:
            return False
    
    def _configure_llm_from_config(self, config: Dict[str, Any]) -> None:
        """Internal method to configure LLM from config dictionary."""
        model = config.get("model", "gpt-4o-mini")
        temperature = config.get("temperature", 0.0)
        max_tokens = config.get("max_tokens", 500)
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        
        # Choose LLM class based on model
        if model.startswith("gpt-4") or model.startswith("gpt-3.5"):
            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=api_key
            )
        else:
            # Fallback to OpenAI for other models
            self.llm = OpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=api_key
            )
