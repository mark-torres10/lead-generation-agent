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

# Mock reply data - realistic email responses from leads
mock_replies = {
    "reply_001": {
        "lead_id": "lead_001",
        "reply_text": "Yes, I'm definitely interested! Can we schedule a call this week to discuss further? I have budget approved and need to make a decision by month-end.",
        "reply_subject": "Re: Follow-up on sales automation",
        "sender_email": "alice@acmeinc.com",
        "timestamp": "2025-05-25 10:30:00"
    },
    "reply_002": {
        "lead_id": "lead_001", 
        "reply_text": "Thanks for reaching out. We're not looking at new solutions right now, but maybe we can revisit this in Q2 next year.",
        "reply_subject": "Re: Follow-up on sales automation",
        "sender_email": "alice@acmeinc.com",
        "timestamp": "2025-05-25 11:15:00"
    },
    "reply_003": {
        "lead_id": "lead_001",
        "reply_text": "Hi, thanks for the information. I'm still evaluating options and need to discuss with my team. Can you send me some case studies and pricing information?",
        "reply_subject": "Re: Follow-up on sales automation", 
        "sender_email": "alice@acmeinc.com",
        "timestamp": "2025-05-25 14:20:00"
    },
    "reply_004": {
        "lead_id": "lead_002",
        "reply_text": "Not interested, please remove me from your list.",
        "reply_subject": "Re: Workflow automation inquiry",
        "sender_email": "bob@betallc.com", 
        "timestamp": "2025-05-25 09:45:00"
    },
    "reply_005": {
        "lead_id": "lead_002",
        "reply_text": "This looks interesting but we're currently tied up with other projects. Could you follow up with me in about 3 months?",
        "reply_subject": "Re: Workflow automation inquiry",
        "sender_email": "bob@betallc.com",
        "timestamp": "2025-05-25 16:30:00"
    }
}

# Mock CRM data (extended from run_qualify_followup.py)
mock_crm = {
    "lead_001": {
        "id": "lead_001",
        "name": "Alice Smith", 
        "company": "Acme Inc",
        "email": "alice@acmeinc.com",
        "status": "contacted",
        "interest": "Looking for sales automation tools",
        "lead_disposition": None,
        "last_contact": "2025-05-24",
        "interaction_history": []
    },
    "lead_002": {
        "id": "lead_002",
        "name": "Bob Jones",
        "company": "Beta LLC", 
        "email": "bob@betallc.com",
        "status": "contacted",
        "interest": "Exploring options for workflow automation",
        "lead_disposition": None,
        "last_contact": "2025-05-24",
        "interaction_history": []
    }
}

def get_llm_chain_for_reply_analysis():
    """Create and return the LLM chain for reply intent analysis."""
    # Initialize OpenAI LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create prompt template for reply analysis
    prompt_template = """
You are an expert sales communication analyst. Analyze the following email reply from a lead to determine their true intent and interest level.

Lead Information:
- Name: {name}
- Company: {company}
- Email: {email}
- Previous Interest: {interest}

Email Reply:
- Subject: {reply_subject}
- Content: {reply_text}
- Timestamp: {timestamp}

Previous Qualification Context:
{previous_context}

Please analyze this reply and provide your assessment in the following format:
DISPOSITION: [engaged/maybe/disinterested]
CONFIDENCE: [0-100]
SENTIMENT: [positive/neutral/negative]
URGENCY: [high/medium/low]
REASONING: [Your detailed analysis of the reply]
NEXT_ACTION: [Specific recommended next step]
FOLLOW_UP_TIMING: [immediate/1-week/1-month/3-months/none]

Consider these factors:
- Explicit interest statements vs polite brush-offs
- Urgency indicators (deadlines, budget cycles)
- Decision-making authority signals
- Specific questions or requests for information
- Timeline mentions and availability
- Tone and language used
"""

    prompt = PromptTemplate(
        input_variables=["name", "company", "email", "interest", "reply_subject", "reply_text", "timestamp", "previous_context"],
        template=prompt_template
    )
    
    return LLMChain(llm=llm, prompt=prompt)

