export const maxDuration = 60;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET() {
  try {
    const backendResponse = await fetch(`${API_URL}/api/documents`);
    if (!backendResponse.ok) {
      const err = await backendResponse.text();
      return new Response(JSON.stringify({ error: err }), { status: backendResponse.status, headers: { "Content-Type": "application/json" } });
    }

    const data = await backendResponse.json();
    return new Response(JSON.stringify(data), { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : String(e) }), { status: 500, headers: { "Content-Type": "application/json" } });
  }
}


// The DELETE function will be created separately.

export async function OPTIONS() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}
