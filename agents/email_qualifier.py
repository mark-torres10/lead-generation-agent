"""Email-based lead qualification agent.

This module provides functionality for qualifying leads based on their email content,
calculating lead scores, and determining priority levels and next actions.
"""

from typing import Dict, Any, Optional
from .agent_core import AgentCore
from .models import LeadQualificationResult


class EmailQualifier:
    """Agent for qualifying leads based on email content and context.
    
    Analyzes lead information from emails to determine qualification scores,
    priority levels, and recommended next actions using LLM-based analysis.
    """
    
    def __init__(self, agent_core: AgentCore, memory_manager: Any):
        """Initialize the EmailQualifier with dependencies.
        
        Args:
            agent_core: Core agent infrastructure for LLM operations
            memory_manager: Memory manager for storing/retrieving lead data
        """
        if agent_core is None:
            raise ValueError("agent_core cannot be None")
        if memory_manager is None:
            raise ValueError("memory_manager cannot be None")
        
        self.agent_core = agent_core
        self.memory_manager = memory_manager
    
    def qualify(self, lead_data: Dict[str, Any]) -> LeadQualificationResult:
        """Qualify a lead based on their email information.
        
        Analyzes lead data including name, company, email content, and interest
        to generate a qualification assessment with score and priority.
        
        Args:
            lead_data: Dictionary containing lead information:
                      - name: Lead's name
                      - company: Lead's company
                      - email: Lead's email address
                      - interest: Expressed interest/message content
                      - email_subject: Subject line of email
                      - email_body: Body content of email
        
        Returns:
            LeadQualificationResult: Qualification results
        
        Raises:
            ValueError: If required lead_data fields are missing
            RuntimeError: If LLM analysis fails
        """
        if not self._validate_lead_data(lead_data):
            raise ValueError("lead_data is missing required fields")
        
        try:
            # Build prompt for qualification
            prompt = self._build_qualification_prompt(lead_data)
            
            # Create LLM chain
            input_variables = ["lead_name", "lead_company", "lead_email", "lead_message", "previous_qualification"]
            chain = self.agent_core.create_llm_chain(prompt, input_variables)
            
            # Get previous qualification if available
            previous_qualification = "None"
            if hasattr(self.memory_manager, 'get_qualification'):
                prev_qual = self.memory_manager.get_qualification(lead_data.get('email', ''))
                if prev_qual:
                    previous_qualification = str(prev_qual)
            
            # Run qualification
            response = chain.run(
                lead_name=lead_data.get('name', 'Unknown'),
                lead_company=lead_data.get('company', 'Unknown'),
                lead_email=lead_data.get('email', 'Unknown'),
                lead_message=lead_data.get('interest', lead_data.get('email_body', 'No message provided')),
                previous_qualification=previous_qualification
            )
            
            # Parse response
            result = self._parse_qualification(response, lead_data)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"LLM analysis failed: {str(e)}")
    
    def analyze_with_context(self, lead_data: Dict[str, Any], previous_qualification: Optional[Dict[str, Any]] = None) -> LeadQualificationResult:
        """Qualify a lead with consideration of previous qualification history.
        
        Performs qualification analysis while taking into account any previous
        qualification results to provide more informed assessment.
        
        Args:
            lead_data: Current lead information (same format as qualify())
            previous_qualification: Previous qualification results if available
        
        Returns:
            LeadQualificationResult: Updated qualification results with context consideration
        
        Raises:
            ValueError: If lead_data is invalid
            RuntimeError: If analysis fails
        """
        if not self._validate_lead_data(lead_data):
            raise ValueError("lead_data is invalid")
        
        try:
            # Build context string from previous qualification
            context = ""
            if previous_qualification:
                context = f"""
Previous Qualification:
- Priority: {previous_qualification.get('priority', 'unknown')}
- Score: {previous_qualification.get('lead_score', 'unknown')}
- Previous Reasoning: {previous_qualification.get('reasoning', 'none')}
- Previous Disposition: {previous_qualification.get('disposition', 'unknown')}
"""
            
            # Build prompt with context
            prompt = self._build_qualification_prompt(lead_data, context)
            
            # Create LLM chain
            input_variables = ["lead_name", "lead_company", "lead_email", "lead_message", "previous_qualification"]
            chain = self.agent_core.create_llm_chain(prompt, input_variables)
            
            # Run qualification with context
            response = chain.run(
                lead_name=lead_data.get('name', 'Unknown'),
                lead_company=lead_data.get('company', 'Unknown'),
                lead_email=lead_data.get('email', 'Unknown'),
                lead_message=lead_data.get('interest', lead_data.get('email_body', 'No message provided')),
                previous_qualification=context or "None"
            )
            
            # Parse response
            result = self._parse_qualification(response, lead_data)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Analysis failed: {str(e)}")
    
    def calculate_score_from_factors(self, factors: Dict[str, Any]) -> int:
        """Calculate lead score based on specific qualification factors.
        
        Computes a numerical score (0-100) based on various lead qualification
        factors such as company size, urgency, budget signals, etc.
        
        Args:
            factors: Dictionary of qualification factors:
                    - company_size: Estimated company size
                    - urgency: Urgency level of request
                    - budget_signals: Indicators of budget availability
                    - authority: Decision-making authority indicators
                    - need: Level of expressed need
        
        Returns:
            int: Lead score from 0-100
        
        Raises:
            ValueError: If factors are invalid or missing
        """
        required_factors = ['company_size', 'urgency', 'budget_signals', 'authority', 'need']
        
        for factor in required_factors:
            if factor not in factors:
                raise ValueError(f"Missing required factor: {factor}")
        
        # Validate factor values
        valid_company_sizes = ['small', 'medium', 'large', 'enterprise']
        valid_urgency_levels = ['low', 'medium', 'high', 'urgent']
        valid_authority_levels = ['none', 'influencer', 'decision_maker', 'executive']
        valid_need_levels = ['low', 'medium', 'high', 'urgent']
        
        if factors['company_size'] not in valid_company_sizes:
            raise ValueError(f"Invalid company_size: {factors['company_size']}")
        if factors['urgency'] not in valid_urgency_levels:
            raise ValueError(f"Invalid urgency: {factors['urgency']}")
        if not isinstance(factors['budget_signals'], bool):
            raise ValueError("budget_signals must be boolean")
        if factors['authority'] not in valid_authority_levels:
            raise ValueError(f"Invalid authority: {factors['authority']}")
        if factors['need'] not in valid_need_levels:
            raise ValueError(f"Invalid need: {factors['need']}")
        
        # Calculate score based on factors
        score = 0
        
        # Company size scoring (0-25 points)
        company_scores = {'small': 10, 'medium': 15, 'large': 20, 'enterprise': 25}
        score += company_scores[factors['company_size']]
        
        # Urgency scoring (0-25 points)
        urgency_scores = {'low': 5, 'medium': 10, 'high': 20, 'urgent': 25}
        score += urgency_scores[factors['urgency']]
        
        # Budget signals (0-20 points)
        if factors['budget_signals']:
            score += 20
        
        # Authority scoring (0-20 points)
        authority_scores = {'none': 0, 'influencer': 5, 'decision_maker': 15, 'executive': 20}
        score += authority_scores[factors['authority']]
        
        # Need scoring (0-10 points)
        need_scores = {'low': 2, 'medium': 5, 'high': 8, 'urgent': 10}
        score += need_scores[factors['need']]
        
        return min(score, 100)  # Cap at 100
    
    def determine_priority_from_score(self, score: int, urgency: str = "medium") -> str:
        """Determine priority level based on lead score and urgency.
        
        Maps numerical lead score and urgency indicators to priority categories
        for sales team action prioritization.
        
        Args:
            score: Lead score from 0-100
            urgency: Urgency level ("high", "medium", "low")
        
        Returns:
            str: Priority level ("high", "medium", "low")
        
        Raises:
            ValueError: If score is out of range or urgency is invalid
        """
        if not (0 <= score <= 100):
            raise ValueError("Score must be between 0 and 100")
        
        valid_urgency_levels = ['low', 'medium', 'high']
        if urgency not in valid_urgency_levels:
            raise ValueError(f"Invalid urgency level: {urgency}")
        
        # Base priority from score
        if score >= 80:
            base_priority = "high"
        elif score >= 50:
            base_priority = "medium"
        else:
            base_priority = "low"
        
        # Adjust based on urgency
        if urgency == "high" and base_priority == "medium":
            return "high"
        elif urgency == "low" and base_priority == "high":
            return "medium"
        
        return base_priority
    
    def _parse_qualification(self, llm_response: str, lead_data: Optional[Dict[str, Any]] = None) -> LeadQualificationResult:
        """Parse LLM qualification response into structured data.
        
        Internal method to extract qualification fields from LLM response text
        and convert them to appropriate data types with validation.
        
        Args:
            llm_response: Raw text response from LLM
            lead_data: Lead data dictionary to inject into parsed result
        
        Returns:
            LeadQualificationResult: Parsed qualification data
        
        Raises:
            ValueError: If response format is invalid
        """
        expected_fields = {
            'priority': 'medium',
            'lead_score': 50,
            'reasoning': 'No specific reasoning provided',
            'next_action': 'Follow up',
            'disposition': 'warm',
            'confidence': 50
        }
        
        parsed = self.agent_core.parse_structured_response(llm_response, expected_fields)
        
        # Inject lead_id, lead_name, lead_company from lead_data if available
        if lead_data:
            missing = []
            if not (lead_data.get('lead_id') or lead_data.get('email')):
                missing.append('lead_id or email')
            if not lead_data.get('name'):
                missing.append('name')
            if not lead_data.get('company'):
                missing.append('company')
            if missing:
                raise ValueError(f"lead_data is missing required fields: {', '.join(missing)}")
            if 'lead_id' not in parsed:
                parsed['lead_id'] = lead_data.get('lead_id') or lead_data.get('email')
            if 'lead_name' not in parsed:
                parsed['lead_name'] = lead_data.get('name')
            if 'lead_company' not in parsed:
                parsed['lead_company'] = lead_data.get('company')
        
        return LeadQualificationResult(**parsed)
    
    def _build_qualification_prompt(self, lead_data: Dict[str, Any], context: str = "") -> str:
        """Build prompt template for lead qualification analysis.
        
        Internal method to construct the prompt template used for LLM-based
        lead qualification including lead data and optional context.
        
        Args:
            lead_data: Lead information to include in prompt
            context: Optional additional context (e.g., previous qualifications)
        
        Returns:
            str: Formatted prompt template for LLM analysis
        
        Raises:
            ValueError: If lead_data is missing required fields
        """
        if not self._validate_lead_data(lead_data):
            raise ValueError("lead_data is missing required fields")
        
        template = """
You are a lead qualification expert. Analyze the following lead information and provide a qualification assessment.

Lead Information:
- Name: {lead_name}
- Company: {lead_company}
- Email: {lead_email}
- Message: {lead_message}

Previous Qualification (if any): {previous_qualification}

""" + context + """

Please provide your assessment in the following format:
Priority: [high/medium/low]
Lead Score: [0-100]
Reasoning: [Your reasoning for the score and priority]
Next Action: [Recommended next action]
Disposition: [hot/warm/cold/unqualified]
Confidence: [0-100]

Consider these factors:
- Company size and potential value
- Urgency indicators in the message
- Budget signals or decision-making authority
- Specific needs expressed
- Quality of the inquiry
"""
        
        return template
    
    def _validate_lead_data(self, lead_data: Dict[str, Any]) -> bool:
        """Validate that lead data contains required fields.
        
        Internal method to check that lead_data dictionary contains all
        necessary fields for qualification analysis.
        
        Args:
            lead_data: Lead data dictionary to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not lead_data or not isinstance(lead_data, dict):
            return False
        
        required_fields = ['name', 'company', 'email']
        
        for field in required_fields:
            if field not in lead_data or not lead_data[field]:
                return False
        
        # Must have either 'interest' or 'email_body' for message content
        if not (lead_data.get('interest') or lead_data.get('email_body')):
            return False
        
        return True
