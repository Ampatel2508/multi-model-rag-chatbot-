"""
Calendar API routes
Endpoints for meeting scheduling and calendar operations using FastMCP
"""

from fastapi import APIRouter, HTTPException, status, Request
import logging
from app.calendar_mcp_server import _schedule_meeting_impl
import hashlib
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

# Track recently scheduled meetings to prevent duplicates
recent_meetings_cache = {}
CACHE_TIMEOUT = 10  # seconds - prevent duplicate scheduling within 10 seconds


def _extract_title_from_message(message: str) -> str:
    """Extract a title from calendar request message"""
    message_lower = message.lower()
    
    patterns = [
        ("schedule ", "with "),
        ("meeting with ", None),
        ("meet ", None),
        ("call with ", None),
        ("book ", "for"),
    ]
    
    for start_pattern, end_pattern in patterns:
        if start_pattern in message_lower:
            start_idx = message_lower.index(start_pattern) + len(start_pattern)
            
            if end_pattern:
                if end_pattern in message_lower[start_idx:]:
                    end_idx = message_lower.index(end_pattern, start_idx)
                    return message[start_idx:end_idx].strip()
            else:
                words = message[start_idx:].split()[:3]
                return " ".join(words).strip()
    
    words = message.split()[:3]
    return " ".join(words) if words else "Meeting"


@router.post("/schedule-meeting")
async def schedule_meeting_endpoint(request: Request):
    """
    Schedule a meeting using FastMCP Calendar Tool
    
    Request body:
    {
        "message": "Schedule a meeting tomorrow at 2 PM to discuss project",
        "title": "Project Discussion" (optional)
    }
    """
    try:
        body = await request.json()
        message = body.get("message", "")
        title = body.get("title")
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required"
            )
        
        # Create a cache key from message and title to prevent duplicate requests
        cache_key = hashlib.md5(f"{message}_{title}".encode()).hexdigest()
        current_time = time.time()
        
        # Check if this exact request was already processed recently
        if cache_key in recent_meetings_cache:
            last_request_time = recent_meetings_cache[cache_key]
            if current_time - last_request_time < CACHE_TIMEOUT:
                logger.warning(f"[Calendar] Duplicate meeting request detected, ignoring: {message}")
                return recent_meetings_cache.get(f"{cache_key}_result", {
                    "success": False,
                    "message": "This meeting was just scheduled. Please wait before scheduling another.",
                    "meeting_data": None,
                    "title": title
                })
        
        # Extract title if not provided
        if not title:
            title = _extract_title_from_message(message)
        
        logger.info(f"[Calendar] Scheduling meeting: {title} - {message}")
        
        # Use FastMCP schedule_meeting implementation
        # Pass duration_minutes=0 to allow the function to extract duration from message
        # If no duration is found in message, it will use 0 (point-in-time event)
        result = _schedule_meeting_impl(
            title=title,
            datetime_text=message,
            duration_minutes=0
        )
        
        logger.info(f"[Calendar] Result: {result}")
        
        response = {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "meeting_data": result.get("event_data"),
            "title": title
        }
        
        # Cache this request for duplicate prevention
        recent_meetings_cache[cache_key] = current_time
        recent_meetings_cache[f"{cache_key}_result"] = response
        
        # Clean up old cache entries periodically
        cutoff_time = current_time - CACHE_TIMEOUT
        keys_to_delete = [k for k, v in recent_meetings_cache.items() if isinstance(v, float) and v < cutoff_time]
        for k in keys_to_delete:
            del recent_meetings_cache[k]
            if f"{k}_result" in recent_meetings_cache:
                del recent_meetings_cache[f"{k}_result"]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling meeting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule meeting: {str(e)}"
        )


