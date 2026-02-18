#!/usr/bin/env python3
"""
MCP Tool for Google Calendar Meeting Scheduling
Detects meeting requests from chat messages and creates calendar events
"""

import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class MeetingExtractor:
    """Extract meeting details from chat messages using NLP patterns"""
    
    # Time patterns (e.g., "3pm", "15:30", "3:00 PM", "at 3")
    TIME_PATTERNS = [
        r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)',  # 3:30 pm
        r'(\d{1,2})\s*(am|pm|AM|PM)',  # 3pm
        r'at\s+(\d{1,2})\s*(?::(\d{2}))?\s*(am|pm|AM|PM)?',  # at 3 pm
    ]
    
    # Date patterns
    DATE_PATTERNS = [
        r'(today)',  # today
        r'(tomorrow)',  # tomorrow
        r'(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))',  # next monday
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # 12/25/2024
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',  # december 25
    ]
    
    # Meeting indicators
    MEETING_KEYWORDS = [
        'meeting', 'schedule', 'call', 'zoom', 'teams', 'conference',
        'chat', 'discussion', 'appointment', 'event', 'gather', 'reserve',
        'book', 'set up', 'arrange', 'plan', 'sync', 'standup', 'stand-up'
    ]
    
    # Duration patterns
    DURATION_PATTERNS = [
        r'(?:for|duration:?)\s*(\d{1,2})\s*(?:hour|hr)s?',  # for 1 hour
        r'(?:for|duration:?)\s*(\d{1,2})\s*(?:minute|min)s?',  # for 30 minutes
    ]
    
    @staticmethod
    def parse_time(time_str: str, base_date: datetime = None) -> Optional[datetime]:
        """Parse time string and return datetime object"""
        if base_date is None:
            base_date = datetime.now()
        
        time_str = time_str.lower().strip()
        
        # Try 24-hour format HH:MM
        try:
            return base_date.replace(
                hour=int(time_str.split(':')[0]),
                minute=int(time_str.split(':')[1]) if ':' in time_str else 0,
                second=0
            )
        except (ValueError, IndexError):
            pass
        
        # Try AM/PM format
        match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            is_pm = match.group(3) == 'pm'
            
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
            
            return base_date.replace(hour=hour, minute=minute, second=0)
        
        return None
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string and return datetime object"""
        date_str = date_str.lower().strip()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Today
        if 'today' in date_str:
            return today
        
        # Tomorrow
        if 'tomorrow' in date_str:
            return today + timedelta(days=1)
        
        # Next X day
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        for day_name, day_num in days.items():
            if day_name in date_str:
                today_weekday = today.weekday()
                days_ahead = (day_num - today_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return today + timedelta(days=days_ahead)
        
        # Explicit date MM/DD/YYYY or DD/MM/YYYY
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
        if match:
            try:
                month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if year < 100:
                    year += 2000
                return datetime(year, month, day)
            except ValueError:
                pass
        
        # Month name format
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        for month_name, month_num in months.items():
            if month_name in date_str:
                match = re.search(rf'{month_name}\s+(\d{{1,2}})', date_str)
                if match:
                    day = int(match.group(1))
                    year = today.year
                    result = datetime(year, month_num, day)
                    if result < today:
                        year += 1
                        result = datetime(year, month_num, day)
                    return result
        
        return None
    
    @staticmethod
    def extract_duration(text: str) -> Optional[int]:
        """Extract meeting duration in minutes"""
        text_lower = text.lower()
        
        # Check for hours
        hours_match = re.search(r'(?:for|duration:?)\s*(\d{1,2})\s*(?:hour|hr)s?', text_lower)
        if hours_match:
            return int(hours_match.group(1)) * 60
        
        # Check for minutes
        minutes_match = re.search(r'(?:for|duration:?)\s*(\d{1,2})\s*(?:minute|min)s?', text_lower)
        if minutes_match:
            return int(minutes_match.group(1))
        
        # Default duration
        return 60
    
    @classmethod
    def extract_meeting_details(cls, message: str) -> Optional[Dict[str, Any]]:
        """
        Extract meeting details from chat message
        Returns dict with keys: title, date, time, duration, participants
        """
        message_lower = message.lower()
        
        # Check if message contains meeting keywords
        has_meeting_keyword = any(keyword in message_lower for keyword in cls.MEETING_KEYWORDS)
        if not has_meeting_keyword:
            return None
        
        # Extract time
        time_match = None
        time_obj = None
        for pattern in cls.TIME_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                time_match = match
                break
        
        # Extract date
        date_match = None
        date_obj = None
        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                date_match = match
                break
        
        # Parse date first
        if date_match:
            date_obj = cls.parse_date(date_match.group(0))
        else:
            date_obj = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Parse time
        if time_match:
            time_text = time_match.group(0)
            time_obj = cls.parse_time(time_text, date_obj)
        else:
            time_obj = date_obj.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Ensure datetime is set
        if time_obj is None:
            time_obj = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Extract duration
        duration = cls.extract_duration(message)
        
        # Extract title (use message context)
        title = cls.extract_title(message)
        
        # Extract participants (emails or names)
        participants = cls.extract_participants(message)
        
        return {
            'title': title,
            'start_time': time_obj.isoformat(),
            'duration_minutes': duration,
            'date': date_obj.strftime('%Y-%m-%d'),
            'time': time_obj.strftime('%H:%M'),
            'participants': participants,
            'description': message
        }
    
    @staticmethod
    def extract_title(message: str) -> str:
        """Extract meeting title from message"""
        # Look for quoted strings
        quoted = re.search(r'"([^"]+)"', message)
        if quoted:
            return quoted.group(1)
        
        # Look for text after "meeting" or "call"
        for keyword in ['about', 'regarding', 'for']:
            match = re.search(rf'{keyword}\s+([^.!?\n]+)', message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Generate from first few words after meeting keyword
        meeting_match = re.search(r'(?:meeting|call|meeting)\s+([^.!?\n]+)', message, re.IGNORECASE)
        if meeting_match:
            text = meeting_match.group(1).strip()
            words = text.split()[:5]
            return ' '.join(words)
        
        return "Meeting"
    
    @staticmethod
    def extract_participants(message: str) -> list:
        """Extract email addresses and participant names"""
        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
        
        # Extract names mentioned with "with" or "and"
        names = []
        with_match = re.search(r'with\s+([^.!?\n]+)', message, re.IGNORECASE)
        if with_match:
            participants_str = with_match.group(1)
            # Split by common separators
            participants = re.split(r'\s+and\s+|,\s*', participants_str)
            names = [p.strip() for p in participants if p.strip()]
        
        return emails + names


class GoogleCalendarManager:
    """Manages Google Calendar integration via MCP"""
    
    def __init__(self, credentials_path: str = None):
        """Initialize calendar manager"""
        self.credentials_path = credentials_path or 'google_credentials.json'
        self.extractor = MeetingExtractor()
        logger.info("GoogleCalendarManager initialized")
    
    def detect_and_extract_meeting(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Detect if user message contains meeting request and extract details
        """
        return self.extractor.extract_meeting_details(user_message)
    
    def format_meeting_for_calendar(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format extracted meeting data for Google Calendar API"""
        start_time = datetime.fromisoformat(meeting_data['start_time'])
        end_time = start_time + timedelta(minutes=meeting_data['duration_minutes'])
        
        event = {
            'summary': meeting_data['title'],
            'description': meeting_data['description'],
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC'
            },
            'attendees': [
                {'email': participant, 'displayName': participant}
                for participant in meeting_data.get('participants', [])
            ] if meeting_data.get('participants') else []
        }
        
        return event


def create_mcp_tool(tool_name: str) -> Dict[str, Any]:
    """Create MCP tool definition"""
    
    tools = {
        'extract_meeting': {
            'name': 'extract_meeting_from_chat',
            'description': 'Extract meeting details from chat messages',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'message': {
                        'type': 'string',
                        'description': 'The user chat message to analyze'
                    }
                },
                'required': ['message']
            }
        },
        'create_calendar_event': {
            'name': 'create_google_calendar_event',
            'description': 'Create an event in Google Calendar',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string', 'description': 'Event title'},
                    'date': {'type': 'string', 'description': 'Event date (YYYY-MM-DD)'},
                    'time': {'type': 'string', 'description': 'Event time (HH:MM)'},
                    'duration_minutes': {'type': 'integer', 'description': 'Duration in minutes'},
                    'description': {'type': 'string', 'description': 'Event description'},
                    'participants': {'type': 'array', 'items': {'type': 'string'}, 'description': 'List of participant emails'}
                },
                'required': ['title', 'date', 'time']
            }
        },
        'list_calendar_events': {
            'name': 'list_google_calendar_events',
            'description': 'List upcoming events from Google Calendar',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'max_results': {'type': 'integer', 'description': 'Maximum number of results', 'default': 10},
                    'days_ahead': {'type': 'integer', 'description': 'Number of days to look ahead', 'default': 7}
                }
            }
        }
    }
    
    return tools.get(tool_name, {})


if __name__ == '__main__':
    # Test the extractor
    test_messages = [
        "Schedule a meeting tomorrow at 3pm about project roadmap",
        "I need to set up a call with john@example.com on Dec 25 for 1 hour",
        "Can you book a meeting next Monday at 10am with the team",
        "Let's have a standup today at 9:30am for 30 minutes"
    ]
    
    extractor = MeetingExtractor()
    for msg in test_messages:
        print(f"\nMessage: {msg}")
        result = extractor.extract_meeting_details(msg)
        if result:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("No meeting detected")
