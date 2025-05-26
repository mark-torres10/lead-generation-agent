"""
Test script for verifying lead persistence across qualify and reply tabs.

This script simulates the following flow:
1. Create a new lead using the same data as the qualify tab (contact form submission).
2. Retrieve and print the lead info after qualification ("before" state).
3. Simulate a reply analysis for the same email (reply tab usage).
4. Retrieve and print the lead info after reply analysis ("after" state).
5. Assert that the lead_id is the same and that the before/after states are consistent.

Expected result: The same lead_id is used for both steps, and the before/after states reflect the correct updates.
"""
import os
import tempfile
from memory.memory_manager import MemoryManager
from memory.memory_store import SQLiteMemoryStore

def main():
    # Use a temp DB for isolation
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    store = SQLiteMemoryStore(db_path)
    mgr = MemoryManager(store)
    try:
        # Step 1: Simulate contact form submission (qualify tab)
        form_data = {
            "name": "Sarah Chen",
            "email": "sarah.chen@techcorp.com",
            "company": "TechCorp Industries",
            "role": "Chief Technology Officer",
            "message": "We're looking for automation solutions to streamline our sales process. We have a team of 200+ sales reps and need better lead management. Budget approved for Q1 implementation."
        }
        lead_id = mgr.get_or_create_lead_id(form_data["email"], form_data)
        # Simulate qualification result
        qualification_data = {
            "priority": "high",
            "lead_score": 85,
            "reasoning": "CTO-level contact from established company showing clear interest in automation solutions",
            "next_action": "Send follow-up email with solution overview",
            "lead_disposition": "hot",
            "disposition_confidence": 90,
            "sentiment": "positive",
            "urgency": "high"
        }
        mgr.save_qualification(lead_id, qualification_data)
        before = mgr.get_qualification(lead_id)
        print("[BEFORE] Lead info after qualification:", before)
        # Step 2: Simulate reply analysis (reply tab)
        reply_content = "Hi Alex, Thanks for reaching out! Your automation platform sounds exactly like what we need. I'd love to see a demo. Are you available for a call next Tuesday or Wednesday afternoon?"
        # Simulate reply analysis result
        reply_analysis = {
            "priority": "high",
            "lead_score": 99,
            "reasoning": "Lead explicitly states interest and requests a call",
            "next_action": "Schedule a discovery call within 24 hours",
            "lead_disposition": "engaged",
            "disposition_confidence": 95,
            "sentiment": "positive",
            "urgency": "high",
            "last_reply_analysis": "Lead explicitly states interest and requests a call",
            "recommended_follow_up": "Schedule a discovery call within 24 hours",
            "follow_up_timing": "immediate"
        }
        mgr.save_qualification(lead_id, reply_analysis)
        after = mgr.get_qualification(lead_id)
        print("[AFTER] Lead info after reply analysis:", after)
        # Step 3: Assert lead_id is the same and before/after states are consistent
        assert lead_id == mgr.get_or_create_lead_id(form_data["email"], form_data), "Lead ID should persist across tabs"
        assert before["priority"] == "high"
        assert after["priority"] == "high"
        assert after["lead_score"] == 99
        print("Test passed: Lead persisted and updated correctly across tabs.")
    finally:
        os.remove(db_path)

if __name__ == "__main__":
    main() 