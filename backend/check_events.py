#!/usr/bin/env python3
"""Check what events currently exist in Google Calendar"""

from app.google_calendar_service import get_calendar_service
from datetime import datetime, timedelta

service = get_calendar_service()

# Get all events
print("Fetching all events from Google Calendar...\n")
events = service.service.events().list(
    calendarId='primary',
    maxResults=50,
    singleEvents=True,
    orderBy='startTime'
).execute().get('items', [])

print(f"Total events: {len(events)}\n")

# Group by status
active = []
cancelled = []

for event in events:
    event_id = event.get('id')
    summary = event.get('summary', 'N/A')
    status = event.get('status', 'confirmed')
    event_type = event.get('eventType', 'default')
    
    if status == 'cancelled':
        cancelled.append({'id': event_id, 'summary': summary, 'type': event_type})
    else:
        active.append({'id': event_id, 'summary': summary, 'type': event_type})

print(f"ACTIVE EVENTS ({len(active)}):")
for evt in active:
    print(f"  ID: {evt['id']}")
    print(f"  Title: {evt['summary']}")
    print(f"  Type: {evt['type']}")
    print()

if cancelled:
    print(f"\nCANCELLED EVENTS ({len(cancelled)}):")
    for evt in cancelled:
        print(f"  ID: {evt['id']}")
        print(f"  Title: {evt['summary']}")
        print(f"  Type: {evt['type']}")
        print()
