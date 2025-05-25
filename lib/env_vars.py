"""
Environment variables loader for the leads AI agent system.
Loads variables from the .env file in the root directory.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Get the root directory (parent of lib directory)
ROOT_DIR = Path(__file__).parent.parent

# Load environment variables from .env file in root directory
env_path = ROOT_DIR / ".env"
load_dotenv(env_path)

# Export commonly used environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate that required environment variables are set
if not OPENAI_API_KEY:
    raise ValueError(
        f"OPENAI_API_KEY not found in environment variables. "
        f"Please ensure it's set in {env_path}"
    ) 