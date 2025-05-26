# Google API Integration Plan

## Problem Statement

- The current integrations structure only supports Gmail (email) and is not organized for extensibility or code reuse.
- There is no support for Google Calendar API, which is needed for new features (e.g., reading/updating calendar events).
- Common Google API logic (OAuth, credential management, service building) is duplicated or will be duplicated across integrations.
- The current flat structure in `integrations/` does not clearly separate Google-specific integrations or encourage modularity.
- There is no unified approach for adding new Google Workspace integrations in the future.

---

## Solution Overview

- Refactor `integrations/` to include a `google/` subfolder for all Google Workspace integrations.
- Move `email_manager.py` into `integrations/google/`.
- Create a new `calendar_manager.py` in `integrations/google/` for Google Calendar API integration.
- Factor out all shared Google API logic (OAuth, credential loading, service creation, token management) into a new `google_api_core.py` base module/class.
    - Both `EmailManager` and `CalendarManager` will inherit from or use this base class for authentication and service setup.
- Ensure both managers have a `__main__` block for standalone testing, following the pattern in `email_manager.py`.
- Update documentation and requirements as needed.

---

## UI/UX Plan

- Not directly applicable for backend integration, but:
    - Ensure any UI that triggers calendar or email actions displays clear success/failure messages.
    - Log and surface errors in a user-friendly way.
    - Maintain all existing UI/UX best practices (see `UI_PRINCIPLES.md`).

---

## Implementation Checklist

- [x] Create `integrations/google/` subfolder.
- [x] Move `email_manager.py` to `integrations/google/email_manager.py`.
- [x] Create `integrations/google/calendar_manager.py` with a class for Calendar API access.
- [x] Implement `google_api_core.py` with:
    - Credential loading (from `credentials.json`/`token.json`)
    - OAuth flow and token refresh logic
    - Service builder for arbitrary Google APIs
    - Configurable scopes per integration
- [x] Refactor `EmailManager` to inherit from/use `GoogleAPICore`.
- [x] Implement `CalendarManager` to inherit from/use `GoogleAPICore` and provide methods for basic calendar operations (e.g., list upcoming events).
- [x] Add `if __name__ == "__main__"` blocks to both managers for standalone testing.
- [x] Update or add README documentation for new structure and usage.
- [x] Update requirements if needed (ensure all Google API dependencies are present).
- [x] Add/extend unit and integration tests (mocking API calls as needed).
- [x] Ensure all new code follows `RULES.md` and `UI_PRINCIPLES.md`.

---

## Progress Update (2025-05-26)

- Google Calendar integration is complete and fully functional.
- UI for meeting scheduling now allows users to select both day and time, with real-time slot availability from Google Calendar.
- All calendar invites are sandboxed for safety.
- The user experience is modern, robust, and prevents double-booking.
- All planned backend and UI/UX improvements for this phase are done.

---

## References

- Planning format: `planning/FORMAT.md`
- Email integration plan: `planning/8_email_manager_integration_planning.md`
- Google Calendar Python Quickstart: [Google Calendar API Quickstart](https://developers.google.com/calendar/api/quickstart/python)
- Existing code: `integrations/email_manager.py`
- UI/UX: `UI_PRINCIPLES.md`
- Dev rules: `RULES.md`

---

**All future bugs and improvements for Google API integrations will be tracked in this file.** 