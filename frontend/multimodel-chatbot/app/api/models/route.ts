/**
 * Models API endpoint - fetches available models from backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(req: Request) {
  try {
    console.log("[Models API] Received request");
    const body = await req.json();
    
    const { provider, apiKey } = body;

    if (!provider || !apiKey) {
      console.warn("[Models API] Missing required fields");
      return new Response(
        JSON.stringify({ error: "Missing provider or apiKey" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    console.log(`[Models API] Fetching models for ${provider}`);

    const backendResponse = await fetch(`${API_URL}/api/models`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        provider,
        api_key: apiKey,
      }),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json();
      console.error("[Models API] Backend error:", errorData);
      return new Response(
        JSON.stringify({
          error: errorData.detail || `Failed to fetch models`,
        }),
        { status: backendResponse.status, headers: { "Content-Type": "application/json" } }
      );
    }

    const data = await backendResponse.json();
    console.log(`[Models API] Success: ${data.models?.length || 0} models`);

    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Models API] Error:", error);
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