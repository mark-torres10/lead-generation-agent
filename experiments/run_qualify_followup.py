import os
import sys
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from memory.memory_store import memory_store

# Load environment variables from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

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

def save_qualification_memory(lead_id, qualification_data):
    """Save qualification results for a lead to SQLite memory."""
    memory_store.save_qualification(lead_id, qualification_data)

def get_qualification_memory(lead_id):
    """Retrieve previous qualification results for a lead from SQLite."""
    return memory_store.get_qualification(lead_id)

def has_been_qualified_before(lead_id):
    """Check if a lead has been qualified before in SQLite."""
    return memory_store.has_qualification(lead_id)

def get_llm_chain():
    """Create and return the LLM chain for lead qualification."""
    # Initialize OpenAI LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create prompt template
    prompt_template = """
You are a sales lead qualification expert. Analyze the following lead information and provide a qualification assessment.

Lead Information:
- Name: {name}
- Company: {company}
- Email: {email}
- Interest: {interest}
- Email Subject: {email_subject}
- Email Body: {email_body}

{memory_context}

Please provide your assessment in the following format:
PRIORITY: [high/medium/low]
SCORE: [0-100]
REASONING: [Your detailed reasoning for the assessment]
NEXT_ACTION: [Recommended next action]

Consider factors like:
- Company size and type
- Expressed interest level
- Urgency indicators
- Budget signals
- Decision-making authority indicators
"""

    prompt = PromptTemplate(
        input_variables=["name", "company", "email", "interest", "email_subject", "email_body", "memory_context"],
        template=prompt_template
    )
    
    return LLMChain(llm=llm, prompt=prompt)

def parse_llm_qualification_response(llm_response):
    """Parse the LLM response into structured qualification data."""
    try:
        # Extract priority
        priority_match = re.search(r'PRIORITY:\s*(\w+)', llm_response, re.IGNORECASE)
        priority = priority_match.group(1).lower() if priority_match else "medium"
        
        # Extract score
        score_match = re.search(r'SCORE:\s*(\d+)', llm_response)
        lead_score = int(score_match.group(1)) if score_match else 50
        
        # Extract reasoning
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?=NEXT_ACTION:|$)', llm_response, re.DOTALL | re.IGNORECASE)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else "Unable to parse reasoning from LLM response"
        
        # Extract next action
        action_match = re.search(r'NEXT_ACTION:\s*(.+?)$', llm_response, re.DOTALL | re.IGNORECASE)
        next_action = action_match.group(1).strip() if action_match else "Follow up via email"
        
        return {
            "priority": priority,
            "lead_score": lead_score,
            "reasoning": reasoning,
            "next_action": next_action
        }
    except Exception as e:
        # Fallback values if parsing fails
        return {
            "priority": "medium",
            "lead_score": 50,
            "reasoning": f"Unable to parse LLM response: {str(e)}",
            "next_action": "Follow up via email"
        }

def llm_qualify_lead(context):
    """Use LLM to qualify a lead with memory context."""
    lead_id = context["id"]
    
    # Check for previous qualification memory
    previous_qualification = get_qualification_memory(lead_id)
    memory_context = ""
    if previous_qualification:
        memory_context = f"""
Previous Qualification History:
- Previous Priority: {previous_qualification['priority']}
- Previous Score: {previous_qualification['lead_score']}
- Previous Reasoning: {previous_qualification['reasoning']}
- Previous Next Action: {previous_qualification['next_action']}

Please consider this previous context when making your new assessment.
"""
    else:
        memory_context = "This is the first time qualifying this lead."
    
    # Get LLM chain and invoke
    chain = get_llm_chain()
    response = chain.invoke({
        "name": context["name"],
        "company": context["company"],
        "email": context["email"],
        "interest": context["interest"],
        "email_subject": context["email_subject"],
        "email_body": context["email_body"],
        "memory_context": memory_context
    })
    
    # Parse the response
    qualification_result = parse_llm_qualification_response(response["text"])
    
    # Save to memory
    save_qualification_memory(lead_id, qualification_result)
    
    return qualification_result

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
    """Main lead qualification using LLM instead of simple rules."""
    # Use LLM to qualify the lead
    llm_result = llm_qualify_lead(context)
    
    # Generate follow-up email based on LLM results
    email_text = (
        f"Hi {context['name']},\n\n"
        f"Thanks for reaching out about {context['interest']} at {context['company']}. "
        f"Based on your inquiry, I think we can definitely help! "
        f"Our next step would be to {llm_result['next_action'].lower()}.\n\n"
        f"Best regards,\nSales Team"
    )
    
    return {
        "priority": llm_result["priority"],
        "lead_score": llm_result["lead_score"],
        "next_action": llm_result["next_action"],
        "email_text": email_text,
        "history": {
            "event": "qualified",
            "priority": llm_result["priority"],
            "lead_score": llm_result["lead_score"],
            "next_action": llm_result["next_action"],
            "reasoning": llm_result["reasoning"]
        }
    }

def send_followup_email(email_text, to_address, lead_id=None):
    """Simulate sending a follow-up email and log to SQLite."""
    # Log to SQLite
    memory_store.log_sent_email(lead_id, to_address, "Follow-up", email_text)
    print(f"[MOCK EMAIL SENT] To: {to_address}\n---\n{email_text}\n---\n")

def update_crm(lead_id, updates):
    """Update the mock CRM with new info and log interactions to SQLite."""
    lead = mock_crm[lead_id]
    for k, v in updates.items():
        if k == "interaction_history":
            lead["interaction_history"].append(v)
            # Also log to SQLite
            memory_store.add_interaction(lead_id, "qualification", v)
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
    print("\n[SENT EMAILS FROM SQLITE]", memory_store.get_sent_emails("lead_001"))
    print("\n[ALL QUALIFIED LEADS]", memory_store.get_all_leads())
