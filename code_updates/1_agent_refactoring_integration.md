# Agent Refactoring Integration Plan

## Overview
Complete the refactoring of the leads AI agent system to ensure all experiments and UI components use the new refactored agent architecture from the `agents/` directory.

## Objectives
- Verify PYTHONPATH and environment setup is working correctly
- Clean up debug code from previous development sessions
- Ensure all experiments use refactored agents from `agents/` directory
- Verify UI components integrate properly with refactored agents
- Maintain test coverage and prevent regressions

## Step-by-Step Implementation Checklist

### Phase 1: Verify Current State & Clean Up
- [x] **1. Verify PYTHONPATH is working correctly**
  - [x] Run `echo $PYTHONPATH` to confirm current directory is included
  - [x] Test basic imports work: `python -c "from lib.env_vars import OPENAI_API_KEY; print('Import successful')"`

- [x] **2. Remove debug code from previous session**
  - [x] Clean up debug print statements in `agents/email_qualifier.py`
  - [x] Clean up debug print statements in `experiments/run_qualification.py`

- [x] **3. Run baseline tests**
  - [x] Execute `python -m pytest tests/ -v` to ensure no regressions
  - [x] Document current test status: **161 passed, 2 failed** - UI backend integration tests failing due to outdated mocks for refactored qualification experiment

### Phase 2: Test & Fix Core Qualification Functionality
- [x] **4. Test the qualification experiment**
  - [x] Run `python experiments/run_qualification.py`
  - [x] If it fails with "No structured data found", examine the LLM response format
  - [x] Fix either the prompt template or response parser as needed - **FIXED**: Updated parser to handle markdown formatting

- [ ] **5. Verify all experiments use refactored agents**
  - [ ] Check `experiments/run_reply_intent.py` uses `ReplyAnalyzer` from `agents/`
  - [ ] Check `experiments/run_schedule_meeting.py` uses `MeetingScheduler` from `agents/`
  - [ ] Check `experiments/run_qualify_followup.py` uses `EmailQualifier` from `agents/`
  - [ ] Update imports and initialization if needed

### Phase 3: Verify UI Integration
- [ ] **6. Check UI components use refactored agents**
  - [ ] Examine `ui/tabs/` to see which agents are imported
  - [ ] Verify `ui/components/` uses agents from `agents/` directory
  - [ ] Update imports and initialization patterns to match new agent architecture

- [ ] **7. Test UI integration**
  - [ ] Run the main application: `python app.py` or `python main.py`
  - [ ] Verify UI can successfully use the refactored agents
  - [ ] Check for any import errors or initialization issues

### Phase 4: Comprehensive Testing & Validation
- [ ] **8. Run comprehensive tests**
  - [ ] Execute all tests: `python -m pytest tests/ -v`
  - [ ] Ensure >90% line coverage as per RULES.md
  - [ ] Fix any failing tests

- [ ] **9. End-to-end validation**
  - [ ] Test each experiment script individually
  - [ ] Verify UI functionality works end-to-end
  - [ ] Confirm all agents work with real OpenAI API calls

- [ ] **10. Final cleanup and documentation**
  - [ ] Remove any remaining debug code
  - [ ] Ensure all imports follow the new architecture
  - [ ] Verify error handling is robust

## Success Criteria
- All tests pass with no regressions
- All experiments run successfully with real API calls
- UI integrates properly with refactored agents
- Code follows RULES.md guidelines (single responsibility, dependency injection, etc.)
- No debug code remains in production files

## Development Guidelines
Following RULES.md:
- **Single Responsibility**: Each change targets a specific integration issue
- **Test Coverage**: Maintain >90% line coverage, run tests frequently
- **Fail Fast**: Validate inputs early and provide meaningful error messages
- **Keep changes narrowly scoped**: Make minimal changes focused on integration
- **Early Returns**: Use guard clauses to reduce nesting
- **Meaningful Names**: Ensure all variables and functions are self-documenting

## Risk Mitigation
- Run tests after each phase to catch regressions early
- Keep changes minimal and focused
- Preserve existing functionality while updating architecture
- Document any breaking changes or required updates

## Timeline Estimate
- Phase 1: 15-20 minutes
- Phase 2: 30-45 minutes  
- Phase 3: 20-30 minutes
- Phase 4: 20-30 minutes
- **Total**: ~1.5-2 hours
