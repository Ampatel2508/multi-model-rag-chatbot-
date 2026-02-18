"""Database service layer for user, chat session, and message management."""

import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.db_models import User, ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management."""
    
    @staticmethod
    def get_or_create_user(db: Session, user_id: str, email: str = None) -> User:
        """Get existing user or create new one."""
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(user_id=user_id, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user


class ChatSessionService:
    """Service for chat session management."""
    
    @staticmethod
    def create_session(db: Session, user_id: str, title: str = None) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(user_id=user_id, title=title or "New Chat")
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
        """Get chat session by ID."""
        return db.query(ChatSession).filter(ChatSession.id == session_id).first()
    
    @staticmethod
    def list_sessions(db: Session, user_id: str) -> List[ChatSession]:
        """List all sessions for a user."""
        return db.query(ChatSession).filter(ChatSession.user_id == user_id).all()


class ChatMessageService:
    """Service for chat message management."""
    
    @staticmethod
    def create_message(
        db: Session,
        session_id: str,
        user_message: str,
        ai_response: str,
        model_used: str = None,
        provider_used: str = None
    ) -> ChatMessage:
        """Save a chat message exchange."""
        message = ChatMessage(
            session_id=session_id,
            user_message=user_message,
            ai_response=ai_response,
            model_used=model_used,
            provider_used=provider_used,
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def get_session_messages(db: Session, session_id: str) -> List[ChatMessage]:
        """Get all messages for a session."""
        return db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.asc()).all()
