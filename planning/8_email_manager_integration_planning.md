# Email Manager Integration Planning

## Status Update (2024-05-26, post-refactor and testable integration)

### Implementation
- `EmailManager` class implemented in `integrations/email_manager.py`.
- Integrated into `qualify_tab.py` and `reply_tab.py`.
- Email sending logic refactored into testable helpers: `send_qualification_email` and `send_reply_analysis_email`.
- Unit and integration tests updated/added to call these helpers directly and patch `EmailManager` for robust, UI-independent testing.
- Old `integrations/email.py` deleted.
- All direct EmailManager tests now reference the correct module and API.

### Test Results
- **All 167/167 tests passed.**
- No failures in any integration or unit tests.
- Integration tests for qualify/reply tabs now patch `EmailManager` and call the new helper functions directly, confirming that email sending is triggered as expected.
- No failures in the new email sending logic or its direct unit tests.

### Refactor Summary
- Email sending logic is now encapsulated in standalone, testable functions (`send_qualification_email`, `send_reply_analysis_email`).
- Integration tests no longer depend on UI context and can patch/mock `EmailManager` in isolation.
- This structure improves maintainability, test coverage, and extensibility for future email features.

### Next Steps
- [x] Fix or mock the SQLite database for all integration/UI tests (ensure test DB is available in all test contexts).
- [x] Patch or update UI tests to ensure all required display functions are mocked (e.g., `display_agent_reasoning`).
- [x] Update or refactor demo/test functions in qualify/reply tabs to ensure they are testable and covered by mocks.
- [x] Re-run the test suite to confirm all tests pass after these changes.
- [x] Refactor email sending logic into testable helpers and update integration tests accordingly.

---
_Last updated: 2024-05-26 by AI assistant._

## Problem Statement
- The current system only simulates email sending (e.g., logs or displays drafted emails) and does not send real emails.
- There is no unified, testable, or extensible integration for sending/receiving emails from the app.
- Users want to send actual emails (e.g., outreach, replies, qualification) to a real address (e.g., mtorres.sandbox@gmail.com) when submitting from the UI in `qualify_tab.py` and `reply_tab.py`.
- Email logic is scattered or missing; no single class manages email connections, sending, or future receiving/monitoring.

---

## Solution Overview
- Create a new `integrations/` folder and an `email.py` module.
- Implement an `EmailManager` class that:
    - Manages all email connections (e.g., SMTP, OAuth, etc. as needed)
    - Exposes a public API: `send_email(message: str, recipients: list[str], subject: str, cc: list[str] = [], bcc: list[str] = [], attachments: list[str] = [], sender: str = None, **kwargs)`
    - Handles sending emails to real addresses (initially, mtorres.sandbox@gmail.com for sandbox/testing)
    - Is designed for easy extension to support receiving, monitoring, and multiple accounts in the future
    - Uses dependency injection for testability (see `RULES.md`)
- Update `ui/tabs/qualify_tab.py` and `ui/tabs/reply_tab.py`:
    - On email submission, call `EmailManager.send_email` with the drafted message and relevant fields
    - Continue to show the drafted email in the UI for user feedback
    - Show a success/failure message based on the real email send result
- Ensure all new code follows `UI_PRINCIPLES.md` and `RULES.md` (clarity, error handling, type hints, testability, etc.)
- Add/extend tests to cover the new integration (mocking real email sends in unit tests)

---

## UI/UX Plan
- No major UI changes, but:
    - On submit in both tabs, show a clear success/failure message for the real email send (in addition to displaying the drafted email)
    - If sending fails, show a user-friendly error and log details for debugging
    - Ensure all actions are visually distinct (success, error, info)
    - Follow progressive disclosure: only show technical error details if needed
    - Maintain all existing UI/UX best practices (see `UI_PRINCIPLES.md`)

---

## Implementation Checklist
- [x] Create `integrations/` folder and `email.py` module
- [x] Implement `EmailManager` class with `send_email` public API (with type hints)
- [x] Support basic SMTP (e.g., Gmail sandbox) for initial implementation
- [x] Add configuration/env support for email credentials (do not hardcode)
- [x] Update `ui/tabs/qualify_tab.py` to use `EmailManager.send_email` on submit
- [x] Update `ui/tabs/reply_tab.py` to use `EmailManager.send_email` on submit
- [x] Show real email send result in the UI (success/failure)
- [x] Add/extend unit and integration tests (mocking email sends)
- [x] Ensure all new code follows `RULES.md` and `UI_PRINCIPLES.md`
- [x] Document usage and configuration in README if needed

---

## References
- Planning format: `planning/FORMAT.md`
- UI/UX: `UI_PRINCIPLES.md`
- Dev rules: `RULES.md`
- Example tabs: `ui/tabs/qualify_tab.py`, `ui/tabs/reply_tab.py`
- Existing email stubs: `tools/email_client.py`, `context/email_parser.py`, `agents/email_qualifier.py`, `ui/components/email_display.py`

---

**All future bugs and improvements for the EmailManager integration will be tracked in this file.** 