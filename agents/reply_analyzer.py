"""Email reply analysis agent.

This module provides functionality for analyzing email replies to determine
intent, sentiment, engagement level, and recommended next actions.
"""

import re
from typing import Dict, Any
from .agent_core import AgentCore


class ReplyAnalyzer:
    """Agent for analyzing email replies and determining next actions.
    
    Analyzes reply content to determine lead intent, sentiment, engagement level,
    and urgency to recommend appropriate follow-up actions.
    """
    
    def __init__(self, agent_core: AgentCore, memory_manager: Any):
        """Initialize the ReplyAnalyzer with dependencies.
        
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
    
    def analyze(self, reply_data: Dict[str, Any], lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an email reply to determine intent and next actions.
        
        Performs comprehensive analysis of reply content considering lead context
        to determine disposition, sentiment, urgency, and recommended actions.
        
        Args:
            reply_data: Dictionary containing reply information:
                       - reply_text: Content of the reply
                       - reply_subject: Subject line of reply
                       - sender_email: Email address of sender
                       - timestamp: When reply was received
                       - lead_id: ID of the lead who replied
            lead_context: Dictionary containing lead background:
                         - name: Lead's name
                         - company: Lead's company
                         - previous_interest: Previously expressed interest
                         - interaction_history: Previous interactions
        
        Returns:
            Dict containing analysis results:
                - disposition: "engaged", "maybe", "disinterested"
                - confidence: Confidence level (0-100)
                - sentiment: "positive", "neutral", "negative"
                - urgency: "high", "medium", "low"
                - reasoning: Detailed analysis reasoning
                - next_action: Specific recommended next step
                - follow_up_timing: "immediate", "1-week", "1-month", "3-months", "none"
                - intent: Specific intent category
        
        Raises:
            ValueError: If required reply_data or lead_context fields are missing
            RuntimeError: If LLM analysis fails
        """
        if not self._validate_reply_data(reply_data):
            raise ValueError("reply_data is missing required fields")
        
        if not lead_context or not isinstance(lead_context, dict):
            raise ValueError("lead_context must be a valid dictionary")
        
        try:
            # Build context string from lead information
            context = self._build_context_string(lead_context)
            
            # Build prompt for analysis
            prompt = self._build_reply_prompt(reply_data, context)
            
            # Create LLM chain
            input_variables = ["reply_text", "reply_subject", "sender_email", "lead_context", "interaction_history"]
            chain = self.agent_core.create_llm_chain(prompt, input_variables)
            
            # Run analysis
            response = chain.run(
                reply_text=reply_data.get('reply_text', ''),
                reply_subject=reply_data.get('reply_subject', ''),
                sender_email=reply_data.get('sender_email', ''),
                lead_context=context,
                interaction_history=lead_context.get('interaction_history', 'No previous interactions')
            )
            
            # Parse response
            result = self._parse_analysis(response)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Reply analysis failed: {str(e)}")
    
    def calculate_score(self, analysis_result: Dict[str, Any]) -> int:
        """Calculate updated lead score based on reply analysis.
        
        Computes a new lead score based on the reply analysis results,
        considering disposition, sentiment, and engagement indicators.
        
        Args:
            analysis_result: Results from analyze() method
        
        Returns:
            int: Updated lead score from 0-100
        
        Raises:
            ValueError: If analysis_result is missing required fields
        """
        required_fields = ['disposition', 'sentiment', 'urgency', 'confidence']
        
        for field in required_fields:
            if field not in analysis_result:
                raise ValueError(f"Missing required field: {field}")
        
        score = 0
        
        # Disposition scoring (0-40 points)
        disposition_scores = {'engaged': 40, 'maybe': 20, 'disinterested': 0}
        score += disposition_scores.get(analysis_result['disposition'], 20)
        
        # Sentiment scoring (0-25 points)
        sentiment_scores = {'positive': 25, 'neutral': 15, 'negative': 0}
        score += sentiment_scores.get(analysis_result['sentiment'], 15)
        
        # Urgency scoring (0-20 points)
        urgency_scores = {'high': 20, 'medium': 10, 'low': 5}
        score += urgency_scores.get(analysis_result['urgency'], 10)
        
        # Confidence adjustment (0-15 points)
        confidence = analysis_result.get('confidence', 50)
        confidence_bonus = min(15, int(confidence * 0.15))
        score += confidence_bonus
        
        return min(score, 100)  # Cap at 100
    
    def determine_priority(self, analysis_result: Dict[str, Any]) -> str:
        """Determine priority level based on reply analysis.
        
        Maps reply analysis results to priority categories for sales team
        action prioritization based on engagement and urgency.
        
        Args:
            analysis_result: Results from analyze() method
        
        Returns:
            str: Priority level ("high", "medium", "low")
        
        Raises:
            ValueError: If analysis_result is invalid
        """
        if not analysis_result or not isinstance(analysis_result, dict):
            raise ValueError("analysis_result must be a valid dictionary")
        
        disposition = analysis_result.get('disposition', 'maybe')
        urgency = analysis_result.get('urgency', 'medium')
        sentiment = analysis_result.get('sentiment', 'neutral')
        
        # High priority conditions
        if disposition == 'engaged' and urgency in ['high', 'medium']:
            return "high"
        if disposition == 'maybe' and urgency == 'high' and sentiment == 'positive':
            return "high"
        
        # Low priority conditions
        if disposition == 'disinterested':
            return "low"
        if sentiment == 'negative' and urgency == 'low':
            return "low"
        
        # Default to medium priority
        return "medium"
    
    def classify_intent(self, reply_text: str, context: Dict[str, Any]) -> str:
        """Classify the specific intent of the reply.
        
        Determines the specific intent category of the reply such as
        meeting request, information request, objection, etc.
        
        Args:
            reply_text: Content of the reply to classify
            context: Additional context for classification
        
        Returns:
            str: Intent category ("interested", "meeting_request", "info_request", 
                 "neutral", "objection", "not_interested")
        
        Raises:
            ValueError: If reply_text is empty or invalid
        """
        if not reply_text or not reply_text.strip():
            raise ValueError("reply_text cannot be empty")
        
        reply_lower = reply_text.lower()
        
        # Meeting request indicators
        meeting_keywords = ['meeting', 'call', 'demo', 'schedule', 'available', 'calendar', 'appointment']
        if any(keyword in reply_lower for keyword in meeting_keywords):
            return "meeting_request"
        
        # Information request indicators
        info_keywords = ['more information', 'details', 'pricing', 'features', 'how does', 'can you tell me']
        if any(keyword in reply_lower for keyword in info_keywords):
            return "info_request"
        
        # Not interested indicators
        not_interested_keywords = ['not interested', 'no thank you', 'remove me', 'unsubscribe', 'not right now']
        if any(keyword in reply_lower for keyword in not_interested_keywords):
            return "not_interested"
        
        # Objection indicators
        objection_keywords = ['too expensive', 'budget', 'already have', 'not sure', 'concerns']
        if any(keyword in reply_lower for keyword in objection_keywords):
            return "objection"
        
        # Interest indicators
        interest_keywords = ['interested', 'sounds good', 'tell me more', 'yes', 'definitely']
        if any(keyword in reply_lower for keyword in interest_keywords):
            return "interested"
        
        return "neutral"
    
    def extract_engagement_signals(self, reply_text: str) -> Dict[str, Any]:
        """Extract engagement signals from reply content.
        
        Identifies specific signals in the reply that indicate level of
        engagement such as questions, urgency indicators, budget mentions, etc.
        
        Args:
            reply_text: Content of the reply to analyze
        
        Returns:
            Dict containing engagement signals:
                - questions_asked: Number of questions in reply
                - urgency_indicators: List of urgency signals found
                - budget_mentions: Whether budget was mentioned
                - timeline_mentions: Any timeline references
                - decision_authority: Indicators of decision-making authority
        
        Raises:
            ValueError: If reply_text is empty
        """
        if not reply_text or not reply_text.strip():
            raise ValueError("reply_text cannot be empty")
        
        # Count questions
        questions_asked = len(re.findall(r'\?', reply_text))
        
        # Find urgency indicators
        urgency_patterns = [
            r'\basap\b', r'\burgent\b', r'\bimmediately\b', r'\bquickly\b',
            r'\bright away\b', r'\bsoon\b', r'\btoday\b', r'\btomorrow\b'
        ]
        urgency_indicators = []
        for pattern in urgency_patterns:
            matches = re.findall(pattern, reply_text, re.IGNORECASE)
            urgency_indicators.extend(matches)
        
        # Check for budget mentions
        budget_patterns = [
            r'\bbudget\b', r'\bcost\b', r'\bprice\b', r'\bpricing\b',
            r'\b\$\d+\b', r'\bmoney\b', r'\bexpensive\b', r'\bafford\b'
        ]
        budget_mentions = any(re.search(pattern, reply_text, re.IGNORECASE) for pattern in budget_patterns)
        
        # Find timeline mentions
        timeline_patterns = [
            r'\bthis week\b', r'\bnext week\b', r'\bthis month\b', r'\bnext month\b',
            r'\bq[1-4]\b', r'\bquarter\b', r'\byear\b', r'\bjanuary\b', r'\bfebruary\b',
            r'\bmarch\b', r'\bapril\b', r'\bmay\b', r'\bjune\b', r'\bjuly\b',
            r'\baugust\b', r'\bseptember\b', r'\boctober\b', r'\bnovember\b', r'\bdecember\b'
        ]
        timeline_mentions = []
        for pattern in timeline_patterns:
            matches = re.findall(pattern, reply_text, re.IGNORECASE)
            timeline_mentions.extend(matches)
        
        # Check for decision authority indicators
        authority_patterns = [
            r'\bi decide\b', r'\bmy decision\b', r'\bi approve\b', r'\bmy team\b',
            r'\bboard\b', r'\bmanagement\b', r'\bceo\b', r'\bcto\b', r'\bvp\b'
        ]
        decision_authority = any(re.search(pattern, reply_text, re.IGNORECASE) for pattern in authority_patterns)
        
        return {
            'questions_asked': questions_asked,
            'urgency_indicators': urgency_indicators,
            'budget_mentions': budget_mentions,
            'timeline_mentions': timeline_mentions,
            'decision_authority': decision_authority
        }
    
    def _parse_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM reply analysis response into structured data.
        
        Internal method to extract analysis fields from LLM response text
        and convert them to appropriate data types with validation.
        
        Args:
            llm_response: Raw text response from LLM
        
        Returns:
            Dict containing parsed analysis data
        
        Raises:
            ValueError: If response format is invalid
        """
        expected_fields = {
            'disposition': 'maybe',
            'confidence': 50,
            'sentiment': 'neutral',
            'urgency': 'medium',
            'reasoning': 'No specific reasoning provided',
            'next_action': 'Follow up',
            'follow_up_timing': '1-week',
            'intent': 'neutral'
        }
        
        return self.agent_core.parse_structured_response(llm_response, expected_fields)
    
    def _build_reply_prompt(self, reply_data: Dict[str, Any], context: str = "") -> str:
        """Build prompt template for reply analysis.
        
        Internal method to construct the prompt template used for LLM-based
        reply analysis including reply data and lead context.
        
        Args:
            reply_data: Reply information to include in prompt
            context: Additional context about the lead
        
        Returns:
            str: Formatted prompt template for LLM analysis
        
        Raises:
            ValueError: If reply_data is missing required fields
        """
        if not self._validate_reply_data(reply_data):
            raise ValueError("reply_data is missing required fields")
        
        template = """
