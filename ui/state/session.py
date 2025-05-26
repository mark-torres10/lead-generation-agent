"""
Session state management for the Streamlit app.
Handles memory manager initialization and form data persistence.
"""

import streamlit as st
import os
from memory.memory_manager import MemoryManager
from memory.memory_store import SQLiteMemoryStore
import time


def initialize_session_state():
    """Initialize session state variables for the app."""
    
    # Initialize memory manager if not exists
    if 'memory_manager' not in st.session_state:
        # Use persistent DB path for the app run
        os.makedirs('data/tmp', exist_ok=True)
        db_path = f"data/tmp/app_db_{int(time.time())}.db"
        st.session_state.db_path = db_path
        memory_store = SQLiteMemoryStore(db_path)
        st.session_state.memory_manager = MemoryManager(memory_store)
    else:
        print(f"[DEBUG] Existing MemoryManager at {st.session_state.db_path}, id={id(st.session_state.memory_manager)}")
    
    # Initialize form data storage
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    
    # Initialize demo results storage
    if 'demo_results' not in st.session_state:
        st.session_state.demo_results = {}
    
    # Initialize lead counter for unique IDs
    if 'lead_counter' not in st.session_state:
        st.session_state.lead_counter = 1


def get_memory_manager() -> MemoryManager:
    """Get the current session's memory manager."""
    return st.session_state.memory_manager


def get_next_lead_id() -> str:
    """Generate a unique lead ID for the session."""
    lead_id = f"demo_lead_{st.session_state.lead_counter:03d}"
    st.session_state.lead_counter += 1
    return lead_id


def store_form_data(tab_name: str, data: dict):
    """Store form data for a specific tab."""
    st.session_state.form_data[tab_name] = data


def get_form_data(tab_name: str) -> dict:
    """Retrieve form data for a specific tab."""
    return st.session_state.form_data.get(tab_name, {})


def store_demo_result(tab_name: str, lead_id: str, result: dict):
    """Store demo result for display."""
    if tab_name not in st.session_state.demo_results:
        st.session_state.demo_results[tab_name] = {}
    st.session_state.demo_results[tab_name][lead_id] = result


def get_demo_result(tab_name: str, lead_id: str) -> dict:
    """Retrieve demo result for display."""
    return st.session_state.demo_results.get(tab_name, {}).get(lead_id, {})


def clear_demo_results(tab_name: str = None):
    """Clear demo results for a tab or all tabs."""
    if tab_name:
        st.session_state.demo_results[tab_name] = {}
    else:
        st.session_state.demo_results = {}
