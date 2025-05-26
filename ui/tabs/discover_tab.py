"""
Discover New Leads Tab - Backend Logic Stubs
"""

import streamlit as st
from agents.agent_core import AgentCore
from lib.constants import default_model
from lib.env_vars import OPENAI_API_KEY

DUMMY_LEADS = []

def find_leads_by_domain(email: str):
    """Return a list of leads at the same domain as the given email, excluding the email itself."""
    if not email or '@' not in email:
        return []
    domain = email.split('@', 1)[1].lower()
    return [lead for lead in DUMMY_LEADS if lead["email"].split('@', 1)[1].lower() == domain and lead["email"].lower() != email.lower()]

def generate_outreach_email(target_email: str, known_email: str) -> str:
    """Generate a draft outreach email to target_email referencing known_email using LLM."""
    # Find target lead info
    target_lead = next((lead for lead in DUMMY_LEADS if lead["email"].lower() == target_email.lower()), None)
    known_lead = next((lead for lead in DUMMY_LEADS if lead["email"].lower() == known_email.lower()), None)
    target_name = target_lead["name"] if target_lead else "there"
    target_company = target_lead["company"] if target_lead else "your company"
    known_name = known_lead["name"] if known_lead else known_email.split("@")[0].title()

    # LLM config
    llm_config = {
        "model": default_model,
        "temperature": 0.3,
        "max_tokens": 500,
        "api_key": OPENAI_API_KEY,
    }
    agent_core = AgentCore(llm_config)
    prompt_template = (
        """
        You are an expert sales development rep. Write a concise, friendly, and highly personalized cold outreach email to {{target_name}} at {{target_company}}. 
        Reference that you are already in touch with their colleague {{known_name}} ({{known_email}}) to establish credibility. 
        Clearly communicate the value of your service: saving hours of manual lead research and message crafting, and helping {{target_company}} discover new opportunities faster. 
        Make the email actionable, easy to read, and end with a clear call to connect. 
        Sign as Alex Thompson, Senior Solutions Consultant.
        Only output the email body (no subject line).
        """
    )
    input_variables = ["target_name", "target_company", "known_name", "known_email"]
    try:
        chain = agent_core.create_llm_chain(prompt_template, input_variables)
        email_body = chain.run(
            target_name=target_name,
            target_company=target_company,
            known_name=known_name,
            known_email=known_email,
        )
        return email_body.strip()
    except Exception as e:
        # Fallback to mock
        print(f"Error generating outreach email: {e}\nFallback to mock")
        return f"Hi {target_name},\n\nI'm reaching out because I'm already working with {known_name} at {target_company}. I thought you might also benefit from what we're doing—helping teams like yours save hours on lead research and outreach. Would you be open to a quick call to explore?\n\nBest,\nAlex Thompson\nSenior Solutions Consultant"

def submit_outreach_email(target_email: str, email_body: str) -> dict:
    """Simulate submitting the outreach email. Returns a dict with success and message."""
    log_outreach_action(target_email, email_body)
    return {"success": True, "message": f"Outreach email sent to {target_email}."}

def no_leads_found_message(email: str) -> str:
    """Return a user-friendly message if no leads are found for the domain."""
    if not email or '@' not in email:
        return "Sorry, we didn't discover any new leads related to {}.".format(email)
    domain = email.split('@', 1)[1].lower()
    return f"Sorry, we didn't discover any new leads related to {email} (domain: {domain})."

def handle_input_change(manual_input: str, demo_selected: str):
    """Allow both manual and demo to be set. If both are set, prefer manual_input if non-empty. Only clear demo_selected if manual_input is set and non-empty."""
    if manual_input:
        return manual_input, ""
    return manual_input, demo_selected

def log_outreach_action(target_email: str, email_body: str):
    """Log the outreach action for testability (no real email sent)."""
    pass

