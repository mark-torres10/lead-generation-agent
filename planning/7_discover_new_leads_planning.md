# UI Discover New Leads Tab Plan

## Problem Statement

- Users want to discover new potential leads at a company when they already know one contact (by email).
- There is no current UI workflow to:
    - Input a known lead's email
    - Find other users at the same domain (from known/demo data)
    - Select a discovered email to target
    - Generate and edit a personalized outreach email referencing the known contact
    - Submit the crafted outreach email
- If no other users are found for a domain, the UI should clearly communicate this.

---

## Solution Overview

- Add a new tab: **Discover new leads** (in `ui/tabs/discover_tab.py`)
- Allow user to:
    1. Enter an email (manual input or select from demo emails; one clears the other)
    2. On submit, extract domain and search for other emails in a dummy dataset (10 domains, 1 email per domain, with overlap to existing demo data)
    3. If matches found, display a list of discovered emails (excluding the original)
    4. User clicks an email to select
    5. LLM generates a draft outreach email referencing the original contact (editable by user)
    6. User can edit and submit the email
    7. If no matches, show a clear message: "Sorry, we didn't discover any new leads related to <original email>."
- Follow UI/UX and error handling best practices from `UI_PRINCIPLES.md` and `RULES.md`.

---

## UI/UX Plan

- **Tab Title:** Discover new leads
- **Step 1:** Email Input
    - Text input for manual email entry
    - Dropdown for demo emails (selecting one clears the other)
    - Clear, prominent call-to-action button
- **Step 2:** Domain Search
    - On submit, show loading indicator
    - If matches: show a card/list of discovered emails (with names if available)
    - If no matches: show a clear, friendly error message
- **Step 3:** Email Selection
    - User clicks a discovered email to select
    - Highlight selected email
- **Step 4:** Outreach Email Generation
    - LLM generates a draft outreach email referencing the original contact
    - Show editable text area for user to review/edit
    - Show reasoning/confidence if available (progressive disclosure)
    - Prominent submit button
- **Step 5:** Submission
    - On submit, show success message and summary
    - Log action for testability (no real email sent)
- **Visuals:**
    - Use Streamlit columns/cards for layout
    - Consistent spacing, clear section headers, progressive disclosure for details
    - Error/success states visually distinct

---

## Implementation Checklist

- [x] Create `ui/tabs/discover_tab.py` with new tab logic
- [x] Add 10 dummy domains/emails (with overlap to demo data)
- [x] Implement email/domain extraction and search logic
- [x] Implement UI for input, selection, and editing
- [x] Integrate LLM draft generation (mock for now, patch in tests)
- [x] Handle no-match and error states gracefully
- [x] Add unit/integration tests in `tests/test_ui_backend_integration.py`
- [x] Ensure all new code follows `UI_PRINCIPLES.md` and `RULES.md`
- [x] Activate conda env `lead-generation-agent` for all tests

---

## References
- See: `6_ui_meeting_tab_planning.md`, `5_ui_reply_tab_planning.md` for structure
- UI/UX: `UI_PRINCIPLES.md`
- Dev rules: `RULES.md`

---

**All future bugs and improvements for the Discover new leads tab will be tracked in this file.** 