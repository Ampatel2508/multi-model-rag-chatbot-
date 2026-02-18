import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser

def extract_datetime(text: str):
    """Extract date and time range from natural language text"""
    now = datetime.now()
    text_lower = text.lower()

    # Parse date
    if "tomorrow" in text_lower:
        date = (now + timedelta(days=1)).date()
    elif "today" in text_lower:
        date = now.date()
    elif "next week" in text_lower or "next monday" in text_lower or "next tuesday" in text_lower:
        # Handle relative dates
        try:
            date = date_parser.parse(text, fuzzy=True).date()
        except:
            date = (now + timedelta(days=7)).date()
    else:
        try:
            date = date_parser.parse(text, fuzzy=True).date()
        except:
            date = now.date()

    # Parse time range
    time_match = re.search(
        r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(to|-|–)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?',
        text_lower
    )

    if not time_match:
        raise ValueError("Time range not found in text. Use format like '3 to 4 pm' or '15:00-16:00'")
    
    sh, sm, sap, _, eh, em, eap = time_match.groups()

    sm = sm or '00'
    em = em or '00'
    sap = sap or 'am'
    eap = eap or sap  # Use same am/pm as start if not specified for end

    start = f"{sh}:{sm} {sap}"
    end = f"{eh}:{em} {eap}"

    try:
        start_dt = date_parser.parse(start)
        end_dt = date_parser.parse(end)
    except:
        raise ValueError(f"Could not parse time: {start} to {end}")

    return (
        date.strftime("%Y-%m-%d"),
        start_dt.strftime("%H:%M"),
        end_dt.strftime("%H:%M"),
    )

def extract_title(text: str):
    """Extract meeting title from text"""
    # Remove common phrases
    title = text.lower()
    patterns_to_remove = [
        r'schedule.*meeting',
        r'schedule.*appointment',
        r'tomorrow',
        r'today',
        r'next\s+\w+day',
        r'from\s+\d+',
        r'to\s+\d+',
        r'(am|pm)',
        r'-|–|to',
    ]
    
    for pattern in patterns_to_remove:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    title = re.sub(r'\s+', ' ', title).strip()
    return title[:100] if title else "Meeting"

def is_cancel_request(text: str) -> bool:
    """Check if the request is to cancel a meeting"""
    cancel_keywords = ['cancel', 'delete', 'remove', 'drop', 'rescind', 'abort', 'discard']
    return any(keyword in text.lower() for keyword in cancel_keywords)

def extract_cancel_details(text: str):
    """Extract meeting details from a cancel request"""
    # Try to extract title
    title_match = re.search(r"(?:cancel|delete)\s+(?:the\s+)?(?:meeting\s+)?(?:called\s+)?['\"]?([^'\"]+)", text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else None
    
    # Try to extract date
    date_text = None
    if "tomorrow" in text.lower():
        now = datetime.now()
        date_text = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        try:
            date_obj = date_parser.parse(text, fuzzy=True).date()
            date_text = date_obj.strftime("%Y-%m-%d")
        except:
            date_text = None
    
    return title, date_text