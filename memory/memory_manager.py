"""Memory manager for business logic operations."""
import json
from datetime import datetime
from typing import Dict, Optional, Any, List
from .memory_store import memory_store

class MemoryManager:
    """High-level memory manager for lead management operations."""
    
    def __init__(self, store=None):
        """Initialize the memory manager with a store."""
        self.store = store or memory_store
    
    # Lead operations
    def save_lead(self, lead_id: str, lead_data: Dict[str, Any]) -> None:
        """Save or update lead information."""
        print(f"[DEBUG] save_lead called with lead_id={lead_id}, lead_data={lead_data}")
        data = {
            "lead_id": lead_id,
            "name": lead_data.get("name"),
            "company": lead_data.get("company"),
            "email": lead_data.get("email"),
            "status": lead_data.get("status", "new")
        }
        print(f"[DEBUG] save_lead inserting/updating: {data}")
        self.store.insert_or_update("leads", data, "lead_id")
    
    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get lead information."""
        results = self.store.get_by_field("leads", "lead_id", lead_id)
        return results[0] if results else None
    
    def get_all_leads(self) -> List[Dict[str, Any]]:
        """Get all leads."""
        return self.store.execute_query("SELECT * FROM leads ORDER BY updated_at DESC")
    
    def get_lead_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get lead information by email (unique per lead)."""
        results = self.store.get_by_field("leads", "email", email)
        return results[0] if results else None

    def get_or_create_lead_id(self, email: str, lead_data: Dict[str, Any]) -> str:
        """Return the lead_id for a given email, creating a new lead if not present."""
        lead = self.get_lead_by_email(email)
        if lead:
            print(f"[DEBUG] get_or_create_lead_id found existing lead: {lead}")
            return lead["lead_id"]
        # Create new lead_id (use a UUID for uniqueness)
        import uuid
        lead_id = f"lead_{uuid.uuid4().hex[:12]}"
        print(f"[DEBUG] get_or_create_lead_id creating new lead_id: {lead_id} for email: {email}")
        data = lead_data.copy()
        data["lead_id"] = lead_id
        data["email"] = email
        self.save_lead(lead_id, data)
        return lead_id
    
    # Qualification operations
    def save_qualification(self, lead_id: str, qualification_data: Dict[str, Any]) -> None:
        """Save qualification results for a lead (always insert a new record)."""
        # Ensure lead exists
        if not self.get_lead(lead_id):
            self.save_lead(lead_id, {"name": "Unknown", "email": "unknown@example.com"})
        now = datetime.now().isoformat()
        self.store.execute_insert(
            "INSERT INTO lead_qualifications (lead_id, priority, lead_score, reasoning, next_action, "
            "lead_disposition, disposition_confidence, sentiment, urgency, last_reply_analysis, "
            "recommended_follow_up, follow_up_timing, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                lead_id, qualification_data.get("priority"), qualification_data.get("lead_score"),
                qualification_data.get("reasoning"), qualification_data.get("next_action"),
                qualification_data.get("lead_disposition"), qualification_data.get("disposition_confidence"),
                qualification_data.get("sentiment"), qualification_data.get("urgency"),
                qualification_data.get("last_reply_analysis"), qualification_data.get("recommended_follow_up"),
                qualification_data.get("follow_up_timing"),
                now, now
            )
        )
    
    def get_qualification(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest qualification for a lead."""
        result = self.get_latest_qualification(lead_id)
        if result:
            # Remove None values and id field for backward compatibility
            clean_result = {}
            for key, value in result.items():
                if key not in ["id", "lead_id"] and value is not None:
                    clean_result[key] = value
            return clean_result
        return None
    
    def get_latest_qualification(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest qualification record for a lead."""
        return self.store.get_latest_by_field("lead_qualifications", "lead_id", lead_id)
    
    def has_qualification(self, lead_id: str) -> bool:
        """Check if a lead has been qualified before."""
        return self.get_latest_qualification(lead_id) is not None
    
    # Meeting operations
    def save_meeting(self, lead_id: str, meeting_data: Dict[str, Any]) -> int:
        """Save meeting information for a lead."""
        # Ensure lead exists
        if not self.get_lead(lead_id):
            self.save_lead(lead_id, {"name": "Unknown", "email": "unknown@example.com"})
        
        # Get existing meeting to update or create new
        existing = self.get_latest_meeting(lead_id)
        
        if existing:
            # Update existing meeting
            data = existing.copy()
            data.update(meeting_data)
            data["updated_at"] = datetime.now().isoformat()
            
            self.store.execute_update(
                "UPDATE meetings SET meeting_status=?, meeting_datetime=?, meeting_type=?, "
                "meeting_duration=?, meeting_urgency=?, meeting_analysis=?, meeting_preferred_time=?, "
                "meeting_notes=?, requested=?, updated_at=? WHERE id=?",
                (
                    data.get("meeting_status"), data.get("meeting_datetime"), data.get("meeting_type"),
                    data.get("meeting_duration"), data.get("meeting_urgency"), data.get("meeting_analysis"),
                    data.get("meeting_preferred_time"), data.get("meeting_notes"), data.get("requested"),
                    data["updated_at"], existing["id"]
                )
            )
            return existing["id"]
        else:
            # Create new meeting
            return self.store.execute_insert(
                "INSERT INTO meetings (lead_id, meeting_status, meeting_datetime, meeting_type, "
                "meeting_duration, meeting_urgency, meeting_analysis, meeting_preferred_time, "
                "meeting_notes, requested) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    lead_id, meeting_data.get("meeting_status"), meeting_data.get("meeting_datetime"),
                    meeting_data.get("meeting_type"), meeting_data.get("meeting_duration"),
                    meeting_data.get("meeting_urgency"), meeting_data.get("meeting_analysis"),
                    meeting_data.get("meeting_preferred_time"), meeting_data.get("meeting_notes"),
                    meeting_data.get("requested", False)
                )
            )
    
    def get_latest_meeting(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest meeting for a lead."""
        return self.store.get_latest_by_field("meetings", "lead_id", lead_id)
    
    def get_meetings(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get all meetings for a lead."""
        return self.store.get_by_field("meetings", "lead_id", lead_id)
    
    # Calendar operations
    def save_calendar_event(self, meeting_id: int, event_data: Dict[str, Any]) -> int:
        """Save calendar event information."""
        return self.store.execute_insert(
            "INSERT INTO calendar_events (meeting_id, calendar_event_id, event_datetime, "
            "duration, status, calendar_link) VALUES (?, ?, ?, ?, ?, ?)",
            (
                meeting_id, event_data.get("calendar_event_id"), event_data.get("event_datetime"),
                event_data.get("duration"), event_data.get("status", "scheduled"),
                event_data.get("calendar_link")
            )
        )
    
    def get_calendar_events(self, meeting_id: int) -> List[Dict[str, Any]]:
        """Get calendar events for a meeting."""
        return self.store.get_by_field("calendar_events", "meeting_id", meeting_id)
    
    # Email operations
    def log_sent_email(self, lead_id: str, to_address: str, subject: str, body: str, 
                      from_address: str = None, email_type: str = "outbound") -> int:
        """Log a sent email."""
        return self.store.execute_insert(
            "INSERT INTO emails (lead_id, to_address, from_address, subject, body, email_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (lead_id, to_address, from_address, subject, body, email_type)
        )
    
    def get_sent_emails(self, lead_id: str = None) -> List[Dict[str, Any]]:
        """Get sent emails, optionally filtered by lead_id."""
        if lead_id:
            return self.store.execute_query(
                "SELECT * FROM emails WHERE lead_id = ? ORDER BY sent_at DESC", (lead_id,)
            )
        else:
            return self.store.execute_query("SELECT * FROM emails ORDER BY sent_at DESC")
    
    # Interaction operations
    def add_interaction(self, lead_id: str, event_type: str, event_data: Dict[str, Any]) -> int:
        """Add an interaction to the history."""
        return self.store.execute_insert(
            "INSERT INTO interactions (lead_id, event_type, event_data) VALUES (?, ?, ?)",
            (lead_id, event_type, json.dumps(event_data))
        )
    
    def get_interaction_history(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get interaction history for a lead."""
        results = self.store.execute_query(
            "SELECT event_type, event_data, timestamp FROM interactions "
            "WHERE lead_id = ? ORDER BY timestamp ASC", (lead_id,)
        )
        
        # Parse JSON event_data
        for result in results:
            result["event_data"] = json.loads(result["event_data"])
        
        return results
    
    # Combined operations for backward compatibility
    def update_qualification_with_meeting(self, lead_id: str, meeting_data: Dict[str, Any]) -> None:
        """Update qualification with meeting information (for backward compatibility)."""
        # Save meeting data
        self.save_meeting(lead_id, meeting_data)
        
        # Update qualification with meeting flags
        qualification_update = {
            "meeting_scheduled": True,
            "meeting_status": meeting_data.get("status", "scheduled")
        }
        self.save_qualification(lead_id, qualification_update)
    
    def get_qualification_with_meeting_info(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get qualification with meeting information merged (for backward compatibility)."""
        qualification = self.get_qualification(lead_id)
        if not qualification:
            return None
        
        # Get latest meeting info
        meeting = self.get_latest_meeting(lead_id)
        if meeting:
            qualification.update({
                "meeting_requested": meeting.get("requested", False),
                "meeting_status": meeting.get("meeting_status"),
                "meeting_datetime": meeting.get("meeting_datetime"),
                "meeting_type": meeting.get("meeting_type"),
                "meeting_duration": meeting.get("meeting_duration"),
                "meeting_urgency": meeting.get("meeting_urgency"),
                "meeting_analysis": meeting.get("meeting_analysis"),
                "meeting_preferred_time": meeting.get("meeting_preferred_time"),
                "meeting_notes": meeting.get("meeting_notes")
            })
        
        return qualification
    
    # Utility operations
    def clear_all_data(self) -> None:
        """Clear all data from the database (useful for testing)."""
        self.store.clear_all_data()

    def get_qualification_history(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get all qualification records for a lead, ordered by updated_at ascending."""
        records = self.store.get_by_field("lead_qualifications", "lead_id", lead_id)
        # Sort by updated_at (or created_at if updated_at missing)
        def get_sort_key(rec):
            return rec.get("updated_at") or rec.get("created_at") or ""
        return sorted(records, key=get_sort_key)

    def list_all_lead_ids(self) -> List[str]:
        """Return all lead IDs in the database."""
        leads = self.get_all_leads()
        return [lead["lead_id"] for lead in leads if "lead_id" in lead]

    def list_all_qualifications(self) -> List[Dict[str, Any]]:
        """Return all qualifications in the database."""
        return self.store.execute_query("SELECT * FROM lead_qualifications ORDER BY updated_at DESC")


# Global instance for backward compatibility
memory_manager = MemoryManager()

# Export both the class and the instance
__all__ = ['MemoryManager', 'memory_manager']
