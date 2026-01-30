from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatSessionBase(BaseModel):
    user_id: int
    title: str = "Nouvelle conversation"

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    session_id: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    profile_state: Dict = {}
