import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pytest

from workflows.run_reply_intent import (
    build_context_from_reply,
    handle_reply,
    mock_replies,
    mock_crm
)
from agents.reply_analyzer import ReplyAnalyzer
from agents.agent_core import AgentCore
from memory.memory_manager import memory_manager
from ui.tabs.reply_tab import determine_demo_intent, generate_mock_intent_response

class TestReplyIntentAnalysis(unittest.TestCase):
    """Test suite for reply intent analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear any existing test data
        self.test_lead_id = "test_lead_001"
        
        # Mock qualification data for testing
        self.mock_qualification = {
            "priority": "medium",
            "lead_score": 75,
            "reasoning": "Test qualification reasoning",
            "next_action": "Follow up via email"
        }
        
        # Mock reply data for testing
        self.mock_reply_data = {
            "lead_id": self.test_lead_id,
            "reply_text": "Yes, I'm very interested! Can we schedule a call?",
            "reply_subject": "Re: Test follow-up",
            "sender_email": "test@example.com",
            "timestamp": "2025-05-25 10:00:00"
        }
    
    def test_reply_analyzer_agent_initialization(self):
        """Test that ReplyAnalyzer agent can be initialized properly."""
        llm_config = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 500,
            "api_key": "test-key"
        }
        
        agent_core = AgentCore(llm_config=llm_config)
        reply_analyzer = ReplyAnalyzer(agent_core, memory_manager)
        
        self.assertIsNotNone(reply_analyzer)
        self.assertEqual(reply_analyzer.agent_core, agent_core)
        self.assertEqual(reply_analyzer.memory_manager, memory_manager)
    
    @patch('agents.agent_core.AgentCore.create_llm_chain')
    def test_reply_analyzer_analyze_method(self, mock_create_chain):
        """Test the ReplyAnalyzer analyze method."""
        # Mock the LLM chain response in the expected format
        mock_chain = MagicMock()
        mock_chain.run.return_value = """
Disposition: engaged
Confidence: 95
Sentiment: positive
Urgency: high
Reasoning: The lead explicitly states interest and requests a call
Next Action: Schedule a discovery call within 24 hours
Follow Up Timing: immediate
Intent: meeting_request
        """
        mock_create_chain.return_value = mock_chain

        llm_config = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 500,
            "api_key": "test-key"
        }

        agent_core = AgentCore(llm_config=llm_config)
        reply_analyzer = ReplyAnalyzer(agent_core, memory_manager)

        reply_data = {
            "reply_text": "Yes, I'm very interested! Can we schedule a call?",
            "reply_subject": "Re: Sales Inquiry",
            "sender_email": "test@example.com",
            "lead_id": self.test_lead_id
        }

        lead_context = {
            "name": "Test User",
            "company": "Test Company",
            "previous_context": "Previous qualification: medium priority"
        }

        result = reply_analyzer.analyze(reply_data, lead_context)

        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("disposition", result)
        self.assertIn("confidence", result)
        self.assertIn("sentiment", result)
        self.assertIn("urgency", result)
        self.assertEqual(result["disposition"], "engaged")
        self.assertEqual(result["sentiment"], "positive")
    
    def test_build_context_from_reply_with_qualification(self):
        """Test building context when lead has previous qualification."""
        # Save a test qualification first
        memory_manager.save_qualification(self.test_lead_id, self.mock_qualification)
        
        # Add test lead to mock CRM
        mock_crm[self.test_lead_id] = {
            "name": "Test User",
            "company": "Test Company",
            "email": "test@example.com",
            "interest": "Test interest"
        }
        
        context = build_context_from_reply(self.test_lead_id, self.mock_reply_data)
        
        self.assertEqual(context["lead_id"], self.test_lead_id)
        self.assertEqual(context["name"], "Test User")
        self.assertEqual(context["company"], "Test Company")
        self.assertIn("Previous Qualification", context["previous_context"])
        self.assertIn("medium", context["previous_context"])  # Priority
        self.assertIn("75", context["previous_context"])      # Score
        
        # Cleanup
        if self.test_lead_id in mock_crm:
            del mock_crm[self.test_lead_id]
    
    def test_build_context_from_reply_no_qualification(self):
        """Test building context when lead has no previous qualification."""
        # Use a lead ID that doesn't exist in memory
        test_lead_id = "nonexistent_lead"
        
        mock_crm[test_lead_id] = {
            "name": "New User",
            "company": "New Company", 
            "email": "new@example.com",
            "interest": "New interest"
        }
        
        reply_data = self.mock_reply_data.copy()
        reply_data["lead_id"] = test_lead_id
        
        context = build_context_from_reply(test_lead_id, reply_data)
        
        self.assertEqual(context["lead_id"], test_lead_id)
        self.assertEqual(context["name"], "New User")
        self.assertIn("No previous qualification found", context["previous_context"])
        
        # Cleanup
        if test_lead_id in mock_crm:
            del mock_crm[test_lead_id]
    
    def test_handle_reply_nonexistent_reply(self):
        """Test handling a reply that doesn't exist."""
        result = handle_reply("lead_001", "nonexistent_reply")
        self.assertIsNone(result)
    
    def test_handle_reply_wrong_lead(self):
        """Test handling a reply for the wrong lead."""
        # reply_001 belongs to lead_001, try to use it for lead_002
        result = handle_reply("lead_002", "reply_001")
        self.assertIsNone(result)

def test_determine_demo_intent_cases():
    cases = [
        ("I'm very interested in your solution!", 'interested'),
        ("Can we schedule a meeting next week?", 'meeting_request'),
        ("Can you send more information about pricing?", 'info_request'),
        ("Not interested, please remove me from your list.", 'not_interested'),
        ("I have some concerns about integration.", 'objection'),
        ("Thank you for your email.", 'neutral'),
    ]
    for text, expected in cases:
        assert determine_demo_intent(text) == expected


def test_generate_mock_intent_response_fields():
    lead_data = {"company": "TestCo"}
    for intent in ['interested', 'meeting_request', 'info_request', 'neutral', 'objection', 'not_interested']:
        reply = f"This is a {intent} reply."
        response = generate_mock_intent_response(intent, reply, lead_data)
        # Check that all required fields are present in the response string
        for field in ["DISPOSITION:", "CONFIDENCE:", "SENTIMENT:", "URGENCY:", "REASONING:", "NEXT_ACTION:", "FOLLOW_UP_TIMING:"]:
            assert field in response
        # Check that the company name is in the reasoning
        assert "TestCo" in response

if __name__ == '__main__':
    unittest.main() 