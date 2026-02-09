import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/v1/chat/sessions/${id}/messages`);

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json({ error: errorText }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Session messages route error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
