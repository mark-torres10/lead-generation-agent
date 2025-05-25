# Project Structure

This document outlines the organized structure of the Lead Qualification AI Agent project.

## Directory Structure

```
leads_ai_agent/
├── README.md                           # Main project documentation
├── PROJECT_STRUCTURE.md               # This file - project organization
├── 1_progress_updates.md              # Development progress tracking
├── constants.py                       # Project constants and configuration
├── requirements.txt                   # Python dependencies
├── data/                              # Data storage
│   └── memory.db                      # SQLite database for persistent memory
├── experiments/                       # Main application scripts
│   └── run_qualify_followup.py       # Main lead qualification script
├── lib/                              # Utility libraries and tools
│   ├── __init__.py                   # Package initializer
│   └── db/                           # Database utilities
│       ├── __init__.py               # Package initializer
│       └── inspect_database.py       # Database inspection tool
├── memory/                           # Memory management system
│   ├── __init__.py                   # Package initializer
│   └── memory_store.py               # SQLite memory store implementation
└── tests/                            # Test files
    ├── test_memory.py                # Original memory tests
    └── test_sqlite_memory.py         # SQLite memory system tests
```

## Key Components

### Core Application
- **`experiments/run_qualify_followup.py`**: Main script that qualifies leads and sends follow-up emails
- **`memory/memory_store.py`**: SQLite-based persistent memory system for storing lead qualifications, emails, and interactions

### Testing
- **`tests/test_sqlite_memory.py`**: Comprehensive tests for the SQLite memory system
- **`tests/test_memory.py`**: Legacy memory tests

### Utilities
- **`lib/db/inspect_database.py`**: Tool for inspecting the SQLite database contents
- **`constants.py`**: Configuration and constants used across the project

### Data
- **`data/memory.db`**: SQLite database file (created automatically)

## Usage

### Running the Main Application
```bash
python experiments/run_qualify_followup.py
```

### Testing the System
```bash
python tests/test_sqlite_memory.py
```

### Inspecting the Database
```bash
python lib/db/inspect_database.py
```

## Features

- **Persistent Memory**: SQLite-based storage for lead qualifications, sent emails, and interaction history
- **Lead Qualification**: AI-powered lead scoring and prioritization
- **Email Tracking**: Logging of all sent emails with timestamps
- **Interaction History**: Complete audit trail of all lead interactions
- **Database Inspection**: Tools for examining stored data

## Dependencies

All Python dependencies are listed in `requirements.txt`. The project requires Python 3.10 or higher. 