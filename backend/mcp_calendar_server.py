#!/usr/bin/env python3
"""
MCP Server for Google Calendar Integration
Provides tools for scheduling meetings, fetching calendar events, and parsing dates
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional
import logging
from dotenv import load_dotenv
import re

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool
import mcp.types as mcp_types

# Google Calendar imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.oauthlib.flow import InstalledAppFlow
from google.calendar import CalendarV3
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Natural language date parsing
from dateutil import parser as date_parser
import arrow

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Calendar API Scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarMCPServer:
    """MCP Server for Google Calendar operations"""
    
    def __init__(self):
        self.server = Server("google-calendar-mcp")
        self.service = None
        self.calendar_id = 'primary'
        self._setup_routes()
        self._initialize_google_calendar()
    
    def _initialize_google_calendar(self):
        """Initialize Google Calendar service with OAuth2"""
        try:
            creds = None
            # Load credentials from file if available
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # If no valid credentials, request authorization
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar: {str(e)}")
            # Continue without service - will fail gracefully on calendar ops
    
    def _setup_routes(self):
        """Set up MCP server routes/tools"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="parse_meeting_date_time",
                    description="Parse natural language text to extract date and time for meeting scheduling",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Natural language text containing date/time information"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="create_calendar_event",
                    description="Create a meeting event on Google Calendar",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Meeting title"
                            },
                            "start_datetime": {
                                "type": "string",
                                "description": "ISO format start datetime (e.g., 2025-02-15T14:00:00)"
                            },
                            "end_datetime": {
                                "type": "string",
                                "description": "ISO format end datetime (e.g., 2025-02-15T15:00:00)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Meeting description/notes"
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of attendee email addresses"
                            }
                        },
                        "required": ["title", "start_datetime", "end_datetime"]
                    }
                ),
                Tool(
                    name="get_calendar_events",
                    description="Fetch calendar events for a specific date range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in ISO format (e.g., 2025-02-15)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in ISO format (e.g., 2025-02-20)"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                ),
                Tool(
                    name="cancel_calendar_event",
                    description="Cancel/delete a calendar event by event ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event_id": {
                                "type": "string",
                                "description": "Google Calendar event ID"
                            }
                        },
                        "required": ["event_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> Any:
            """Handle tool calls"""
            try:
                if name == "parse_meeting_date_time":
                    return self._parse_meeting_date_time(arguments.get("text", ""))
                elif name == "create_calendar_event":
                    return self._create_calendar_event(arguments)
                elif name == "get_calendar_events":
                    return self._get_calendar_events(
                        arguments.get("start_date"),
                        arguments.get("end_date")
                    )
                elif name == "cancel_calendar_event":
                    return self._cancel_calendar_event(arguments.get("event_id", ""))
                else:
                    return {"error": f"Unknown tool: {name}"}
            except Exception as e:
                logger.error(f"Error calling tool {name}: {str(e)}")
                return {"error": str(e)}
    
    def _parse_meeting_date_time(self, text: str) -> dict:
        """Parse natural language text to extract date and time"""
        try:
            # Common meeting patterns
            patterns = [
                # "schedule meeting on February 15 at 2 PM"
                r'(?:schedule|set|book|meeting|at|on)\s+([a-zA-Z]+\s+\d{1,2})\s+(?:at|@)\s+(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?',
                # "tomorrow at 3:30 PM"
                r'(tomorrow|today|next\s+\w+)\s+(?:at|@)\s+(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?',
                # "Feb 15, 2025 2 PM"
                r'([a-zA-Z]+\s+\d{1,2},?\s*\d{4}?)\s+(?:at|@)?\s*(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?',
            ]
            
            # Try to parse with dateutil first (most flexible)
            try:
                parsed = date_parser.parse(text, fuzzy=True)
                return {
                    "success": True,
                    "date": parsed.date().isoformat(),
                    "time": parsed.time().isoformat(),
                    "datetime": parsed.isoformat(),
                    "raw_text": text
                }
            except:
                pass
            
            # Fall back to regex patterns
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    try:
                        # Try to construct datetime from matched groups
                        date_str = groups[0]
                        hour = int(groups[1])
                        minute = int(groups[2]) if groups[2] else 0
                        period = groups[3].lower() if groups[3] else ''
                        
                        if period in ['pm'] and hour != 12:
                            hour += 12
                        elif period in ['am'] and hour == 12:
                            hour = 0
                        
                        parsed = date_parser.parse(date_str)
                        parsed = parsed.replace(hour=hour, minute=minute)
                        
                        return {
                            "success": True,
                            "date": parsed.date().isoformat(),
                            "time": f"{hour:02d}:{minute:02d}:00",
                            "datetime": parsed.isoformat(),
                            "raw_text": text
                        }
                    except:
                        continue
            
            return {
                "success": False,
                "error": "Could not parse date and time from text",
                "raw_text": text
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_text": text
            }
    
    def _create_calendar_event(self, args: dict) -> dict:
        """Create a calendar event"""
        if not self.service:
            return {"error": "Google Calendar service not initialized"}
        
        try:
            event = {
                'summary': args.get('title', 'Meeting'),
                'description': args.get('description', ''),
                'start': {
                    'dateTime': args.get('start_datetime'),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': args.get('end_datetime'),
                    'timeZone': 'UTC',
                },
            }
            
            # Add attendees if provided
            if args.get('attendees'):
                event['attendees'] = [
                    {'email': email} for email in args.get('attendees', [])
                ]
            
            # Create event
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Event created: {event.get('id')}")
            return {
                "success": True,
                "event_id": event.get('id'),
                "event_link": event.get('htmlLink'),
                "title": event.get('summary')
            }
        
        except HttpError as e:
            return {"error": f"Google Calendar API error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_calendar_events(self, start_date: str, end_date: str) -> dict:
        """Get calendar events for a date range"""
        if not self.service:
            return {"error": "Google Calendar service not initialized"}
        
        try:
            # Convert dates to RFC3339 format
            start_dt = datetime.fromisoformat(start_date).isoformat() + 'Z'
            end_dt = datetime.fromisoformat(end_date).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_dt,
                timeMax=end_dt,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return {
                "success": True,
                "events": events,
                "count": len(events)
            }
        
        except HttpError as e:
            return {"error": f"Google Calendar API error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _cancel_calendar_event(self, event_id: str) -> dict:
        """Cancel/delete a calendar event"""
        if not self.service:
            return {"error": "Google Calendar service not initialized"}
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            return {
                "success": True,
                "message": f"Event {event_id} deleted successfully"
            }
        
        except HttpError as e:
            return {"error": f"Google Calendar API error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Google Calendar MCP Server...")
        async with await self.server.listeninig():
            logger.info("Google Calendar MCP Server running...")
            await self.server.wait_for_shutdown()


def main():
    """Entry point"""
    server = GoogleCalendarMCPServer()
    import asyncio
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
