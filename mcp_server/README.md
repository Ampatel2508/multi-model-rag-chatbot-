# MCP Server for Google Calendar Integration

This folder contains the Model Context Protocol (MCP) server implementation for Google Calendar integration in the Multi-Model Chatbot.

## Structure

```
mcp_server/
├── server.py                  # MCP server entry point
├── meeting_scheduler.py       # Meeting detection and extraction logic
├── google_calendar_api.py     # Google Calendar API wrapper
├── __init__.py               # Package initialization
└── requirements.txt          # Python dependencies
```

## Components

### 1. **server.py** - MCP Server
The main MCP server that provides tools for:
- `extract_meeting_from_chat`: Analyzes user messages to detect meeting requests
- `create_google_calendar_event`: Creates calendar events based on extracted data
- `list_google_calendar_events`: Retrieves upcoming calendar events

### 2. **meeting_scheduler.py** - Meeting Detection
Implements natural language processing for:
- Extracting meeting time patterns (e.g., "3pm", "15:30", "at 3")
- Extracting date patterns (e.g., "today", "tomorrow", "next monday")
- Extracting duration information (e.g., "for 1 hour", "30 minutes")
- Identifying participants and attendees
- Generating meeting titles from context

### 3. **google_calendar_api.py** - Calendar Integration
Wrapper around Google Calendar API providing:
- Event creation with attendees and reminders
- Event listing with date range filtering
- Event updates and deletion
- Event retrieval

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Calendar Setup

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable the Google Calendar API

2. **Create Service Account**:
   - Go to "Service Accounts" in the Cloud Console
   - Create a new service account
   - Create a JSON key file
   - Download the key file

3. **Configure Environment Variables**:
   ```bash
   # In your .env file
   GOOGLE_CREDENTIALS_FILE=/path/to/google-credentials.json
   GOOGLE_CALENDAR_ID=primary
   ```

4. **Share Calendar with Service Account** (if using different calendar):
   - Copy the service account email from the JSON file
   - Share your Google Calendar with that email

### 3. Starting the MCP Server

```bash
python mcp_server/server.py
```

The server will start listening for tool calls from the backend.

## Integration with Backend

The backend's `main.py` integrates with this MCP server by:

1. Calling `extract_meeting_from_chat` to analyze user messages
2. If a meeting is detected, extracting:
   - Title
   - Date and time
   - Duration
   - Participants
3. Creating the calendar event via `create_google_calendar_event`
4. Returning confirmation to the user

### Backend Endpoint Usage

```python
# In main.py, the /api/backend-chat endpoint:

# 1. Extract meeting from user message
meeting_data = await call_mcp_tool("extract_meeting_from_chat", {
    "message": user_message
})

if meeting_data and meeting_data.get('detected'):
    # 2. Create calendar event
    calendar_event = await call_mcp_tool("create_google_calendar_event", {
        "title": meeting_data['title'],
        "date": meeting_data['date'],
        "time": meeting_data['time'],
        "duration_minutes": meeting_data['duration_minutes'],
        "description": meeting_data['description'],
        "participants": meeting_data.get('participants', [])
    })
    
    # 3. Include confirmation in AI response
```

## Usage Examples

### Example 1: Simple Meeting
**User Message**: "Schedule a meeting tomorrow at 3pm"

**Extracted**:
- Title: "Meeting"
- Date: 2024-01-16 (tomorrow)
- Time: 15:00
- Duration: 60 minutes

### Example 2: Detailed Meeting
**User Message**: "I need a call with john@example.com about project roadmap next Monday at 10am for 1.5 hours"

**Extracted**:
- Title: "Project Roadmap"
- Date: 2024-01-22
- Time: 10:00
- Duration: 90 minutes
- Participants: ["john@example.com"]

### Example 3: Team Standup
**User Message**: "Let's have a standup today at 9:30am with the team for 30 minutes"

**Extracted**:
- Title: "Standup"
- Date: 2024-01-15 (today)
- Time: 09:30
- Duration: 30 minutes

## Features

### Meeting Detection Keywords
The system recognizes these keywords to identify meeting requests:
- meeting, schedule, call, zoom, teams, conference
- chat, discussion, appointment, event, gather, reserve
- book, set up, arrange, plan, sync, standup, stand-up

### Time Formats Supported
- `3pm`, `3:00 PM`
- `15:30`, `3:30 PM`
- `at 3`, `at 3:30`

### Date Formats Supported
- `today`, `tomorrow`
- `next monday` (or any day)
- `12/25/2024`, `12-25-2024`
- `December 25`

### Duration Formats Supported
- `for 1 hour`, `for 30 minutes`
- `1 hour meeting`, `30 min call`

## Error Handling

The MCP server handles errors gracefully:
- Missing credentials → Returns warning and disables calendar features
- Invalid message format → Returns "No meeting detected"
- API errors → Logs error and returns error response

## Extending the Server

To add new tools:

1. Add the tool function to `server.py`
2. Register it in `@server.call_tool`
3. Add it to `@server.list_tools`
4. Update this documentation

Example:

```python
@server.call_tool
async def call_tool(name: str, arguments: dict) -> ToolResult:
    if name == "my_new_tool":
        result = do_something(arguments)
        return ToolResult(
            content=[TextContent(type="text", text=json.dumps(result))],
            is_error=False
        )
```

## Performance Notes

- **Meeting Detection**: ~50ms per message (regex-based, no API calls)
- **Calendar API**: ~500ms per operation (network dependent)
- **Caching**: Consider caching user's calendar settings for faster access

## Security Considerations

1. **Credentials**: Store Google credentials in environment variables, never in code
2. **Scope Limiting**: Service account uses minimal required scopes
3. **Rate Limiting**: Implement rate limiting on calendar operations
4. **Input Validation**: All user inputs are validated before processing

## Troubleshooting

### Meeting not detected
- Check that message contains meeting keywords
- Verify time/date format matches patterns above
- Review logs for extraction issues

### Calendar events not created
- Verify Google Calendar credentials are valid
- Ensure service account has calendar access
- Check network connectivity

### Wrong time detected
- Provide explicit AM/PM notation
- Use 24-hour format for clarity
- Specify timezone if different from UTC

## Future Enhancements

- [ ] Timezone support (currently UTC)
- [ ] Meeting location suggestions
- [ ] Calendar conflict detection
- [ ] Automatic attendee lookup
- [ ] Meeting reminder customization
- [ ] Recurring event support
- [ ] Multi-language support
