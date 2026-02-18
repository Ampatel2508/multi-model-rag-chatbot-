#!/usr/bin/env python3
"""Check specific event by ID"""

from app.google_calendar_service import get_calendar_service

service = get_calendar_service()
event_id = 'g3g946ep3vr2qcu0jrm46hd59o'

print(f"Checking for event: {event_id}\n")

try:
    event = service.service.events().get(calendarId='primary', eventId=event_id).execute()
    print(f'Event found!')
    print(f'ID: {event.get("id")}')
    print(f'Summary: {event.get("summary")}')
    print(f'Status: {event.get("status")}')
    print(f'Type: {event.get("eventType")}')
except Exception as e:
    error_str = str(e)
    print(f'Error: {error_str}')
    
    # Check if it's a 404
    if '404' in error_str or 'not found' in error_str.lower():
        print('\nThis event does not exist in Google Calendar!')