def render_discover_tab():
    """Render the Discover New Leads tab UI."""
    st.markdown("""
    ### 🔎 Discover New Leads
    
    Enter the email of a known contact to discover other potential leads at the same company. Select a discovered email to generate and edit a personalized outreach email.
    """)

    st.markdown("""
    #### Ways we can discover new leads
    - **CC/BCC on emails**: Identify additional contacts included in email threads.
    - **Attendees on Zoom/Google Calendar meetings**: Extract leads from meeting participant lists.
    - **3rd party integrations**: Leverage platforms like Leadspace, LinkedIn, Apollo, and Clearbit for enriched lead data.
    - **CRM exports**: Import leads from Salesforce, HubSpot, or other CRM systems.
    - **Website form submissions**: Capture new leads from demo requests, contact forms, or newsletter signups.
    - **Public company directories**: Scrape or import contacts from company websites or industry directories.
    - **Social media connections**: Find leads via LinkedIn connections, Twitter followers, or relevant groups.
    - **Event attendee lists**: Use lists from conferences, webinars, or trade shows.
    """)

    # --- Demo data (10 dummy leads, some overlap with other tabs) ---
    global DUMMY_LEADS
    if not DUMMY_LEADS:
        DUMMY_LEADS = [
            {"name": "Alice Johnson", "email": "alice@acmecorp.com", "company": "Acme Corp"},
            {"name": "Bob Smith", "email": "bob@acmecorp.com", "company": "Acme Corp"},
            {"name": "Sarah Chen", "email": "sarah.chen@techcorp.com", "company": "TechCorp Industries"},
            {"name": "David Kim", "email": "david.kim@innovatetech.com", "company": "InnovateTech Solutions"},
            {"name": "Priya Patel", "email": "priya@finwise.com", "company": "Finwise"},
            {"name": "John Lee", "email": "john.lee@medigen.com", "company": "Medigen"},
            {"name": "Maria Garcia", "email": "maria@greengrid.com", "company": "GreenGrid"},
            {"name": "Tom Brown", "email": "tom@buildwise.com", "company": "Buildwise"},
            {"name": "Linda Xu", "email": "linda@cybercore.com", "company": "Cybercore"},
            {"name": "Omar Farouk", "email": "omar@logix.com", "company": "Logix"},
        ]

    # --- State management ---
    if 'discover_manual_email' not in st.session_state:
        st.session_state.discover_manual_email = ""
    if 'discover_demo_email' not in st.session_state:
        st.session_state.discover_demo_email = ""
    if 'discover_selected_lead' not in st.session_state:
        st.session_state.discover_selected_lead = None
    if 'discover_outreach_draft' not in st.session_state:
        st.session_state.discover_outreach_draft = ""
    if 'discover_submit_result' not in st.session_state:
        st.session_state.discover_submit_result = None

    # --- Email input section ---
    st.subheader("Step 1: Enter or Select a Known Lead's Email")
    col1, col2 = st.columns([2, 1])
    with col1:
        manual_email = st.text_input("Enter email of a known contact", value=st.session_state.discover_manual_email, key="discover_manual_email_input")
    with col2:
        demo_options = [lead["email"] for lead in DUMMY_LEADS]
        demo_email = st.selectbox("Or pick a demo email", ["(None)"] + demo_options, index=0, key="discover_demo_email_select")
        if demo_email == "(None)":
            demo_email = ""

    # --- Input logic: prefer manual if set ---
    manual_email, demo_email = handle_input_change(manual_email, demo_email)
    st.session_state.discover_manual_email = manual_email
    st.session_state.discover_demo_email = demo_email
    input_email = manual_email or demo_email

    # --- Step 2: Discover leads ---
    discovered_leads = []
    if input_email:
        discovered_leads = find_leads_by_domain(input_email)
        if discovered_leads:
            st.success(f"Found {len(discovered_leads)} other lead(s) at this domain:")
            for i, lead in enumerate(discovered_leads):
                lead_label = f"{lead['name']} <{lead['email']}>"
                if st.button(f"Select {lead_label}", key=f"discover_select_{i}"):
                    st.session_state.discover_selected_lead = lead
        else:
            st.warning(no_leads_found_message(input_email))
    else:
        st.info("Enter or select an email to discover new leads.")

    # --- Step 3: Outreach email generation ---
    selected_lead = st.session_state.discover_selected_lead
    if selected_lead:
        st.subheader(f"Step 3: Generate Outreach Email to {selected_lead['name']} <{selected_lead['email']}> (editable)")
        st.info("""
        **Save hours of manual research and message crafting** — let AI generate a personalized, high-converting outreach email in seconds.\n\nThis email references your existing contact to boost credibility and is tailored to maximize response rates.
        """, icon="💡")
        # Try to generate outreach email, fallback to mock
        try:
            draft = generate_outreach_email(selected_lead["email"], input_email)
        except Exception:
            draft = f"Hi {selected_lead['name']},\n\nWe're working with {input_email} and thought you might be interested in what we're doing at {selected_lead['company']}. Would love to connect!\n\nBest,\nYour Name"
        st.session_state.discover_outreach_draft = st.text_area("Outreach Email Draft", value=draft, height=180, key="discover_outreach_draft_area")
        if st.button("Send Outreach Email", key="discover_send_btn"):
            result = submit_outreach_email(selected_lead["email"], st.session_state.discover_outreach_draft)
            st.session_state.discover_submit_result = result
            st.success(result["message"])
    elif input_email and discovered_leads:
        st.info("Select a lead above to generate an outreach email.")

    # --- Step 4: Submission result ---
    if st.session_state.discover_submit_result:
        st.success(st.session_state.discover_submit_result["message"]) 