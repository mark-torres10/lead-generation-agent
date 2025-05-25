from memory.memory_manager import memory_manager
from agents.agent_core import AgentCore
from agents.reply_analyzer import ReplyAnalyzer
from lib.env_vars import OPENAI_API_KEY

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

def create_reply_analyzer():
    """Create and return the ReplyAnalyzer agent."""
    # LLM configuration
    llm_config = {
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "max_tokens": 1000,
        "api_key": OPENAI_API_KEY
    }
    
    # Create agent core
    agent_core = AgentCore(llm_config)
    
    # Create and return ReplyAnalyzer
    return ReplyAnalyzer(agent_core, memory_manager)

def build_context_from_reply(lead_id, reply_data):
    """Build context for reply analysis including lead history."""
    # Get lead info from CRM
    lead = mock_crm.get(lead_id, {})
    
    # Get previous qualification from memory manager
    previous_qualification = memory_manager.get_qualification(lead_id)
    previous_context = ""
    
    if previous_qualification:
        previous_context = f"""
Previous Qualification:
- Priority: {previous_qualification['priority']}
- Score: {previous_qualification['lead_score']}
- Previous Reasoning: {previous_qualification['reasoning']}
- Next Action: {previous_qualification['next_action']}
"""
    else:
        previous_context = "No previous qualification found for this lead."
    
    # Build context for LLM
    context = {
        "lead_id": lead_id,
        "name": lead.get("name", "Unknown"),
        "company": lead.get("company", "Unknown"),
        "email": lead.get("email", "Unknown"),
        "interest": lead.get("interest", "Unknown"),
        "reply_subject": reply_data.get("reply_subject", ""),
        "reply_text": reply_data.get("reply_text", ""),
        "timestamp": reply_data.get("timestamp", ""),
        "previous_context": previous_context
    }
    
    return context

def analyze_reply_intent(context):
    """Analyze reply intent using ReplyAnalyzer agent and return structured results."""
    print(f"🤖 Analyzing reply intent for {context['name']} from {context['company']}")
    
    # Get ReplyAnalyzer
    reply_analyzer = create_reply_analyzer()
    
    # Prepare reply data for the agent
    reply_data = {
        "reply_text": context.get("reply_text", ""),
        "reply_subject": context.get("reply_subject", ""),
        "sender_email": context.get("email", ""),
        "timestamp": context.get("timestamp", ""),
        "lead_id": context.get("lead_id", "")
    }
    
    # Prepare lead context for the agent
    lead_context = {
        "name": context.get("name", ""),
        "company": context.get("company", ""),
        "previous_interest": context.get("interest", ""),
        "interaction_history": context.get("previous_context", "No previous interactions")
    }
    
    # Run analysis
    try:
        analysis_result = reply_analyzer.analyze(reply_data, lead_context)
        
        # Calculate lead score and priority using the agent's methods
        lead_score = reply_analyzer.calculate_score(analysis_result)
        priority = reply_analyzer.determine_priority(analysis_result)
        
        # Add calculated values to the result
        analysis_result["lead_score"] = lead_score
        analysis_result["priority"] = priority
        
        print("✅ Analysis Result:")
        for key, value in analysis_result.items():
            print(f"   {key}: {value}")
        
        # Update qualification in memory with reply analysis
        lead_id = context.get("lead_id")
        if lead_id:
            # Get existing qualification to preserve required fields
            existing_qualification = memory_manager.get_qualification(lead_id)
            
            qualification_update = {
                # Required fields (preserve existing or set defaults)
                "priority": priority,
                "lead_score": lead_score,
                "reasoning": analysis_result["reasoning"],
                "next_action": analysis_result["next_action"],
                # Reply analysis specific fields
                "lead_disposition": analysis_result["disposition"],
                "disposition_confidence": analysis_result["confidence"],
                "sentiment": analysis_result["sentiment"],
                "urgency": analysis_result["urgency"],
                "last_reply_analysis": analysis_result["reasoning"],
                "recommended_follow_up": analysis_result["next_action"],
                "follow_up_timing": analysis_result["follow_up_timing"]
            }
            
            # If there's an existing qualification, preserve some fields
            if existing_qualification:
                # Keep the original reasoning if it exists, append reply analysis
                original_reasoning = existing_qualification.get("reasoning", "")
                if original_reasoning and original_reasoning != analysis_result["reasoning"]:
                    qualification_update["reasoning"] = f"{original_reasoning}\n\nReply Analysis: {analysis_result['reasoning']}"
            
            memory_manager.save_qualification(lead_id, qualification_update)
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ Error during reply analysis: {str(e)}")
        # Return default analysis on error
        return {
            "disposition": "maybe",
            "confidence": 50,
            "sentiment": "neutral",
            "urgency": "medium", 
            "reasoning": f"Analysis failed: {str(e)}",
            "next_action": "Manual review required",
            "follow_up_timing": "1-week",
            "lead_score": 50,
            "priority": "medium"
        }

