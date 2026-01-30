"""
Negotiation session database models
"""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
import json


class NegotiationSessionCreate(BaseModel):
    """Schema for creating a new negotiation session"""
    user_id: int
    initial_offer_data: dict
    max_rounds: int = 5


class NegotiationSession(BaseModel):
    """Negotiation session model"""
    id: Optional[int] = None
    session_id: str
    user_id: int
    status: str = "active"  # active, completed, expired, rejected, max_rounds_reached
    current_round: int = 1
    max_rounds: int = 5
    initial_offer_data: dict
    current_offer_data: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(default_factory=lambda: datetime.now() + timedelta(hours=24))

    class Config:
        from_attributes = True


class NegotiationHistoryCreate(BaseModel):
    """Schema for creating negotiation history entry"""
    session_id: str
    round_number: int
    speaker: str  # 'client' or 'agent'
    message: str
    offer_data: Optional[dict] = None
    action: str  # 'propose', 'counter', 'accept', 'reject'


class NegotiationHistory(BaseModel):
    """Negotiation history model"""
    id: Optional[int] = None
    session_id: str
    round_number: int
    speaker: str
    message: str
    offer_data: Optional[dict] = None
    action: str
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class NegotiationMessageRequest(BaseModel):
    """Request schema for sending a message in negotiation"""
    message: str
    counter_offer: Optional[dict] = None
    action: str = "counter"  # 'counter', 'accept', 'reject'


class NegotiationMessageResponse(BaseModel):
    """Response schema for negotiation message"""
    agent_response: str
    revised_offer: Optional[dict] = None
    round: int
    remaining_rounds: int
    status: str
    session_id: str
