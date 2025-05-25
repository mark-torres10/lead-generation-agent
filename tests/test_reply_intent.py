import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.run_reply_intent import (
    parse_reply_analysis_response,
    build_context_from_reply,
    analyze_reply_intent,
    handle_reply,
    mock_replies,
    mock_crm
)
from memory.memory_manager import memory_manager

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
    
    def test_parse_reply_analysis_response_complete(self):
        """Test parsing a complete LLM response."""
        llm_response = """
        DISPOSITION: engaged
        CONFIDENCE: 95
        SENTIMENT: positive
        URGENCY: high
        REASONING: The lead explicitly states interest and requests a call, indicating strong engagement.
        NEXT_ACTION: Schedule a discovery call within 24 hours
        FOLLOW_UP_TIMING: immediate
        """
        
        result = parse_reply_analysis_response(llm_response)
        
        self.assertEqual(result["disposition"], "engaged")
        self.assertEqual(result["confidence"], 95)
        self.assertEqual(result["sentiment"], "positive")
        self.assertEqual(result["urgency"], "high")
        self.assertIn("explicitly states interest", result["reasoning"])
        self.assertIn("Schedule a discovery call", result["next_action"])
        self.assertEqual(result["follow_up_timing"], "immediate")
    
    def test_parse_reply_analysis_response_partial(self):
        """Test parsing a partial LLM response with missing fields."""
        llm_response = """
        DISPOSITION: maybe
        CONFIDENCE: 60
        REASONING: Lead shows some interest but needs more information.
        """
        
        result = parse_reply_analysis_response(llm_response)
        
        self.assertEqual(result["disposition"], "maybe")
        self.assertEqual(result["confidence"], 60)
        self.assertEqual(result["sentiment"], "neutral")  # Default value
        self.assertEqual(result["urgency"], "medium")     # Default value
        self.assertIn("shows some interest", result["reasoning"])
        self.assertEqual(result["next_action"], "Follow up via email")  # Default
        self.assertEqual(result["follow_up_timing"], "1-week")          # Default
    
    def test_parse_reply_analysis_response_malformed(self):
        """Test parsing a malformed LLM response."""
        llm_response = "This is not a properly formatted response."
        
        result = parse_reply_analysis_response(llm_response)
        
        # Should return default values
        self.assertEqual(result["disposition"], "maybe")
        self.assertEqual(result["confidence"], 70)
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["urgency"], "medium")
        self.assertEqual(result["next_action"], "Follow up via email")
        self.assertEqual(result["follow_up_timing"], "1-week")
    
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
        del mock_crm[test_lead_id]
    
    @patch('experiments.run_reply_intent.get_llm_chain_for_reply_analysis')
    def test_analyze_reply_intent_updates_qualification(self, mock_llm_chain):
        """Test that reply analysis updates existing qualification."""
        # Setup mock LLM response
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {"text": """
            DISPOSITION: engaged
            CONFIDENCE: 90
            SENTIMENT: positive
            URGENCY: high
            REASONING: Strong interest expressed
            NEXT_ACTION: Schedule call
            FOLLOW_UP_TIMING: immediate
        """}
        mock_llm_chain.return_value = mock_chain
        
        # Save initial qualification
        memory_manager.save_qualification(self.test_lead_id, self.mock_qualification)
        
        # Add test lead to mock CRM
        mock_crm[self.test_lead_id] = {
            "name": "Test User",
            "company": "Test Company",
            "email": "test@example.com",
            "interest": "Test interest"
        }
        
        context = build_context_from_reply(self.test_lead_id, self.mock_reply_data)
        result = analyze_reply_intent(context)
        
        # Check analysis result
        self.assertEqual(result["disposition"], "engaged")
        self.assertEqual(result["confidence"], 90)
        self.assertEqual(result["sentiment"], "positive")
        
        # Check that qualification was updated in memory
        updated_qualification = memory_manager.get_qualification(self.test_lead_id)
        self.assertEqual(updated_qualification["lead_disposition"], "engaged")
        self.assertEqual(updated_qualification["disposition_confidence"], 90)
        self.assertEqual(updated_qualification["sentiment"], "positive")
        
        # Cleanup
        del mock_crm[self.test_lead_id]
    
    def test_handle_reply_nonexistent_reply(self):
        """Test handling a reply that doesn't exist."""
        result = handle_reply("lead_001", "nonexistent_reply")
        self.assertIsNone(result)
    
    def test_handle_reply_wrong_lead(self):
        """Test handling a reply for the wrong lead."""
        # reply_001 belongs to lead_001, try to use it for lead_002
        result = handle_reply("lead_002", "reply_001")
        self.assertIsNone(result)
    
    @patch('experiments.run_reply_intent.get_llm_chain_for_reply_analysis')
    def test_handle_reply_success(self, mock_llm_chain):
        """Test successful reply handling end-to-end."""
        # Setup mock LLM response
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {"text": """
            DISPOSITION: engaged
            CONFIDENCE: 85
            SENTIMENT: positive
            URGENCY: medium
            REASONING: Lead shows clear interest and asks for next steps
            NEXT_ACTION: Send product demo link
            FOLLOW_UP_TIMING: 1-week
        """}
        mock_llm_chain.return_value = mock_chain
        
        # Use existing mock data
        result = handle_reply("lead_001", "reply_001")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["disposition"], "engaged")
        self.assertEqual(result["confidence"], 85)
        self.assertEqual(result["sentiment"], "positive")
        
        # Check that CRM was updated
        self.assertEqual(mock_crm["lead_001"]["lead_disposition"], "engaged")
        self.assertEqual(mock_crm["lead_001"]["sentiment"], "positive")
    
    def test_disposition_categories(self):
        """Test that all expected disposition categories are handled."""
        test_cases = [
            ("DISPOSITION: engaged", "engaged"),
            ("DISPOSITION: maybe", "maybe"),
            ("DISPOSITION: disinterested", "disinterested"),
            ("DISPOSITION: ENGAGED", "engaged"),  # Case insensitive
            ("No disposition found", "maybe")     # Default
        ]
        
        for llm_text, expected_disposition in test_cases:
            result = parse_reply_analysis_response(llm_text)
            self.assertEqual(result["disposition"], expected_disposition)
    
    def test_confidence_parsing(self):
        """Test confidence score parsing."""
        test_cases = [
            ("CONFIDENCE: 95", 95),
            ("CONFIDENCE: 0", 0),
            ("CONFIDENCE: 100", 100),
            ("No confidence found", 70)  # Default
        ]
        
        for llm_text, expected_confidence in test_cases:
            result = parse_reply_analysis_response(llm_text)
            self.assertEqual(result["confidence"], expected_confidence)
    
    def test_sentiment_parsing(self):
        """Test sentiment parsing."""
        test_cases = [
            ("SENTIMENT: positive", "positive"),
            ("SENTIMENT: negative", "negative"),
            ("SENTIMENT: neutral", "neutral"),
            ("SENTIMENT: POSITIVE", "positive"),  # Case insensitive
            ("No sentiment found", "neutral")     # Default
        ]
        
        for llm_text, expected_sentiment in test_cases:
            result = parse_reply_analysis_response(llm_text)
            self.assertEqual(result["sentiment"], expected_sentiment)
    
    def test_urgency_parsing(self):
        """Test urgency parsing."""
        test_cases = [
            ("URGENCY: high", "high"),
            ("URGENCY: medium", "medium"),
            ("URGENCY: low", "low"),
            ("URGENCY: HIGH", "high"),    # Case insensitive
            ("No urgency found", "medium") # Default
        ]
        
        for llm_text, expected_urgency in test_cases:
            result = parse_reply_analysis_response(llm_text)
            self.assertEqual(result["urgency"], expected_urgency)
    
    def test_follow_up_timing_parsing(self):
        """Test follow-up timing parsing."""
        test_cases = [
            ("FOLLOW_UP_TIMING: immediate", "immediate"),
            ("FOLLOW_UP_TIMING: 1-week", "1-week"),
            ("FOLLOW_UP_TIMING: 1-month", "1-month"),
            ("FOLLOW_UP_TIMING: 3-months", "3-months"),
            ("FOLLOW_UP_TIMING: none", "none"),
            ("No timing found", "1-week")  # Default
        ]
        
        for llm_text, expected_timing in test_cases:
            result = parse_reply_analysis_response(llm_text)
            self.assertEqual(result["follow_up_timing"], expected_timing)

