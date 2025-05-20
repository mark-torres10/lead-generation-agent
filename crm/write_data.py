import json

from crm.constants import default_crm_path

def update_lead(lead_id, updates, path=default_crm_path):
    with open(path, "r") as f:
        leads = json.load(f)

    for lead in leads:
        if lead["id"] == lead_id:
            lead.update(updates)

    with open(path, "w") as f:
        json.dump(leads, f, indent=2)
