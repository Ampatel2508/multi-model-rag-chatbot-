"""
Google Calendar Service - Core meeting creation logic
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarService:
    """Handle Google Calendar event creation"""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar"""
        try:
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            credentials_path = os.path.join(backend_dir, 'credentials.json')
            token_path = os.path.join(backend_dir, 'token.json')
            
            print(f"[DEBUG] Backend dir: {backend_dir}")
            print(f"[DEBUG] Credentials path: {credentials_path}")
            print(f"[DEBUG] Token path: {token_path}")
            
            if os.path.exists(token_path):
                print(f"[DEBUG] Token file exists, loading credentials")
                self.credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            if not self.credentials or not self.credentials.valid:
                print(f"[DEBUG] Credentials not valid or don't exist")
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    print(f"[DEBUG] Refreshing expired credentials")
                    self.credentials.refresh(GoogleRequest())
                else:
                    if not os.path.exists(credentials_path):
                        logger.error(f"credentials.json not found at {credentials_path}")
                        print(f"[ERROR] credentials.json not found at {credentials_path}")
                        return
                    
                    print(f"[DEBUG] Running auth flow")
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                
                with open(token_path, 'w') as token:
                    token.write(self.credentials.to_json())
                print(f"[DEBUG] Token saved to {token_path}")
            
            self.service = build('calendar', 'v3', credentials=self.credentials)
            logger.info("✅ Google Calendar authenticated")
            print("[SUCCESS] Google Calendar authenticated")
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            print(f"[ERROR] Authentication failed: {e}")
            import traceback
            traceback.print_exc()
    
    def create_meeting(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int = 60,
        description: str = ""
    ) -> Optional[dict]:

        try:
            if not self.service:
                logger.error("Calendar service not initialized")
                print("[ERROR] Calendar service not initialized")
                return None
            
            import pytz
            kolkata_tz = pytz.timezone('Asia/Kolkata')
            
            # If start_time is timezone-aware, convert to Asia/Kolkata
            if start_time.tzinfo is not None:
                start_time = start_time.astimezone(kolkata_tz)
            else:
                # If naive, assume it's already in Asia/Kolkata
                start_time = kolkata_tz.localize(start_time)
            
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Get the date and time components for logging
            print(f"[DEBUG] Timezone-converted start_time: {start_time}")
            print(f"[DEBUG] Date: {start_time.strftime('%Y-%m-%d')}, Time: {start_time.strftime('%H:%M:%S')}")
            print(f"[DEBUG] Duration minutes: {duration_minutes}")
            
            # Create ISO string WITH timezone offset
            # This tells Google Calendar: "This time is already in this timezone"
            # We MUST include the +05:30 offset so Google doesn't misinterpret it as UTC
            start_iso_clean = start_time.isoformat()
            
            print(f"[DEBUG] ISO strings with timezone offset:")
            print(f"[DEBUG] start_iso_clean: {start_iso_clean}")
            
            # Build event object
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_iso_clean,
                    'timeZone': 'Asia/Kolkata',
                },
            }
            
            # Only add end time if duration is specified (not point-in-time)
            if duration_minutes > 0:
                end_iso_clean = end_time.isoformat()
                print(f"[DEBUG] end_iso_clean: {end_iso_clean}")
                event['end'] = {
                    'dateTime': end_iso_clean,
                    'timeZone': 'Asia/Kolkata',
                }
            else:
                # For point-in-time events, set end = start
                event['end'] = {
                    'dateTime': start_iso_clean,
                    'timeZone': 'Asia/Kolkata',
                }
                print(f"[DEBUG] Point-in-time event: no duration specified")
            
            print(f"[DEBUG] Event to send to Google Calendar:")
            print(f"  Title: {event['summary']}")
            print(f"  Start: {event['start']}")
            print(f"  End: {event['end']}")
            print(f"[DEBUG] Sending event to Google Calendar: {event}")
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            print(f"[DEBUG] Response from Google Calendar:")
            print(f"  ID: {created_event.get('id')}")
            print(f"  Summary: {created_event.get('summary')}")
            print(f"  Start: {created_event.get('start')}")
            print(f"  End: {created_event.get('end')}")
            
            link = created_event.get('htmlLink')
            logger.info(f"✅ Meeting created: {title} - {link}")
            print(f"[SUCCESS] Event created in Google Calendar: {link}")
            
            # Return event data for frontend display
            return {
                'id': created_event.get('id'),
                'summary': created_event.get('summary'),
                'start': created_event.get('start'),  # Return full start object with dateTime and timeZone
                'end': created_event.get('end'),      # Return full end object with dateTime and timeZone
                'htmlLink': link
            }
        except Exception as e:
            logger.error(f"❌ Failed to create meeting: {e}")
            print(f"[ERROR] Exception creating meeting: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


# Global instance
_calendar_service = None

def get_calendar_service() -> GoogleCalendarService:
    """Get or create calendar service instance"""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = GoogleCalendarService()
    return _calendar_service