def update_crm_with_disposition(lead_id, analysis_result):
    """Update CRM and memory with reply analysis results."""
    print(f"💾 Updating CRM for lead {lead_id}")
    
    # Update mock CRM
    if lead_id in mock_crm:
        mock_crm[lead_id]["lead_disposition"] = analysis_result["disposition"]
        mock_crm[lead_id]["sentiment"] = analysis_result["sentiment"]
        mock_crm[lead_id]["last_contact"] = analysis_result.get("timestamp", "2025-05-25")
        
        # Add to interaction history
        interaction = {
            "type": "reply_analysis",
            "disposition": analysis_result["disposition"],
            "confidence": analysis_result["confidence"],
            "sentiment": analysis_result["sentiment"],
            "timestamp": analysis_result.get("timestamp", "2025-05-25")
        }
        mock_crm[lead_id]["interaction_history"].append(interaction)
    
    # Update qualification in memory with reply analysis
    qualification_update = {
        "lead_disposition": analysis_result["disposition"],
        "disposition_confidence": analysis_result["confidence"],
        "sentiment": analysis_result["sentiment"],
        "urgency": analysis_result["urgency"],
        "last_reply_analysis": analysis_result["reasoning"],
        "recommended_follow_up": analysis_result["next_action"],
        "follow_up_timing": analysis_result["follow_up_timing"]
    }
    
    memory_manager.save_qualification(lead_id, qualification_update)
    
    print(f"✅ Updated qualification for {lead_id}")

def handle_reply(lead_id, reply_id):
    """Handle a reply end-to-end: analyze intent and update records."""
    print(f"📧 Analyzing reply from {lead_id}")
    
    # Get reply data
    if reply_id not in mock_replies:
        print(f"❌ Reply {reply_id} not found")
        return None
    
    reply_data = mock_replies[reply_id]
    
    # Validate that the reply belongs to the correct lead
    if reply_data.get("lead_id") != lead_id:
        print(f"❌ Reply {reply_id} does not belong to lead {lead_id}")
        return None
    
    print(f'Reply: "{reply_data["reply_text"][:100]}..."')
    
    # Build context for analysis
    context = build_context_from_reply(lead_id, reply_data)
    
    # Analyze the reply
    analysis_result = analyze_reply_intent(context)
    
    # Update CRM with results
    update_crm_with_disposition(lead_id, analysis_result)
    
    # Log interaction in memory
    interaction_data = {
        "reply_text": reply_data["reply_text"],
        "analysis_result": analysis_result,
        "timestamp": reply_data["timestamp"]
    }
    
    memory_manager.add_interaction(lead_id, "reply_analyzed", interaction_data)
    
    return analysis_result

def demo_reply_scenarios():
    """Demo the reply intent analysis system with various scenarios."""
    print("🎯 REPLY INTENT ANALYSIS DEMO")
    print("=" * 60)
    
    # Process each reply
    results = {}
    for reply_id, reply_data in mock_replies.items():
        lead_id = reply_data["lead_id"]
        print(f"\n📧 Processing {reply_id} from {lead_id}")
        print("-" * 40)
        
        result = handle_reply(lead_id, reply_id)
        results[reply_id] = result
    
    # Show final analysis summary
    print(f"\n{'='*60}")
    print("FINAL ANALYSIS SUMMARY")
    print(f"{'='*60}")
    
    for lead_id, lead_data in mock_crm.items():
        print(f"\n🏢 Lead: {lead_id}")
        print(f"   Name: {lead_data['name']}")
        print(f"   Company: {lead_data['company']}")
        print(f"   Current Disposition: {lead_data.get('lead_disposition', 'Unknown')}")
        print(f"   Interactions: {len(lead_data['interaction_history'])}")
        
        # Show latest qualification
        qualification = memory_manager.get_qualification(lead_id)
        if qualification:
            print("   Latest Analysis:")
            print(f"     Disposition: {qualification.get('lead_disposition', 'N/A')}")
            print(f"     Confidence: {qualification.get('disposition_confidence', 'N/A')}")
            print(f"     Sentiment: {qualification.get('sentiment', 'N/A')}")
            print(f"     Next Action: {qualification.get('recommended_follow_up', 'N/A')}")
            print(f"     Follow-up Timing: {qualification.get('follow_up_timing', 'N/A')}")

if __name__ == "__main__":
    demo_reply_scenarios()
