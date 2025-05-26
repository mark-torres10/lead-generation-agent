# UI Qualification Results Enhancement Plan

## Objective
Modernize and enrich the qualification results display in the UI to:
- Surface key signals/factors that influenced the AI's decision
- Show what would improve the AI's confidence (if confidence is low)
- Display before/after CRM state for the lead
- Show a timeline of all interactions/submissions for the lead (persisted in SQLite)
- Ensure all changes are robustly tested and validated

# Recent UI Fixes and Bug Fixes (Changelog Candidates)

- **Fix:** Improved urgency extraction in lead qualification. The LLM prompt now includes explicit instructions and examples for mapping natural language cues (e.g., 'wrapped up in 4-6 weeks', 'budget approved for Q1', 'as soon as possible') to the correct urgency level. 'Not specified' is only used if there are truly no urgency cues. This ensures that leads with clear timing or deadline signals are classified with 'high' or 'urgent' urgency, not 'not specified'.

- **Fix:** Form submission now always uses user-edited values, not just sample defaults. The form data submitted to the agent reflects any changes made by the user after selecting a sample, ensuring accurate qualification and display.
- **Fix:** The "Clear Results" button now robustly resets the UI state and does not raise exceptions, even if the previous result was a Pydantic model or had missing fields.
- **Fix:** The urgency field in qualification results now displays "Not specified" if missing, empty, or invalid, and provides user guidance to improve AI confidence by adding more details.
- **Test:** Added unit tests to ensure:
    - Form submission uses the latest user-edited or custom values (not just sample data).
    - Clearing results does not raise exceptions and resets the UI state as expected.
    - Urgency fallback logic is robust for minimal or incomplete lead submissions.

**Note:** All future described changes or bug fixes will be appended to this section for tracking and changelog generation.

---

## Implementation Checklist

### 1. Signals/Factors & Confidence Improvement
- [x] Update backend (agent & workflow) to extract and return key signals/factors used in qualification (urgency extraction fix)
- [x] Update prompt templates to encourage LLM to output signals/factors and confidence improvement suggestions (urgency prompt fix)
- [ ] Update `LeadQualificationResult` model to include `signals` (List[str]) and `confidence_improvements` (List[str] or str)
- [ ] Update UI to display signals/factors as chips or a list
- [ ] Update UI to display "What would improve confidence?" if confidence < threshold
- [x] Add/extend tests in `tests/test_ui_backend_integration.py` to validate:
    - [x] Signals/factors are present and displayed
    - [x] Confidence improvement suggestions are present and displayed when confidence is low
    - [x] Urgency fallback logic is robust for minimal or incomplete lead submissions
    - [x] Form submission uses the latest user-edited or custom values (not just sample data)
    - [x] Clearing results does not raise exceptions and resets the UI state as expected

### 2. CRM Before/After Display
- [ ] Update UI to show a side-by-side before/after CRM record for the lead
- [ ] Ensure the "before" state is always the unqualified/default state
- [ ] Ensure the "after" state uses the latest qualification result
- [ ] Add/extend tests to validate correct before/after display for new and repeat leads

### 3. Timeline/Interaction History
- [ ] Update backend to log every qualification submission/interactions for a lead in SQLite
- [ ] Update UI to display a timeline of all interactions/submissions for the lead
- [ ] Add/extend tests to validate:
    - [ ] Timeline is updated on each submission
    - [ ] Timeline persists across multiple submissions for the same lead/email

### 4. Integration & UX Polish
- [ ] Review UI for clarity, accessibility, and stakeholder appeal
- [ ] Add tooltips, icons, and color coding for clarity
- [ ] Ensure all new fields are optional and robust to missing data
- [ ] Add/extend tests for all new UI/UX logic

---

## Notes
- All code changes must adhere to `RULES.md` (clarity, type safety, testability, etc.)
- Pause for review after this plan is written before proceeding with implementation. 