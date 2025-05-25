import pytest
from unittest.mock import patch, MagicMock
import experiments.run_qualify_followup as rqf

@pytest.fixture(autouse=True)
def reset_state():
    # Reset mock CRM, sent_emails, and qualification memory before each test
    rqf.mock_crm["lead_001"].update({
        "status": "new",
        "interaction_history": [],
        "lead_score": None,
        "priority": None,
        "next_action": None
    })
    rqf.sent_emails.clear()
    # Reset qualification memory
    if hasattr(rqf, 'qualification_memory'):
        rqf.qualification_memory.clear()
    yield

def test_save_and_get_qualification_memory():
    """Test that we can save and retrieve qualification memory for a lead."""
    lead_id = "lead_001"
    qualification_data = {
        "priority": "high",
        "lead_score": 85,
        "reasoning": "Large company with clear budget signals",
        "next_action": "Schedule demo call"
    }
    
    rqf.save_qualification_memory(lead_id, qualification_data)
    retrieved = rqf.get_qualification_memory(lead_id)
    
    assert retrieved == qualification_data
    assert rqf.has_been_qualified_before(lead_id) == True

def test_has_been_qualified_before_false():
    """Test that has_been_qualified_before returns False for new leads."""
    assert rqf.has_been_qualified_before("new_lead_999") == False

def test_get_qualification_memory_none_for_new_lead():
    """Test that get_qualification_memory returns None for leads not seen before."""
    assert rqf.get_qualification_memory("new_lead_999") is None

@patch('experiments.run_qualify_followup.get_llm_chain')
def test_llm_qualify_lead_new_lead(mock_get_llm_chain):
    """Test LLM qualification for a lead that hasn't been seen before."""
    # Mock the LLM response
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "text": "PRIORITY: high\nSCORE: 90\nREASONING: Acme Inc is a large corporation showing strong interest in sales automation\nNEXT_ACTION: Schedule intro call"
    }
    mock_get_llm_chain.return_value = mock_chain
    
    context = rqf.extract_lead_context("lead_001")
    result = rqf.llm_qualify_lead(context)
    
    assert result["priority"] == "high"
    assert result["lead_score"] == 90
    assert "Acme Inc" in result["reasoning"]
    assert result["next_action"] == "Schedule intro call"
    
    # Verify the lead was saved to memory
    assert rqf.has_been_qualified_before("lead_001") == True

@patch('experiments.run_qualify_followup.get_llm_chain')
def test_llm_qualify_lead_with_memory(mock_get_llm_chain):
    """Test LLM qualification for a lead that has been seen before."""
    # First, save some previous qualification memory
    previous_qualification = {
        "priority": "medium",
        "lead_score": 75,
        "reasoning": "Previously showed moderate interest",
        "next_action": "Send follow-up email"
    }
    rqf.save_qualification_memory("lead_001", previous_qualification)
    
    # Mock the LLM response that should consider previous context
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "text": "PRIORITY: high\nSCORE: 85\nREASONING: Based on previous interaction and renewed interest, upgrading priority\nNEXT_ACTION: Schedule demo call"
    }
    mock_get_llm_chain.return_value = mock_chain
    
    context = rqf.extract_lead_context("lead_001")
    result = rqf.llm_qualify_lead(context)
    
    # Verify the LLM was called with memory context
    call_args = mock_chain.invoke.call_args[0][0]
    assert "previous qualification" in call_args["memory_context"].lower()
    assert "medium" in call_args["memory_context"]  # Previous priority should be in context
    
    assert result["priority"] == "high"
    assert result["lead_score"] == 85

def test_parse_llm_qualification_response():
    """Test parsing of LLM response into structured data."""
    llm_response = "PRIORITY: high\nSCORE: 92\nREASONING: Enterprise client with clear budget and timeline\nNEXT_ACTION: Schedule technical demo"
    
    result = rqf.parse_llm_qualification_response(llm_response)
    
    assert result["priority"] == "high"
    assert result["lead_score"] == 92
    assert result["reasoning"] == "Enterprise client with clear budget and timeline"
    assert result["next_action"] == "Schedule technical demo"

def test_parse_llm_qualification_response_malformed():
    """Test parsing of malformed LLM response with fallback values."""
    llm_response = "This is a malformed response without proper structure"
    
    result = rqf.parse_llm_qualification_response(llm_response)
    
    # Should have fallback values
    assert result["priority"] == "medium"
    assert result["lead_score"] == 50
    assert "Unable to parse" in result["reasoning"]

@patch('experiments.run_qualify_followup.llm_qualify_lead')
def test_run_lead_qualifier_agent_uses_llm(mock_llm_qualify):
    """Test that run_lead_qualifier_agent now uses LLM instead of simple rules."""
    mock_llm_qualify.return_value = {
        "priority": "high",
        "lead_score": 88,
        "reasoning": "LLM-generated reasoning",
        "next_action": "Schedule call"
    }
    
    context = rqf.extract_lead_context("lead_001")
    result = rqf.run_lead_qualifier_agent(context)
    
    # Verify LLM was called
    mock_llm_qualify.assert_called_once_with(context)
    
    # Verify result structure
    assert result["priority"] == "high"
    assert result["lead_score"] == 88
    assert "email_text" in result  # Should still generate follow-up email
    assert "history" in result  # Should still create history entry

@patch('experiments.run_qualify_followup.get_llm_chain')
def test_end_to_end_with_llm_qualification(mock_get_llm_chain):
    """Test the complete flow with LLM qualification."""
    # Mock the LLM response
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "text": "PRIORITY: high\nSCORE: 95\nREASONING: Acme Inc shows strong buying signals\nNEXT_ACTION: Schedule demo"
    }
    mock_get_llm_chain.return_value = mock_chain
    
    # Run the complete flow
    rqf.handle_new_lead("lead_001")
    
    # Verify CRM was updated with LLM results
    lead = rqf.mock_crm["lead_001"]
    assert lead["priority"] == "high"
    assert lead["lead_score"] == 95
    assert len(lead["interaction_history"]) == 1
    
    # Verify email was sent
    assert len(rqf.sent_emails) == 1
    
    # Verify memory was saved
    assert rqf.has_been_qualified_before("lead_001") == True 