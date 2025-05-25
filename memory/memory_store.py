"""Memory store."""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Optional, Any

class SQLiteMemoryStore:
    """SQLite-based memory store for lead qualification data."""
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS qualification_memory (
                    lead_id TEXT PRIMARY KEY,
                    priority TEXT NOT NULL,
                    lead_score INTEGER NOT NULL,
                    reasoning TEXT NOT NULL,
                    next_action TEXT NOT NULL,
                    lead_disposition TEXT,
                    disposition_confidence INTEGER,
                    sentiment TEXT,
                    urgency TEXT,
                    last_reply_analysis TEXT,
                    recommended_follow_up TEXT,
                    follow_up_timing TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add new columns to existing table if they don't exist
            try:
                conn.execute("ALTER TABLE qualification_memory ADD COLUMN lead_disposition TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                conn.execute("ALTER TABLE qualification_memory ADD COLUMN disposition_confidence INTEGER")
            except sqlite3.OperationalError:
                pass
                
            try:
                conn.execute("ALTER TABLE qualification_memory ADD COLUMN sentiment TEXT")
            except sqlite3.OperationalError:
                pass
                
            try:
                conn.execute("ALTER TABLE qualification_memory ADD COLUMN urgency TEXT")
            except sqlite3.OperationalError:
                pass
                
            try:
                conn.execute("ALTER TABLE qualification_memory ADD COLUMN last_reply_analysis TEXT")
            except sqlite3.OperationalError:
                pass
                
            try:
                conn.execute("ALTER TABLE qualification_memory ADD COLUMN recommended_follow_up TEXT")
            except sqlite3.OperationalError:
                pass
                
            try:
                conn.execute("ALTER TABLE qualification_memory ADD COLUMN follow_up_timing TEXT")
            except sqlite3.OperationalError:
                pass
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interaction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES qualification_memory (lead_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sent_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT,
                    to_address TEXT NOT NULL,
                    subject TEXT,
                    body TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_qualification(self, lead_id: str, qualification_data: Dict[str, Any]) -> None:
        """Save qualification results for a lead."""
        with sqlite3.connect(self.db_path) as conn:
            # Build dynamic SQL based on available fields
            base_fields = ["lead_id", "priority", "lead_score", "reasoning", "next_action", "updated_at"]
            base_values = [
                lead_id,
                qualification_data["priority"],
                qualification_data["lead_score"],
                qualification_data["reasoning"],
                qualification_data["next_action"],
                datetime.now().isoformat()
            ]
            
            # Add optional fields if they exist in the data
            optional_fields = [
                "lead_disposition", "disposition_confidence", "sentiment", "urgency",
                "last_reply_analysis", "recommended_follow_up", "follow_up_timing"
            ]
            
            for field in optional_fields:
                if field in qualification_data:
                    base_fields.append(field)
                    base_values.append(qualification_data[field])
            
            placeholders = ", ".join(["?"] * len(base_fields))
            fields_str = ", ".join(base_fields)
            
            conn.execute(f"""
                INSERT OR REPLACE INTO qualification_memory 
                ({fields_str})
                VALUES ({placeholders})
            """, base_values)
            conn.commit()
    
    def get_qualification(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve qualification results for a lead."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM qualification_memory WHERE lead_id = ?
            """, (lead_id,))
            
            row = cursor.fetchone()
            if row:
                # Convert row to dict, excluding None values for cleaner output
                result = {}
                for key in row.keys():
                    if key != "lead_id" and row[key] is not None:
                        result[key] = row[key]
                return result
            return None
    
    def has_qualification(self, lead_id: str) -> bool:
        """Check if a lead has been qualified before."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM qualification_memory WHERE lead_id = ?
            """, (lead_id,))
            return cursor.fetchone() is not None
    
    def add_interaction(self, lead_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Add an interaction to the history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO interaction_history (lead_id, event_type, event_data)
                VALUES (?, ?, ?)
            """, (lead_id, event_type, json.dumps(event_data)))
            conn.commit()
    
    def get_interaction_history(self, lead_id: str) -> list:
        """Get interaction history for a lead."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT event_type, event_data, timestamp
                FROM interaction_history 
                WHERE lead_id = ?
                ORDER BY timestamp ASC
            """, (lead_id,))
            
            return [
                {
                    "event_type": row["event_type"],
                    "event_data": json.loads(row["event_data"]),
                    "timestamp": row["timestamp"]
                }
                for row in cursor.fetchall()
            ]
    
    def log_sent_email(self, lead_id: str, to_address: str, subject: str, body: str) -> None:
        """Log a sent email."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sent_emails (lead_id, to_address, subject, body)
                VALUES (?, ?, ?, ?)
            """, (lead_id, to_address, subject, body))
            conn.commit()
    
    def get_sent_emails(self, lead_id: str = None) -> list:
        """Get sent emails, optionally filtered by lead_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if lead_id:
                cursor = conn.execute("""
                    SELECT * FROM sent_emails WHERE lead_id = ? ORDER BY sent_at DESC
                """, (lead_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM sent_emails ORDER BY sent_at DESC
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_leads(self) -> list:
        """Get all leads that have been qualified."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT lead_id, priority, lead_score, updated_at
                FROM qualification_memory 
                ORDER BY updated_at DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def clear_all_data(self) -> None:
        """Clear all data from the database (useful for testing)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM interaction_history")
            conn.execute("DELETE FROM sent_emails")
            conn.execute("DELETE FROM qualification_memory")
            conn.commit()

# Global instance
memory_store = SQLiteMemoryStore()
