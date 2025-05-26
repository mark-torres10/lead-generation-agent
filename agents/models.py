"""Pydantic models for agent functionality."""
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Union
from datetime import datetime

class AgentConfig(BaseModel):
    """Configuration for an agent."""
    model: str
    temperature: float
    max_tokens: int
    api_key: str

# --- Lead Qualification Models ---

class LeadInput(BaseModel):
    """Input data for lead qualification."""
    name: str
    company: str
    email: EmailStr
    interest: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    # Additional fields for enrichment
    company_size: Optional[Union[str, int]] = None
    industry: Optional[str] = None
    lead_source: Optional[str] = None
    role: Optional[str] = None

    @validator('name', 'company', 'email')
    def not_empty(cls, v):
        if not v or not str(v).strip():
            raise ValueError('Field must not be empty')
        return v

class QualificationFactors(BaseModel):
    """Factors for lead qualification scoring."""
    company_size: str
    urgency: str
    budget_signals: bool
    authority: str
    need: str

    @validator('company_size')
    def valid_company_size(cls, v):
        if v not in ['small', 'medium', 'large', 'enterprise']:
            raise ValueError('Invalid company_size')
        return v
    @validator('urgency')
    def valid_urgency(cls, v):
        if v not in ['low', 'medium', 'high', 'urgent']:
            raise ValueError('Invalid urgency')
        return v
    @validator('authority')
    def valid_authority(cls, v):
        if v not in ['none', 'influencer', 'decision_maker', 'executive']:
            raise ValueError('Invalid authority')
        return v
    @validator('need')
    def valid_need(cls, v):
        if v not in ['low', 'medium', 'high', 'urgent']:
            raise ValueError('Invalid need')
        return v

class LeadQualificationResult(BaseModel):
    """Qualification result for a lead."""
    lead_id: Optional[str]
    lead_name: Optional[str]
    lead_company: Optional[str]
    priority: str
    lead_score: int
    reasoning: str
    next_action: str
    disposition: str
    confidence: int
    sentiment: Optional[str] = None
    urgency: Optional[str] = None
    # For backward compatibility
    lead_disposition: Optional[str] = None
    disposition_confidence: Optional[int] = None
    # New fields for explainability
    signals: Optional[list[str]] = None
    confidence_improvements: Optional[Union[list[str], str]] = None

# --- Meeting Scheduling Models ---

class MeetingRequestInput(BaseModel):
    """Input data for meeting scheduling requests."""
    request_text: str
    sender_email: EmailStr
    preferred_times: Optional[str] = None
    meeting_type: Optional[str] = None
    lead_id: Optional[str] = None

class MeetingAnalysisResult(BaseModel):
    """Result of meeting request analysis."""
    intent: str
    urgency: str
    preferred_duration: int
    time_preferences: str
    meeting_type: str
    flexibility: str
    next_action: str

class MeetingBookingResult(BaseModel):
    """Result of a meeting booking attempt."""
    booking_id: Optional[str]
    confirmation_message: str
    calendar_link: Optional[str]
    status: str

class MeetingProposal(BaseModel):
    """A proposed meeting time option."""
    option_number: int
    start_time: datetime
    end_time: datetime
    day_of_week: str
    formatted_time: str
    score: int

# --- Reply Analysis Models ---

class ReplyInput(BaseModel):
    """Input data for reply analysis."""
    reply_text: str
    reply_subject: Optional[str] = None
    sender_email: EmailStr
    timestamp: Optional[datetime] = None
    lead_id: Optional[str] = None

class EngagementSignals(BaseModel):
    """Signals of engagement extracted from a reply."""
    questions_asked: int
    urgency_indicators: List[str]
    budget_mentions: bool
    timeline_mentions: List[str]
    decision_authority: bool

class ReplyAnalysisResult(BaseModel):
    """Result of reply analysis."""
    disposition: str
    confidence: int
    sentiment: str
    urgency: str
    reasoning: str
    next_action: str
    follow_up_timing: str
    intent: str
    lead_score: Optional[int] = None
    priority: Optional[str] = None
    # For backward compatibility
    lead_disposition: Optional[str] = None
    disposition_confidence: Optional[int] = None
