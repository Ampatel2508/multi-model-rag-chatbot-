export const maxDuration = 60;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ id: string }> | { id: string } }
) {
  try {
    // Handle both old and new Next.js param signatures
    const resolvedParams = params instanceof Promise ? await params : params;
    const id = resolvedParams?.id || "";
    
    if (!id) {
      return new Response(JSON.stringify({ error: 'Document id required' }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const backendResponse = await fetch(`${API_URL}/api/documents/${id}`, {
      method: "DELETE",
    });

    if (!backendResponse.ok) {
      const err = await backendResponse.json().catch(() => ({}));
      return new Response(
        JSON.stringify({ error: err.detail || "Delete failed" }),
        {
          status: backendResponse.status,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    const data = await backendResponse.json();
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(
      JSON.stringify({
        error: e instanceof Error ? e.message : String(e),
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
      "Access-Control-Allow-Methods": "DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}
