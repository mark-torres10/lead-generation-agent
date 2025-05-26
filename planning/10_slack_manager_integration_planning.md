# Slack Manager Integration Plan

## Problem Statement

- There is currently no integration for Slack in the system.
- Users want notifications in Slack channels for key events (lead qualification, inbound replies, meeting invites).
- Manual copy-pasting of email/calendar content into Slack is inefficient and error-prone.
- There is no unified, testable, or extensible integration for posting to Slack channels from the app.
- Slack channel IDs may change, and channel names must be mapped reliably.

---

## Solution Overview

- Implement a `SlackManager` class in `integrations/slack_manager.py`.
    - Handles authentication using the `SLACK_BOT_TOKEN` from `lib/env_vars.py`.
    - Uses the official `slack_sdk` for robust, future-proof integration.
    - Provides a public API: `send_message(channel_name: str, title: str, body: str)`.
        - Finds the channel ID by name (caching for efficiency).
        - Posts a message with the title in **bold** and the body as plain text.
    - Handles errors gracefully and logs them.
- Add a test suite in `integrations/tests/test_slack_manager.py`:
    - Mocks Slack API calls for unit testing.
    - Tests channel lookup, message formatting, and error handling.
- Document usage in `integrations/README.md`.
- Add `slack_sdk` to `requirements.in` and update `requirements.txt`.

---

## UI/UX Plan

- Not directly applicable (backend integration).
- Ensure that any UI-triggered Slack notifications display clear success/failure messages if surfaced.
- Log and surface errors in a user-friendly way if needed.

---

## Implementation Checklist

- [x] Add `slack_sdk` to `integrations/requirements.in` and recompile `requirements.txt`.
- [x] Implement `SlackManager` in `integrations/slack_manager.py`:
    - [x] Load and validate `SLACK_BOT_TOKEN` from `lib/env_vars.py`.
    - [x] Implement channel name → ID lookup (with caching).
    - [x] Implement `send_message(channel_name, title, body)` with proper formatting.
    - [x] Handle and log errors robustly.
- [x] Add unit tests in `integrations/tests/test_slack_manager.py`:
    - [x] Test successful message sending.
    - [x] Test channel lookup and caching.
    - [x] Test error handling (e.g., invalid token, channel not found).
- [ ] Update `integrations/README.md` with Slack integration usage.
- [x] Ensure all new code follows `RULES.md` and is type-annotated.
- [x] (Optional) Add a `__main__` block for standalone testing.

---

## Progress Note

- SlackManager is fully implemented, tested, and integrated into all relevant UI tabs. All core requirements are complete and verified. Only documentation in `integrations/README.md` remains.

---

## References

- Planning format: `