import sqlite3
import os
from memory.memory_manager import memory_manager

def inspect_database():
    """Inspect the contents of the SQLite database."""
    print('🔍 Database Inspection')
    print('=' * 40)
    
    # Check if database file exists
    if not os.path.exists(memory_manager.db_path):
        print('❌ Database file does not exist')
        return
    
    print(f'📁 Database location: {memory_manager.db_path}')
    print(f'📊 Database size: {os.path.getsize(memory_manager.db_path)} bytes')
    print()
    
    # Get all qualified leads
    leads = memory_manager.get_all_leads()
    print(f'👥 Total qualified leads: {len(leads)}')
    for lead in leads:
        print(f'   - {lead["lead_id"]}: {lead["priority"]} priority, score {lead["lead_score"]}')
    print()
    
    # Get all sent emails
    emails = memory_manager.get_sent_emails()
    print(f'📧 Total sent emails: {len(emails)}')
    for email in emails[:5]:  # Show first 5
        print(f'   - To: {email["to_address"]} at {email["sent_at"]}')
    if len(emails) > 5:
        print(f'   ... and {len(emails) - 5} more')
    print()
    
    # Show interaction history for each lead
    for lead in leads:
        lead_id = lead["lead_id"]
        interactions = memory_manager.get_interaction_history(lead_id)
        print(f'📝 Interactions for {lead_id}: {len(interactions)}')
        for interaction in interactions:
            print(f'   - {interaction["event_type"]} at {interaction["timestamp"]}')
    
    print()
    
    # Raw table counts
    with sqlite3.connect(memory_manager.db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM qualification_memory")
        qual_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM sent_emails")
        email_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM interaction_history")
        interaction_count = cursor.fetchone()[0]
        
        print('📊 Raw table counts:')
        print(f'   - qualification_memory: {qual_count} records')
        print(f'   - sent_emails: {email_count} records')
        print(f'   - interaction_history: {interaction_count} records')

if __name__ == "__main__":
    inspect_database() 