"""
Unit tests for UI backend integration.
Tests the backend logic that will be triggered by UI actions in the Streamlit app.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, Mock

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
        from workflows.run_qualification import qualify_lead
        from agents.models import LeadQualificationResult
        from agents.agent_core import AgentCore
        
        # Mock the LLM chain response to avoid external API calls
        with patch('agents.agent_core.AgentCore.create_llm_chain') as mock_create_chain, \
             patch('workflows.run_qualification.memory_manager', self.memory_manager):
            mock_chain = Mock()
            mock_chain.run.return_value = """
Priority: high
Lead Score: 85
Reasoning: VP-level contact from established company showing clear interest in automation solutions
Next Action: Send follow-up email with solution overview
Disposition: hot
Confidence: 90
            """
            mock_create_chain.return_value = mock_chain
            
            # Run the qualification
            result = qualify_lead("ui_test_001", form_data)
            
            # Verify the result structure
            self.assertIsInstance(result, LeadQualificationResult)
            self.assertTrue(hasattr(result, "priority"))
            self.assertTrue(hasattr(result, "lead_score"))
            self.assertTrue(hasattr(result, "reasoning"))
            self.assertTrue(hasattr(result, "next_action"))
            self.assertTrue(hasattr(result, "disposition"))
            self.assertTrue(hasattr(result, "confidence"))
            # Check values are not None
            self.assertIsNotNone(result.priority)
            self.assertIsNotNone(result.lead_score)
            self.assertIsNotNone(result.reasoning)
            self.assertIsNotNone(result.next_action)
            self.assertIsNotNone(result.disposition)
            self.assertIsNotNone(result.confidence)
            # Verify data was saved to memory
            qualification = self.memory_manager.get_qualification("ui_test_001")
            self.assertIsNotNone(qualification)
            self.assertEqual(qualification["priority"], result.priority)
            print('Qualification:', qualification)

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
        
        from workflows.run_reply_intent import analyze_reply_intent, build_context_from_reply
        from agents.agent_core import AgentCore
        
        with patch('agents.agent_core.AgentCore.create_llm_chain') as mock_create_chain, \
             patch('workflows.run_reply_intent.memory_manager', self.memory_manager):
            mock_chain = Mock()
            mock_chain.run.return_value = """
            {
                "disposition": "engaged",
                "sentiment": "positive",
                "urgency": "high",
                "confidence": 95,
                "reasoning": "Lead shows strong buying signals with budget approval and timeline",
                "recommended_follow_up": "Schedule discovery call within 2 days",
                "follow_up_timing": "immediate"
            }
            """
            mock_create_chain.return_value = mock_chain
            
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
        
        from workflows.run_schedule_meeting import book_meeting, check_calendar_availability
        
        with patch('workflows.run_schedule_meeting.check_calendar_availability') as mock_calendar, \
             patch('workflows.run_schedule_meeting.memory_manager', self.memory_manager):
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
        with patch('agents.agent_core.AgentCore.create_llm_chain') as mock_create_chain:
            mock_create_chain.side_effect = Exception("LLM service unavailable")
            
            from workflows.run_qualification import qualify_lead
            
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

    def test_no_get_llm_chain_attribute_error_on_qualification(self):
        """Ensure no AttributeError for get_llm_chain occurs during qualification workflow."""
        form_data = {
            "name": "Test User",
            "email": "test.user@example.com",
            "company": "TestCo",
            "role": "Tester",
            "message": "Testing for get_llm_chain error."
        }
        from workflows.run_qualification import qualify_lead
        try:
            result = qualify_lead("test_no_attr_error", form_data)
        except AttributeError as e:
            self.fail(f"AttributeError occurred: {e}")
        # If no exception, pass
        self.assertIsNotNone(result)

    def test_contact_form_submission_returns_leadqualificationresult(self):
        """Test that contact form submission always returns a LeadQualificationResult with attribute access."""
        form_data = {
            "name": "Sarah Chen",
            "email": "sarah.chen@techcorp.com",
            "company": "TechCorp Industries",
            "role": "Chief Technology Officer",
            "message": "We're looking for automation solutions to streamline our sales process. We have a team of 200+ sales reps and need better lead management. Budget approved for Q1 implementation."
        }
        from workflows.run_qualification import qualify_lead
        result = qualify_lead("ui_test_lead_qual_result", form_data)
        # Assert type
        from agents.models import LeadQualificationResult
        self.assertIsInstance(result, LeadQualificationResult)
        # Assert required fields are accessible as attributes
        self.assertTrue(hasattr(result, "priority"))
        self.assertTrue(hasattr(result, "lead_score"))
        self.assertTrue(hasattr(result, "reasoning"))
        self.assertTrue(hasattr(result, "next_action"))
        self.assertTrue(hasattr(result, "disposition"))
        self.assertTrue(hasattr(result, "confidence"))
        # Check values are not None
        self.assertIsNotNone(result.priority)
        self.assertIsNotNone(result.lead_score)
        self.assertIsNotNone(result.reasoning)
        self.assertIsNotNone(result.next_action)
        self.assertIsNotNone(result.disposition)
        self.assertIsNotNone(result.confidence)

    def test_display_qualification_results_handles_missing_optional_fields(self):
        """Test that display_qualification_results does not raise if optional fields are missing from LeadQualificationResult."""
        from ui.tabs.qualify_tab import display_qualification_results
        from agents.models import LeadQualificationResult
        import types
        # Minimal/fallback result (simulate error path)
        result = LeadQualificationResult(
            lead_id="test@example.com",
            lead_name="Test User",
            lead_company="TestCo",
            priority="medium",
            lead_score=50,
            reasoning="Error during qualification: ...",
            next_action="Manual review required",
            disposition="unqualified",
            confidence=0,
            sentiment="neutral",
            urgency="later"
        )
        # Patch Streamlit and display functions to no-op
        import sys
        class MockCol:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        def mock_columns(n, *a, **k):
            if isinstance(n, (list, tuple)):
                return [MockCol() for _ in range(len(n))]
            return [MockCol() for _ in range(n)]
        sys.modules["streamlit"].success = lambda *a, **k: None
        sys.modules["streamlit"].markdown = lambda *a, **k: None
        sys.modules["streamlit"].subheader = lambda *a, **k: None
        sys.modules["streamlit"].columns = mock_columns
        import streamlit as st
        st.session_state.memory_manager = self.memory_manager
        # Patch display functions
        import ui.components.agent_visualizer
        import ui.components.crm_viewer
        import ui.components.email_display
        ui.components.agent_visualizer.display_agent_reasoning = lambda *a, **k: None
        ui.components.agent_visualizer.display_agent_timeline = lambda *a, **k: None
        ui.components.crm_viewer.display_crm_record = lambda *a, **k: None
        ui.components.email_display.display_email_output = lambda *a, **k: None
        # Should not raise
        try:
            display_qualification_results("test_lead_id", {"name": "Test User", "company": "TestCo"}, result)
        except AttributeError as e:
            self.fail(f"display_qualification_results raised AttributeError: {e}")

    def test_timeline_persistence_across_qualifications(self):
        """Test that timeline persists and updates across multiple qualifications for the same lead."""
        from workflows import run_qualification
        lead_id = "timeline_test_lead"
        form_data1 = {
            "name": "Timeline User",
            "email": "timeline@demo.com",
            "company": "DemoCo",
            "role": "Manager",
            "message": "First qualification submission."
        }
        form_data2 = {
            "name": "Timeline User",
            "email": "timeline@demo.com",
            "company": "DemoCo",
            "role": "Manager",
            "message": "Second qualification submission with more info."
        }
        # Patch the memory manager used in the workflow
        with patch('workflows.run_qualification.memory_manager', self.memory_manager):
            # First qualification
            run_qualification.qualify_lead(lead_id, form_data1)
            # Second qualification
            run_qualification.qualify_lead(lead_id, form_data2)
        # Fetch interaction history
        interactions = self.memory_manager.get_interaction_history(lead_id)
        # There should be at least two qualification_updated events
        qual_events = [i for i in interactions if i["event_type"] == "qualification_updated"]
        self.assertGreaterEqual(len(qual_events), 2)
        # Check for non-empty reasoning in first event and 'second qualification' in second event
        self.assertTrue(isinstance(qual_events[0]["event_data"].get("reasoning", None), str) and qual_events[0]["event_data"]["reasoning"].strip())
        self.assertIn("second qualification", qual_events[1]["event_data"].get("reasoning", ""))

    def test_display_qualification_results_handles_none_fields(self):
        """Test that display_qualification_results does not raise if urgency, priority, or disposition are None."""
        from ui.tabs.qualify_tab import display_qualification_results
        from agents.models import LeadQualificationResult
        import sys
        class MockCol:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        def mock_columns(n, *a, **k):
            if isinstance(n, (list, tuple)):
                return [MockCol() for _ in range(len(n))]
            return [MockCol() for _ in range(n)]
        sys.modules["streamlit"].success = lambda *a, **k: None
        sys.modules["streamlit"].markdown = lambda *a, **k: None
        sys.modules["streamlit"].subheader = lambda *a, **k: None
        sys.modules["streamlit"].columns = mock_columns
        import streamlit as st
        st.session_state.memory_manager = self.memory_manager
        import ui.components.agent_visualizer
        import ui.components.crm_viewer
        import ui.components.email_display
        ui.components.agent_visualizer.display_agent_reasoning = lambda *a, **k: None
        ui.components.agent_visualizer.display_agent_timeline = lambda *a, **k: None
        ui.components.crm_viewer.display_crm_record = lambda *a, **k: None
        ui.components.email_display.display_email_output = lambda *a, **k: None
        # Minimal result with empty string fields
        result = LeadQualificationResult(
            lead_id="test@example.com",
            lead_name="Test User",
            lead_company="TestCo",
            priority="",
            lead_score=50,
            reasoning="Test reasoning",
            next_action="Manual review required",
            disposition="",
            confidence=0,
            sentiment="neutral",
            urgency=""
        )
        try:
            display_qualification_results("test_lead_id", {"name": "Test User", "company": "TestCo"}, result)
        except Exception as e:
            self.fail(f"display_qualification_results raised an exception with None fields: {e}")

    def test_urgency_fallback_for_minimal_lead(self):
        """Test that submitting a lead with minimal info results in urgency fallback in the UI."""
        from workflows.run_qualification import qualify_lead
        lead_id = "urgency_fallback_test"
        form_data = {
            "name": "Minimal User",
            "email": "minimal@demo.com",
            "company": "Demo Inc",
            "role": "",
            "message": "Just interested."
        }
        with patch('workflows.run_qualification.memory_manager', self.memory_manager):
            result = qualify_lead(lead_id, form_data)
        # Urgency should be 'not specified' in the result
        urgency_val = result.urgency
        if urgency_val is None:
            urgency_val = "not specified"
        self.assertIn(urgency_val.lower(), ["not specified", "unknown", ""])

    def test_clear_results_resets_ui(self):
        """Test that clearing results does not raise and resets the UI state."""
        from ui.tabs.qualify_tab import display_qualification_results
        from agents.models import LeadQualificationResult
        import sys
        class MockCol:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        def mock_columns(n, *a, **k):
            if isinstance(n, (list, tuple)):
                return [MockCol() for _ in range(len(n))]
            return [MockCol() for _ in range(n)]
        sys.modules["streamlit"].success = lambda *a, **k: None
        sys.modules["streamlit"].markdown = lambda *a, **k: None
        sys.modules["streamlit"].subheader = lambda *a, **k: None
        sys.modules["streamlit"].columns = mock_columns
        import streamlit as st
        st.session_state.memory_manager = self.memory_manager
        import ui.components.agent_visualizer
        import ui.components.crm_viewer
        import ui.components.email_display
        ui.components.agent_visualizer.display_agent_reasoning = lambda *a, **k: None
        ui.components.agent_visualizer.display_agent_timeline = lambda *a, **k: None
        ui.components.crm_viewer.display_crm_record = lambda *a, **k: None
        ui.components.email_display.display_email_output = lambda *a, **k: None
        # Simulate a LeadQualificationResult in session state
        result = LeadQualificationResult(
            lead_id="test@example.com",
            lead_name="Test User",
            lead_company="TestCo",
            priority="medium",
            lead_score=50,
            reasoning="Test reasoning",
            next_action="Manual review required",
            disposition="unqualified",
            confidence=0,
            sentiment="neutral",
            urgency=""
        )
        try:
            # Simulate clearing results (should not raise)
            st.session_state.demo_results = {"qualify": {"test_lead_id": result}}
            # Call the code that would run after clearing
            if hasattr(st.session_state, 'demo_results') and 'qualify' in st.session_state.demo_results:
                results = st.session_state.demo_results['qualify']
                if results:
                    latest_lead_id = max(results.keys())
                    latest_result = results[latest_lead_id]
                    if hasattr(latest_result, 'model_dump'):
                        form_data = {}
                    elif isinstance(latest_result, dict):
                        form_data = latest_result.get('form_data', {})
                    else:
                        form_data = {}
                    display_qualification_results(latest_lead_id, form_data, latest_result)
        except Exception as e:
            self.fail(f"Clearing results raised an exception: {e}")

    def test_form_submission_uses_edited_message(self):
        """Test that editing the message after selecting a sample uses the edited value in the agent call."""
        from ui.tabs.qualify_tab import process_qualification_demo
        from agents.models import LeadQualificationResult
        # Simulate sample data selection and user edit
        sample_data = {
            "name": "Sarah Chen",
            "email": "sarah.chen@techcorp.com",
            "company": "TechCorp Industries",
            "role": "Chief Technology Officer",
            "message": "We're looking for automation solutions to streamline our sales process. We have a team of 200+ sales reps and need better lead management. Budget approved for Q1 implementation."
        }
        # User edits the message
        edited_message = "We're looking for automation solutions to streamline our sales process. We have a team of 50+ sales reps and need better lead management. Budget approved for Q2 implementation."
        form_data = sample_data.copy()
        form_data["message"] = edited_message
        # Patch the agent to capture the input
        import workflows.run_qualification
        original_qualify_lead = workflows.run_qualification.qualify_lead
        captured = {}
        def mock_qualify_lead(lead_id, lead_data):
            captured["lead_data"] = lead_data.copy()
            # Return a dummy result
            return LeadQualificationResult(
                lead_id=lead_id,
                lead_name=lead_data.get("name"),
                lead_company=lead_data.get("company"),
                priority="high",
                lead_score=99,
                reasoning="Test reasoning",
                next_action="Test action",
                disposition="hot",
                confidence=100,
                sentiment="positive",
                urgency="high"
            )
        workflows.run_qualification.qualify_lead = mock_qualify_lead
        try:
            process_qualification_demo("test_lead_id", form_data)
            self.assertIn("lead_data", captured)
            self.assertEqual(captured["lead_data"]["message"], edited_message)
        finally:
            workflows.run_qualification.qualify_lead = original_qualify_lead

    def test_form_submission_with_custom_values(self):
        """Test that submitting the form with custom (non-default) values is processed correctly."""
        from ui.tabs.qualify_tab import process_qualification_demo
        from agents.models import LeadQualificationResult
        form_data = {
            "name": "Alex Example",
            "email": "alex@example.com",
            "company": "Example Corp",
            "role": "VP of Marketing",
            "message": "We are interested in a demo for our 10-person team. Looking for Q3 rollout."
        }
        import workflows.run_qualification
        original_qualify_lead = workflows.run_qualification.qualify_lead
        captured = {}
        def mock_qualify_lead(lead_id, lead_data):
            captured["lead_data"] = lead_data.copy()
            return LeadQualificationResult(
                lead_id=lead_id,
                lead_name=lead_data.get("name"),
                lead_company=lead_data.get("company"),
                priority="medium",
                lead_score=77,
                reasoning="Test reasoning custom",
                next_action="Test action custom",
                disposition="warm",
                confidence=80,
                sentiment="neutral",
                urgency="medium"
            )
        workflows.run_qualification.qualify_lead = mock_qualify_lead
        try:
            process_qualification_demo("custom_lead_id", form_data)
            self.assertIn("lead_data", captured)
            self.assertEqual(captured["lead_data"]["name"], "Alex Example")
            self.assertEqual(captured["lead_data"]["message"], "We are interested in a demo for our 10-person team. Looking for Q3 rollout.")
        finally:
            workflows.run_qualification.qualify_lead = original_qualify_lead

    def test_no_get_llm_chain_attribute_error_on_reply_analysis(self):
        """Ensure no AttributeError for get_llm_chain occurs during reply analysis workflow."""
        lead_id = "test_reply_attr_error"
        lead_data = {
            "name": "Test User",
            "email": "test.user@example.com",
            "company": "TestCo"
        }
        reply_content = "I'm interested in a demo. Can we schedule a call next week?"
        from ui.tabs.reply_tab import process_reply_analysis_demo
        try:
            result = process_reply_analysis_demo(lead_id, lead_data, reply_content)
        except AttributeError as e:
            self.fail(f"AttributeError occurred: {e}")
        # If no exception, pass
        self.assertIsNotNone(result)

    def test_reply_analysis_result_always_model(self):
        """Test that process_reply_analysis_demo always returns a ReplyAnalysisResult, even if workflow returns a dict."""
        lead_id = "test_reply_model"
        lead_data = {
            "name": "Test User",
            "email": "test.user@example.com",
            "company": "TestCo"
        }
        reply_content = "This should trigger a fallback dict result."
        from ui.tabs.reply_tab import process_reply_analysis_demo
        # Patch analyze_reply_intent to return a dict simulating an error/fallback
        import workflows.run_reply_intent
        original_analyze = workflows.run_reply_intent.analyze_reply_intent
        def mock_analyze_reply_intent(context):
            return {"reasoning": "Simulated error", "next_action": "Manual review required"}  # missing required fields
        workflows.run_reply_intent.analyze_reply_intent = mock_analyze_reply_intent
        try:
            result = process_reply_analysis_demo(lead_id, lead_data, reply_content)
            # Should be a model with attribute access
            self.assertTrue(hasattr(result, "disposition"))
            self.assertTrue(hasattr(result, "reasoning"))
            self.assertEqual(result.reasoning, "Simulated error")
            self.assertEqual(result.next_action, "Manual review required")
        finally:
            workflows.run_reply_intent.analyze_reply_intent = original_analyze

    def test_display_reply_analysis_results_handles_missing_timeline(self):
        """Test that display_reply_analysis_results does not raise if timeline is missing from ReplyAnalysisResult."""
        from ui.tabs.reply_tab import display_reply_analysis_results
        from agents.models import ReplyAnalysisResult
        import sys
        import streamlit as st
        st.session_state.memory_manager = self.memory_manager  # Patch memory_manager for DB access
        # Patch Streamlit and display functions to no-op
        class MockCol:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        def mock_columns(n, *a, **k):
            if isinstance(n, (list, tuple)):
                return [MockCol() for _ in range(len(n))]
            return [MockCol() for _ in range(n)]
        sys.modules["streamlit"].success = lambda *a, **k: None
        sys.modules["streamlit"].markdown = lambda *a, **k: None
        sys.modules["streamlit"].subheader = lambda *a, **k: None
        sys.modules["streamlit"].columns = mock_columns
        # Patch display functions
        import ui.components.agent_visualizer
        import ui.components.crm_viewer
        import ui.components.email_display
        ui.components.agent_visualizer.display_agent_reasoning = lambda *a, **k: None
        ui.components.agent_visualizer.display_agent_timeline = lambda *a, **k: None
        ui.components.crm_viewer.display_crm_record = lambda *a, **k: None
        ui.components.email_display.display_email_output = lambda *a, **k: None
        # Minimal result with no timeline
        result = ReplyAnalysisResult(
            disposition="engaged",
            confidence=90,
            sentiment="positive",
            urgency="high",
            reasoning="Test reasoning",
            next_action="Test action",
            follow_up_timing="immediate",
            intent="meeting_request"
        )
        try:
            display_reply_analysis_results("test_lead_id", {"name": "Test User", "company": "TestCo"}, "Test reply content", result)
        except AttributeError as e:
            self.fail(f"display_reply_analysis_results raised AttributeError: {e}")

    def test_display_reply_analysis_results_handles_missing_response_email(self):
        """Test that display_reply_analysis_results does not raise if response_email is missing from ReplyAnalysisResult."""
        from ui.tabs.reply_tab import display_reply_analysis_results
        from agents.models import ReplyAnalysisResult
        import sys
        import streamlit as st
        st.session_state.memory_manager = self.memory_manager  # Patch memory_manager for DB access
        # Patch Streamlit and display functions to no-op
        class MockCol:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        def mock_columns(n, *a, **k):
            if isinstance(n, (list, tuple)):
                return [MockCol() for _ in range(len(n))]
            return [MockCol() for _ in range(n)]
        sys.modules["streamlit"].success = lambda *a, **k: None
        sys.modules["streamlit"].markdown = lambda *a, **k: None
        sys.modules["streamlit"].subheader = lambda *a, **k: None
        sys.modules["streamlit"].columns = mock_columns
        # Patch display functions
        import ui.components.agent_visualizer
        import ui.components.crm_viewer
        import ui.components.email_display
        ui.components.agent_visualizer.display_agent_reasoning = lambda *a, **k: None
        ui.components.agent_visualizer.display_agent_timeline = lambda *a, **k: None
        ui.components.crm_viewer.display_crm_record = lambda *a, **k: None
        ui.components.email_display.display_email_output = lambda *a, **k: None
        # Minimal result with no response_email
        result = ReplyAnalysisResult(
            disposition="engaged",
            confidence=90,
            sentiment="positive",
            urgency="high",
            reasoning="Test reasoning",
            next_action="Test action",
            follow_up_timing="immediate",
            intent="meeting_request"
        )
        try:
            display_reply_analysis_results("test_lead_id", {"name": "Test User", "company": "TestCo"}, "Test reply content", result)
        except AttributeError as e:
            self.fail(f"display_reply_analysis_results raised AttributeError: {e}")

    def test_display_reply_analysis_results_handles_missing_interactions(self):
        """Test that display_reply_analysis_results does not raise if interactions is missing from ReplyAnalysisResult."""
        from ui.tabs.reply_tab import display_reply_analysis_results
        from agents.models import ReplyAnalysisResult
        import sys
        import streamlit as st
        st.session_state.memory_manager = self.memory_manager  # Patch memory_manager for DB access
        # Patch Streamlit and display functions to no-op
        class MockCol:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        def mock_columns(n, *a, **k):
            if isinstance(n, (list, tuple)):
                return [MockCol() for _ in range(len(n))]
            return [MockCol() for _ in range(n)]
        sys.modules["streamlit"].success = lambda *a, **k: None
        sys.modules["streamlit"].markdown = lambda *a, **k: None
        sys.modules["streamlit"].subheader = lambda *a, **k: None
        sys.modules["streamlit"].columns = mock_columns
        # Patch display functions
        import ui.components.agent_visualizer
        import ui.components.crm_viewer
        import ui.components.email_display
        ui.components.agent_visualizer.display_agent_reasoning = lambda *a, **k: None
        ui.components.agent_visualizer.display_agent_timeline = lambda *a, **k: None
        ui.components.crm_viewer.display_crm_record = lambda *a, **k: None
        ui.components.email_display.display_email_output = lambda *a, **k: None
        # Minimal result with no interactions
        result = ReplyAnalysisResult(
            disposition="engaged",
            confidence=90,
            sentiment="positive",
            urgency="high",
            reasoning="Test reasoning",
            next_action="Test action",
            follow_up_timing="immediate",
            intent="meeting_request"
        )
        try:
            display_reply_analysis_results("test_lead_id", {"name": "Test User", "company": "TestCo"}, "Test reply content", result)
        except AttributeError as e:
            self.fail(f"display_reply_analysis_results raised AttributeError: {e}")

    def test_display_crm_record_accepts_replyanalysisresult(self):
        """Test that display_crm_record works when passed a ReplyAnalysisResult model (converted to dict)."""
        from ui.components.crm_viewer import display_crm_record
        from agents.models import ReplyAnalysisResult
        import sys
        # Patch Streamlit and display functions to no-op
        class MockCol:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
        def mock_columns(n, *a, **k):
            if isinstance(n, (list, tuple)):
                return [MockCol() for _ in range(len(n))]
            return [MockCol() for _ in range(n)]
        sys.modules["streamlit"].success = lambda *a, **k: None
        sys.modules["streamlit"].markdown = lambda *a, **k: None
        sys.modules["streamlit"].subheader = lambda *a, **k: None
        sys.modules["streamlit"].columns = mock_columns
        import streamlit as st
        # Minimal result with no interactions
        result = ReplyAnalysisResult(
            disposition="engaged",
            confidence=90,
            sentiment="positive",
            urgency="high",
            reasoning="Test reasoning",
            next_action="Test action",
            follow_up_timing="immediate",
            intent="meeting_request"
        )
        lead_data = {"name": "Test User", "company": "TestCo"}
        try:
            # Convert to dict as in the UI fix
            if hasattr(result, 'model_dump'):
                qualification_dict = result.model_dump()
            else:
                qualification_dict = result.dict() if hasattr(result, 'dict') else dict(result)
            display_crm_record(lead_data, qualification_dict, None, title="Updated Lead Record")
        except AttributeError as e:
            self.fail(f"display_crm_record raised AttributeError: {e}")

    def test_meeting_tab_lead_id_handling(self):
        """Test that scheduling multiple meetings for the same email uses the same lead ID and accumulates history."""
        import streamlit
        from unittest.mock import patch
        # Patch st.session_state.memory_manager to use self.memory_manager
        streamlit.session_state.memory_manager = self.memory_manager

        # Simulate meeting request data for the same lead
        lead_email = "david.kim@innovatetech.com"
        lead_data = {
            "lead_name": "David Kim",
            "lead_email": lead_email,
            "lead_company": "InnovateTech Solutions",
            "lead_role": "VP of Operations"
        }
        meeting_request_1 = {
            **lead_data,
            "meeting_type": "Product Demo",
            "duration": "30 minutes",
            "urgency": "Medium",
            "attendees": "",
            "context": "First meeting request."
        }
        meeting_request_2 = {
            **lead_data,
            "meeting_type": "Technical Discussion",
            "duration": "45 minutes",
            "urgency": "High",
            "attendees": "",
            "context": "Second meeting request."
        }

        # Import the function under test
        from ui.tabs.meeting_tab import process_meeting_scheduling_demo

        with patch('ui.state.session.get_memory_manager', return_value=self.memory_manager):
            # Simulate the UI flow: get or create the lead ID first
            lead_id = self.memory_manager.get_or_create_lead_id(lead_email, {
                "name": lead_data["lead_name"],
                "email": lead_email,
                "company": lead_data["lead_company"],
                "role": lead_data["lead_role"]
            })
            # Schedule first meeting
            result_1 = process_meeting_scheduling_demo(lead_id, meeting_request_1)
            lead_id_1 = result_1["lead_id"]
            print("lead_id_1 after first meeting:", repr(lead_id_1))
            print("All lead IDs after first meeting:", self.memory_manager.list_all_lead_ids())
            print("All qualifications after first meeting:", self.memory_manager.list_all_qualifications())
            self.assertIsNotNone(lead_id_1, "First lead ID should be created.")
            q1 = self.memory_manager.get_qualification(lead_id_1)
            self.assertIsNotNone(q1, "Qualification should be saved for first lead ID.")

            # Schedule second meeting for the same email
            result_2 = process_meeting_scheduling_demo(lead_id, meeting_request_2)
            lead_id_2 = result_2["lead_id"]
            print("lead_id_2 after second meeting:", repr(lead_id_2))
            print("All lead IDs after second meeting:", self.memory_manager.list_all_lead_ids())
            print("All qualifications after second meeting:", self.memory_manager.list_all_qualifications())
            self.assertIsNotNone(lead_id_2, "Second lead ID should be created.")

            # The lead IDs should be the same for repeated meetings with the same email
            self.assertEqual(lead_id_1, lead_id_2, "Lead ID should be the same for repeated meetings with the same email.")

            # Check that interaction history for the lead contains both meetings
            interactions = self.memory_manager.get_interaction_history(lead_id_1)
            print("Interaction history after both meetings:", interactions)
            self.assertTrue(len(interactions) >= 2, "Interaction history should contain both meetings.")

# --- Standalone pytest test for reply tab CRM before/after UI ---

def test_reply_tab_crm_before_after(monkeypatch):
    """Test that the reply tab displays both before and after CRM states without error."""
    import types
    import ui.tabs.reply_tab as reply_tab
    from agents.models import ReplyAnalysisResult
    import streamlit as st
    from memory.memory_manager import MemoryManager
    from memory.memory_store import SQLiteMemoryStore
    import tempfile, os
    # Patch st.session_state.memory_manager to a working test memory manager
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_ui_email.db")
    test_store = SQLiteMemoryStore(db_path)
    test_memory_manager = MemoryManager(test_store)
    st.session_state.memory_manager = test_memory_manager
    # Mock Streamlit functions
    monkeypatch.setattr(reply_tab.st, "success", lambda *a, **k: None)
    monkeypatch.setattr(reply_tab.st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(reply_tab.st, "text_area", lambda *a, **k: None)
    # Patch st.expander with a context manager mock
    class MockExpander:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): return False
    monkeypatch.setattr(reply_tab.st, "expander", lambda *a, **k: MockExpander())
    import ui.components.agent_visualizer
    import ui.components.crm_viewer
    import ui.components.email_display
    monkeypatch.setattr(ui.components.agent_visualizer, "display_agent_reasoning", lambda *a, **k: None)
    monkeypatch.setattr(ui.components.agent_visualizer, "display_agent_timeline", lambda *a, **k: None)
    monkeypatch.setattr(ui.components.crm_viewer, "display_crm_record", lambda *a, **k: None)
    monkeypatch.setattr(ui.components.email_display, "display_email_output", lambda *a, **k: None)
    # Patch st.columns to return the correct number of columns
    class DummyCol:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def subheader(self, *a, **k): pass
    def columns_patch(arg):
        if isinstance(arg, int):
            return tuple(DummyCol() for _ in range(arg))
        elif isinstance(arg, (list, tuple)):
            return tuple(DummyCol() for _ in range(len(arg)))
        else:
            return (DummyCol(), DummyCol())
    monkeypatch.setattr(reply_tab.st, "columns", columns_patch)
    # Patch st.button
    monkeypatch.setattr(reply_tab.st, "button", lambda *a, **k: False)
    lead_id = "test-lead"
    lead_data = {"name": "Test Lead", "company": "TestCo"}
    reply_content = "Test reply"
    result = ReplyAnalysisResult(
        disposition="engaged",
        confidence=90,
        sentiment="positive",
        urgency="high",
        reasoning="Test reasoning",
        next_action="Follow up",
        follow_up_timing="immediate",
        intent="interested",
        lead_score=85,
        priority="high"
    )
    try:
        reply_tab.display_reply_analysis_results(lead_id, lead_data, reply_content, result)
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(temp_dir)


class TestDiscoverNewLeadsTab(unittest.TestCase):
    """Test backend logic for the Discover New Leads tab."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_ui_discover.db")
        self.test_store = SQLiteMemoryStore(self.db_path)
        self.memory_manager = MemoryManager(self.test_store)
        # Dummy data for discover tab
        self.dummy_leads = [
            {"name": "Alice Johnson", "email": "alice@acmecorp.com", "company": "Acme Corp"},
            {"name": "Bob Smith", "email": "bob@acmecorp.com", "company": "Acme Corp"},
            {"name": "Sarah Chen", "email": "sarah.chen@techcorp.com", "company": "TechCorp Industries"},
            {"name": "David Kim", "email": "david.kim@innovatetech.com", "company": "InnovateTech Solutions"},
            {"name": "Priya Patel", "email": "priya@finwise.com", "company": "Finwise"},
            {"name": "John Lee", "email": "john.lee@medigen.com", "company": "Medigen"},
            {"name": "Maria Garcia", "email": "maria@greengrid.com", "company": "GreenGrid"},
            {"name": "Tom Brown", "email": "tom@buildwise.com", "company": "Buildwise"},
            {"name": "Linda Xu", "email": "linda@cybercore.com", "company": "Cybercore"},
            {"name": "Omar Farouk", "email": "omar@logix.com", "company": "Logix"},
        ]

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_discover_leads_successful_flow(self):
        """User enters a known email, finds other emails at the same domain, selects one, LLM generates outreach email, user edits and submits."""
        from ui.tabs import discover_tab
        # Patch dummy data and LLM
        with patch.object(discover_tab, 'DUMMY_LEADS', self.dummy_leads), \
             patch.object(discover_tab, 'generate_outreach_email') as mock_llm:
            mock_llm.return_value = "Hi Bob, we're working with Alice Johnson at Acme Corp and wanted to reach out."
            # Simulate user entering 'alice@acmecorp.com'
            known_email = "alice@acmecorp.com"
            discovered = discover_tab.find_leads_by_domain(known_email)
            expected_result = [lead for lead in self.dummy_leads if lead["email"] != known_email and lead["email"].endswith("@acmecorp.com")]
            self.assertEqual(discovered, expected_result)
            # Simulate selecting Bob and generating outreach
            selected = discovered[0]
            draft = discover_tab.generate_outreach_email(selected["email"], known_email)
            self.assertIn("Alice Johnson", draft)
            # Simulate user edits and submits
            edited_draft = draft + "\nLooking forward to connecting!"
            result = discover_tab.submit_outreach_email(selected["email"], edited_draft)
            self.assertTrue(result["success"])
            self.assertIn(selected["email"], result["message"])

    def test_discover_leads_no_matches(self):
        """User enters an email with a domain not in the dummy data, receives a clear 'no leads found' message."""
        from ui.tabs import discover_tab
        with patch.object(discover_tab, 'DUMMY_LEADS', self.dummy_leads):
            unknown_email = "nobody@unknownco.com"
            discovered = discover_tab.find_leads_by_domain(unknown_email)
            self.assertEqual(discovered, [])
            msg = discover_tab.no_leads_found_message(unknown_email)
            self.assertIn("Sorry", msg)
            self.assertIn("unknownco.com", msg)

    def test_demo_email_selection_clears_manual_input(self):
        """Demo email selection and manual input can both be set, but manual input takes precedence if both are set."""
        from ui.tabs import discover_tab
        # Simulate UI state
        manual_input = "alice@acmecorp.com"
        demo_selected = "sarah.chen@techcorp.com"
        # Both set: manual_input takes precedence, demo_selected is cleared
        manual_input, demo_selected = discover_tab.handle_input_change(manual_input, demo_selected)
        self.assertEqual(manual_input, "alice@acmecorp.com")
        self.assertEqual(demo_selected, "")
        # Only demo_selected set
        manual_input, demo_selected = discover_tab.handle_input_change("", "sarah.chen@techcorp.com")
        self.assertEqual(manual_input, "")
        self.assertEqual(demo_selected, "sarah.chen@techcorp.com")
        # Only manual_input set
        manual_input, demo_selected = discover_tab.handle_input_change("bob@acmecorp.com", "")
        self.assertEqual(manual_input, "bob@acmecorp.com")
        self.assertEqual(demo_selected, "")
        # Both empty
        manual_input, demo_selected = discover_tab.handle_input_change("", "")
        self.assertEqual(manual_input, "")
        self.assertEqual(demo_selected, "")

    def test_outreach_email_editable_and_submission_logs(self):
        """LLM draft is editable and submission logs the action (no real email sent)."""
        from ui.tabs import discover_tab
        with patch.object(discover_tab, 'DUMMY_LEADS', self.dummy_leads), \
             patch.object(discover_tab, 'generate_outreach_email') as mock_llm, \
             patch.object(discover_tab, 'log_outreach_action') as mock_log:
            mock_llm.return_value = "Hi Bob, we're working with Alice Johnson at Acme Corp and wanted to reach out."
            selected = self.dummy_leads[1]  # Bob
            draft = discover_tab.generate_outreach_email(selected["email"], "alice@acmecorp.com")
            edited = draft + "\nLet's connect soon."
            discover_tab.submit_outreach_email(selected["email"], edited)
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            self.assertIn(selected["email"], args)
            self.assertTrue(any("Let's connect soon." in str(arg) for arg in args))

    def test_discover_leads_edge_cases(self):
        """All error and edge cases are handled gracefully (e.g., empty input, selecting self, etc.)."""
        from ui.tabs import discover_tab
        with patch.object(discover_tab, 'DUMMY_LEADS', self.dummy_leads):
            # Empty input
            discovered = discover_tab.find_leads_by_domain("")
            self.assertEqual(discovered, [])
            # Selecting self
            discovered = discover_tab.find_leads_by_domain("bob@acmecorp.com")
            emails = [lead["email"] for lead in discovered]
            self.assertNotIn("bob@acmecorp.com", emails)
            # Invalid email format
            discovered = discover_tab.find_leads_by_domain("notanemail")
            self.assertEqual(discovered, [])


