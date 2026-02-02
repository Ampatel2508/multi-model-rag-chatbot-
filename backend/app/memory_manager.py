"""Memory Manager - Handles conversation history and context using LangChain Memory."""

import logging
from typing import Dict, List, Optional
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationMemoryManager:
    """
    Manages conversation history and context for each chat session.
    Uses LangChain's ChatMessageHistory to maintain context across multiple turns.
    """
    
    def __init__(self, memory_type: str = "buffer", max_tokens: int = 2000):
        """
        Initialize the memory manager.
        
        Args:
            memory_type: Type of memory ("buffer" or "summary")
            max_tokens: Maximum tokens to keep in memory
        """
        self.memory_type = memory_type
        self.max_tokens = max_tokens
        self.sessions: Dict[str, ChatMessageHistory] = {}
        logger.info(f"Memory Manager initialized with {memory_type} memory")
    
    def get_or_create_session(self, session_id: str) -> ChatMessageHistory:
        """
        Get existing session memory or create a new one.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            ChatMessageHistory instance for the session
        """
        if session_id not in self.sessions:
            logger.info(f"Creating new memory session: {session_id}")
            
            # Create message history for storing the conversation
            history = ChatMessageHistory()
            
            self.sessions[session_id] = history
            logger.info(f"✓ Session {session_id} created")
        
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, user_message: str, ai_response: str):
        """
        Add a user message and AI response to the session memory.
        
        Args:
            session_id: Session identifier
            user_message: The user's input
            ai_response: The assistant's response
        """
        try:
            history = self.get_or_create_session(session_id)
            
            # Add messages to history
            history.add_user_message(user_message)
            history.add_ai_message(ai_response)
            
            logger.debug(f"Added message to session {session_id}")
            logger.debug(f"Total messages in session: {len(history.messages)}")
            
        except Exception as e:
            logger.error(f"Error adding message to memory: {e}")
    
    def get_chat_history(self, session_id: str) -> str:
        """
        Get formatted chat history for the session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Formatted chat history as string
        """
        try:
            history = self.get_or_create_session(session_id)
            
            # Format messages for display
            formatted = []
            for msg in history.messages:
                if isinstance(msg, HumanMessage):
                    formatted.append(f"User: {msg.content}")
                elif isinstance(msg, AIMessage):
                    formatted.append(f"Assistant: {msg.content}")
            
            return "\n".join(formatted) if formatted else ""
            
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return ""
    
    def get_chat_history_messages(self, session_id: str) -> List[BaseMessage]:
        """
        Get raw chat history messages for the session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of BaseMessage objects
        """
        try:
            history = self.get_or_create_session(session_id)
            return history.messages
            
        except Exception as e:
            logger.error(f"Error retrieving chat history messages: {e}")
            return []
    
    def clear_session(self, session_id: str):
        """
        Clear memory for a specific session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} cleared from memory")
    
    def clear_all_sessions(self):
        """Clear memory for all sessions."""
        self.sessions.clear()
        logger.info("All sessions cleared from memory")
    
    def get_session_summary(self, session_id: str) -> Dict:
        """
        Get a summary of the session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session information
        """
        memory = self.get_or_create_session(session_id)
        messages = self.get_chat_history_messages(session_id)
        
        return {
            "session_id": session_id,
            "message_count": len(messages),
            "memory_type": self.memory_type,
            "last_updated": datetime.now().isoformat(),
            "preview": self.get_chat_history(session_id)[:200] + "..." if self.get_chat_history(session_id) else "No messages yet"
        }
    
    def export_session(self, session_id: str) -> Dict:
        """
        Export session history as JSON-serializable dictionary.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary containing session history
        """
        try:
            messages = self.get_chat_history_messages(session_id)
            
            exported = {
                "session_id": session_id,
                "exported_at": datetime.now().isoformat(),
                "messages": []
            }
            
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    exported["messages"].append({
                        "role": "user",
                        "content": msg.content
                    })
                elif isinstance(msg, AIMessage):
                    exported["messages"].append({
                        "role": "assistant",
                        "content": msg.content
                    })
            
            return exported
            
        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return {}
    
    def build_context_prompt(self, session_id: str, current_question: str, system_context: str = "") -> str:
        """
        Build a complete prompt with chat history context.
        
        Args:
            session_id: Session identifier
            current_question: The current user question
            system_context: Additional system context (e.g., document content)
            
        Returns:
            Complete prompt with history and context
        """
        chat_history = self.get_chat_history(session_id)
        
        prompt = ""
        
        if system_context:
            prompt += f"CONTEXT:\n{system_context}\n\n"
        
        if chat_history:
            prompt += f"CONVERSATION HISTORY:\n{chat_history}\n\n"
        
        prompt += f"CURRENT QUESTION:\n{current_question}"
        
        return prompt


# Global memory manager instance
_memory_manager = None


def get_memory_manager() -> ConversationMemoryManager:
    """Get or create the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = ConversationMemoryManager()
    return _memory_manager
