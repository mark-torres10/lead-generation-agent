# Agent Models Migration and Integration Plan

## Objective
Introduce and integrate Pydantic models for all core agent data structures in `@agents`, update type hints and usages in `@ui`, `@workflows`, and `@tests` to use these models, and ensure no test regressions. Add a `default_config.yaml` in `@config` for default configuration loading.

---

## Implementation Checklist

### 1. Model Design & Extraction
- [x] Review all core agent files in `@agents` (`agent_core.py`, `email_qualifier.py`, `meeting_scheduler.py`, `reply_analyzer.py`) to identify all input/output data structures that should be modeled.
- [x] For each agent, define Pydantic models in `@agents/models.py` for:
  - [x] Input data (e.g., lead info, meeting request, reply data)
  - [x] Output/result data (e.g., qualification result, meeting booking result, reply analysis result)
  - [x] Any shared/common structures (e.g., Lead, Meeting, Qualification, Reply, etc.)
- [x] Ensure all models have docstrings, type annotations, and validation logic as appropriate.
- [x] Refactor existing models in `models.py` to avoid duplication and ensure consistency.

### 2. Agent Refactoring
- [x] Refactor each agent class (`EmailQualifier`, `MeetingScheduler`, `ReplyAnalyzer`) to:
  - [x] Accept and return Pydantic models instead of raw dicts where appropriate.
  - [x] Update all method signatures and docstrings to use the new models and type hints.
  - [x] Ensure all internal data validation uses Pydantic model validation.
  - [x] Maintain backward compatibility for any public API that may be used externally (if required).

### 3. Workflow Updates
- [x] Update all workflow scripts in `@workflows` to:
  - [x] Use the new Pydantic models for agent input/output.
  - [x] Update type hints and variable names for clarity and consistency.
  - [x] Refactor any logic that manipulates agent data to use model attributes instead of dict keys.
  - [x] Ensure all workflow entry points and demo functions are compatible with the new models.

### 4. UI Integration (Pydantic Models & Config Loader)
- [x] Refactor all UI code in `@ui` to use the new config loader (`get_config`) for any agent/LLM config.
- [x] Remove any hardcoded config or direct environment variable usage in UI code.
- [x] Update all UI flows to use Pydantic models for agent data (inputs/outputs).
- [x] Update type hints and function signatures in UI to use Pydantic models.
- [x] Refactor UI logic to use model attributes instead of dict keys for agent data.
- [x] Ensure all UI demo and visualization flows (qualification, meeting scheduling, reply analysis) are compatible with the new models.
- [x] Manually test all UI flows for correct display and interaction with new models.
- [ ] Review UI for best UX practices, error handling, and user feedback.
- [ ] Document any UI config-driven options or behaviors in the UI or documentation.
- [x] Adhere to all standards and guidelines in `RULES.md`.

### 5. Test Refactoring
- [x] Update all tests in `@tests` and `@agents/tests` to:
  - [x] Use the new Pydantic models for constructing test data and asserting results.
  - [x] Update type hints and assertions to use model attributes.
  - [x] Refactor any test utilities or fixtures to use the new models.
  - [x] Ensure all tests pass with no regressions (tests must remain green).

### 6. Configuration Improvements
- [ ] Add a `default_config.yaml` file in `@config` with sensible defaults for agent configuration.
- [ ] Update config loading logic (if present) to fall back to `default_config.yaml` if no other config is provided.
- [ ] Document the config loading behavior in the README or relevant docstring.

### 7. Code Quality & Compliance
- [x] Ensure all changes follow the project's `RULES.md`:
  - [x] Single Responsibility Principle, Dependency Injection, Interface Segregation, etc.
  - [x] Complete type hints for all public APIs.
  - [x] No magic numbers, meaningful names, and function/method length limits.
  - [x] Test isolation, coverage, and naming standards.
- [x] Run static type checks (e.g., mypy) and linters (e.g., flake8, black) to ensure code quality.

### 8. Final Validation
- [x] Manually test all UI flows to ensure correct display and interaction with new models.
- [x] Review and update documentation/comments as needed for clarity.
- [x] Summarize changes and migration steps in a code update log.

---

**Note:**
- The original migration specs are referenced in `progress_updates/12_agent_models_migration.md`.
- **Remaining work:**
  - Migrate all Pydantic v1 validators to `@field_validator` for Pydantic v2 compliance.
  - Review UI for best UX practices, error handling, and user feedback.
  - Add and document `default_config.yaml` for agent configuration defaults.
  - Document any UI config-driven options or behaviors in the UI or documentation.
