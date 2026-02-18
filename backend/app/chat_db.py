import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import os

# Store database in backend directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BACKEND_DIR, 'chat_sessions.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            provider TEXT,
            model TEXT,
            metadata TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_session(user_id: str, session_id: str):
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT OR IGNORE INTO sessions (id, user_id, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (session_id, user_id, now, now))
    c.execute('''
        UPDATE sessions SET updated_at = ? WHERE id = ?
    ''', (now, session_id))
    conn.commit()
    conn.close()

def save_message(user_id: str, session_id: str, role: str, content: str, provider: str = None, model: str = None, metadata: str = None):
    from uuid import uuid4
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    msg_id = str(uuid4())
    c.execute('''
        INSERT INTO messages (id, session_id, user_id, role, content, timestamp, provider, model, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (msg_id, session_id, user_id, role, content, now, provider, model, metadata))
    conn.commit()
    conn.close()

def get_sessions(user_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC
    ''', (user_id,))
    sessions = [dict(row) for row in c.fetchall()]
    conn.close()
    return sessions

def get_messages(session_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC
    ''', (session_id,))
    messages = [dict(row) for row in c.fetchall()]
    conn.close()
    return messages

def delete_session(session_id: str):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
    c.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    conn.commit()
    conn.close()

def get_last_user_context(user_id: str) -> Dict[str, str]:
    """
    Extract universal context from user's previous chats.
    Returns recent messages and important information from all previous conversations.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[get_last_user_context] Retrieving context for user_id: {user_id}")
    
    # Try to read from chat_history.db which has the actual data
    alt_db_path = os.path.join(BACKEND_DIR, 'chat_history.db')
    logger.info(f"[get_last_user_context] Checking alternate database: {alt_db_path}")
    logger.info(f"[get_last_user_context] Alternate DB exists: {os.path.exists(alt_db_path)}")
    
    try:
        # Try alternate database first if it exists
        if os.path.exists(alt_db_path):
            logger.info(f"[get_last_user_context] Using alternate database: chat_history.db")
            conn = sqlite3.connect(alt_db_path)
            c = conn.cursor()
            
            # Get messages from chat_messages table in chat_history.db
            # This table has different schema: message_id, session_id, user_id, user_message, ai_response, ...
            c.execute('''
                SELECT user_message, ai_response FROM chat_messages 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 20
            ''', (user_id,))
            
            rows = c.fetchall()
            logger.info(f"[get_last_user_context] Retrieved {len(rows)} message pairs from chat_history.db")
            conn.close()
            
            if rows:
                # Build universal context from previous messages
                context_lines = []
                for user_msg, ai_resp in rows:
                    context_lines.append(f"[User] {user_msg}")
                    if ai_resp:
                        context_lines.append(f"[Assistant] {ai_resp}")
                
                # Reverse to get chronological order (oldest to newest)
                context_lines = context_lines[::-1]
                
                context = {
                    "previous_context": "\n".join(context_lines)
                }
                
                logger.info(f"[get_last_user_context] Built context with {len(context_lines)} lines, total length: {len(context['previous_context'])} characters")
                logger.info(f"[get_last_user_context] Context preview: {context['previous_context'][:300]}...")
                return context
    except Exception as e:
        logger.warning(f"[get_last_user_context] Failed to read from chat_history.db: {e}")
    
    # Fallback to regular database
    logger.info(f"[get_last_user_context] Falling back to primary database: {DB_PATH}")
    conn = get_db()
    c = conn.cursor()
    
    # Get the last 20 messages from all sessions (both user and assistant messages)
    c.execute('''
        SELECT role, content, timestamp FROM messages 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 20
    ''', (user_id,))
    
    messages = [dict(row) for row in c.fetchall()]
    logger.info(f"[get_last_user_context] Retrieved {len(messages)} messages from primary database")
    conn.close()
    
    if not messages:
        logger.info(f"[get_last_user_context] No messages found for user_id: {user_id}")
        return {}
    
    logger.info(f"[get_last_user_context] Processing {len(messages)} messages")
    # Reverse to get chronological order (oldest to newest)
    messages = messages[::-1]
    
    # Build universal context from previous messages
    context_lines = [
        f"[{msg['role'].capitalize()}] {msg['content']}"
        for msg in messages
    ]
    context = {
        "previous_context": "\n".join(context_lines)
    }
    
    logger.info(f"[get_last_user_context] Built context with {len(context_lines)} lines, total length: {len(context['previous_context'])} characters")
    
    # Also extract specific patterns if they exist (name, preferences, etc.)
    all_content = " ".join([msg['content'] for msg in messages])
    
    # Extract name if mentioned
    if 'my name is' in all_content.lower():
        for msg in messages:
            if 'my name is' in msg['content'].lower():
                words = msg['content'].lower().split('my name is')[-1].strip().split()
                if words:
                    context['name'] = words[0].capitalize()
                    logger.info(f"[get_last_user_context] Extracted name: {context['name']}")
                break
    
    # Extract other key information
    if 'email' in all_content.lower():
        context['has_email'] = True
    if 'phone' in all_content.lower():
        context['has_phone'] = True
    
    logger.info(f"[get_last_user_context] Final context keys: {context.keys()}")
    return context


# Call this at startup
init_db()
