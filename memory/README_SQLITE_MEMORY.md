# SQLite Memory System for Lead Qualification

This system uses SQLite for persistent storage of lead qualification data, interaction history, and sent emails.

## Architecture

The memory system consists of three main tables:

### 1. `qualification_memory`
Stores lead qualification results:
- `lead_id` (PRIMARY KEY): Unique identifier for the lead
- `priority`: Lead priority (high/medium/low)
- `lead_score`: Numerical score (0-100)
- `reasoning`: LLM's reasoning for the qualification
- `next_action`: Recommended next action
- `created_at`: When first qualified
- `updated_at`: When last updated

### 2. `interaction_history`
Tracks all interactions with leads:
- `id`: Auto-incrementing primary key
- `lead_id`: Foreign key to qualification_memory
- `event_type`: Type of interaction (e.g., "qualification")
- `event_data`: JSON data about the interaction
- `timestamp`: When the interaction occurred

### 3. `sent_emails`
Logs all emails sent to leads:
- `id`: Auto-incrementing primary key
- `lead_id`: Associated lead (can be NULL)
- `to_address`: Recipient email address
- `subject`: Email subject line
- `body`: Email content
- `sent_at`: When the email was sent

## Usage

### Basic Operations

```python
from memory.memory_store import memory_store

# Save qualification results
memory_store.save_qualification("lead_001", {
    "priority": "high",
    "lead_score": 85,
    "reasoning": "Strong interest and budget signals",
    "next_action": "Schedule demo call"
})

# Retrieve qualification
qualification = memory_store.get_qualification("lead_001")

# Check if lead has been qualified
if memory_store.has_qualification("lead_001"):
    print("Lead already qualified")

# Log an interaction
memory_store.add_interaction("lead_001", "qualification", {
    "event": "qualified",
    "priority": "high",
    "score": 85
})

# Log sent email
memory_store.log_sent_email("lead_001", "alice@example.com", "Follow-up", "Email content")
```

### Advanced Queries

```python
# Get all qualified leads
all_leads = memory_store.get_all_leads()

# Get interaction history for a lead
interactions = memory_store.get_interaction_history("lead_001")

# Get sent emails for a specific lead
emails = memory_store.get_sent_emails("lead_001")

# Get all sent emails
all_emails = memory_store.get_sent_emails()
```

## Testing

Run the comprehensive test suite:

```bash
python test_sqlite_memory.py
```

This test demonstrates:
- Database initialization
- Lead qualification with memory context
- Email logging
- Interaction history tracking
- Data persistence across instances

## Database Inspection

Use the inspection tool to view database contents:

```bash
python inspect_database.py
```

This shows:
- Database file location and size
- Total qualified leads
- Sent emails summary
- Interaction history
- Raw table counts

## Benefits of SQLite Memory

1. **Persistence**: Data survives application restarts
2. **Scalability**: Can handle thousands of leads efficiently
3. **Queryability**: Use SQL for complex queries and reporting
4. **Reliability**: ACID transactions ensure data integrity
5. **Portability**: Single file database, easy to backup/move
6. **No Dependencies**: SQLite is built into Python

## File Structure

```
memory/
├── __init__.py              # Package initialization
└── memory_store.py          # SQLite memory store implementation

data/
└── memory.db               # SQLite database file (auto-created)
```

## Integration with LLM

The memory system integrates seamlessly with the LLM qualification process:

1. **Before qualification**: Check if lead has been qualified before
2. **During qualification**: Include previous context in LLM prompt
3. **After qualification**: Save results and log interaction
4. **Email sending**: Log all outbound communications

This creates a comprehensive audit trail and enables the LLM to make more informed decisions based on historical context.

## Performance Considerations

- Database operations are optimized with proper indexing
- Connection pooling via context managers
- Minimal memory footprint (data stored on disk)
- Fast lookups via primary key indexes
- Efficient JSON storage for complex interaction data

## Future Enhancements

Potential improvements:
- Add database migrations for schema changes
- Implement data archiving for old leads
- Add full-text search capabilities
- Create database backup/restore utilities
- Add performance monitoring and metrics 