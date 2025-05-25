from memory.memory_manager import memory_manager
from agents.agent_core import AgentCore
from agents.email_qualifier import EmailQualifier
from lib.config_loader import get_config

# Mock CRM data
mock_crm = {
    "lead_001": {
        "id": "lead_001",
        "name": "Alice Smith",
        "company": "Acme Inc",
        "email": "alice@acmeinc.com",
        "status": "new",
        "interest": "Looking for sales automation tools",
        "email_subject": "Interested in your product",
        "email_body": "Hi, I'm interested in learning more about your sales automation platform.",
        "interaction_history": [],
        "lead_score": None,
        "priority": None,
        "next_action": None
    },
    "lead_002": {
        "id": "lead_002",
        "name": "Bob Jones",
        "company": "Beta LLC",
        "email": "bob@betallc.com",
        "status": "new",
        "interest": "Exploring options for workflow automation",
        "email_subject": "Workflow automation inquiry",
        "email_body": "Hello, can you tell me about your workflow automation features?",
        "interaction_history": [],
        "lead_score": None,
        "priority": None,
        "next_action": None
    }
}

# Track sent emails for testing
sent_emails = []

def create_email_qualifier():
    """Create and return the EmailQualifier agent."""
    llm_config = get_config()
    agent_core = AgentCore(llm_config)
    return EmailQualifier(agent_core, memory_manager)

def save_qualification_memory(lead_id, qualification_data):
    """Save qualification results for a lead to SQLite memory."""
    memory_manager.save_qualification(lead_id, qualification_data)

def get_qualification_memory(lead_id):
    """Retrieve previous qualification results for a lead from SQLite."""
    return memory_manager.get_qualification(lead_id)

def has_been_qualified_before(lead_id):
    """Check if a lead has been qualified before in SQLite."""
    qualification = memory_manager.get_qualification(lead_id)
    return qualification is not None

def llm_qualify_lead(context):
    """Use EmailQualifier agent to qualify a lead with memory context."""
    lead_id = context["id"]
    
    # Create EmailQualifier agent
    qualifier = create_email_qualifier()
    
    # Prepare lead data for the agent
    lead_data = {
        "name": context["name"],
        "company": context["company"],
        "email": context["email"],
        "interest": context.get("interest", context.get("email_body", "")),  # Use interest or email_body
        "email_subject": context.get("email_subject", ""),
        "email_body": context.get("email_body", "")
    }
    
    try:
        # Run qualification using the agent
        qualification_result = qualifier.qualify(lead_data)
        
        print(f"✅ Qualification Result for {lead_id}:")
        if hasattr(qualification_result, 'model_dump'):
            for key, value in qualification_result.model_dump().items():
                print(f"   {key}: {value}")
        else:
            for key, value in qualification_result.items():
                print(f"   {key}: {value}")
        
        return qualification_result
        
    except Exception as e:
        print(f"❌ Error during qualification: {str(e)}")
        # Return default qualification on error
        default_qualification = {
            'priority': 'medium',
            'lead_score': 50,
            'reasoning': f'Error during qualification: {str(e)}',
            'next_action': 'Manual review required',
            'lead_disposition': 'unqualified',
            'disposition_confidence': 0,
            'sentiment': 'neutral',
            'urgency': 'later'
        }
        save_qualification_memory(lead_id, default_qualification)
        return default_qualification

def load_from_crm(lead_id):
    """Retrieve a lead from the mock CRM by ID."""
    return mock_crm[lead_id]

def extract_lead_context(lead_id):
    """Extract relevant context from the lead for qualification."""
    lead = load_from_crm(lead_id)
    return {
        "id": lead["id"],
        "name": lead["name"],
        "company": lead["company"],
        "email": lead["email"],
        "interest": lead["interest"],
        "email_subject": lead["email_subject"],
        "email_body": lead["email_body"],
        "history": lead["interaction_history"]
    }

def run_lead_qualifier_agent(context):
    """Main lead qualification using EmailQualifier agent."""
    # Use EmailQualifier agent to qualify the lead
    llm_result = llm_qualify_lead(context)

    # If llm_result is a Pydantic model, convert to dict for downstream usage
    if hasattr(llm_result, 'model_dump'):
        llm_result_dict = llm_result.model_dump()
    else:
        llm_result_dict = llm_result

    # Generate follow-up email based on agent results
    email_text = (
        f"Hi {context['name']},\n\n"
        f"Thanks for reaching out about {context['interest']} at {context['company']}. "
        f"Based on your inquiry, I think we can definitely help! "
        f"Our next step would be to {llm_result_dict['next_action'].lower()}.\n\n"
        f"Best regards,\nSales Team"
    )

    return {
        "priority": llm_result_dict["priority"],
        "lead_score": llm_result_dict["lead_score"],
        "next_action": llm_result_dict["next_action"],
        "email_text": email_text,
        "history": {
            "event": "qualified",
            "priority": llm_result_dict["priority"],
            "lead_score": llm_result_dict["lead_score"],
            "next_action": llm_result_dict["next_action"],
            "reasoning": llm_result_dict["reasoning"]
        }
    }

def send_followup_email(email_text, to_address, lead_id=None):
    """Simulate sending a follow-up email and log to memory."""
    # Log to memory manager
    memory_manager.log_sent_email(lead_id, to_address, "Follow-up", email_text)
    # Also track in global list for testing
    sent_emails.append({
        "lead_id": lead_id,
        "to": to_address,
        "subject": "Follow-up",
        "body": email_text
    })
    print(f"[MOCK EMAIL SENT] To: {to_address}\n---\n{email_text}\n---\n")

def update_crm(lead_id, updates):
    """Update the mock CRM with new info and log interactions to memory."""
    lead = mock_crm[lead_id]
    for k, v in updates.items():
        if k == "interaction_history":
            lead["interaction_history"].append(v)
            # Also log to memory manager
            memory_manager.add_interaction(lead_id, "qualification", v)
        else:
            lead[k] = v

def handle_new_lead(lead_id):
    """Main flow: qualify lead, send follow-up, update CRM."""
    lead = load_from_crm(lead_id)
    context = extract_lead_context(lead_id)
    result = run_lead_qualifier_agent(context)
    send_followup_email(result["email_text"], lead["email"], lead_id)
    update_crm(lead_id, {
        "priority": result["priority"],
        "lead_score": result["lead_score"],
        "next_action": result["next_action"],
        "interaction_history": result["history"]
    })
    print(f"[CRM UPDATED] Lead {lead_id} updated with priority={result['priority']}, lead_score={result['lead_score']}")

if __name__ == "__main__":
    handle_new_lead("lead_001")
    print("\n[CRM STATE]", mock_crm["lead_001"])
    print("\n[SENT EMAILS FROM MEMORY]", memory_manager.get_sent_emails("lead_001"))
    print("\n[QUALIFICATION DATA]", memory_manager.get_qualification("lead_001"))
