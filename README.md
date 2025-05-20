# AI Agent Demo – Smart Lead Engagement & CRM Enrichment

## Overview
This project demonstrates an AI agent that automates lead follow-ups, simulates multi-turn conversations, and updates a mock CRM with enriched information. It is designed for interview demonstration purposes.

## Features
- Mock CRM with sample leads
- AI agent logic (mocked LLM, memory, task chaining)
- Lead conversation simulator
- CRM enrichment and logging
- CLI or Streamlit UI (optional)

## Setup
1. Clone the repo
2. Install Python 3.10+ and dependencies (see requirements.txt)
3. Run the main script (to be implemented)

## Repo Structure
- `crm/` – Mock CRM data and loader
- `agent/` – AI agent logic and chains
- `simulator/` – Lead response simulator
- `logs/` – Output logs and CRM state
- `config/` – Configuration files

## Usage
To run any Python file in the repo, you can, beyond just normal `python <file>` usage, use the `run.sh` file. This sets the `PYTHONPATH` to be based on the current repo. For example, to run `python -m crm.load_data` with that script, you can run `./run.sh python -m crm.load_data`.
