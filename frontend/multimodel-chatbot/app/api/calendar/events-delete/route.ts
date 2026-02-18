import { NextRequest, NextResponse } from 'next/server';

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const title = searchParams.get('title');
    const date = searchParams.get('date');

    // Build query string for backend
    let queryString = '';
    if (title) queryString += `?title=${encodeURIComponent(title)}`;
    if (date) queryString += `${queryString ? '&' : '?'}date=${encodeURIComponent(date)}`;

    const backendUrl = `http://localhost:8000/api/calendar/events${queryString}`;
    console.log('[Calendar Delete] Proxying DELETE to:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[Calendar Delete] Error:', error);
    return NextResponse.json(
      { error: 'Failed to delete calendar event' },
      { status: 500 }
    );
  }
}
