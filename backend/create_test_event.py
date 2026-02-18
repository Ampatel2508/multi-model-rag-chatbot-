#!/usr/bin/env python3
"""Create a test event to delete"""

from app.google_calendar_service import get_calendar_service
from datetime import datetime, timedelta

service = get_calendar_service()

# Create a test event for today at 2 PM
now = datetime.now()
start_time = now.replace(hour=14, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(minutes=30)

event = {
    'summary': 'Test Meeting - Delete Me',
    'description': 'This is a test event created for deletion testing',
    'start': {
        'dateTime': start_time.isoformat(),
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': end_time.isoformat(),
        'timeZone': 'Asia/Kolkata',
    },
}

try:
    created_event = service.service.events().insert(calendarId='primary', body=event).execute()
    print(f'✓ Test event created!')
    print(f'ID: {created_event["id"]}')
    print(f'Title: {created_event["summary"]}')
    print(f'Start: {created_event["start"]["dateTime"]}')
except Exception as e:
    print(f'✗ Error: {str(e)}')
