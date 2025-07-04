import pytest
from unittest.mock import patch, MagicMock
import workflows.run_qualify_followup as rqf

@pytest.fixture(autouse=True)
def reset_state():
    # Reset mock CRM and sent_emails before each test
    rqf.mock_crm["lead_001"].update({
        "status": "new",
        "interaction_history": [],
        "lead_score": None,
        "priority": None,
        "next_action": None
    })
    rqf.sent_emails.clear()
    yield

def test_load_from_crm():
    lead = rqf.load_from_crm("lead_001")
    assert lead["name"] == "Alice Smith"
    assert lead["company"] == "Acme Inc"

def test_extract_lead_context():
    context = rqf.extract_lead_context("lead_001")
    assert context["name"] == "Alice Smith"
    assert "sales automation" in context["interest"]
    assert "Acme Inc" in context["company"]
    assert "Interested in your product" in context["email_subject"]

@patch('workflows.run_qualify_followup.llm_qualify_lead')
def test_run_lead_qualifier_agent_high_priority(mock_llm_qualify):
    # Mock the LLM to return high priority for Acme Inc (maintaining original test expectation)
    mock_llm_qualify.return_value = {
        "priority": "high",
        "lead_score": 90,
        "reasoning": "Acme Inc is a large corporation showing strong interest",
        "next_action": "Schedule intro call"
    }
    
    context = rqf.extract_lead_context("lead_001")
    result = rqf.run_lead_qualifier_agent(context)
    assert result["priority"] == "high"
    assert result["lead_score"] == 90
    assert "Acme Inc" in result["email_text"]

    # Test for a medium priority lead
    mock_llm_qualify.return_value = {
        "priority": "medium",
        "lead_score": 70,
        "reasoning": "Beta LLC shows moderate interest",
        "next_action": "Send product brochure"
    }
    context2 = rqf.extract_lead_context("lead_002")
    result2 = rqf.run_lead_qualifier_agent(context2)
    assert result2["priority"] == "medium"
    assert result2["lead_score"] == 70


def test_send_followup_email():
    rqf.send_followup_email("Test body", "test@example.com")
    assert len(rqf.sent_emails) == 1
    assert rqf.sent_emails[0]["to"] == "test@example.com"
    assert "Test body" in rqf.sent_emails[0]["body"]


def test_update_crm():
    rqf.update_crm("lead_001", {"priority": "high", "lead_score": 99, "interaction_history": {"event": "test"}})
    assert rqf.mock_crm["lead_001"]["priority"] == "high"
    assert rqf.mock_crm["lead_001"]["lead_score"] == 99
    assert rqf.mock_crm["lead_001"]["interaction_history"][-1]["event"] == "test"


@patch('workflows.run_qualify_followup.llm_qualify_lead')
def test_handle_new_lead_end_to_end(mock_llm_qualify):
    # Mock the LLM qualification
    mock_llm_qualify.return_value = {
        "priority": "high",
        "lead_score": 90,
        "reasoning": "Acme Inc shows strong buying signals",
        "next_action": "Schedule intro call"
    }
    
    rqf.handle_new_lead("lead_001")
    lead = rqf.mock_crm["lead_001"]
    assert lead["priority"] == "high"
    assert lead["lead_score"] == 90
    assert lead["next_action"] is not None
    assert len(lead["interaction_history"]) == 1
    assert len(rqf.sent_emails) == 1 