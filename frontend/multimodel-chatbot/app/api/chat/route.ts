/**
 * Chat API endpoint - handles chat requests and forwards to backend
 */

export const maxDuration = 60;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(req: Request) {
  try {
    console.log("[Chat API] Received request");
    const body = await req.json();
    
    // Accept both camelCase and snake_case field names
    const { 
      question, 
      apiKey, 
      api_key,
      provider, 
      model, 
      documentIds, 
      document_ids,
      url,
      user_id,
      session_id,
      conversation_history
    } = body;

    const finalApiKey = apiKey || api_key;
    const finalDocumentIds = documentIds || document_ids;
    const finalUserId = user_id;
    const finalSessionId = session_id;

    if (!finalApiKey || !provider || !model || !question) {
      console.warn("[Chat API] Missing required fields");
      return new Response(
        JSON.stringify({ error: "Missing required fields" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    console.log(`[Chat API] Forwarding to backend: ${API_URL}/api/chat`);

    const backendRequest = {
      question,
      provider,
      model,
      api_key: finalApiKey,
      document_ids: finalDocumentIds || [],
      url: url || null,
      session_id: finalSessionId,
      user_id: finalUserId,
      conversation_history: conversation_history || [],
    };

    const backendResponse = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(backendRequest),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json();
      console.error("[Chat API] Backend error:", errorData);
      return new Response(
        JSON.stringify({
          error: errorData.detail || `Backend error: ${backendResponse.statusText}`,
        }),
        { status: backendResponse.status, headers: { "Content-Type": "application/json" } }
      );
    }

    const data = await backendResponse.json();
    console.log("[Chat API] Success");

    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Chat API] Error:", error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Internal server error",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}

export async function OPTIONS() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}