def parse_reply_analysis_response(llm_response):
    """Parse the LLM response into structured reply analysis data."""
    try:
        # Extract disposition
        disposition_match = re.search(r'DISPOSITION:\s*(\w+)', llm_response, re.IGNORECASE)
        disposition = disposition_match.group(1).lower() if disposition_match else "maybe"
        
        # Extract confidence
        confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', llm_response)
        confidence = int(confidence_match.group(1)) if confidence_match else 70
        
        # Extract sentiment
        sentiment_match = re.search(r'SENTIMENT:\s*(\w+)', llm_response, re.IGNORECASE)
        sentiment = sentiment_match.group(1).lower() if sentiment_match else "neutral"
        
        # Extract urgency
        urgency_match = re.search(r'URGENCY:\s*(\w+)', llm_response, re.IGNORECASE)
        urgency = urgency_match.group(1).lower() if urgency_match else "medium"
        
        # Extract reasoning
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?=NEXT_ACTION:|$)', llm_response, re.DOTALL | re.IGNORECASE)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else "Unable to parse reasoning from LLM response"
        
        # Extract next action
        action_match = re.search(r'NEXT_ACTION:\s*(.+?)(?=FOLLOW_UP_TIMING:|$)', llm_response, re.DOTALL | re.IGNORECASE)
        next_action = action_match.group(1).strip() if action_match else "Follow up via email"
        
        # Extract follow-up timing
        timing_match = re.search(r'FOLLOW_UP_TIMING:\s*(\S+)', llm_response, re.IGNORECASE)
        follow_up_timing = timing_match.group(1).lower() if timing_match else "1-week"
        
        return {
            "disposition": disposition,
            "confidence": confidence,
            "sentiment": sentiment,
            "urgency": urgency,
            "reasoning": reasoning,
            "next_action": next_action,
            "follow_up_timing": follow_up_timing
        }
    except Exception as e:
        # Fallback values if parsing fails
        return {
            "disposition": "maybe",
            "confidence": 50,
            "sentiment": "neutral", 
            "urgency": "medium",
            "reasoning": f"Unable to parse LLM response: {str(e)}",
            "next_action": "Follow up via email",
            "follow_up_timing": "1-week"
        }

def build_context_from_reply(lead_id, reply_data):
    """Build context for reply analysis including lead history."""
    # Get lead info from CRM
    lead = mock_crm.get(lead_id, {})
    
    # Get previous qualification from SQLite
    previous_qualification = memory_store.get_qualification(lead_id)
    previous_context = ""
    
    if previous_qualification:
        previous_context = f"""
Previous Qualification:
- Priority: {previous_qualification['priority']}
- Score: {previous_qualification['lead_score']}
- Previous Reasoning: {previous_qualification['reasoning']}
- Previous Next Action: {previous_qualification['next_action']}
"""
    else:
        previous_context = "No previous qualification found."
    
    # Get interaction history
    interactions = memory_store.get_interaction_history(lead_id)
    if interactions:
        previous_context += f"\nRecent Interactions: {len(interactions)} recorded"
    
    return {
        "lead_id": lead_id,
        "name": lead.get("name", "Unknown"),
        "company": lead.get("company", "Unknown"),
        "email": lead.get("email", "Unknown"),
        "interest": lead.get("interest", "Unknown"),
        "reply_subject": reply_data["reply_subject"],
        "reply_text": reply_data["reply_text"],
        "timestamp": reply_data["timestamp"],
        "previous_context": previous_context
    }

def analyze_reply_intent(context):
    """Use LLM to analyze reply intent and determine lead disposition."""
    lead_id = context["lead_id"]
    
    # Get LLM chain and invoke
    chain = get_llm_chain_for_reply_analysis()
    response = chain.invoke({
        "name": context["name"],
        "company": context["company"],
        "email": context["email"],
        "interest": context["interest"],
        "reply_subject": context["reply_subject"],
        "reply_text": context["reply_text"],
        "timestamp": context["timestamp"],
        "previous_context": context["previous_context"]
    })
    
    # Parse the response
    analysis_result = parse_reply_analysis_response(response["text"])
    
    # Update the lead's qualification with new disposition
    existing_qualification = memory_store.get_qualification(lead_id)
    if existing_qualification:
        # Update existing qualification with disposition info
        updated_qualification = existing_qualification.copy()
        updated_qualification.update({
            "lead_disposition": analysis_result["disposition"],
            "disposition_confidence": analysis_result["confidence"],
            "sentiment": analysis_result["sentiment"],
            "urgency": analysis_result["urgency"],
            "last_reply_analysis": analysis_result["reasoning"],
            "recommended_follow_up": analysis_result["next_action"],
            "follow_up_timing": analysis_result["follow_up_timing"]
        })
        memory_store.save_qualification(lead_id, updated_qualification)
    
    return analysis_result

