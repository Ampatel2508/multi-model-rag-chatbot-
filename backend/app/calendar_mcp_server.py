import dateparser
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Google Calendar MCP")


def _schedule_meeting_impl(
    title: str,
    datetime_text: str,
    duration_minutes: int = 30
) -> dict:

    try:
        import re
        
        print(f"[DEBUG] Raw input: {datetime_text}")
        print(f"[DEBUG] Title: {title}")
        print(f"[DEBUG] Default duration_minutes: {duration_minutes}")
        
        extracted_duration = None
        duration_search = datetime_text
        
        # Find all number-unit combinations
        number_unit_pairs = re.findall(r'(\d+)\s*(?:hour|hr|h|minute|min|m)', duration_search, re.IGNORECASE)
        unit_pairs = re.findall(r'\d+\s*(hour|hr|h|minute|min|m)', duration_search, re.IGNORECASE)
        
        if number_unit_pairs and unit_pairs:
            print(f"[DEBUG] Found duration components - numbers: {number_unit_pairs}, units: {unit_pairs}")
            
            total_minutes = 0
            for i, (num_str, unit) in enumerate(zip(number_unit_pairs, unit_pairs)):
                num = int(num_str)
                unit_lower = unit.lower()
                
                if unit_lower.startswith('h'):  # hour, hr, h
                    minutes_to_add = num * 60
                    total_minutes += minutes_to_add
                    print(f"[DEBUG]   Component {i+1}: {num} hour(s) = {minutes_to_add} minutes")
                else:  # minute, min, m
                    total_minutes += num
                    print(f"[DEBUG]   Component {i+1}: {num} minute(s) = {num} minutes")
            
            if total_minutes > 0:
                extracted_duration = total_minutes
                print(f"[DEBUG] Total extracted duration: {extracted_duration} minutes")
        
        # If duration was extracted, use it; otherwise use default (or 0 if no default specified)
        if extracted_duration is not None:
            duration_minutes = extracted_duration
            print(f"[DEBUG] Using extracted duration: {duration_minutes} minutes")
        else:
            print(f"[DEBUG] No duration specified in message, using default: {duration_minutes} minutes")

        end_time_pattern = r'(?:to|until|till|-)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM|a\.m\.|p\.m\.|noon|midnight))'
        end_time_match = re.search(end_time_pattern, datetime_text, re.IGNORECASE)
        
        extracted_end_time = None
        if end_time_match and extracted_duration is None:  # Only use end time if duration wasn't explicitly specified
            extracted_end_time = end_time_match.group(1)
            print(f"[DEBUG] Extracted end time: {extracted_end_time}")
        
        cleaned_text = datetime_text
        # Remove only specific keywords but preserve dates
        cleaned_text = re.sub(r'(can\s+we|let\'?s\s+)', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\b(also|and|then|a|an)\s+', '', cleaned_text, flags=re.IGNORECASE)  # Remove just the words, not patterns
        cleaned_text = cleaned_text.strip()

        # Normalize time expressions like '2.30pm' to '2:30pm' for better parsing
        # Replace patterns like 2.30pm, 14.05, 9.00 am, etc. with 2:30pm, 14:05, 9:00 am
        cleaned_text = re.sub(r'(\d{1,2})\.(\d{2})\s*([ap]\.?m\.?|AM|PM|a\.m\.|p\.m\.|noon|midnight)?', r'\1:\2 \3', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'(\d{1,2})\.(\d{2})', r'\1:\2', cleaned_text)  # For times without am/pm
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize whitespace

        print(f"[DEBUG] Cleaned and normalized text: {cleaned_text}")
        
        # Improved: Extract the most specific time (hour and minute) if present
        # Pattern to match date with time (hour and minute), support both ':' and '.' as time separators
        time_patterns = [
            # e.g., "10 February 2026 at 15:45", "Feb 10 at 15.45", "2026-02-10 15:45", "Feb 10 at 2.30pm"
            r'((?:\d{1,2}(?:st|nd|rd|th)?\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w]*\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w]*|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w]*\s+\d{1,2}(?:st|nd|rd|th)?)(?:\s+at|,)?\s+(\d{1,2}[:\.]\d{2}\s*(?:am|pm|AM|PM)?|\d{1,2}\s*(?:am|pm|AM|PM|noon|midnight))',
            # e.g., "tomorrow at 15:45", "today at 3.45 pm"
            r'(tomorrow|today|tonight)(?:\s+at)?\s+(\d{1,2}[:\.]\d{2}\s*(?:am|pm|AM|PM)?|\d{1,2}\s*(?:am|pm|AM|PM|noon|midnight))',
            # e.g., "next Monday at 14:00"
            r'(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))(?:\s+at)?\s+(\d{1,2}[:\.]\d{2}\s*(?:am|pm|AM|PM)?|\d{1,2}\s*(?:am|pm|AM|PM|noon|midnight))',
            # e.g., "this Friday at 09:30"
            r'(this\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))(?:\s+at)?\s+(\d{1,2}[:\.]\d{2}\s*(?:am|pm|AM|PM)?|\d{1,2}\s*(?:am|pm|AM|PM|noon|midnight))',
        ]

        extracted_time = None
        for i, pattern in enumerate(time_patterns):
            match = re.search(pattern, cleaned_text, re.IGNORECASE)
            if match:
                # Extract only the date+time portion, ignore trailing words (like 'for 30 minutes')
                # Use the span of the match to slice the cleaned_text
                extracted_time = cleaned_text[match.start():match.end()].strip()
                print(f"[DEBUG] Matched pattern {i+1}: {pattern}")
                print(f"[DEBUG] Extracted time: {extracted_time}")
                break

        # If no match, try to find just the day and add default time
        if not extracted_time:
            day_only_patterns = [
                r'(tomorrow|today|tonight)',
                r'(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))',
                r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w]*)',
                r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w]*\s+\d{1,2}(?:st|nd|rd|th)?)',
            ]
            for pattern in day_only_patterns:
                match = re.search(pattern, cleaned_text, re.IGNORECASE)
                if match:
                    extracted_time = match.group(1).lower() + " at 2:00 PM"
                    print(f"[DEBUG] Day only match, using default time: {extracted_time}")
                    break

        # If still nothing found, try the cleaned text as-is
        if not extracted_time:
            extracted_time = cleaned_text if cleaned_text else datetime_text
            print(f"[DEBUG] No patterns matched, using entire text: {extracted_time}")
            print(f"[DEBUG] No patterns matched, using cleaned text: {extracted_time}")

        print(f"[DEBUG] Final extracted_time to parse: {extracted_time}")
        
        # Parse natural language date/time
        start_time = dateparser.parse(
            extracted_time,
            settings={
                "TIMEZONE": "Asia/Kolkata",
                "RETURN_AS_TIMEZONE_AWARE": True,
                "PREFER_DATES_FROM": "future"
            }
        )
        
        print(f"[DEBUG] Parsed start_time: {start_time}")
        if start_time:
            print(f"[DEBUG] Parsed datetime details: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")
        
        if not start_time:
            print(f"[ERROR] Failed to parse: {extracted_time}")
            return {
                "success": False,
                "message": f"❌ Could not understand the date & time. Please use formats like 'tomorrow at 2pm', 'next Monday 10:00 AM', or '16 feb at 12pm'. You said: '{datetime_text}'",
                "event_data": None
            }
        
        # PARSE END TIME IF EXTRACTED
        end_time_parsed = None
        if extracted_end_time and extracted_duration is None:  # Only calculate from end time if duration wasn't explicit
            try:
                # Parse end time - use same date as start_time if not specified
                end_time_str = extracted_end_time
                
                # If end time doesn't have a date, use start date
                if not any(re.search(pattern, end_time_str, re.IGNORECASE) for pattern in [
                    r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
                    r'\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
                    r'(?:tomorrow|today|tonight|next\s+\w+|this\s+\w+)'
                ]):
                    # Combine start date with end time
                    start_date_str = start_time.strftime('%B %d, %Y')
                    end_time_str = f"{start_date_str} {end_time_str}"
                    print(f"[DEBUG] Constructed end time string: {end_time_str}")
                
                end_time_parsed = dateparser.parse(
                    end_time_str,
                    settings={
                        "TIMEZONE": "Asia/Kolkata",
                        "RETURN_AS_TIMEZONE_AWARE": True,
                        "PREFER_DATES_FROM": "future"
                    }
                )
                
                if end_time_parsed:
                    print(f"[DEBUG] Parsed end_time: {end_time_parsed}")
                    print(f"[DEBUG] End datetime details: {end_time_parsed.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")
                    
                    # Calculate duration from start and end times
                    from datetime import datetime, timedelta
                    time_diff = end_time_parsed - start_time
                    calculated_duration = int(time_diff.total_seconds() / 60)
                    
                    if calculated_duration > 0:
                        duration_minutes = calculated_duration
                        print(f"[DEBUG] Calculated duration from end time: {duration_minutes} minutes")
                    else:
                        print(f"[DEBUG] End time is before or same as start time, keeping duration as 0")
                else:
                    print(f"[DEBUG] Could not parse end time: {end_time_str}")
            except Exception as e:
                print(f"[DEBUG] Error parsing end time: {e}")
        
        # Import here to avoid blocking on module load
        from app.google_calendar_service import get_calendar_service
        
        # Get calendar service and create meeting
        calendar_service = get_calendar_service()
        print(f"[DEBUG] Creating meeting: {title}")
        print(f"[DEBUG] Start time: {start_time}")
        print(f"[DEBUG] Parsed datetime: {start_time.strftime('%Y-%m-%d %H:%M %Z')} (TZ: {start_time.tzinfo})")
        
        event_data = calendar_service.create_meeting(
            title=title,
            start_time=start_time,
            duration_minutes=duration_minutes
        )
        
        if not event_data:
            print(f"[ERROR] Failed to create meeting - event_data is None")
            return {
                "success": False,
                "message": f"❌ Failed to create meeting '{title}'. Please check your Google Calendar connection.",
                "event_data": None
            }
        
        # Build success message with duration info
        duration_text = f"\n⏱️ Duration: {duration_minutes} minutes" if duration_minutes > 0 else ""
        
        print(f"[SUCCESS] Meeting created: {event_data}")
        return {
            "success": True,
            "message": f"✅ Perfect! I've scheduled a meeting for you:\n\n📅 **{title}**\n🕐 **{start_time.strftime('%B %d, %Y at %I:%M %p %Z')}**{duration_text}\n\nThe event has been added to your calendar. You can view it in your calendar app!",
            "event_data": event_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error scheduling meeting: {str(e)}",
            "event_data": None
        }


@mcp.tool()
def schedule_meeting(
    title: str,
    datetime_text: str,
    duration_minutes: int = 30
) -> str:

    result = _schedule_meeting_impl(title, datetime_text, duration_minutes)
    return result.get("message", "")


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
