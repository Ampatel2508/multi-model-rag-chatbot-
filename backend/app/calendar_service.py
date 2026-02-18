"""
Calendar Service Module
Handles meeting scheduling and calendar operations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class CalendarService:
    
    def __init__(self, mcp_client=None):

        self.mcp_client = mcp_client
    
    async def schedule_meeting_from_chat(self, message: str, title: Optional[str] = None) -> Dict[str, Any]:

        try:
            # Parse date and time from message
            datetime_info = await self._parse_meeting_datetime(message)
            
            if not datetime_info.get("success"):
                return {
                    "success": False,
                    "error": "Could not extract date and time from message",
                    "message": message
                }
            
            # Extract meeting title from message if not provided
            if not title:
                title = self._extract_meeting_title(message)
            
            # Create event
            start_time = datetime_info.get("datetime")
            # Default 1 hour meeting duration
            start_dt = datetime.fromisoformat(start_time)
            end_dt = start_dt + timedelta(hours=1)
            
            event_result = await self._create_calendar_event(
                summary=title,
                start_time=start_dt.isoformat(),
                end_time=end_dt.isoformat(),
                description=message
            )
            
            return {
                "success": event_result.get("success", True),
                "event_id": event_result.get("event_id"),
                "title": title,
                "start_time": datetime_info.get("datetime"),
                "date": datetime_info.get("date"),
                "time": datetime_info.get("time"),
                "link": event_result.get("link")
            }
        
        except Exception as e:
            logger.error(f"Error scheduling meeting: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _parse_meeting_datetime(self, text: str) -> Dict[str, Any]:
        try:
            if not self.mcp_client:
                # Fallback to local parsing
                return self._local_parse_datetime(text)
            
            result = await self.mcp_client.call_tool(
                "parse_datetime",
                {"text": text}
            )
            
            return json.loads(result.text) if hasattr(result, 'text') else result
        except Exception as e:
            logger.warning(f"MCP parsing failed, using local fallback: {e}")
            return self._local_parse_datetime(text)
    
    def _local_parse_datetime(self, text: str) -> Dict[str, Any]:
        """Fallback local datetime parsing"""
        try:
            parsed = date_parser.parse(text, fuzzy=True)
            return {
                "success": True,
                "datetime": parsed.isoformat(),
                "date": parsed.date().isoformat(),
                "time": parsed.time().isoformat(),
                "formatted": parsed.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_calendar_event(self, **kwargs) -> Dict[str, Any]:
        """Create calendar event via MCP server"""
        try:
            if not self.mcp_client:
                return {"success": True, "message": "Mock event created (MCP client not available)"}
            
            result = await self.mcp_client.call_tool(
                "create_event",
                kwargs
            )
            
            return json.loads(result.text) if hasattr(result, 'text') else result
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_calendar_events(self, start_date: str, end_date: str, max_results: int = 10) -> Dict[str, Any]:

        try:
            if not self.mcp_client:
                return {
                    "success": True,
                    "events": [],
                    "count": 0,
                    "message": "MCP client not available"
                }
            
            result = await self.mcp_client.call_tool(
                "list_events",
                {
                    "start_date": start_date,
                    "end_date": end_date,
                    "max_results": max_results
                }
            )
            
            return json.loads(result.text) if hasattr(result, 'text') else result
        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}")
            return {
                "success": False,
                "error": str(e),
                "events": []
            }
    
    async def cancel_meeting(self, event_id: str) -> Dict[str, Any]:
        """Cancel a scheduled meeting"""
        try:
            if not self.mcp_client:
                return {"success": True, "message": "Mock event deleted"}
            
            result = await self.mcp_client.call_tool(
                "delete_event",
                {"event_id": event_id}
            )
            
            return json.loads(result.text) if hasattr(result, 'text') else result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_meeting_title(self, message: str) -> str:
        """Extract meeting title from message"""
        import re
        
        msg = message.lower()
        
        # Try to extract meaningful content between common phrases
        # Pattern: "schedule/book/set [a] meeting [with X] [on DATE] [at TIME]"
        # We want to extract X or the remaining text
        
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
    
    async def get_events_for_date(self, date: str) -> Dict[str, Any]:
        """Get all events for a specific date"""
        try:
            # Get events for the entire day
            start_date = date
            end_date = date
            
            result = await self.get_calendar_events(start_date, end_date, max_results=50)
            
            if result.get("success"):
                # Group by date
                events_by_date = {}
                for event in result.get("events", []):
                    event_date = event.get("start", "").split("T")[0]
                    if event_date not in events_by_date:
                        events_by_date[event_date] = []
                    events_by_date[event_date].append(event)
                
                return {
                    "success": True,
                    "events": events_by_date.get(date, []),
                    "date": date
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_events(self, start_date: str, end_date: str, max_results: int = 10) -> Dict[str, Any]:
        """Alias for get_calendar_events - compatibility wrapper"""
        return await self.get_calendar_events(start_date, end_date, max_results)
    
    async def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Alias for cancel_meeting - compatibility wrapper"""
        return await self.cancel_meeting(event_id)
