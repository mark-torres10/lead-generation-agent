"""Memory store with star schema design."""
import sqlite3
import os
from typing import Dict, Optional, Any, List

class SQLiteMemoryStore:
    """Generic SQLite-based memory store with star schema design."""
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with star schema tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Core leads table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    lead_id TEXT PRIMARY KEY,
                    name TEXT,
                    company TEXT,
                    email TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Lead qualifications table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lead_qualifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT NOT NULL,
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
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads (lead_id)
                )
            """)
            
            # Meetings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT NOT NULL,
                    meeting_status TEXT,
                    meeting_datetime TEXT,
                    meeting_type TEXT,
                    meeting_duration TEXT,
                    meeting_urgency TEXT,
                    meeting_analysis TEXT,
                    meeting_preferred_time TEXT,
                    meeting_notes TEXT,
                    requested BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads (lead_id)
                )
            """)
            
            # Calendar events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id INTEGER,
                    calendar_event_id TEXT UNIQUE,
                    event_datetime TEXT NOT NULL,
                    duration TEXT,
                    status TEXT DEFAULT 'scheduled',
                    calendar_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings (id)
                )
            """)
            
            # Emails table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT,
                    to_address TEXT NOT NULL,
                    from_address TEXT,
                    subject TEXT,
                    body TEXT NOT NULL,
                    email_type TEXT DEFAULT 'outbound',
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads (lead_id)
                )
            """)
            
            # Interactions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads (lead_id)
                )
            """)
            
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the last row ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an UPDATE query and return the number of affected rows."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_delete(self, query: str, params: tuple = ()) -> int:
        """Execute a DELETE query and return the number of affected rows."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def insert_or_update(self, table: str, data: Dict[str, Any], key_field: str) -> int:
        """Insert or update a record in the specified table."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if record exists
            cursor = conn.execute(f"SELECT 1 FROM {table} WHERE {key_field} = ?", (data[key_field],))
            exists = cursor.fetchone() is not None
            
            if exists:
                # Update existing record
                set_clause = ", ".join([f"{k} = ?" for k in data.keys() if k != key_field])
                values = [v for k, v in data.items() if k != key_field]
                values.append(data[key_field])
                
                query = f"UPDATE {table} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE {key_field} = ?"
                cursor = conn.execute(query, values)
                conn.commit()
                return cursor.rowcount
            else:
                # Insert new record
                fields = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                values = list(data.values())
                
                query = f"INSERT INTO {table} ({fields}) VALUES ({placeholders})"
                cursor = conn.execute(query, values)
                conn.commit()
                return cursor.lastrowid
    
    def get_by_field(self, table: str, field: str, value: Any) -> List[Dict[str, Any]]:
        """Get records from table where field equals value."""
        return self.execute_query(f"SELECT * FROM {table} WHERE {field} = ?", (value,))
    
    def get_latest_by_field(self, table: str, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """Get the most recent record from table where field equals value."""
        results = self.execute_query(
            f"SELECT * FROM {table} WHERE {field} = ? ORDER BY updated_at DESC LIMIT 1", 
            (value,)
        )
        return results[0] if results else None
    
    def clear_all_data(self) -> None:
        """Clear all data from the database (useful for testing)."""
        tables = ['interactions', 'calendar_events', 'emails', 'meetings', 'lead_qualifications', 'leads']
        with sqlite3.connect(self.db_path) as conn:
            for table in tables:
                conn.execute(f"DELETE FROM {table}")
            conn.commit()

# Global instance
memory_store = SQLiteMemoryStore()
