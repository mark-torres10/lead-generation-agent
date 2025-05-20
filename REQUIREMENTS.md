# 🧾 Product Requirements Document (PRD)

## Title  
AI Agent Demo – Smart Lead Engagement & CRM Enrichment

## Prepared For  
Interview demonstration for an AI automation role involving CRM, LLM agents, and business operations automation.

---

## 1. Objective

Build a demo-ready AI agent that automates lead follow-ups, simulates multi-turn conversations, and updates a CRM with contextually enriched information such as interaction history, inferred lead priority, and recommended next steps.

This demo should:
- Demonstrate agentic reasoning with memory.
- Highlight CRM integration (mocked).
- Show how to scale memory and task chaining in real-world use.
- Simulate multiple leads and multiple back-and-forth conversations.

---

## 2. Scope & Constraints

- ❌ No real API access to Zoho, Gmail, or Pinecone.
- ✅ Everything must be simulated or mocked.
- ⏱ Time constraint: 20 hours.
- 🎯 Target audience: Interviewers evaluating AI agentic system design, implementation fluency, and product thinking.

---

## 3. Functional Requirements

| Feature                             | Description                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| Lead ingestion                      | Load leads from mock CRM (JSON or SQLite)                                   |
| AI agent logic                      | Use LangChain agent with memory + chained tasks                             |
| Email generation                    | Use OpenAI (or mock) to create follow-up emails                             |
| Lead conversation simulator         | Simulate 5-turn conversations with interested and disinterested leads       |
| CRM enrichment                      | Update CRM with: status, priority, next_action, interaction_history         |
| Logging and visualization           | View email content and CRM updates; optional: Streamlit or logs             |
| Memory management                   | Store history per lead; simulate summarization tradeoff logic               |
| Multi-lead processing               | Process multiple leads in a single run with isolated memory per lead        |

---

## 4. Non-Functional Requirements

- Run locally (CLI or Streamlit UI)
- Python 3.10+, LangChain, OpenAI (mockable), basic data storage
- No need for login/authentication
- Clear logs and structured output

---

## 5. Architecture Overview

```
+-------------------------+
|    Mock CRM (JSON)      |
+-------------------------+
             |
             v
+-------------------------+
| AI Agent (LangChain)    |   <-- Memory per lead (in-memory or file-based)
| - Email composer        |
| - Lead qualifier        |
| - Action recommender    |
+-------------------------+
             |
             v
+-------------------------+
| Lead Response Simulator |
+-------------------------+
             |
             v
+-------------------------+
| CRM Updater + Logger    |
+-------------------------+
```

---

## 6. Data Models

### Lead (from CRM)
```json
{
  "id": "lead_001",
  "name": "Alice",
  "email": "alice@acme.com",
  "company": "Acme Corp",
  "interests": "dashboards, marketing automation",
  "status": "new",
  "interaction_history": [],
  "inferred_priority": null,
  "recommended_action": null
}
```

### Conversation Turn
```json
{
  "agent": "Hi Alice, I saw you're interested in dashboards...",
  "lead": "Yes, we're exploring some tools."
}
```

---

## 7. Implementation Order

| Phase | Task                                                                 |
|-------|----------------------------------------------------------------------|
| 0     | Scaffold repo: create CRM mock, config, and setup                    |
| 1     | Build mock CRM loader/updater (JSON-based)                          |
| 2     | Implement LangChain agent with memory                               |
| 3     | Add task chaining: email → priority → action                        |
| 4     | Simulate 5-turn conversations (agent ↔ simulated lead)              |
| 5     | Update CRM with output: status, interaction history, recommendations|
| 6     | Run multi-lead loop with isolated memory                            |
| 7     | Add logs or Streamlit UI for demo                                   |
| 8     | Document memory scaling strategies (summarization, Pinecone, Redis) |
| 9     | Write README + interview script                                     |

---

## 8. Epics and Stories (Checklist)

### ✅ EPIC 1: Foundation Setup
- [x] Scaffold project: create folders for `crm/`, `agent/`, `simulator/`, `logs/`
- [x] Install dependencies (LangChain, OpenAI, etc.)
- [x] Create `mock_crm.json` with 3–5 sample leads

### ✅ EPIC 2: Agent Core Logic
- [x] Build LangChain LLMChain for email generation
- [x] Add chain for priority inference
- [x] Add chain for action recommendation
- [x] Combine into `SequentialChain`

### ✅ EPIC 3: Agent Memory Handling
- [x] Use `ConversationBufferMemory` or `dict` per lead
- [x] Store memory per lead during run
- [x] Use memory to vary tone/content in follow-ups

### ✅ EPIC 4: Lead Simulator
- [x] Simulate lead responses (interested + uninterested flows)
- [x] Run 5-turn exchanges for each flow
- [x] Log conversation history

### ✅ EPIC 5: CRM Updates & Enrichment
- [x] Update CRM with: new status, priority, recommended action
- [x] Append to interaction history

### ✅ EPIC 6: Orchestration for Multi-Lead
- [x] Loop over leads with independent memory
- [x] Run agent + simulator + update CRM
- [x] Print/log output per lead

### ✅ EPIC 7: Optional UI + Logging
- [x] CLI-based or Streamlit visualizer
- [x] Show CRM state before and after
- [x] Log JSONs of interactions

### ✅ EPIC 8: Memory Scaling Design
- [x] Write design notes for Pinecone integration
- [x] Outline summarization vs full-history tradeoffs
- [x] Describe fallback strategies

---

## 9. Success Criteria (MVP Demo)

- ✅ At least 2 leads simulated end-to-end (1 interested, 1 not)
- ✅ Each lead has 5-turn back-and-forths
- ✅ Output includes memory usage, updated CRM, and actionable insight
- ✅ You can walk through how this design scales with real APIs and vector memory
