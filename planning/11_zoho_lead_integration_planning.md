# Zoho CRM Lead Integration Plan

## Problem Statement

- The current system does not create leads in Zoho CRM when a new contact is qualified via the UI.
- There is no Zoho integration module in `integrations/`, and no code path from `qualify_tab.py` to Zoho.
- Lead data is not synchronized with Zoho CRM, limiting sales workflow automation and reporting.
- Users want every qualified lead to be automatically created in Zoho CRM upon form submission.

---

## Solution Overview

- Created a new `zoho_manager.py` module in `integrations/` for Zoho CRM integration.
- Implemented a `ZohoManager` class with a public API:  
  `create_lead(data: dict) -> dict`
    - Accepts a dictionary of lead/contact data.
    - Handles all Zoho API logic for creating a lead using the `requests` library (SDK was not reliable in this environment).
    - Returns the Zoho API response or raises a clear exception on failure.
- All Zoho authentication/config is loaded from environment or config files (never hardcoded).
- In `ui/tabs/qualify_tab.py`, after a successful form submission and qualification, `ZohoManager.create_lead()` is called with the relevant data and `source` set to "Qualification Inbound".
- Displays a clear success/failure message in the UI based on the Zoho API result.
- Automated access token refresh using the `refresh_token`, `client_id`, and `client_secret` from config.
- Added/extended tests to mock Zoho API calls and verify correct data is sent.
- Documented usage and configuration in the README if needed.

---

## UI/UX Plan

- No major UI changes.
- On form submission, after qualification and email send:
    - Attempts to create the lead in Zoho CRM.
    - Shows a clear success or error message to the user (e.g., "Lead created in Zoho CRM" or "Failed to create lead in Zoho: <error>").
    - Logs technical errors for debugging, but only shows user-friendly messages in the UI.
- Follows all existing UI/UX best practices (`UI_PRINCIPLES.md`).

---

## Implementation Checklist

- [x] Create `integrations/zoho_manager.py` with a `ZohoManager` class.
- [x] Implement `create_lead(data: dict)` using the Zoho API via the `requests` library (SDK replaced due to reliability issues).
- [x] Load Zoho auth/config from environment or config files.
- [x] Add error handling and logging for all API calls.
- [x] Add a testable helper function for lead creation (for mocking in tests).
- [x] Update `ui/tabs/qualify_tab.py` to call `ZohoManager.create_lead()` after qualification.
- [x] Display Zoho lead creation result in the UI.
- [x] Add/extend unit and integration tests (mocking Zoho API).
- [x] Document usage/configuration in the README if needed.
- [x] Ensure all new code follows `RULES.md` and `UI_PRINCIPLES.md`.

---

## Notes

- The official Zoho Python SDK was not working reliably in this environment, so the integration uses the `requests` library for direct API calls. Access token refresh is fully automated.

---

## References

- Planning format: `planning/FORMAT.md`
- Email integration plan: `planning/8_email_manager_integration_planning.md`
- Google API integration plan: `planning/9_google_api_integration_planning.md`
- Zoho API docs: https://www.zoho.com/crm/developer/docs/api/v2/
- Example code chunk (see user message)
- UI/UX: `UI_PRINCIPLES.md`
- Dev rules: `RULES.md`
- `integrations/zoho_manager.py`, `ui/tabs/qualify_tab.py`

---

**All future bugs and improvements for the Zoho integration will be tracked in this file.** 