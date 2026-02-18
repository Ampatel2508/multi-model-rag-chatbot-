#!/usr/bin/env python3
"""Check event status after deletion"""

from app.google_calendar_service import get_calendar_service

service = get_calendar_service()
event_id = 'g3g946ep3vr2qcu0jrm46hd59o'

try:
    event = service.service.events().get(calendarId='primary', eventId=event_id).execute()
    print(f'Event Status: {event.get("status")}')
    print(f'Event Summary: {event.get("summary")}')
except Exception as e:
    print(f'Error: {str(e)}')
