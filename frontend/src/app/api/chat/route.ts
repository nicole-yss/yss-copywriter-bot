import { NextRequest, NextResponse } from 'next/server';

// Allow up to 60s for file processing + Claude streaming
export const maxDuration = 60;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { messages, contentType, platform, files, sessionId } = body;

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json({ error: 'Messages must be an array' }, { status: 400 });
    }

    // Messages are already in { role, content } format from chat-interface
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const url = `${backendUrl}/api/v1/chat/stream`;

    const backendBody: Record<string, unknown> = {
      messages,
      contentType: contentType || 'caption',
      platform: platform || 'instagram',
      sessionId: sessionId || undefined,
    };

    // Include files if present
    if (files && Array.isArray(files) && files.length > 0) {
      backendBody.files = files;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(backendBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', errorText);
      return new Response(errorText, {
        status: response.status,
        headers: { 'Content-Type': 'text/plain' },
      });
    }

    if (!response.body) {
      return NextResponse.json({ error: 'No response body' }, { status: 500 });
    }

    // Forward the session ID header from backend
    const sessionIdHeader = response.headers.get('X-Session-Id') || '';

    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'X-Session-Id': sessionIdHeader,
      },
    });
  } catch (error) {
    console.error('Route error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        message: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}
