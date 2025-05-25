"""
Lead qualification experiment using the new EmailQualifier agent.
"""
from typing import Dict, Any

from agents.agent_core import AgentCore
from agents.email_qualifier import EmailQualifier
from memory.memory_manager import memory_manager
from lib.config_loader import get_config


def create_email_qualifier() -> EmailQualifier:
    """Initialize the EmailQualifier agent."""
    llm_config = get_config()
    agent_core = AgentCore(llm_config=llm_config)
    return EmailQualifier(agent_core=agent_core, memory_manager=memory_manager)

def qualify_lead(lead_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """Qualify a lead using the EmailQualifier agent and save results to memory."""
    print(f"\n=== Qualifying Lead: {lead_id} ===")
    
    # Check if we have previous qualification
    previous_qualification = memory_manager.get_qualification(lead_id)
    if previous_qualification:
        print(f"Previous qualification found: {previous_qualification}")
    
    try:
        # Create qualifier and run qualification
        qualifier = create_email_qualifier()
        
        # Fix the lead data to match EmailQualifier expectations
        # EmailQualifier expects 'interest' or 'email_body' instead of 'message'
        if 'message' in lead_data and 'interest' not in lead_data:
            lead_data['interest'] = lead_data['message']
        
        print(f"Lead data being processed: {lead_data}")
        
        qualification_result = qualifier.qualify(lead_data)
        
        print("Qualification Result:")
        if hasattr(qualification_result, 'model_dump'):
            for key, value in qualification_result.model_dump().items():
                print(f"  {key}: {value}")
        else:
            for key, value in qualification_result.items():
                print(f"  {key}: {value}")
        
        # Save to memory
        memory_manager.save_qualification(lead_id, qualification_result)
        
        # Also save lead info if not exists
        memory_manager.save_lead(lead_id, lead_data)
        
        print(f"\nQualification saved to memory for lead: {lead_id}")
        
        # Always return as LeadQualificationResult
        from agents.models import LeadQualificationResult
        if isinstance(qualification_result, dict):
            # Ensure required fields are present
            qualification_result.setdefault('lead_id', lead_data.get('email', lead_id))
            qualification_result.setdefault('lead_name', lead_data.get('name', ''))
            qualification_result.setdefault('lead_company', lead_data.get('company', ''))
            return LeadQualificationResult(**qualification_result)
        return qualification_result
        
    except Exception as e:
        print(f"Error qualifying lead {lead_id}: {str(e)}")
        # Return a default qualification on error
        default_qualification = {
            'priority': 'medium',
            'lead_score': 50,
            'reasoning': f'Error during qualification: {str(e)}',
            'next_action': 'Manual review required',
            'lead_disposition': 'unqualified',
            'disposition_confidence': 0,
            'sentiment': 'neutral',
            'urgency': 'later',
            'disposition': 'unqualified',
            'confidence': 0,
            'lead_id': lead_data.get('email', lead_id),
            'lead_name': lead_data.get('name', ''),
            'lead_company': lead_data.get('company', '')
        }
        memory_manager.save_qualification(lead_id, default_qualification)
        from agents.models import LeadQualificationResult
        return LeadQualificationResult(**default_qualification)

def demo_qualification():
    """Demo the qualification system with sample leads."""
    
    # Sample leads with enhanced data structure
    leads = {
        "lead_001": {
            "name": "John Smith",
            "company": "TechCorp Inc",
            "email": "john.smith@techcorp.com",
            "message": "Hi, I'm interested in your enterprise software solution. We're a 500-person company looking to streamline our operations. Can we schedule a demo this week?",
            "company_size": "500",
            "industry": "Technology",
            "lead_source": "website"
        },
        "lead_002": {
            "name": "Sarah Johnson", 
            "company": "StartupXYZ",
            "email": "sarah@startupxyz.com",
            "message": "Just browsing your website. Might be interested in the future.",
            "company_size": "10",
            "industry": "Startup",
            "lead_source": "organic"
        },
        "lead_003": {
            "name": "Mike Chen",
            "company": "Global Enterprises",
            "email": "m.chen@globalent.com", 
            "message": "We need a solution ASAP. Our current system is failing and we have a board meeting next week. Budget is not an issue.",
            "company_size": "1000+",
            "industry": "Enterprise",
            "lead_source": "referral"
        }
    }
    
    print("Starting Lead Qualification Demo")
    print("=" * 50)
    print("Using EmailQualifier Agent")
    print("=" * 50)
    
    # Qualify each lead
    results = {}
    for lead_id, lead_data in leads.items():
        results[lead_id] = qualify_lead(lead_id, lead_data)
    
    print("\n" + "=" * 50)
    print("QUALIFICATION SUMMARY")
    print("=" * 50)
    
    # Show all qualifications with enhanced display
    for lead_id, lead_data in leads.items():
        qualification = results.get(lead_id)
        if qualification:
            print(f"\nLead: {lead_id} - {lead_data['name']} ({lead_data['company']})")
            print(f"  Priority: {qualification.get('priority', 'N/A')}")
            print(f"  Score: {qualification.get('lead_score', 'N/A')}")
            print(f"  Disposition: {qualification.get('lead_disposition', 'N/A')}")
            print(f"  Confidence: {qualification.get('disposition_confidence', 'N/A')}%")
            print(f"  Sentiment: {qualification.get('sentiment', 'N/A')}")
            print(f"  Urgency: {qualification.get('urgency', 'N/A')}")
            print(f"  Next Action: {qualification.get('next_action', 'N/A')}")
            print(f"  Reasoning: {qualification.get('reasoning', 'N/A')[:100]}...")
    
    # Show memory contents
    print("\n" + "=" * 50)
    print("MEMORY STORE CONTENTS")
    print("=" * 50)
    
    all_leads = memory_manager.get_all_leads()
    print(f"\nTotal leads in memory: {len(all_leads)}")
    for lead in all_leads:
        print(f"  {lead['lead_id']}: {lead['name']} ({lead['company']})")
    
    # Show agent performance summary
    print("\n" + "=" * 50)
    print("AGENT PERFORMANCE SUMMARY")
    print("=" * 50)
    
    high_priority = sum(1 for r in results.values() if r.get('priority') == 'high')
    avg_score = sum(r.get('lead_score', 0) for r in results.values()) / len(results)
    
    print(f"High Priority Leads: {high_priority}/{len(results)}")
    print(f"Average Lead Score: {avg_score:.1f}")
    print(f"Successful Qualifications: {len([r for r in results.values() if r.get('lead_score', 0) > 0])}/{len(results)}")

if __name__ == "__main__":
    demo_qualification() 