"""
Lead qualification experiment using LangChain and OpenAI.
"""
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import from memory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.memory_manager import memory_manager
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def get_llm_chain():
    """Initialize the LLM and create a chain for lead qualification."""
    llm = OpenAI(temperature=0.7, max_tokens=500)
    
    prompt_template = PromptTemplate(
        input_variables=["lead_name", "lead_company", "lead_email", "lead_message", "previous_qualification"],
        template="""
You are a lead qualification expert. Analyze the following lead information and provide a qualification assessment.

Lead Information:
- Name: {lead_name}
- Company: {lead_company}
- Email: {lead_email}
- Message: {lead_message}

Previous Qualification (if any): {previous_qualification}

Please provide your assessment in the following format:
Priority: [high/medium/low]
Lead Score: [0-100]
Reasoning: [Your reasoning for the score and priority]
Next Action: [Recommended next action]
Lead Disposition: [hot/warm/cold/unqualified]
Disposition Confidence: [0-100]
Sentiment: [positive/neutral/negative]
Urgency: [immediate/soon/later/none]
Last Reply Analysis: [Analysis of their last message]
Recommended Follow-up: [Specific follow-up recommendation]
Follow-up Timing: [immediate/within_24h/within_week/later]
"""
    )
    
    return LLMChain(llm=llm, prompt=prompt_template)

def parse_llm_response(response_text):
    """Parse the LLM response into structured data."""
    lines = response_text.strip().split('\n')
    result = {}
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_').replace('-', '_')
            value = value.strip()
            
            # Convert specific fields to appropriate types
            if key in ['lead_score', 'disposition_confidence']:
                try:
                    result[key] = int(value)
                except ValueError:
                    result[key] = 0
            else:
                result[key] = value
    
    # Ensure all required fields are present with defaults
    defaults = {
        'priority': 'medium',
        'lead_score': 50,
        'reasoning': 'No specific reasoning provided',
        'next_action': 'Follow up',
        'lead_disposition': 'warm',
        'disposition_confidence': 50,
        'sentiment': 'neutral',
        'urgency': 'later',
        'last_reply_analysis': 'No analysis provided',
        'recommended_follow_up': 'Standard follow-up',
        'follow_up_timing': 'within_week'
    }
    
    for key, default_value in defaults.items():
        if key not in result:
            result[key] = default_value
    
    return result

def qualify_lead(lead_id, lead_data):
    """Qualify a lead using the LLM and save results to memory."""
    print(f"\n=== Qualifying Lead: {lead_id} ===")
    
    # Check if we have previous qualification
    previous_qualification = memory_manager.get_qualification(lead_id)
    previous_qual_text = "None" if not previous_qualification else str(previous_qualification)
    
    # Get LLM chain and run qualification
    chain = get_llm_chain()
    
    response = chain.run(
        lead_name=lead_data.get('name', 'Unknown'),
        lead_company=lead_data.get('company', 'Unknown'),
        lead_email=lead_data.get('email', 'Unknown'),
        lead_message=lead_data.get('message', 'No message provided'),
        previous_qualification=previous_qual_text
    )
    
    print(f"LLM Response:\n{response}")
    
    # Parse the response
    qualification_result = parse_llm_response(response)
    
    print(f"\nParsed Qualification:")
    for key, value in qualification_result.items():
        print(f"  {key}: {value}")
    
    # Save to memory
    memory_manager.save_qualification(lead_id, qualification_result)
    
    # Also save lead info if not exists
    memory_manager.save_lead(lead_id, lead_data)
    
    print(f"\nQualification saved to memory for lead: {lead_id}")
    
    return qualification_result

def demo_qualification():
    """Demo the qualification system with sample leads."""
    
    # Sample leads
    leads = {
        "lead_001": {
            "name": "John Smith",
            "company": "TechCorp Inc",
            "email": "john.smith@techcorp.com",
            "message": "Hi, I'm interested in your enterprise software solution. We're a 500-person company looking to streamline our operations. Can we schedule a demo this week?"
        },
        "lead_002": {
            "name": "Sarah Johnson", 
            "company": "StartupXYZ",
            "email": "sarah@startupxyz.com",
            "message": "Just browsing your website. Might be interested in the future."
        },
        "lead_003": {
            "name": "Mike Chen",
            "company": "Global Enterprises",
            "email": "m.chen@globalent.com", 
            "message": "We need a solution ASAP. Our current system is failing and we have a board meeting next week. Budget is not an issue."
        }
    }
    
    print("Starting Lead Qualification Demo")
    print("=" * 50)
    
    # Qualify each lead
    for lead_id, lead_data in leads.items():
        qualify_lead(lead_id, lead_data)
    
    print("\n" + "=" * 50)
    print("QUALIFICATION SUMMARY")
    print("=" * 50)
    
    # Show all qualifications
    for lead_id in leads.keys():
        qualification = memory_manager.get_qualification(lead_id)
        if qualification:
            print(f"\nLead: {lead_id}")
            print(f"  Priority: {qualification.get('priority')}")
            print(f"  Score: {qualification.get('lead_score')}")
            print(f"  Disposition: {qualification.get('lead_disposition')}")
            print(f"  Next Action: {qualification.get('next_action')}")
            print(f"  Urgency: {qualification.get('urgency')}")
    
    # Show memory contents
    print("\n" + "=" * 50)
    print("MEMORY STORE CONTENTS")
    print("=" * 50)
    
    all_leads = memory_manager.get_all_leads()
    print(f"\nTotal leads in memory: {len(all_leads)}")
    for lead in all_leads:
        print(f"  {lead['lead_id']}: {lead['name']} ({lead['company']})")

if __name__ == "__main__":
    demo_qualification() 