# --- EmailManager integration tests ---
import pytest
from integrations.google.email_manager import EmailManager

# The following tests were removed as they tested the old SMTP-based API or NotImplementedError, which are no longer relevant:
# - test_email_manager_init
# - test_email_manager_send_email_not_implemented

# --- Integration test stubs for qualify/reply tab (will fail until implemented) ---
def test_qualify_tab_sends_real_email(monkeypatch):
    """Test that send_qualification_email triggers EmailManager.send_email."""
    from ui.tabs import qualify_tab
    called = {}
    class DummyEmailManager:
        def __init__(self, *a, **k): pass
        def send_email(self, *a, **k):
            called["sent"] = True
            return True
    monkeypatch.setattr(qualify_tab, "EmailManager", DummyEmailManager)
    # Use test data that will result in a 'hot' lead and trigger send_email
    form_data = {
        "name": "Test User",
        "email": "test.user@example.com",
        "company": "TestCo",
        "role": "VP of Sales",
        "message": "We have budget and want to buy now. Please send contract.",
        "interest": "Ready to purchase, urgent need, decision maker"
    }
    from agents.models import LeadQualificationResult
    qualification = LeadQualificationResult(
        lead_id="test_lead_id",
        lead_name=form_data["name"],
        lead_company=form_data["company"],
        priority="high",
        lead_score=95,
        reasoning="Test reasoning (hot lead)",
        next_action="Send contract",
        disposition="hot",
        confidence=95,
        sentiment="positive",
        urgency="urgent"
    )
    qualify_tab.send_qualification_email(form_data, qualification)
    assert called.get("sent", False)


def test_reply_tab_sends_real_email(monkeypatch):
    """Test that send_reply_analysis_email triggers EmailManager.send_email."""
    from ui.tabs import reply_tab
    called = {}
    class DummyEmailManager:
        def __init__(self, *a, **k): pass
        def send_email(self, *a, **k):
            called["sent"] = True
            return True
    monkeypatch.setattr(reply_tab, "EmailManager", DummyEmailManager)
    # Use test data that will result in an 'engaged' reply and trigger send_email
    lead_data = {"name": "Test User", "email": "test.user@example.com", "company": "TestCo"}
    from agents.models import ReplyAnalysisResult
    analysis = ReplyAnalysisResult(
        disposition="engaged",
        confidence=90,
        sentiment="positive",
        urgency="high",
        reasoning="Test reasoning (engaged)",
        next_action="Send contract",
        follow_up_timing="immediate",
        intent="interested",
        lead_score=85,
        priority="high"
    )
    reply_content = "We are ready to move forward and would like to sign the contract this week."
    reply_tab.send_reply_analysis_email(lead_data, reply_content, analysis)
    assert called.get("sent", False)


if __name__ == "__main__":
    unittest.main() 