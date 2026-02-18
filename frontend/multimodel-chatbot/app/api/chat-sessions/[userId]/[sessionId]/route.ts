import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string; sessionId: string }> } | { params: { userId: string; sessionId: string } }
) {
  // Handle both old and new Next.js param signatures
  let userId: string;
  let sessionId: string;
  
  if (params instanceof Promise) {
    const resolvedParams = await params;
    userId = resolvedParams.userId;
    sessionId = resolvedParams.sessionId;
  } else {
    userId = params.userId;
    sessionId = params.sessionId;
  }

  if (!userId || !sessionId) {
    console.error('[API] userId or sessionId is required');
    return NextResponse.json(
      { error: 'userId and sessionId are required' },
      { status: 400 }
    );
  }
  
  console.log('[API] Fetching session details:', { userId, sessionId });

  try {
    const response = await fetch(
      `http://localhost:8000/api/chat-sessions/${userId}/${sessionId}`,
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
        { error: 'Failed to fetch session details', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[API] Session details fetched successfully');
    return NextResponse.json(data);
  } catch (error) {
    console.error('[API] Error fetching chat session details:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string; sessionId: string }> } | { params: { userId: string; sessionId: string } }
) {
  // Handle both old and new Next.js param signatures
  let userId: string;
  let sessionId: string;
  
  if (params instanceof Promise) {
    const resolvedParams = await params;
    userId = resolvedParams.userId;
    sessionId = resolvedParams.sessionId;
  } else {
    userId = params.userId;
    sessionId = params.sessionId;
  }

  if (!userId || !sessionId) {
    console.error('[API] userId or sessionId is required');
    return NextResponse.json(
      { error: 'userId and sessionId are required' },
      { status: 400 }
    );
  }
  
  console.log('[API] Saving message to session:', { userId, sessionId });

  try {
    const body = await request.json();
    
    const response = await fetch(
      `http://localhost:8000/api/chat-sessions/${userId}/${sessionId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      }
    );

    if (!response.ok) {
      console.error('[API] Backend returned error:', response.status);
      const errorText = await response.text();
      console.error('[API] Error response:', errorText);
      return NextResponse.json(
        { error: 'Failed to save message', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[API] Message saved successfully');
    return NextResponse.json(data);
  } catch (error) {
    console.error('[API] Error saving message to chat session:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string; sessionId: string }> } | { params: { userId: string; sessionId: string } }
) {
  // Handle both old and new Next.js param signatures
  let userId: string;
  let sessionId: string;
  
  if (params instanceof Promise) {
    const resolvedParams = await params;
    userId = resolvedParams.userId;
    sessionId = resolvedParams.sessionId;
  } else {
    userId = params.userId;
    sessionId = params.sessionId;
  }

  if (!userId || !sessionId) {
    console.error('[API] userId or sessionId is required');
    return NextResponse.json(
      { error: 'userId and sessionId are required' },
      { status: 400 }
    );
  }
  
  console.log('[API] Deleting session:', { userId, sessionId });

  try {
    const response = await fetch(
      `http://localhost:8000/api/chat-sessions/${userId}/${sessionId}`,
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

    const data = await response.json();
    console.log('[API] Session deleted successfully');
    return NextResponse.json(data);
  } catch (error) {
    console.error('[API] Error deleting chat session:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
