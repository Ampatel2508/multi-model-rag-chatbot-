import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string }> } | { params: { userId: string } }
) {
  // Handle both old and new Next.js param signatures
  let userId: string;
  
  if (params instanceof Promise) {
    const resolvedParams = await params;
    userId = resolvedParams.userId;
  } else {
    userId = params.userId;
  }

  if (!userId) {
    console.error('[API] userId is required');
    return NextResponse.json({ error: 'userId is required' }, { status: 400 });
  }
  
  console.log('[API] Fetching sessions for userId:', userId);

  try {
    const response = await fetch(
      `http://localhost:8000/api/chat-sessions/${userId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      console.error('[API] Backend returned error:', response.status);
      const errorText = await response.text();
      console.error('[API] Error response:', errorText);
      return NextResponse.json(
        { error: 'Failed to fetch sessions', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[API] Sessions fetched successfully:', data.count, 'sessions');
    return NextResponse.json(data);
  } catch (error) {
    console.error('[API] Error fetching chat sessions:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
