import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "calendar_events.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        location TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def get_meeting_by_id(meeting_id: int):
    """Retrieve a meeting by its ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM meetings WHERE id = ?",
        (meeting_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_meeting(meeting_id: int):
    """Delete a meeting by its ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    conn.commit()
    conn.close()

def get_all_meetings():
    """Retrieve all meetings"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM meetings ORDER BY date, start_time")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]