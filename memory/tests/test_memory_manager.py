import os
import tempfile
import pytest
from memory.memory_manager import MemoryManager
from memory.memory_store import SQLiteMemoryStore

def fresh_manager():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    store = SQLiteMemoryStore(db_path)
    mgr = MemoryManager(store)
    return mgr, db_path

def test_get_or_create_lead_id_and_email_uniqueness():
    mgr, db_path = fresh_manager()
    try:
        lead_data = {"name": "Alice", "company": "Acme", "email": "alice@acme.com"}
        lead_id1 = mgr.get_or_create_lead_id("alice@acme.com", lead_data)
        lead_id2 = mgr.get_or_create_lead_id("alice@acme.com", {"name": "Alice2"})
        assert lead_id1 == lead_id2
        lead = mgr.get_lead_by_email("alice@acme.com")
        assert lead["lead_id"] == lead_id1
        assert lead["name"] == "Alice"
        # New email gets new lead_id
        lead_id3 = mgr.get_or_create_lead_id("bob@acme.com", {"name": "Bob"})
        assert lead_id3 != lead_id1
    finally:
        os.remove(db_path)

def test_save_and_get_lead():
    mgr, db_path = fresh_manager()
    try:
        lead_id = "lead_123"
        mgr.save_lead(lead_id, {"name": "Test", "company": "TCo", "email": "t@t.com"})
        lead = mgr.get_lead(lead_id)
        assert lead["name"] == "Test"
        assert lead["email"] == "t@t.com"
        all_leads = mgr.get_all_leads()
        assert any(l["lead_id"] == lead_id for l in all_leads)
    finally:
        os.remove(db_path)

def test_save_and_get_qualification():
    mgr, db_path = fresh_manager()
    try:
        lead_id = mgr.get_or_create_lead_id("qual@t.com", {"name": "Qual"})
        qual_data = {"priority": "high", "lead_score": 90, "reasoning": "Test", "next_action": "Act"}
        mgr.save_qualification(lead_id, qual_data)
        qual = mgr.get_qualification(lead_id)
        assert qual["priority"] == "high"
        assert qual["lead_score"] == 90
        latest = mgr.get_latest_qualification(lead_id)
        assert latest["priority"] == "high"
    finally:
        os.remove(db_path)

def test_save_and_get_meeting():
    mgr, db_path = fresh_manager()
    try:
        lead_id = mgr.get_or_create_lead_id("meet@t.com", {"name": "Meet"})
        meeting_data = {"meeting_status": "scheduled", "meeting_datetime": "2024-01-01T10:00"}
        mgr.save_meeting(lead_id, meeting_data)
        meeting = mgr.get_latest_meeting(lead_id)
        assert meeting["meeting_status"] == "scheduled"
        meetings = mgr.get_meetings(lead_id)
        assert any(m["meeting_status"] == "scheduled" for m in meetings)
    finally:
        os.remove(db_path)

def test_log_and_get_sent_email():
    mgr, db_path = fresh_manager()
    try:
        lead_id = mgr.get_or_create_lead_id("mail@t.com", {"name": "Mail"})
        mgr.log_sent_email(lead_id, "mail@t.com", "Subj", "Body")
        emails = mgr.get_sent_emails(lead_id)
        assert any(e["subject"] == "Subj" for e in emails)
    finally:
        os.remove(db_path)

def test_add_and_get_interaction():
    mgr, db_path = fresh_manager()
    try:
        lead_id = mgr.get_or_create_lead_id("int@t.com", {"name": "Int"})
        mgr.add_interaction(lead_id, "event_type", {"foo": "bar"})
        history = mgr.get_interaction_history(lead_id)
        assert any(h["event_type"] == "event_type" for h in history)
        assert history[0]["event_data"]["foo"] == "bar"
    finally:
        os.remove(db_path)

def test_clear_all_data():
    mgr, db_path = fresh_manager()
    try:
        lead_id = mgr.get_or_create_lead_id("clear@t.com", {"name": "Clear"})
        mgr.save_qualification(lead_id, {"priority": "low", "lead_score": 10, "reasoning": "R", "next_action": "N"})
        mgr.clear_all_data()
        assert mgr.get_lead_by_email("clear@t.com") is None
        assert mgr.get_qualification(lead_id) is None
    finally:
        os.remove(db_path)

