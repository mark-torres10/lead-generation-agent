"""Pydantic models for agent functionality."""
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Configuration for an agent."""
    model: str
    temperature: float
    max_tokens: int
    api_key: str

class LeadQualification(BaseModel):
    """Qualification result for a lead."""
    lead_id: str
    lead_name: str
    lead_company: str
