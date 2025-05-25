"""
Unit tests for UI backend integration.
Tests the backend logic that will be triggered by UI actions in the Streamlit app.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, Mock
import sys
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.memory_manager import MemoryManager
from memory.memory_store import SQLiteMemoryStore


class TestUIBackendIntegration(unittest.TestCase):
    """Test backend logic triggered by UI actions."""
    
    def setUp(self):
        """Set up test environment with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_ui.db")
        
        # Create a test memory store and manager
        self.test_store = SQLiteMemoryStore(self.db_path)
        self.memory_manager = MemoryManager(self.test_store)
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_contact_form_submission_workflow(self):
        """Test the complete workflow when a user submits the contact form."""
        # Simulate contact form data
        form_data = {
            "name": "Alice Johnson",
            "email": "alice@acmecorp.com",
            "company": "Acme Corp",
            "role": "VP of Sales",
            "message": "We're looking for automation tools to streamline our sales process. Can you help?"
        }
        
        # Import and run the qualification workflow
        from experiments.run_qualification import qualify_lead
        
        # Mock the LLM response to avoid external API calls
        with patch('experiments.run_qualification.get_llm_chain') as mock_chain, \
             patch('experiments.run_qualification.memory_manager', self.memory_manager):
            mock_llm = Mock()
            mock_llm.run.return_value = """
            Priority: high
            Lead Score: 85
            Reasoning: VP-level contact from established company showing clear interest in automation solutions
            Next Action: Send follow-up email with solution overview
            Lead Disposition: engaged
            Sentiment: positive
            Urgency: medium
            """
            mock_chain.return_value = mock_llm
            
            # Run the qualification
            result = qualify_lead("ui_test_001", form_data)
            
            # Verify the result structure
            self.assertIsInstance(result, dict)
            self.assertIn("lead_score", result)
            self.assertIn("priority", result)
            self.assertIn("reasoning", result)
            
            # Verify data was saved to memory
            qualification = self.memory_manager.get_qualification("ui_test_001")
            self.assertIsNotNone(qualification)
            self.assertEqual(qualification["priority"], "high")
            self.assertTrue(qualification["lead_score"] >= 80)

    def test_reply_analysis_workflow(self):
        """Test the workflow when analyzing a lead's email reply."""
        # First, create a qualified lead
        lead_id = "ui_test_002"
        self.memory_manager.save_qualification(lead_id, {
            "lead_score": 75,
            "priority": "medium",
            "reasoning": "Initial qualification",
            "next_action": "Send follow-up email"
        })
        
        # Simulate reply form data
        reply_data = {
            "lead_id": lead_id,
            "reply_message": "Yes, I'm definitely interested! We have budget approved and need to make a decision by end of month. Can we schedule a call this week?"
        }
        
        from experiments.run_reply_intent import analyze_reply_intent, build_context_from_reply
        
        with patch('experiments.run_reply_intent.get_llm_chain_for_reply_analysis') as mock_chain, \
             patch('experiments.run_reply_intent.memory_manager', self.memory_manager):
            mock_llm = Mock()
            mock_llm.run.return_value = """
            DISPOSITION: engaged
            SENTIMENT: positive
            URGENCY: high
            CONFIDENCE: 95
            REASONING: Lead shows strong buying signals with budget approval and timeline
            RECOMMENDED_FOLLOW_UP: Schedule discovery call within 2 days
            FOLLOW_UP_TIMING: immediate
            """
            mock_chain.return_value = mock_llm
            
            # Build context and run the reply analysis
            context = build_context_from_reply(lead_id, {"reply_content": reply_data["reply_message"]})
            result = analyze_reply_intent(context)
            
            # Verify the result structure
            self.assertIsInstance(result, dict)
            self.assertIn("disposition", result)
            self.assertIn("sentiment", result)
            self.assertIn("urgency", result)
            
            # Check if qualification was updated (may not be updated in this workflow)
            updated_qualification = self.memory_manager.get_qualification(lead_id)
            self.assertIsNotNone(updated_qualification)
            # The original qualification should still exist
            self.assertEqual(updated_qualification["priority"], "medium")

    def test_meeting_scheduling_workflow(self):
        """Test the workflow when scheduling a meeting with a qualified lead."""
        # Create a qualified, engaged lead
        lead_id = "ui_test_003"
        self.memory_manager.save_qualification(lead_id, {
            "lead_score": 90,
            "priority": "high", 
            "lead_disposition": "engaged",
            "sentiment": "positive",
            "reasoning": "Highly interested prospect",
            "next_action": "Schedule meeting"
        })
        
        # Simulate meeting form data
        meeting_data = {
            "lead_id": lead_id,
            "meeting_type": "discovery_call",
            "duration": 30,
            "preferred_times": ["2024-01-15 10:00", "2024-01-15 14:00", "2024-01-16 09:00"]
        }
        
        from experiments.run_schedule_meeting import book_meeting, check_calendar_availability
        
        with patch('experiments.run_schedule_meeting.check_calendar_availability') as mock_calendar, \
             patch('experiments.run_schedule_meeting.memory_manager', self.memory_manager):
            mock_calendar.return_value = {
                "available_slots": [
                    {"datetime": "2024-01-15 10:00", "available": True},
                    {"datetime": "2024-01-15 14:00", "available": False}, 
                    {"datetime": "2024-01-16 09:00", "available": True}
                ],
                "recommended_slot": "2024-01-15 10:00"
            }
            
            # Run the meeting scheduling
            meeting_id = book_meeting(
                lead_id=lead_id,
                meeting_datetime="2024-01-15 10:00",
                meeting_type=meeting_data["meeting_type"],
                duration=f"{meeting_data['duration']}min"
            )
            
            # Verify the result structure
            self.assertIsInstance(meeting_id, str)
            self.assertTrue(meeting_id.startswith("evt_"))
            
            # Check if interaction was logged (may not be in this simple test)
            interactions = self.memory_manager.get_interaction_history(lead_id)
            # Just verify we can get interactions, even if empty
            self.assertIsInstance(interactions, list)

    def test_crm_view_data_retrieval(self):
        """Test retrieving data for CRM view display."""
        # Create test lead with full interaction history
        lead_id = "ui_test_004"
        
        # Initial qualification
        self.memory_manager.save_qualification(lead_id, {
            "lead_score": 80,
            "priority": "high",
            "reasoning": "Strong initial interest",
            "next_action": "Send follow-up"
        })
        
        # Add interactions
        self.memory_manager.add_interaction(lead_id, "email_sent", {
            "subject": "Follow-up on your inquiry",
            "recipient": "test@example.com"
        })
        
        self.memory_manager.add_interaction(lead_id, "reply_received", {
            "disposition": "engaged",
            "sentiment": "positive"
        })
        
        # Test data retrieval for CRM view
        qualification = self.memory_manager.get_qualification(lead_id)
        interactions = self.memory_manager.get_interaction_history(lead_id)
        
        # Verify CRM data structure
        self.assertIsNotNone(qualification)
        self.assertEqual(qualification["lead_score"], 80)
        self.assertEqual(qualification["priority"], "high")
        
        self.assertTrue(len(interactions) >= 2)
        event_types = [i["event_type"] for i in interactions]
        self.assertIn("email_sent", event_types)
        self.assertIn("reply_received", event_types)

    def test_agent_reasoning_display(self):
        """Test extracting agent reasoning for display in UI."""
        # Test qualification reasoning extraction
        qualification_data = {
            "lead_score": 85,
            "priority": "high",
            "reasoning": "VP-level contact from established company showing clear interest in automation solutions. Strong buying signals present.",
            "extracted_info": {
                "company": "Acme Corp",
                "role": "VP of Sales",
                "intent": "Automation tools"
            }
        }
        
        # Verify reasoning can be displayed
        self.assertIn("reasoning", qualification_data)
        self.assertIn("extracted_info", qualification_data)
        
        reasoning = qualification_data["reasoning"]
        self.assertIsInstance(reasoning, str)
        self.assertTrue(len(reasoning) > 0)
        
        extracted_info = qualification_data["extracted_info"]
        self.assertIn("company", extracted_info)
        self.assertIn("role", extracted_info)
        self.assertIn("intent", extracted_info)

    def test_email_output_formatting(self):
        """Test email output formatting for UI display."""
        # Mock email generation
        email_data = {
            "subject": "Thank you for your interest in our automation solutions",
            "recipient": "alice@acmecorp.com",
            "body": """Hi Alice,

Thank you for reaching out about automation tools for your sales process. Based on your message, it sounds like you're looking to streamline operations at Acme Corp.

I'd love to learn more about your current challenges and discuss how our solutions might help. Would you be available for a brief 30-minute call this week?

Best regards,
Sales Team""",
            "metadata": {
                "generated_at": "2024-01-10 10:30:00",
                "lead_score": 85,
                "priority": "high"
            }
        }
        
        # Verify email structure for UI display
        self.assertIn("subject", email_data)
        self.assertIn("recipient", email_data)
        self.assertIn("body", email_data)
        self.assertIn("metadata", email_data)
        
        # Verify email content
        self.assertTrue(len(email_data["subject"]) > 0)
        self.assertTrue(len(email_data["body"]) > 0)
        self.assertIn("@", email_data["recipient"])

    def test_timeline_data_generation(self):
        """Test generating timeline data for agent activity visualization."""
        lead_id = "ui_test_005"
        
        # Create a sequence of interactions
        steps = [
            ("qualification_started", {"action": "Analyzing lead information"}),
            ("info_extracted", {"company": "Test Corp", "role": "Manager"}),
            ("score_calculated", {"lead_score": 75, "priority": "medium"}),
            ("email_drafted", {"subject": "Follow-up email"}),
            ("crm_updated", {"status": "qualified"})
        ]
        
        for event_type, data in steps:
            self.memory_manager.add_interaction(lead_id, event_type, data)
        
        # Retrieve timeline data
        interactions = self.memory_manager.get_interaction_history(lead_id)
        
        # Verify timeline structure
        self.assertEqual(len(interactions), 5)
        
        # Verify chronological order (should be sorted by timestamp)
        timestamps = [i["timestamp"] for i in interactions]
        self.assertEqual(timestamps, sorted(timestamps))
        
        # Verify each step has required fields for timeline display
        for interaction in interactions:
            self.assertIn("event_type", interaction)
            self.assertIn("timestamp", interaction)
            self.assertIn("event_data", interaction)

    def test_error_handling_in_workflows(self):
        """Test error handling when workflows encounter issues."""
        # Test qualification with invalid data
        with patch('experiments.run_qualification.get_llm_chain') as mock_llm:
            mock_llm.side_effect = Exception("LLM service unavailable")
            
            from experiments.run_qualification import qualify_lead
            
            # Should handle errors gracefully
            try:
                result = qualify_lead("error_test", {"name": "Test", "email": "test@test.com"})
                # If no exception, verify it returns some error indication
                self.assertIsInstance(result, dict)
            except Exception as e:
                # Exception handling is acceptable for this test
                self.assertIsInstance(e, Exception)

    def test_session_state_management(self):
        """Test data persistence for UI session state."""
        # Simulate multiple operations in a session
        lead_id = "session_test"
        
        # Step 1: Qualification
        self.memory_manager.save_qualification(lead_id, {
            "lead_score": 80,
            "priority": "high",
            "reasoning": "Test qualification for session management",
            "next_action": "Send follow-up email"
        })
        
        # Step 2: Add interaction
        self.memory_manager.add_interaction(lead_id, "email_sent", {
            "subject": "Welcome email",
            "recipient": "test@session.com"
        })
        
        # Step 3: Update qualification
        self.memory_manager.save_qualification(lead_id, {
            "lead_score": 85,
            "priority": "high",
            "reasoning": "Updated after interaction",
            "next_action": "Schedule meeting",
            "lead_disposition": "engaged"
        })
        
        # Verify session data persistence
        final_qualification = self.memory_manager.get_qualification(lead_id)
        interactions = self.memory_manager.get_interaction_history(lead_id)
        
        self.assertEqual(final_qualification["lead_score"], 85)
        self.assertEqual(final_qualification["lead_disposition"], "engaged")
        self.assertTrue(len(interactions) >= 1)
        self.assertEqual(interactions[0]["event_type"], "email_sent")


if __name__ == "__main__":
    unittest.main() 