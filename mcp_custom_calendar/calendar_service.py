from calendar_db import get_connection, delete_meeting
from datetime import datetime

WORK_START = "09:00"
WORK_END = "18:00"

class SchedulingService:
    """Service for managing meeting scheduling."""
    
    def get_meetings(self, date: str):
        """Get all meetings for a specific date"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, title, start_time, end_time FROM meetings WHERE date = ? ORDER BY start_time",
            (date,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_meetings_time_slots(self, date: str):
        """Get time slots (start, end tuples) for conflict checking"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT start_time, end_time FROM meetings WHERE date = ? ORDER BY start_time",
            (date,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [(r["start_time"], r["end_time"]) for r in rows]
    
    def has_conflict(self, start: str, end: str, date: str):
        """Check if a time slot conflicts with existing meetings"""
        meetings = self.get_meetings_time_slots(date)
        for m_start, m_end in meetings:
            if not (end <= m_start or start >= m_end):
                return True
        return False
    
    def available_slots(self, meetings):
        """Find available time slots"""
        slots = []
        current_time = WORK_START

        for m_start, m_end in meetings:
            if current_time < m_start:
                slots.append((current_time, m_start))
            current_time = max(current_time, m_end)

        if current_time < WORK_END:
            slots.append((current_time, WORK_END))

        return slots

    def save_meeting(self, date, start: str, end: str, title: str, description: str = None, location: str = None):
        """Save a meeting to the database"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO meetings (date, start_time, end_time, title, description, location) VALUES (?, ?, ?, ?, ?, ?)",
            (str(date), start, end, title, description or "", location or "")
        )
        conn.commit()
        meeting_id = cursor.lastrowid
        conn.close()
        return meeting_id

    def cancel_meeting(self, meeting_id: int):
        """Cancel/delete a meeting"""
        delete_meeting(meeting_id)
        return True

    def find_meeting_by_title_and_date(self, title: str, date: str):
        """Find a meeting by title and date (for cancellation)"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, title, date, start_time, end_time FROM meetings WHERE title LIKE ? AND date = ?",
            (f"%{title}%", date)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


# Legacy function wrappers for backward compatibility
def get_meetings(date: str):
    """Get all meetings for a specific date"""
    service = SchedulingService()
    return service.get_meetings(date)

def get_meetings_time_slots(date: str):
    """Get time slots (start, end tuples) for conflict checking"""
    service = SchedulingService()
    return service.get_meetings_time_slots(date)

def has_conflict(start: str, end: str, date: str):
    """Check if a time slot conflicts with existing meetings"""
    service = SchedulingService()
    return service.has_conflict(start, end, date)

def available_slots(meetings):
    """Find available time slots"""
    service = SchedulingService()
    return service.available_slots(meetings)

def save_meeting(date: str, start: str, end: str, title: str, description: str = None, location: str = None):
    """Save a meeting to the database"""
    service = SchedulingService()
    return service.save_meeting(date, start, end, title, description, location)

def cancel_meeting(meeting_id: int):
    """Cancel/delete a meeting"""
    service = SchedulingService()
    return service.cancel_meeting(meeting_id)

def find_meeting_by_title_and_date(title: str, date: str):
    """Find a meeting by title and date (for cancellation)"""
    service = SchedulingService()
    return service.find_meeting_by_title_and_date(title, date)    