/**
 * Calendar Event Delete Endpoint
 * Handles deletion of specific calendar events by ID
 * Route: DELETE /api/calendar/events/[eventId]
 */

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ eventId: string }> }
) {
  try {
    // Await params in Next.js 15+
    const { eventId } = await params;

    console.log("[Calendar Delete] Received DELETE request for event:", eventId);

    if (!eventId) {
      console.error("[Calendar Delete] No event ID provided");
      return new Response(
        JSON.stringify({
          error: "No event ID provided",
          success: false,
        }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    // Build backend URL with the event_id in the path
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const backendPath = `/api/calendar/events/${encodeURIComponent(eventId)}`;

    const fullUrl = `${backendUrl}${backendPath}`;
    console.log("[Calendar Delete] Calling backend at:", fullUrl);

    const backendResponse = await fetch(fullUrl, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    console.log("[Calendar Delete] Backend response status:", backendResponse.status);

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error("[Calendar Delete] Backend error:", errorText);
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
    console.log("[Calendar Delete] Success, deleted event:", eventId);

    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Calendar Delete] Error:", error);
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
