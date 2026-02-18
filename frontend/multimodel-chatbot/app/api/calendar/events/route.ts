/**
 * Calendar Events Endpoint Proxy
 * Bridges frontend calendar event requests to the Python FastAPI backend
 */

export async function GET(req: Request) {
  try {
    // Parse query parameters from URL
    const url = new URL(req.url);
    const startDate = url.searchParams.get('start_date');
    const endDate = url.searchParams.get('end_date');
    const maxResults = url.searchParams.get('max_results') || '50';

    console.log("[Calendar Events Proxy] Received GET request");
    console.log("[Calendar Events Proxy] Params:", { startDate, endDate, maxResults });

    // Build backend URL with query parameters
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const backendPath = "/api/calendar/events";
    
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    params.append('max_results', maxResults);

    const fullUrl = `${backendUrl}${backendPath}?${params.toString()}`;
    console.log("[Calendar Events Proxy] Calling backend at:", fullUrl);

    const backendResponse = await fetch(fullUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    console.log("[Calendar Events Proxy] Backend response status:", backendResponse.status);

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error("[Calendar Events Proxy] Backend error:", errorText);
      return new Response(
        JSON.stringify({ 
          error: `Backend error: ${backendResponse.status}`,
          details: errorText,
          success: false,
          events: [],
          count: 0
        }),
        { status: backendResponse.status, headers: { "Content-Type": "application/json" } }
      );
    }

    const data = await backendResponse.json();
    console.log("[Calendar Events Proxy] Success, returned", data.count || 0, "events");

    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Calendar Events Proxy] Error:", error);
    return new Response(
      JSON.stringify({ 
        error: "Failed to fetch calendar events",
        details: String(error),
        success: false,
        events: [],
        count: 0
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}

// DELETE for collection is handled by dynamic route in [eventId]/route.ts
// This handler supports deletion by title and date (for chat interface)
export async function DELETE(request: Request) {
  try {
    const url = new URL(request.url);
    const title = url.searchParams.get('title');
    const date = url.searchParams.get('date');

    console.log("[Calendar Events Proxy] Received DELETE request");
    console.log("[Calendar Events Proxy] Params:", { title, date });

    if (!title || !date) {
      console.error("[Calendar Events Proxy] Missing title or date");
      return new Response(
        JSON.stringify({
          error: "Missing title or date parameter",
          success: false,
        }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    // Build backend URL with query parameters
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const backendPath = "/api/calendar/events";
    
    const params = new URLSearchParams();
    params.append('title', title);
    params.append('date', date);

    const fullUrl = `${backendUrl}${backendPath}?${params.toString()}`;
    console.log("[Calendar Events Proxy] Calling backend at:", fullUrl);

    const backendResponse = await fetch(fullUrl, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    console.log("[Calendar Events Proxy] Backend response status:", backendResponse.status);

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error("[Calendar Events Proxy] Backend error:", errorText);
      return new Response(
        JSON.stringify({
          error: `Backend error: ${backendResponse.status}`,
          details: errorText,
          success: false,
        }),
        {
          status: backendResponse.status,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    const data = await backendResponse.json();
    console.log("[Calendar Events Proxy] Success, deleted event");

    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Calendar Events Proxy] Error:", error);
    return new Response(
      JSON.stringify({
        error: "Failed to delete calendar event",
        details: String(error),
        success: false,
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
// This handler is for future bulk delete operations if needed
