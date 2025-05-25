from crm.load_data import load_leads
from crm.write_data import update_lead
from simulator.interaction_engine import run_conversation

def process_all_leads():
    leads = load_leads()
    for lead in leads:
        if lead["status"] == "new":
            result = run_conversation(lead)
            update_lead(lead["id"], {
                "status": "contacted",
                "inferred_priority": result["priority"],
                "recommended_action": result["next_action"],
                "interaction_history": result["history"]
            })
            print(f"Processed {lead['name']}")

if __name__ == "__main__":
    process_all_leads()
