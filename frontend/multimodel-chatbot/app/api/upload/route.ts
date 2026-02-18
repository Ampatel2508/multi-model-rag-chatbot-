/**
 * Upload API endpoint - handles file uploads to backend
 */

export const maxDuration = 60;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(req: Request) {
  try {
    console.log("[Upload API] Received request");
    const formData = await req.formData();
    const file = formData.get("file") as File;

    if (!file) {
      console.warn("[Upload API] No file provided");
      return new Response(
        JSON.stringify({ error: "No file provided" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    console.log(`[Upload API] Uploading file: ${file.name}`);

    // Forward to backend
    const backendFormData = new FormData();
    backendFormData.append("file", file);

    const backendResponse = await fetch(`${API_URL}/api/upload`, {
      method: "POST",
      body: backendFormData,
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json();
      console.error("[Upload API] Backend error:", errorData);
      return new Response(
        JSON.stringify({
          error: errorData.detail || `Upload failed: ${backendResponse.statusText}`,
        }),
        { status: backendResponse.status, headers: { "Content-Type": "application/json" } }
      );
    }

    const data = await backendResponse.json();
    console.log("[Upload API] Success:", data);

    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Upload API] Error:", error);
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