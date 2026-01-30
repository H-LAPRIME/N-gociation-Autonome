"""
Database utilities for negotiation sessions
Stores session data in JSON files (temporary storage per session)
"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List
import uuid
from pathlib import Path

from app.schemas.negotiation_session import (
    NegotiationSession,
    NegotiationSessionCreate,
    NegotiationHistory,
    NegotiationHistoryCreate
)


class NegotiationDatabase:
    """Simple JSON-based database for negotiation sessions"""
    
    def __init__(self, data_dir: str = "data/negotiations"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.data_dir / "sessions.json"
        self.history_dir = self.data_dir / "history"
        self.history_dir.mkdir(exist_ok=True)
        
        # Initialize sessions file if doesn't exist
        if not self.sessions_file.exists():
            self._save_sessions({})
    
    def _load_sessions(self) -> dict:
        """Load all sessions from JSON file"""
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_sessions(self, sessions: dict):
        """Save all sessions to JSON file"""
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False, default=str)
    
    def _get_history_file(self, session_id: str) -> Path:
        """Get history file path for a session"""
        return self.history_dir / f"{session_id}.json"
    
    def _load_history(self, session_id: str) -> List[dict]:
        """Load history for a session"""
        history_file = self._get_history_file(session_id)
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save_history(self, session_id: str, history: List[dict]):
        """Save history for a session"""
        history_file = self._get_history_file(session_id)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False, default=str)
    
    def create_session(self, session_data: NegotiationSessionCreate) -> NegotiationSession:
        """Create a new negotiation session"""
        sessions = self._load_sessions()
        
        # Generate unique session ID
        session_id = f"NEG-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Create session object
        session = NegotiationSession(
            session_id=session_id,
            user_id=session_data.user_id,
            initial_offer_data=session_data.initial_offer_data,
            current_offer_data=session_data.initial_offer_data,
            max_rounds=session_data.max_rounds,
            status="active",
            current_round=1
        )
        
        # Save to sessions
        sessions[session_id] = session.model_dump(mode='json')
        self._save_sessions(sessions)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[NegotiationSession]:
        """Get a session by ID"""
        sessions = self._load_sessions()
        session_data = sessions.get(session_id)
        
        if not session_data:
            return None
        
        return NegotiationSession(**session_data)
    
    def get_active_session_by_user(self, user_id: int) -> Optional[NegotiationSession]:
        """Get active negotiation session for a user"""
        sessions = self._load_sessions()
        
        for session_data in sessions.values():
            if session_data['user_id'] == user_id and session_data['status'] == 'active':
                return NegotiationSession(**session_data)
        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its history"""
        sessions = self._load_sessions()
        if session_id in sessions:
            del sessions[session_id]
            self._save_sessions(sessions)
            
            # Delete history file if exists
            history_file = self._get_history_file(session_id)
            if history_file.exists():
                os.remove(history_file)
            return True
        return False
    
    def update_session(self, session: NegotiationSession) -> NegotiationSession:
        """Update a session"""
        sessions = self._load_sessions()
        
        # Update timestamp
        session.updated_at = datetime.now()
        
        # Save
        sessions[session.session_id] = session.model_dump(mode='json')
        self._save_sessions(sessions)
        
        return session
    
    def add_history(self, history_data: NegotiationHistoryCreate) -> NegotiationHistory:
        """Add a history entry"""
        history = self._load_history(history_data.session_id)
        
        # Create history entry
        entry = NegotiationHistory(
            id=len(history) + 1,
            **history_data.model_dump()
        )
        
        # Add to history
        history.append(entry.model_dump(mode='json'))
        self._save_history(history_data.session_id, history)
        
        return entry
    
    def get_history(self, session_id: str) -> List[NegotiationHistory]:
        """Get all history for a session"""
        history = self._load_history(session_id)
        return [NegotiationHistory(**entry) for entry in history]
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        sessions = self._load_sessions()
        now = datetime.now()
        
        expired_ids = []
        for session_id, session_data in sessions.items():
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if now > expires_at and session_data['status'] == 'active':
                session_data['status'] = 'expired'
                expired_ids.append(session_id)
        
        if expired_ids:
            self._save_sessions(sessions)
        
        return len(expired_ids)


# Global instance
negotiation_db = NegotiationDatabase()
