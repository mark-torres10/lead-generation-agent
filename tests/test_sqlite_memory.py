import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.run_qualify_followup import *
from memory.memory_store import memory_store, SQLiteMemoryStore

print('🗄️  Testing SQLite Memory Functionality')
print('=' * 50)

# Clear any existing data for clean test
memory_store.clear_all_data()

print('1. Initial state - Database is empty')
print(f'   Leads in database: {memory_store.get_all_leads()}')
print()

# First qualification
print('2. First qualification of lead_001')
context = extract_lead_context('lead_001')
result1 = llm_qualify_lead(context)
print(f'   Priority: {result1["priority"]}')
print(f'   Score: {result1["lead_score"]}')
print(f'   Reasoning: {result1["reasoning"][:100]}...')
print()

print('3. Database after first qualification')
all_leads = memory_store.get_all_leads()
print(f'   Leads in database: {[lead["lead_id"] for lead in all_leads]}')
if all_leads:
    lead_data = memory_store.get_qualification('lead_001')
    print(f'   Stored priority: {lead_data["priority"]}')
    print(f'   Stored score: {lead_data["lead_score"]}')
    print(f'   Created at: {lead_data["created_at"]}')
print()

# Second qualification - should use memory
print('4. Second qualification of lead_001 (should use SQLite memory)')
result2 = llm_qualify_lead(context)
print(f'   Priority: {result2["priority"]}')
print(f'   Score: {result2["lead_score"]}')
print(f'   Reasoning: {result2["reasoning"][:100]}...')
print()

# Check if the LLM mentions previous qualification
if 'previous' in result2["reasoning"].lower() or 'before' in result2["reasoning"].lower():
    print('✅ LLM appears to be using SQLite memory context!')
else:
    print('⚠️  LLM may not be using memory context explicitly')

print()

# Test email logging
print('5. Testing email logging')
send_followup_email("Test email content", "alice@acmeinc.com", "lead_001")
sent_emails = memory_store.get_sent_emails("lead_001")
print(f'   Emails sent to lead_001: {len(sent_emails)}')
if sent_emails:
    print(f'   Latest email to: {sent_emails[0]["to_address"]}')
    print(f'   Email sent at: {sent_emails[0]["sent_at"]}')
print()

# Test interaction history
print('6. Testing interaction history')
memory_store.add_interaction("lead_001", "qualification", {
    "event": "qualified",
    "priority": result2["priority"],
    "score": result2["lead_score"]
})

interactions = memory_store.get_interaction_history("lead_001")
print(f'   Interactions for lead_001: {len(interactions)}')
for i, interaction in enumerate(interactions):
    print(f'   {i+1}. {interaction["event_type"]} at {interaction["timestamp"]}')

print()

# Test persistence by creating a new memory store instance
print('7. Testing persistence with new instance')
new_memory_store = SQLiteMemoryStore()
persistent_data = new_memory_store.get_qualification('lead_001')
if persistent_data:
    print('✅ Data persisted successfully!')
    print(f'   Retrieved priority: {persistent_data["priority"]}')
    print(f'   Retrieved score: {persistent_data["lead_score"]}')
else:
    print('❌ Data not persisted')

print('\n🎯 SQLite memory test completed!') 