class TestReplyIntentIntegration(unittest.TestCase):
    """Integration tests for reply intent analysis with SQLite memory."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.test_lead_id = "integration_test_lead"
        
        # Clean up any existing data
        if memory_manager.has_qualification(self.test_lead_id):
            # Note: We don't have a delete method, so we'll work around existing data
            pass
    
    def test_memory_persistence_across_analyses(self):
        """Test that multiple reply analyses are properly stored and retrieved."""
        # Save initial qualification
        initial_qualification = {
            "priority": "medium",
            "lead_score": 70,
            "reasoning": "Initial qualification",
            "next_action": "Follow up"
        }
        memory_manager.save_qualification(self.test_lead_id, initial_qualification)
        
        # Simulate first reply analysis by updating the qualification directly
        first_analysis = {
            "disposition": "maybe",
            "confidence": 60,
            "sentiment": "neutral",
            "urgency": "medium",
            "reasoning": "First reply analysis",
            "next_action": "Send more info",
            "follow_up_timing": "1-week"
        }
        
        # Update qualification with first analysis (matching the actual implementation)
        updated_qualification = initial_qualification.copy()
        updated_qualification.update({
            "lead_disposition": first_analysis["disposition"],
            "disposition_confidence": first_analysis["confidence"],
            "sentiment": first_analysis["sentiment"]
        })
        memory_manager.save_qualification(self.test_lead_id, updated_qualification)
        
        # Add interaction
        memory_manager.add_interaction(self.test_lead_id, "reply_analysis", first_analysis)
        
        # Verify data persistence
        retrieved_qualification = memory_manager.get_qualification(self.test_lead_id)
        self.assertEqual(retrieved_qualification["lead_disposition"], "maybe")
        self.assertEqual(retrieved_qualification["disposition_confidence"], 60)
        
        interactions = memory_manager.get_interaction_history(self.test_lead_id)
        reply_analyses = [i for i in interactions if i["event_type"] == "reply_analysis"]
        self.assertGreaterEqual(len(reply_analyses), 1)

if __name__ == "__main__":
    print("🧪 Running Reply Intent Analysis Tests")
    print("=" * 50)
    
    # Run the tests
    unittest.main(verbosity=2) 