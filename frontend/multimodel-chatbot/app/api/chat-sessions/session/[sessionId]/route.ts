import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ sessionId: string }> } | { params: { sessionId: string } }
) {
  // Handle both old and new Next.js param signatures
  let sessionId: string;
  
  if (params instanceof Promise) {
    const resolvedParams = await params;
    sessionId = resolvedParams.sessionId;
  } else {
    sessionId = params.sessionId;
  }

  if (!sessionId) {
    console.error('[API] sessionId is required');
    return NextResponse.json(
      { error: 'sessionId is required' },
      { status: 400 }
    );
  }
  
  console.log('[API] Fetching session:', { sessionId });

  try {
    const response = await fetch(
      `${API_URL}/api/chat-sessions/${sessionId}`,
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
        { error: 'Failed to fetch session', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[API] Session fetched successfully');
    return NextResponse.json(data);
  } catch (error) {
    console.error('[API] Error fetching session:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ sessionId: string }> } | { params: { sessionId: string } }
) {
  // Handle both old and new Next.js param signatures
  let sessionId: string;
  
  if (params instanceof Promise) {
    const resolvedParams = await params;
    sessionId = resolvedParams.sessionId;
  } else {
    sessionId = params.sessionId;
  }

  if (!sessionId) {
    console.error('[API] sessionId is required');
    return NextResponse.json(
      { error: 'sessionId is required' },
      { status: 400 }
    );
  }
  
  console.log('[API] Deleting session:', { sessionId });

  try {
    const response = await fetch(
      `${API_URL}/api/chat-sessions/${sessionId}`,
      {
        method: 'DELETE',
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
        { error: 'Failed to delete session', details: errorText },
        { status: response.status }
      );
    }

    console.log('[API] Session deleted successfully');
    return NextResponse.json({ success: true, message: 'Session deleted' });
  } catch (error) {
    console.error('[API] Error deleting session:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