You are an expert email reply analyst. Analyze the following email reply to determine the lead's intent, sentiment, and engagement level.

Reply Information:
- Reply Text: {reply_text}
- Subject: {reply_subject}
- Sender: {sender_email}

Lead Context: {lead_context}

Interaction History: {interaction_history}

""" + context + """

Please provide your analysis in the following format:
Disposition: [engaged/maybe/disinterested]
Confidence: [0-100]
Sentiment: [positive/neutral/negative]
Urgency: [high/medium/low]
Reasoning: [Your detailed reasoning for the assessment]
Next Action: [Specific recommended next step]
Follow Up Timing: [immediate/1-week/1-month/3-months/none]
Intent: [interested/meeting_request/info_request/neutral/objection/not_interested]

Consider these factors:
- Tone and language used in the reply
- Specific questions or requests made
- Urgency indicators and timeline mentions
- Budget or decision-making authority signals
- Overall engagement level and interest
"""
        
        return template
    
    def _validate_reply_data(self, reply_data: Dict[str, Any]) -> bool:
        """Validate that reply data contains required fields.
        
        Internal method to check that reply_data dictionary contains all
        necessary fields for analysis.
        
        Args:
            reply_data: Reply data dictionary to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not reply_data or not isinstance(reply_data, dict):
            return False
        
        required_fields = ['reply_text', 'sender_email']
        
        for field in required_fields:
            if field not in reply_data or not reply_data[field]:
                return False
        
        return True
    
    def _calculate_engagement_score(self, signals: Dict[str, Any]) -> int:
        """Calculate numerical engagement score from signals.
        
        Internal method to convert engagement signals into a numerical
        score that can be used for lead scoring calculations.
        
        Args:
            signals: Engagement signals from extract_engagement_signals()
        
        Returns:
            int: Engagement score from 0-100
        """
        score = 0
        
        # Questions indicate engagement (up to 20 points)
        questions = signals.get('questions_asked', 0)
        score += min(20, questions * 5)
        
        # Urgency indicators (up to 25 points)
        urgency_count = len(signals.get('urgency_indicators', []))
        score += min(25, urgency_count * 8)
        
        # Budget mentions show serious consideration (20 points)
        if signals.get('budget_mentions', False):
            score += 20
        
        # Timeline mentions show planning (15 points)
        timeline_count = len(signals.get('timeline_mentions', []))
        if timeline_count > 0:
            score += 15
        
        # Decision authority is valuable (20 points)
        if signals.get('decision_authority', False):
            score += 20
        
        return min(score, 100)
    
    def _build_context_string(self, lead_context: Dict[str, Any]) -> str:
        """Build context string from lead information.
        
        Internal method to format lead context into a readable string
        for inclusion in LLM prompts.
        
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
        
        if lead_context.get('previous_interest'):
            context_parts.append(f"Previous Interest: {lead_context['previous_interest']}")
        
        return "\n".join(context_parts) if context_parts else "No additional context available"
