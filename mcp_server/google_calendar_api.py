#!/usr/bin/env python3
"""
Google Calendar API Integration Module
Handles authentication and calendar operations
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class GoogleCalendarAPI:
    """Handles Google Calendar API operations"""
    
    def __init__(self, credentials_file: Optional[str] = None):
        """
        Initialize Google Calendar API client
        
        Args:
            credentials_file: Path to Google service account JSON file
        """
        self.credentials_file = credentials_file or os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        self.service = None
        
        if self.credentials_file and os.path.exists(self.credentials_file):
            self._initialize_service()
        else:
            logger.warning("Google Calendar credentials not configured")
    
    def _initialize_service(self):
        """Initialize Google Calendar service"""
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            scopes = ['https://www.googleapis.com/auth/calendar']
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar API service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")
            self.service = None
    
    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        attendees: List[str] = None,
        location: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Create an event in Google Calendar
        
        Args:
            title: Event title
            start_time: Start datetime
            end_time: End datetime
            description: Event description
            attendees: List of attendee email addresses
            location: Event location
        
        Returns:
            Event data dict or None if failed
        """
        if not self.service:
            logger.warning("Calendar service not initialized")
            return None
        
        try:
            event = {
                'summary': title,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC'
                },
                'attendees': [
                    {'email': email}
                    for email in (attendees or [])
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10}
                    ]
                }
            }
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                sendNotifications=True
            ).execute()
            
            logger.info(f"Event created: {created_event.get('id')}")
            return created_event
        
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None
    
    def list_events(
        self,
        max_results: int = 10,
        days_ahead: int = 7,
        search_query: str = ""
    ) -> List[Dict[str, Any]]:
        """
        List upcoming events from Google Calendar
        
        Args:
            max_results: Maximum number of events to return
            days_ahead: Number of days in the future to check
            search_query: Optional search query
        
        Returns:
            List of event dictionaries
        """
        if not self.service:
            logger.warning("Calendar service not initialized")
            return []
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            end_time = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                timeMax=end_time,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime',
                q=search_query if search_query else None
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} events")
            return events
        
        except Exception as e:
            logger.error(f"Failed to list calendar events: {e}")
            return []
    
    def update_event(
        self,
        event_id: str,
        title: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        description: str = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing calendar event"""
        if not self.service:
            logger.warning("Calendar service not initialized")
            return None
        
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields
            if title:
                event['summary'] = title
            if description:
                event['description'] = description
            if start_time:
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC'
                }
            if end_time:
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC'
                }
            
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Event updated: {event_id}")
            return updated_event
        
        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event"""
        if not self.service:
            logger.warning("Calendar service not initialized")
            return False
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            logger.info(f"Event deleted: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            return False
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific calendar event"""
        if not self.service:
            logger.warning("Calendar service not initialized")
            return None
        
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return event
        except Exception as e:
            logger.error(f"Failed to get event: {e}")
            return None


# Global instance
_calendar_api = None


def get_calendar_api() -> GoogleCalendarAPI:
    """Get or create Google Calendar API instance"""
    global _calendar_api
    if _calendar_api is None:
        _calendar_api = GoogleCalendarAPI()
    return _calendar_api


def initialize_calendar_api(credentials_file: str):
    """Initialize calendar API with specific credentials file"""
    global _calendar_api
    _calendar_api = GoogleCalendarAPI(credentials_file)
    return _calendar_api