def update_crm_with_disposition(lead_id, analysis_result):
    """Update the mock CRM with reply analysis results."""
    if lead_id in mock_crm:
        mock_crm[lead_id].update({
            "lead_disposition": analysis_result["disposition"],
            "sentiment": analysis_result["sentiment"],
            "urgency": analysis_result["urgency"],
            "next_action": analysis_result["next_action"],
            "follow_up_timing": analysis_result["follow_up_timing"]
        })
        
        # Log interaction to SQLite
        interaction_data = {
            "event": "reply_analyzed",
            "disposition": analysis_result["disposition"],
            "confidence": analysis_result["confidence"],
            "sentiment": analysis_result["sentiment"],
            "reasoning": analysis_result["reasoning"],
            "next_action": analysis_result["next_action"]
        }
        memory_store.add_interaction(lead_id, "reply_analysis", interaction_data)

def handle_reply(lead_id, reply_id):
    """Main flow: analyze reply intent, update disposition, recommend next action."""
    # Get reply data
    reply_data = mock_replies.get(reply_id)
    if not reply_data:
        print(f"❌ Reply {reply_id} not found")
        return None
        
    if reply_data["lead_id"] != lead_id:
        print(f"❌ Reply {reply_id} does not belong to lead {lead_id}")
        return None
    
    print(f"📧 Analyzing reply from {lead_id}")
    print(f"Reply: \"{reply_data['reply_text'][:100]}...\"")
    
    # Build context and analyze
    context = build_context_from_reply(lead_id, reply_data)
    analysis_result = analyze_reply_intent(context)
    
    # Update CRM
    update_crm_with_disposition(lead_id, analysis_result)
    
    print(f"\n🎯 Analysis Results:")
    print(f"   Disposition: {analysis_result['disposition']}")
    print(f"   Confidence: {analysis_result['confidence']}%")
    print(f"   Sentiment: {analysis_result['sentiment']}")
    print(f"   Urgency: {analysis_result['urgency']}")
    print(f"   Next Action: {analysis_result['next_action']}")
    print(f"   Follow-up Timing: {analysis_result['follow_up_timing']}")
    print(f"   Reasoning: {analysis_result['reasoning'][:200]}...")
    
    return analysis_result

def demo_reply_scenarios():
    """Demo function to test different reply scenarios."""
    print("🔍 Reply Intent Analysis Demo")
    print("=" * 50)
    
    # Test scenarios
    scenarios = [
        ("lead_001", "reply_001", "Highly Interested Reply"),
        ("lead_001", "reply_002", "Polite Decline Reply"), 
        ("lead_001", "reply_003", "Maybe/Evaluating Reply"),
        ("lead_002", "reply_004", "Direct Rejection Reply"),
        ("lead_002", "reply_005", "Delayed Interest Reply")
    ]
    
    for lead_id, reply_id, scenario_name in scenarios:
        print(f"\n📋 Scenario: {scenario_name}")
        print("-" * 30)
        result = handle_reply(lead_id, reply_id)
        print()

if __name__ == "__main__":
    # Run demo scenarios
    demo_reply_scenarios()
    
    # Show final CRM state
    print("\n📊 Final CRM State:")
    print("=" * 30)
    for lead_id, lead_data in mock_crm.items():
        print(f"\n{lead_id}: {lead_data['name']} ({lead_data['company']})")
        print(f"   Disposition: {lead_data.get('lead_disposition', 'Not analyzed')}")
        print(f"   Sentiment: {lead_data.get('sentiment', 'Unknown')}")
        print(f"   Next Action: {lead_data.get('next_action', 'None')}")
    
    # Show SQLite memory state
    print(f"\n💾 SQLite Memory State:")
    print("=" * 30)
    all_leads = memory_store.get_all_leads()
    for lead in all_leads:
        print(f"Lead {lead['lead_id']}: {lead.get('lead_disposition', 'No disposition')} disposition")
        interactions = memory_store.get_interaction_history(lead['lead_id'])
        reply_analyses = [i for i in interactions if i['event_type'] == 'reply_analysis']
        print(f"   Reply analyses: {len(reply_analyses)}")
