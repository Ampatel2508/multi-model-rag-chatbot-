/**
 * Calendar Schedule Meeting Endpoint Proxy
 * Bridges frontend calendar requests to the Python FastAPI backend
 */

export async function POST(req: Request) {
  try {
    console.log("[Calendar Proxy] Received request");
    const body = await req.json();
    console.log("[Calendar Proxy] Body:", body);

    const { message, session_id, user_id, title } = body;

    if (!message) {
      console.warn("[Calendar Proxy] Missing message field");
      return new Response(
        JSON.stringify({ error: "Missing message field" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    // Call backend
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    console.log("[Calendar Proxy] Calling backend at:", backendUrl + "/api/calendar/schedule-meeting");

    const backendRequest = {
      message,
      session_id,
      user_id,
      title
    };

    const backendResponse = await fetch(backendUrl + "/api/calendar/schedule-meeting", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(backendRequest),
    });

    console.log("[Calendar Proxy] Backend response status:", backendResponse.status);

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error("[Calendar Proxy] Backend error:", errorText);
      return new Response(
        JSON.stringify({ 
          error: `Backend error: ${backendResponse.status}`,
          details: errorText
        }),
        { status: backendResponse.status, headers: { "Content-Type": "application/json" } }
      );
    }

    const data = await backendResponse.json();
    console.log("[Calendar Proxy] Success:", data);

    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Calendar Proxy] Error:", error);
    return new Response(
      JSON.stringify({ error: "Failed to schedule meeting", details: String(error) }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
