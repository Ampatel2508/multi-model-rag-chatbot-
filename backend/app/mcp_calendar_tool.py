"""
Direct MCP Calendar Tool - Simple endpoint to create events via MCP
"""
import os
import json
import logging
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# Google Calendar imports
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

class MCPCalendarTool:
    """Direct Google Calendar tool for meeting scheduling"""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
            token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.json')
            
            if os.path.exists(token_path):
                self.credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(GoogleRequest())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials
                with open(token_path, 'w') as token:
                    token.write(self.credentials.to_json())
            
            self.service = build('calendar', 'v3', credentials=self.credentials)
            logger.info("✅ Google Calendar authenticated")
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
    
    def parse_and_create_event(self, message: str, title: str = None) -> dict:
        """
        Parse natural language message and create calendar event
        
        Args:
            message: User message like "schedule meeting tomorrow at 2 PM"
            title: Optional meeting title
            
        Returns:
            Dictionary with event details or error
        """
        try:
            if not self.service:
                return {"success": False, "error": "Calendar service not initialized"}
            
            # Parse datetime from message
            parsed_dt = date_parser.parse(message, fuzzy=True, ignoretz=True)
            
            # Ensure it's in the future
            if parsed_dt < datetime.now():
                parsed_dt = datetime.now() + timedelta(days=1)
            
            # Extract title if not provided
            if not title:
                title = self._extract_title(message)
            
            # Create event
            start_time = parsed_dt.isoformat()
            end_time = (parsed_dt + timedelta(hours=1)).isoformat()
            
            event = {
                'summary': title,
                'description': message,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                },
            }
            
            # Create in Google Calendar
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return {
                "success": True,
                "event_id": created_event.get('id'),
                "title": created_event.get('summary'),
                "start": created_event.get('start', {}).get('dateTime'),
                "link": created_event.get('htmlLink'),
                "message": f"✅ Meeting '{title}' scheduled successfully!"
            }
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Could not schedule meeting: {str(e)}"
            }
    
    def _extract_title(self, message: str) -> str:
        """Extract meeting title from message"""
        import re
        
        msg = message.lower()
        
        # Try to extract meaningful content from common patterns
        # Pattern: "schedule/book/set [a] meeting [with X] [on DATE] [at TIME]"
        
        # First, try to extract "with <names/people>"
        with_match = re.search(r'\bwith\s+([^,;.!?]+?)(?:\s+(?:on|at|tomorrow|today|next|this)\b|$)', msg, re.IGNORECASE)
        if with_match:
            title = with_match.group(1).strip()
            # Remove time if it snuck in
            title = re.sub(r'\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)', '', title)
            # Remove date patterns
            title = re.sub(r'\d{1,2}(?:st|nd|rd|th)?\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', '', title, flags=re.IGNORECASE)
            title = title.strip()
            if title and len(title) > 1:
                return title.title()
        
        # Next, remove all structural words and dates/times, keep what remains
        title = msg
        
        # Remove action phrases
        action_phrases = [
            r'\bcan you\b', r'\bschedule meeting\b', r'\bbook meeting\b', r'\bschedule\b',
            r'\bbook\b', r'\bset\s+(?:a\s+)?meeting\b', r'\bcreate meeting\b', r'\bplease\b',
            r'\balso\b', r'\bthen\b', r'\bmeeting\b', r'\bcall\b', r'\band\b',
        ]
        
        for phrase in action_phrases:
            title = re.sub(phrase, ' ', title, flags=re.IGNORECASE)
        
        # Remove time patterns (including times like "12 noon", "3 pm")
        title = re.sub(r'\d{1,2}(?:\s+)?(?:noon|midnight)', ' ', title, flags=re.IGNORECASE)
        title = re.sub(r'\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)', ' ', title, flags=re.IGNORECASE)
        title = re.sub(r'\d{1,2}:\d{2}', ' ', title)
        
        # Remove date patterns
        title = re.sub(r'\d{1,2}(?:st|nd|rd|th)?(?:\s+|-)(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w]*', ' ', title, flags=re.IGNORECASE)
        title = re.sub(r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w]*(?:\s+|,|-)\d{1,2}(?:st|nd|rd|th)?', ' ', title, flags=re.IGNORECASE)
        
        # Remove day/time references
        title = re.sub(r'\b(?:tomorrow|today|tonight|next|this|at|on|from|during|in|for)\b', ' ', title, flags=re.IGNORECASE)
        title = re.sub(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', ' ', title, flags=re.IGNORECASE)
        
        # Clean up multiple spaces and trim
        title = ' '.join(title.split()).strip()
        
        # If nothing left, use default
        if not title or len(title) < 2:
            return "Meeting"
        
        # Remove very short words (single letters except 'i', 'a', 'or')
        words = title.split()
        filtered = [w for w in words if len(w) > 1 or w.lower() in ['i', 'a', 'or']]
        
        if filtered:
            return ' '.join(filtered[:5]).title()
        else:
            return "Meeting"


# Global instance
_mcp_calendar = None

def get_mcp_calendar() -> MCPCalendarTool:
    """Get or create MCP calendar tool instance"""
    global _mcp_calendar
    if _mcp_calendar is None:
        _mcp_calendar = MCPCalendarTool()
    return _mcp_calendar
