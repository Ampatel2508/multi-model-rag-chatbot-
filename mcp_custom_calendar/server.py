from fastmcp import FastMCP
from calendar_db import initialize_db, get_all_meetings
from calendar_service import (
    get_meetings,
    get_meetings_time_slots,
    has_conflict,
    available_slots,
    save_meeting,
    cancel_meeting,
    find_meeting_by_title_and_date
)
from nlp_parser import extract_datetime, extract_title, is_cancel_request, extract_cancel_details
import requests
import json
from datetime import datetime

initialize_db()

app = FastMCP(name="mcp_custom_calendar")

# Backend API base URL
BACKEND_URL = "http://localhost:8000"

@app.tool(
    name="schedule_meeting_custom",
    description=(
        "Schedule a meeting in the custom calendar using natural language. "
        "Examples: 'Schedule a meeting tomorrow from 3 to 4 for project discussion', "
        "'Schedule meeting on 2026-02-05 from 10am to 11am for team standup'"
    ),
)
def schedule_meeting_tool(user_request: str):
    """
    Schedule a meeting with date, time, and title extracted from user request.
    Checks for conflicts and provides available slots if needed.
    """
    try:
        date, start_time, end_time = extract_datetime(user_request)
        title = extract_title(user_request)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to parse request: {str(e)}",
            "details": str(e)
        }
    
    # Check for time conflicts
    if has_conflict(start_time, end_time, date):
        meetings = get_meetings_time_slots(date)
        available = available_slots(meetings)
        return {
            "status": "conflict",
            "message": "The requested time slot conflicts with an existing meeting.",
            "requested_time": {
                "date": date,
                "start_time": start_time,
                "end_time": end_time
            },
            "available_slots": available if available else "No available slots on this date"
        }
    
    try:
        meeting_id = save_meeting(date, start_time, end_time, title)
        return {
            "status": "success",
            "message": "Meeting scheduled successfully",
            "meeting": {
                "id": meeting_id,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "title": title
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save meeting: {str(e)}"
        }

@app.tool(
    name="cancel_meeting_custom",
    description=(
        "Cancel/delete a meeting from the custom calendar. "
        "You can cancel by meeting ID or by title and date. "
        "Examples: 'Cancel meeting 5', 'Cancel project discussion tomorrow'"
    ),
)
def cancel_meeting_tool(user_request: str):
    """
    Cancel a meeting from the calendar.
    Can cancel by meeting ID or by title and date.
    """
    import re
    
    # Try to extract meeting ID from request
    id_match = re.search(r'meeting\s+(\d+)|id\s+(\d+)|#(\d+)|(\d+)', user_request, re.IGNORECASE)
    if id_match:
        meeting_id = int(id_match.group(1) or id_match.group(2) or id_match.group(3) or id_match.group(4))
        try:
            cancel_meeting(meeting_id)
            return {
                "status": "success",
                "message": f"Meeting {meeting_id} has been cancelled successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to cancel meeting {meeting_id}: {str(e)}"
            }
    
    # Try to extract title and date from request
    try:
        title, date = extract_cancel_details(user_request)
        
        if not title or not date:
            return {
                "status": "error",
                "message": "Could not extract meeting details. Please provide meeting title or ID and date."
            }
        
        meetings = find_meeting_by_title_and_date(title, date)
        
        if not meetings:
            return {
                "status": "not_found",
                "message": f"No meeting found with title '{title}' on {date}"
            }
        
        if len(meetings) > 1:
            return {
                "status": "ambiguous",
                "message": f"Found {len(meetings)} meetings matching your criteria. Please be more specific or use meeting ID.",
                "meetings": [{
                    "id": m["id"],
                    "title": m["title"],
                    "date": m["date"],
                    "start_time": m["start_time"],
                    "end_time": m["end_time"]
                } for m in meetings]
            }
        
        meeting = meetings[0]
        cancel_meeting(meeting["id"])
        
        return {
            "status": "success",
            "message": f"Meeting '{meeting['title']}' scheduled for {meeting['date']} at {meeting['start_time']} has been cancelled successfully"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to process cancellation: {str(e)}"
        }

@app.tool(
    name="get_calendar_meetings",
    description=(
        "Retrieve all meetings for a specific date or all upcoming meetings. "
        "Examples: 'Show meetings for tomorrow', 'Get calendar for 2026-02-05', 'List all meetings'"
    ),
)
def get_calendar_meetings_tool(date_request: str = None):
    """
    Get all meetings for a specific date or all meetings if no date specified.
    """
    try:
        if not date_request or date_request.lower() in ['all', 'upcoming', 'everything']:
            # Return all meetings
            meetings = get_all_meetings()
            
            if not meetings:
                return {
                    "status": "success",
                    "message": "No meetings scheduled",
                    "meetings": []
                }
            
            return {
                "status": "success",
                "message": f"Found {len(meetings)} meetings",
                "meetings": [{
                    "id": m["id"],
                    "date": m["date"],
                    "title": m["title"],
                    "start_time": m["start_time"],
                    "end_time": m["end_time"]
                } for m in meetings]
            }
        
        # Parse specific date
        try:
            date, _, _ = extract_datetime(date_request)
        except:
            # Try direct date parsing
            from dateutil import parser as date_parser
            date = date_parser.parse(date_request, fuzzy=True).strftime("%Y-%m-%d")
        
        meetings = get_meetings(date)
        
        if not meetings:
            return {
                "status": "success",
                "message": f"No meetings scheduled for {date}",
                "date": date,
                "meetings": []
            }
        
        return {
            "status": "success",
            "message": f"Found {len(meetings)} meetings for {date}",
            "date": date,
            "meetings": [{
                "id": m["id"],
                "title": m["title"],
                "start_time": m["start_time"],
                "end_time": m["end_time"]
            } for m in meetings]
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve meetings: {str(e)}"
        }

# ============= Google Calendar Tools =============

@app.tool(
    name="schedule_meeting_google",
    description=(
        "Schedule a meeting on Google Calendar using natural language. "
        "This tool automatically creates events on the user's Google Calendar. "
        "Examples: 'Schedule a meeting tomorrow from 3 to 4 for project discussion', "
        "'Schedule meeting on Feb 4 from 2pm to 3pm for team standup'"
    ),
)
def schedule_meeting_google_tool(user_request: str):
    """
    Schedule a meeting on Google Calendar with date, time, and title extracted from user request.
    """
    try:
        # Extract date and time from user request
        date, start_time, end_time = extract_datetime(user_request)
        title = extract_title(user_request)
        
        # Format date to DD-Mon format if needed
        if len(date.split('-')) == 3:  # YYYY-MM-DD format
            parsed_date = datetime.strptime(date, "%Y-%m-%d")
            date = parsed_date.strftime("%d-%b")
        
        # Call backend API to schedule on Google Calendar
        payload = {
            "title": title or "Meeting",
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "description": user_request
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/schedule-google-meeting",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return {
                    "status": "success",
                    "message": "Meeting scheduled successfully on Google Calendar",
                    "meeting": {
                        "event_id": data.get("event_id"),
                        "title": data.get("event_title"),
                        "date": data.get("event_date"),
                        "start_time": data.get("start_time"),
                        "end_time": data.get("end_time")
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": data.get("message", "Failed to schedule meeting on Google Calendar")
                }
        else:
            return {
                "status": "error",
                "message": f"Backend error: {response.status_code}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to schedule meeting: {str(e)}",
            "details": str(e)
        }

@app.tool(
    name="cancel_meeting_google",
    description=(
        "Cancel/delete a meeting from Google Calendar using the event ID. "
        "Example: 'Cancel meeting event-abc123def456'"
    ),
)
def cancel_meeting_google_tool(event_id: str):
    """
    Cancel a meeting from Google Calendar using the event ID.
    """
    try:
        if not event_id or not event_id.strip():
            return {
                "status": "error",
                "message": "Event ID is required to cancel a meeting"
            }
        
        # Call backend API to cancel on Google Calendar
        payload = {
            "event_id": event_id.strip()
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/cancel-google-meeting",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return {
                    "status": "success",
                    "message": f"Meeting cancelled successfully from Google Calendar",
                    "event_title": data.get("event_title", "Meeting")
                }
            else:
                return {
                    "status": "error",
                    "message": data.get("message", "Failed to cancel meeting")
                }
        else:
            return {
                "status": "error",
                "message": f"Backend error: {response.status_code}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to cancel meeting: {str(e)}"
        }

if __name__ == "__main__":
    app.run()