def test_qualify_and_reply_flow():
    mgr, db_path = fresh_manager()
    try:
        # Step 1: Qualify lead
        form_data = {"name": "Sarah Chen", "email": "sarah.chen@techcorp.com", "company": "TechCorp Industries"}
        lead_id1 = mgr.get_or_create_lead_id(form_data["email"], form_data)
        qual_data = {"priority": "high", "lead_score": 85, "reasoning": "Qualified", "next_action": "Follow up"}
        mgr.save_qualification(lead_id1, qual_data)
        before = mgr.get_qualification(lead_id1)
        # Step 2: Reply analysis for same email
        reply_data = {"priority": "high", "lead_score": 99, "reasoning": "Replied", "next_action": "Schedule call"}
        lead_id2 = mgr.get_or_create_lead_id(form_data["email"], form_data)
        mgr.save_qualification(lead_id2, reply_data)
        after = mgr.get_qualification(lead_id2)
        # Assert same lead_id and correct before/after
        assert lead_id1 == lead_id2
        assert before["lead_score"] == 85
        assert after["lead_score"] == 99
    finally:
        os.remove(db_path)

def test_display_reply_analysis_results_queries_db():
    # Simulate the logic that should be in the reply tab: get before state from DB
    mgr, db_path = fresh_manager()
    try:
        form_data = {"name": "Sarah Chen", "email": "sarah.chen@techcorp.com", "company": "TechCorp Industries"}
        lead_id = mgr.get_or_create_lead_id(form_data["email"], form_data)
        qual_data = {"priority": "high", "lead_score": 85, "reasoning": "Qualified", "next_action": "Follow up"}
        mgr.save_qualification(lead_id, qual_data)
        # Simulate reply tab logic: get before state from DB
        before = mgr.get_qualification(lead_id)
        print(f"[TEST DEBUG] Before state from DB: {before}")
        assert before["lead_score"] == 85
    finally:
        os.remove(db_path)

def test_lead_id_consistency_between_tabs():
    mgr, db_path = fresh_manager()
    try:
        form_data = {"name": "Sarah Chen", "email": "sarah.chen@techcorp.com", "company": "TechCorp Industries"}
        lead_id1 = mgr.get_or_create_lead_id(form_data["email"], form_data)
        lead_id2 = mgr.get_or_create_lead_id(form_data["email"], form_data)
        print(f"[TEST DEBUG] Lead IDs: {lead_id1}, {lead_id2}")
        assert lead_id1 == lead_id2
    finally:
        os.remove(db_path)

def test_qualification_save_and_retrieve():
    mgr, db_path = fresh_manager()
    try:
        form_data = {"name": "Sarah Chen", "email": "sarah.chen@techcorp.com", "company": "TechCorp Industries"}
        lead_id = mgr.get_or_create_lead_id(form_data["email"], form_data)
        qual_data = {"priority": "high", "lead_score": 85, "reasoning": "Qualified", "next_action": "Follow up"}
        mgr.save_qualification(lead_id, qual_data)
        retrieved = mgr.get_qualification(lead_id)
        print(f"[TEST DEBUG] Saved: {qual_data}, Retrieved: {retrieved}")
        assert retrieved["lead_score"] == 85
        assert retrieved["priority"] == "high"
    finally:
        os.remove(db_path)

def test_qualification_history_inserts():
    mgr, db_path = fresh_manager()
    try:
        form_data = {"name": "Sarah Chen", "email": "sarah.chen@techcorp.com", "company": "TechCorp Industries"}
        lead_id = mgr.get_or_create_lead_id(form_data["email"], form_data)
        qual1 = {"priority": "high", "lead_score": 85, "reasoning": "Qualified", "next_action": "Follow up"}
        qual2 = {"priority": "high", "lead_score": 99, "reasoning": "Replied", "next_action": "Schedule call"}
        mgr.save_qualification(lead_id, qual1)
        mgr.save_qualification(lead_id, qual2)
        history = mgr.get_qualification_history(lead_id)
        print(f"[TEST DEBUG] Qualification history: {history}")
        assert len(history) == 2
        assert history[0]["lead_score"] == 85
        assert history[1]["lead_score"] == 99
    finally:
        os.remove(db_path) 