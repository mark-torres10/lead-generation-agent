# Agent Models Migration and Integration Plan

## Objective
Introduce and integrate Pydantic models for all core agent data structures in `@agents`, update type hints and usages in `@ui`, `@workflows`, and `@tests` to use these models, and ensure no test regressions. Add a `default_config.yaml` in `@config` for default configuration loading.

---

## Implementation Checklist

### 1. Model Design & Extraction
- [ ] Review all core agent files in `@agents` (`agent_core.py`, `email_qualifier.py`, `meeting_scheduler.py`, `reply_analyzer.py`) to identify all input/output data structures that should be modeled.
- [ ] For each agent, define Pydantic models in `@agents/models.py` for:
  - [ ] Input data (e.g., lead info, meeting request, reply data)
  - [ ] Output/result data (e.g., qualification result, meeting booking result, reply analysis result)
  - [ ] Any shared/common structures (e.g., Lead, Meeting, Qualification, Reply, etc.)
- [ ] Ensure all models have docstrings, type annotations, and validation logic as appropriate.
- [ ] Refactor existing models in `models.py` to avoid duplication and ensure consistency.

### 2. Agent Refactoring
- [ ] Refactor each agent class (`EmailQualifier`, `MeetingScheduler`, `ReplyAnalyzer`) to:
  - [ ] Accept and return Pydantic models instead of raw dicts where appropriate.
  - [ ] Update all method signatures and docstrings to use the new models and type hints.
  - [ ] Ensure all internal data validation uses Pydantic model validation.
  - [ ] Maintain backward compatibility for any public API that may be used externally (if required).

### 3. Workflow Updates
- [ ] Update all workflow scripts in `@workflows` to:
  - [ ] Use the new Pydantic models for agent input/output.
  - [ ] Update type hints and variable names for clarity and consistency.
  - [ ] Refactor any logic that manipulates agent data to use model attributes instead of dict keys.
  - [ ] Ensure all workflow entry points and demo functions are compatible with the new models.

### 4. UI Integration
- [ ] Update all relevant UI files in `@ui` (`components`, `tabs`, `state`) to:
  - [ ] Accept and display data using the new Pydantic models.
  - [ ] Update type hints and function signatures for all UI components that interact with agent data.
  - [ ] Refactor any logic that accesses agent data to use model attributes.
  - [ ] Ensure all demo and visualization flows (e.g., qualification, meeting scheduling, reply analysis) are compatible with the new models.

### 5. Test Refactoring
- [ ] Update all tests in `@tests` and `@agents/tests` to:
  - [ ] Use the new Pydantic models for constructing test data and asserting results.
  - [ ] Update type hints and assertions to use model attributes.
  - [ ] Refactor any test utilities or fixtures to use the new models.
  - [ ] Ensure all tests pass with no regressions (tests must remain green).

### 6. Configuration Improvements
- [ ] Add a `default_config.yaml` file in `@config` with sensible defaults for agent configuration.
- [ ] Update config loading logic (if present) to fall back to `default_config.yaml` if no other config is provided.
- [ ] Document the config loading behavior in the README or relevant docstring.

### 7. Code Quality & Compliance
- [ ] Ensure all changes follow the project's `RULES.md`:
  - [ ] Single Responsibility Principle, Dependency Injection, Interface Segregation, etc.
  - [ ] Complete type hints for all public APIs.
  - [ ] No magic numbers, meaningful names, and function/method length limits.
  - [ ] Test isolation, coverage, and naming standards.
- [ ] Run static type checks (e.g., mypy) and linters (e.g., flake8, black) to ensure code quality.

### 8. Final Validation
- [ ] Manually test all UI flows to ensure correct display and interaction with new models.
- [ ] Review and update documentation/comments as needed for clarity.
- [ ] Summarize changes and migration steps in a code update log.

---

**Awaiting approval before proceeding with implementation.**
