import json

from crm.constants import default_crm_path

def load_leads(path=default_crm_path):
    with open(path, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    leads = load_leads()
    print(leads)
    breakpoint()
