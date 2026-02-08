"""
Chat API Endpoints
------------------
Handles chat session management including creation, retrieval, and message persistence.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from app.schemas.chat_session import ChatSession, ChatSessionCreate, ChatMessage
from app.database.chat_db import chat_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(current_user: dict = Depends(get_current_user)):
    """Create a new chat session for the current user"""
    return chat_db.create_session(user_id=current_user["user_id"])

@router.get("/sessions", response_model=List[ChatSession])
async def list_chat_sessions(current_user: dict = Depends(get_current_user)):
    """List all sessions for the current user"""
    return chat_db.list_user_sessions(user_id=current_user["user_id"])

@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific chat session by ID"""
    session = chat_db.get_session(session_id)
    if not session or session.user_id != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a chat session"""
    session = chat_db.get_session(session_id)
    if not session or session.user_id != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Session not found")
    
    success = chat_db.delete_session(session_id)
    return {"success": success}

@router.post("/sessions/{session_id}/messages", response_model=ChatSession)
async def add_message_to_session(session_id: str, message: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Add a message to an existing session (used for manual persistence if needed)"""
    session = chat_db.get_session(session_id)
    if not session or session.user_id != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.messages.append(message)
    return chat_db.update_session(session)
