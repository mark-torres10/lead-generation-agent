import pytest
from unittest.mock import patch, MagicMock
import workflows.run_qualify_followup as rqf

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
    
    # Check that the core data matches (ignoring timestamps)
    assert retrieved["priority"] == qualification_data["priority"]
    assert retrieved["lead_score"] == qualification_data["lead_score"]
    assert retrieved["reasoning"] == qualification_data["reasoning"]
    assert retrieved["next_action"] == qualification_data["next_action"]
    # Check that timestamps were added
    assert "created_at" in retrieved
    assert "updated_at" in retrieved
    assert rqf.has_been_qualified_before(lead_id) == True

def test_has_been_qualified_before_false():
    """Test that has_been_qualified_before returns False for new leads."""
    assert rqf.has_been_qualified_before("new_lead_999") == False

def test_get_qualification_memory_none_for_new_lead():
    """Test that get_qualification_memory returns None for leads not seen before."""
    assert rqf.get_qualification_memory("new_lead_999") is None

@patch('agents.agent_core.AgentCore.create_llm_chain')
def test_llm_qualify_lead_new_lead(mock_create_chain):
    """Test LLM qualification for a lead that hasn't been seen before."""
    # Mock the LLM response in the expected string format
    mock_chain = MagicMock()
    mock_chain.run.return_value = """priority: high
lead_score: 90
reasoning: Acme Inc is a large corporation showing strong interest in sales automation
next_action: Schedule intro call
disposition: hot
confidence: 90"""
    mock_create_chain.return_value = mock_chain
    
    context = rqf.extract_lead_context("lead_001")
    result = rqf.run_lead_qualifier_agent(context)
    
    assert result["priority"] == "high"
    assert result["lead_score"] == 90
    assert "Acme Inc" in result["history"]["reasoning"]  # reasoning is in the history sub-dict
    assert result["next_action"] == "Schedule intro call"
    
    # Verify the lead was saved to memory
    assert rqf.has_been_qualified_before("lead_001") == True

@patch('agents.agent_core.AgentCore.create_llm_chain')
def test_llm_qualify_lead_with_memory(mock_create_chain):
    """Test LLM qualification for a lead that has been seen before."""
    # First, save some previous qualification memory
    previous_qualification = {
        "priority": "medium",
        "lead_score": 75,
        "reasoning": "Previously showed moderate interest",
        "next_action": "Send follow-up email"
    }
    rqf.save_qualification_memory("lead_001", previous_qualification)
    
    # Mock the LLM response in the expected string format
    mock_chain = MagicMock()
    mock_chain.run.return_value = """priority: high
lead_score: 85
reasoning: Based on previous interaction and renewed interest, upgrading priority
next_action: Schedule demo call
disposition: hot
confidence: 85"""
    mock_create_chain.return_value = mock_chain
    
    context = rqf.extract_lead_context("lead_001")
    result = rqf.run_lead_qualifier_agent(context)
    
    assert result["priority"] == "high"
    assert result["lead_score"] == 85

@patch('agents.agent_core.AgentCore.create_llm_chain')
def test_run_lead_qualifier_agent_uses_llm(mock_create_chain):
    """Test that run_lead_qualifier_agent now uses EmailQualifier agent."""
    mock_chain = MagicMock()
    mock_chain.run.return_value = """priority: high
lead_score: 88
reasoning: LLM-generated reasoning
next_action: Schedule call
disposition: hot
confidence: 90"""
    mock_create_chain.return_value = mock_chain
    
    context = rqf.extract_lead_context("lead_001")
    result = rqf.run_lead_qualifier_agent(context)
    
    # Verify result structure
    assert result["priority"] == "high"
    assert result["lead_score"] == 88
    assert "email_text" in result  # Should still generate follow-up email
    assert "history" in result  # Should still create history entry

@patch('agents.agent_core.AgentCore.create_llm_chain')
def test_end_to_end_with_llm_qualification(mock_create_chain):
    """Test the complete flow with LLM qualification."""
    # Mock the LLM response in the expected string format
    mock_chain = MagicMock()
    mock_chain.run.return_value = """priority: high
lead_score: 95
reasoning: Acme Inc shows strong buying signals
next_action: Schedule demo
disposition: hot
confidence: 95"""
    mock_create_chain.return_value = mock_chain
    
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