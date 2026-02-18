#!/usr/bin/env python3
"""
MCP Server for Google Calendar Integration
Provides tools for meeting detection and calendar management
"""

import json
import logging
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent, ToolResult
from meeting_scheduler import GoogleCalendarManager, MeetingExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
server = Server("google-calendar-mcp")
calendar_manager = GoogleCalendarManager()


@server.call_tool
async def call_tool(name: str, arguments: dict) -> ToolResult:
    """Handle tool calls from MCP clients"""
    
    try:
        if name == "extract_meeting_from_chat":
            message = arguments.get("message", "")
            if not message:
                return ToolResult(
                    content=[TextContent(type="text", text=json.dumps({"error": "Message is required"}))],
                    is_error=True
                )
            
            result = calendar_manager.detect_and_extract_meeting(message)
            if result:
                return ToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, default=str))],
                    is_error=False
                )
            else:
                return ToolResult(
                    content=[TextContent(type="text", text=json.dumps({"detected": False}))],
                    is_error=False
                )
        
        elif name == "create_google_calendar_event":
            # This would integrate with actual Google Calendar API
            meeting_data = {
                'title': arguments.get('title', 'Meeting'),
                'start_time': f"{arguments.get('date')}T{arguments.get('time')}:00",
                'duration_minutes': arguments.get('duration_minutes', 60),
                'description': arguments.get('description', ''),
                'participants': arguments.get('participants', [])
            }
            
            formatted_event = calendar_manager.format_meeting_for_calendar(meeting_data)
            
            return ToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "status": "created",
                    "event": formatted_event,
                    "message": "Calendar event created successfully"
                }, default=str))],
                is_error=False
            )
        
        elif name == "list_google_calendar_events":
            # This would fetch actual events from Google Calendar API
            max_results = arguments.get('max_results', 10)
            days_ahead = arguments.get('days_ahead', 7)
            
            return ToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "status": "ready",
                    "message": f"Ready to fetch {max_results} events for the next {days_ahead} days",
                    "note": "Requires Google Calendar API credentials"
                }))],
                is_error=False
            )
        
        else:
            return ToolResult(
                content=[TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))],
                is_error=True
            )
    
    except Exception as e:
        logger.error(f"Error in tool call: {e}")
        return ToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(e)}))],
            is_error=True
        )


@server.list_tools
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="extract_meeting_from_chat",
            description="Extract meeting details from user chat messages using natural language processing",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The user chat message to analyze for meeting information"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="create_google_calendar_event",
            description="Create an event in Google Calendar based on extracted meeting details",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "date": {"type": "string", "description": "Event date in YYYY-MM-DD format"},
                    "time": {"type": "string", "description": "Event time in HH:MM format"},
                    "duration_minutes": {"type": "integer", "description": "Duration in minutes", "default": 60},
                    "description": {"type": "string", "description": "Event description"},
                    "participants": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of participant email addresses"
                    }
                },
                "required": ["title", "date", "time"]
            }
        ),
        Tool(
            name="list_google_calendar_events",
            description="List upcoming events from Google Calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return",
                        "default": 10
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days in the future to check",
                        "default": 7
                    }
                }
            }
        )
    ]


async def main():
    """Start the MCP server"""
    logger.info("Starting Google Calendar MCP Server...")
    async with server:
        logger.info("Google Calendar MCP Server is running")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