@router.get("/events")
async def get_calendar_events(
    start_date: str = None,
    end_date: str = None,
    max_results: int = 50
):
    """
    Get calendar events
    
    Query parameters:
    - start_date: Optional start date (ISO format: YYYY-MM-DD)
    - end_date: Optional end date (ISO format: YYYY-MM-DD)
    - max_results: Maximum number of events to return (default: 10)
    """
    try:
        # Import here to avoid blocking on module load
        from app.google_calendar_service import get_calendar_service
        calendar_service = get_calendar_service()
        
        if not calendar_service.service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Calendar service not available"
            )
        
        # Build query parameters
        query_params = {
            'calendarId': 'primary',
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        # Add date filters if provided
        if start_date:
            query_params['timeMin'] = f"{start_date}T00:00:00Z"
        if end_date:
            query_params['timeMax'] = f"{end_date}T23:59:59Z"
        
        # Get events
        events_result = calendar_service.service.events().list(**query_params).execute()
        
        events = events_result.get('items', [])
        logger.info(f"[Calendar] Fetched {len(events)} events from Google Calendar")
        
        # Format events for frontend - ensure start/end are strings
        formatted_events = []
        for event in events:
            # Skip cancelled events
            if event.get('status') == 'cancelled':
                logger.debug(f"[Calendar] Skipping cancelled event: {event.get('summary')}")
                continue
            
            # Process start time
            start = event.get('start', {})
            if isinstance(start, dict):
                start_str = start.get('dateTime', start.get('date', ''))
            else:
                start_str = str(start)
            
            # Convert UTC datetime to Asia/Kolkata timezone for display
            if start_str and 'T' in start_str:
                try:
                    from datetime import datetime
                    import pytz
                    
                    # Parse the UTC datetime (e.g., 2026-02-27T08:30:00Z)
                    if start_str.endswith('Z'):
                        utc_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    elif '+' in start_str or start_str.count('-') > 2:  # Has timezone
                        utc_dt = datetime.fromisoformat(start_str)
                    else:
                        utc_dt = datetime.fromisoformat(start_str)
                    
                    # Convert to Asia/Kolkata timezone
                    kolkata_tz = pytz.timezone('Asia/Kolkata')
                    if utc_dt.tzinfo is None:
                        # Assume UTC if no timezone
                        utc_dt = pytz.UTC.localize(utc_dt)
                    kolkata_dt = utc_dt.astimezone(kolkata_tz)
                    
                    # Format as ISO string with timezone offset
                    start_str = kolkata_dt.isoformat()
                    logger.debug(f"[Calendar] Converted start time from UTC to Asia/Kolkata: {start_str}")
                except Exception as e:
                    logger.debug(f"[Calendar] Could not convert timezone for {start_str}: {e}")
            
            # Process end time
            end = event.get('end', {})
            if isinstance(end, dict):
                end_str = end.get('dateTime', end.get('date', ''))
            else:
                end_str = str(end)
            
            # Convert UTC datetime to Asia/Kolkata timezone for display
            if end_str and 'T' in end_str:
                try:
                    from datetime import datetime
                    import pytz
                    
                    # Parse the UTC datetime
                    if end_str.endswith('Z'):
                        utc_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                    elif '+' in end_str or end_str.count('-') > 2:  # Has timezone
                        utc_dt = datetime.fromisoformat(end_str)
                    else:
                        utc_dt = datetime.fromisoformat(end_str)
                    
                    # Convert to Asia/Kolkata timezone
                    kolkata_tz = pytz.timezone('Asia/Kolkata')
                    if utc_dt.tzinfo is None:
                        # Assume UTC if no timezone
                        utc_dt = pytz.UTC.localize(utc_dt)
                    kolkata_dt = utc_dt.astimezone(kolkata_tz)
                    
                    # Format as ISO string with timezone offset
                    end_str = kolkata_dt.isoformat()
                    logger.debug(f"[Calendar] Converted end time from UTC to Asia/Kolkata: {end_str}")
                except Exception as e:
                    logger.debug(f"[Calendar] Could not convert timezone for {end_str}: {e}")
            
            event_type = event.get('eventType', 'default')
            event_id = event.get('id')
            
            formatted_events.append({
                'id': event_id,
                'summary': event.get('summary', 'Event'),
                'start': start_str,
                'end': end_str,
                'htmlLink': event.get('htmlLink', ''),
                'eventType': event_type,
                'canDelete': event_type not in ['birthday', 'holiday', 'focusTime', 'outOfOffice', 'workingLocation']
            })
        
        logger.info(f"[Calendar] Returning {len(formatted_events)} events")
        
        return {
            "success": True,
            "events": formatted_events,
            "count": len(formatted_events),
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "max_results": max_results
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch events: {str(e)}"
        )


@router.delete("/events")
async def delete_calendar_event_by_query(
    title: str = None,
    date: str = None
):
    """Delete a calendar event by title and/or date"""
    try:
        from app.google_calendar_service import get_calendar_service
        from datetime import datetime, timedelta
        
        calendar_service = get_calendar_service()
        
        if not calendar_service.service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Calendar service not available"
            )
        
        # Build query to find events
        events_result = calendar_service.service.events().list(
            calendarId='primary',
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        deleted_count = 0
        
        # Filter events by title and/or date
        for event in events:
            event_title = event.get('summary', '').lower()
            search_title = (title or '').lower()
            
            title_match = not search_title or search_title in event_title or event_title == search_title
            
            date_match = True
            if date:
                try:
                    event_start = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
                    if event_start:
                        event_date = event_start.split('T')[0] if 'T' in event_start else event_start
                        date_match = date in event_date or event_date == date
                except:
                    date_match = False
            
            if title_match and date_match:
                try:
                    calendar_service.service.events().delete(
                        calendarId='primary',
                        eventId=event['id']
                    ).execute()
                    deleted_count += 1
                    logger.info(f"Deleted event: {event.get('summary')} - {event['id']}")
                except Exception as e:
                    logger.error(f"Failed to delete event {event['id']}: {e}")
        
        if deleted_count == 0:
            logger.warning(f"No events found matching criteria: title={title}, date={date}")
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} event(s)",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error deleting events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete events: {str(e)}"
        )



