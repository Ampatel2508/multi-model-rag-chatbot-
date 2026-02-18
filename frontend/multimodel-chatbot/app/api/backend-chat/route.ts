/**
 * Backend proxy endpoint
 * Bridges frontend chat requests to the Python FastAPI backend
 */

export const maxDuration = 60;

export async function POST(req: Request) {
  try {
    console.log("[Backend Proxy] Received request");
    const body = await req.json();
    console.log("[Backend Proxy] Body:", body);

    const {
      question,
      apiKey,
      api_key,
      provider,
      model,
      session_id,
      user_id,
      document_ids = [],
      url = null,
      save_to_db = true,
      conversation_history = [],
    } = body;

    // Support both apiKey and api_key field names
    const finalApiKey = apiKey || api_key;

    if (!finalApiKey || !provider || !model || !question) {
      console.warn("[Backend Proxy] Missing required fields");
      return new Response(
        JSON.stringify({ error: "Missing required fields" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    console.log("[Backend Proxy] Question:", question.substring(0, 100));

    // Call backend
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    console.log("[Backend Proxy] Calling backend at:", backendUrl);

    const backendRequest = {
      question,
      provider,
      model,
      api_key: finalApiKey,
      session_id,
      user_id,
      document_ids,
      url,
      save_to_db,
      conversation_history,
    };

    console.log("[Backend Proxy] Backend request:", backendRequest);

    const backendResponse = await fetch(`${backendUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(backendRequest),
    });

    console.log("[Backend Proxy] Backend response status:", backendResponse.status);

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error("[Backend Proxy] Backend error:", errorText);
      return new Response(
        JSON.stringify({
          error: `Backend error: ${backendResponse.statusText}`,
          details: errorText,
        }),
        { status: backendResponse.status, headers: { "Content-Type": "application/json" } }
      );
    }

    const backendData = await backendResponse.json();
    console.log("[Backend Proxy] Backend data:", backendData);

    // Return the backend response directly
    return new Response(JSON.stringify(backendData), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error("[Backend Proxy] Error:", error);
    return new Response(
      JSON.stringify({
        error: "Internal server error",
        message: error instanceof Error ? error.message : "Unknown error",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
