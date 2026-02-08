import json
import os
from datetime import datetime
from typing import Optional, List, Dict
import uuid
from pathlib import Path
from app.schemas.chat_session import ChatSession, ChatMessage

class ChatDatabase:
    """Simple JSON-based database for chat sessions"""
    
    def __init__(self, data_dir: str = "data/chats"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.data_dir / "chat_sessions.json"
        
        # Initialize sessions file if doesn't exist
        if not self.sessions_file.exists():
            self._save_sessions({})
    
    def _load_sessions(self) -> dict:
        """Load all sessions from JSON file"""
        try:
            if not self.sessions_file.exists():
                return {}
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_sessions(self, sessions: dict):
        """Save all sessions to JSON file"""
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False, default=str)
    
    def create_session(self, user_id: int, title: str = "Nouvelle conversation") -> ChatSession:
        """Create a new chat session"""
        sessions = self._load_sessions()
        
        session_id = f"CHAT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=title,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            profile_state={}
        )
        
        sessions[session_id] = session.model_dump(mode='json')
        self._save_sessions(sessions)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID"""
        sessions = self._load_sessions()
        session_data = sessions.get(session_id)
        
        if not session_data:
            return None
        
        return ChatSession(**session_data)
    
    def list_user_sessions(self, user_id: int) -> List[ChatSession]:
        """List all sessions for a specific user"""
        sessions = self._load_sessions()
        user_sessions = []
        
        for session_data in sessions.values():
            if session_data['user_id'] == user_id:
                user_sessions.append(ChatSession(**session_data))
        
        # Sort by updated_at descending
        user_sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return user_sessions
    
    def update_session(self, session: ChatSession) -> ChatSession:
        """Update a session"""
        sessions = self._load_sessions()
        session.updated_at = datetime.now()
        sessions[session.session_id] = session.model_dump(mode='json')
        self._save_sessions(sessions)
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        sessions = self._load_sessions()
        if session_id in sessions:
            del sessions[session_id]
            self._save_sessions(sessions)
            return True
        return False

# Global instance
chat_db = ChatDatabase()