@router.delete("/events/{event_id}")
async def delete_calendar_event(event_id: str):
    """Delete a calendar event by event ID"""
    try:
        import urllib.parse
        # Decode the event_id in case it's URL encoded
        decoded_event_id = urllib.parse.unquote(event_id)
        
        logger.info(f"[Calendar] Attempting to delete event: {decoded_event_id}")
        
        # Import here to avoid blocking on module load
        from app.google_calendar_service import get_calendar_service
        calendar_service = get_calendar_service()
        
        if not calendar_service.service:
            logger.error("[Calendar] Calendar service not available")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Calendar service not available"
            )
        
        try:
            # First try to get the event to verify it exists and check its type
            event = None
            try:
                event = calendar_service.service.events().get(
                    calendarId='primary',
                    eventId=decoded_event_id
                ).execute()
                
                event_type = event.get('eventType', 'default')
                event_status = event.get('status', 'confirmed')
                event_summary = event.get('summary', 'Unknown')
                logger.info(f"[Calendar] Found event to delete: {event_summary} (type: {event_type}, status: {event_status}, id: {decoded_event_id})")
                
                # Check if event is already cancelled
                if event_status == 'cancelled':
                    logger.info(f"[Calendar] Event already cancelled, treating as deleted: {decoded_event_id}")
                    return {
                        "success": True,
                        "message": f"Event already deleted",
                        "event_id": decoded_event_id
                    }
                
                # Check if this is a special event type that cannot be deleted
                if event_type in ['birthday', 'holiday', 'focusTime', 'outOfOffice', 'workingLocation']:
                    logger.warning(f"[Calendar] Cannot delete {event_type} event: {decoded_event_id}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot delete {event_type} events. This event type is managed by Google Calendar and cannot be deleted."
                    )
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as get_error:
                error_msg = str(get_error)
                logger.warning(f"[Calendar] Error during event verification - {error_msg}")
                if "404" in error_msg or "Not Found" in error_msg:
                    logger.warning(f"[Calendar] Event not found during verification: {decoded_event_id}")
                    logger.warning(f"[Calendar] Full error message: {error_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Event not found or already deleted"
                    )
                # Otherwise try to delete anyway (might be a transient issue)
                logger.warning(f"[Calendar] Error verifying event, attempting deletion anyway: {error_msg}")
            
            # Try to delete the event
            logger.info(f"[Calendar] Deleting event: {decoded_event_id}")
            calendar_service.service.events().delete(
                calendarId='primary',
                eventId=decoded_event_id
            ).execute()
            
            logger.info(f"[Calendar] Successfully deleted event: {decoded_event_id}")
            
            return {
                "success": True,
                "message": f"Event deleted successfully",
                "event_id": decoded_event_id
            }
            
        except HTTPException:
            raise
        except Exception as inner_e:
            error_msg = str(inner_e)
            logger.error(f"[Calendar] Failed to delete event {decoded_event_id}: {error_msg}")
            
            # Check if it's a "not found" error (404) or "already deleted" (410)
            if "404" in error_msg or "Not Found" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Event not found"
                )
            elif "410" in error_msg or "has been deleted" in error_msg:
                logger.info(f"[Calendar] Event already deleted: {decoded_event_id}")
                return {
                    "success": True,
                    "message": f"Event already deleted",
                    "event_id": decoded_event_id
                }
            # Check for event type restriction error
            elif "eventTypeRestriction" in error_msg or "event type" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This event type cannot be deleted. Only regular calendar events can be deleted."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete event: {error_msg}"
                )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Calendar] Unexpected error deleting event {event_id}: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {error_msg}"
        )
