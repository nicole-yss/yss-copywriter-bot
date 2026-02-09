"""
Chat router with streaming support.

POST /stream accepts messages + optional file attachments (images, PDFs, text).
Research is performed via Perplexity API before generation.
Files are sent to Claude as multimodal content blocks (vision, documents).
"""

import base64
import os
import sys
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from backend.services.rag_service import RAGService
from backend.services.research_service import research_topic
from backend.prompts.system_prompt import build_system_prompt
from tools.utils.supabase_client import get_supabase_client
from tools.generate_embeddings import generate_embedding

router = APIRouter()

# Maps file MIME types to Claude content block types
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
PDF_TYPES = {"application/pdf"}
TEXT_TYPES = {"text/plain", "text/markdown", "text/csv"}


def build_content_blocks(text: str, files: list[dict]) -> list[dict] | str:
    """
    Build Claude content blocks from user text + attached files.

    If no files, returns plain string (simpler API call).
    If files present, returns content array with file blocks + text.
    """
    if not files:
        return text

    blocks: list[dict] = []

    for file in files:
        file_type = file.get("type", "")
        file_data = file.get("data", "")
        file_name = file.get("name", "unknown")

        if file_type in IMAGE_TYPES:
            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": file_type,
                    "data": file_data,
                },
            })
        elif file_type in PDF_TYPES:
            blocks.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": file_data,
                },
            })
        elif file_type in TEXT_TYPES or file_name.endswith((".txt", ".md", ".csv")):
            # Decode base64 text content and include inline
            try:
                decoded_text = base64.b64decode(file_data).decode("utf-8")
                blocks.append({
                    "type": "text",
                    "text": f"--- Attached file: {file_name} ---\n{decoded_text}\n--- End of {file_name} ---",
                })
            except Exception:
                blocks.append({
                    "type": "text",
                    "text": f"[Could not read file: {file_name}]",
                })

    # Add the user's text message last
    if text:
        blocks.append({"type": "text", "text": text})
    elif not blocks:
        blocks.append({"type": "text", "text": "Please analyze the attached files."})

    return blocks


FEEDBACK_POSITIVE = {
    "love it", "perfect", "great", "yes", "good", "nice", "amazing",
    "exactly", "that works", "nailed it", "keep it", "on brand",
    "this is it", "spot on", "brilliant", "awesome",
}
FEEDBACK_NEGATIVE = {
    "too formal", "too casual", "too long", "too short", "shorter",
    "longer", "change", "don't like", "more", "less", "not right",
    "off brand", "try again", "rework", "redo", "tweak", "rewrite",
    "not quite", "tone down", "tone up", "too much", "not enough",
}


def _is_feedback_message(text: str) -> tuple[bool, str]:
    """Check if a user message is feedback on previous output. Returns (is_feedback, rating)."""
    lower = text.lower().strip()
    # Short messages after an assistant response are likely feedback
    if len(lower.split()) > 40:
        return False, ""
    for phrase in FEEDBACK_POSITIVE:
        if phrase in lower:
            return True, "positive"
    for phrase in FEEDBACK_NEGATIVE:
        if phrase in lower:
            return True, "negative"
    return False, ""


def _save_conversational_feedback(messages: list[dict], content_type: str, platform: str):
    """Detect and save conversational feedback from chat history."""
    if len(messages) < 2:
        return
    # Check if the latest user message is feedback on a prior assistant message
    latest = messages[-1]
    if latest.get("role") != "user":
        return
    # Find the most recent assistant message
    assistant_msg = None
    user_msg_before = None
    for m in reversed(messages[:-1]):
        if m["role"] == "assistant" and assistant_msg is None:
            assistant_msg = m["content"]
        elif m["role"] == "user" and assistant_msg is not None:
            user_msg_before = m["content"]
            break

    if not assistant_msg:
        return

    is_feedback, rating = _is_feedback_message(latest["content"])
    if not is_feedback:
        return

    try:
        embedding = generate_embedding(assistant_msg[:2000])
    except Exception:
        embedding = None

    try:
        supabase = get_supabase_client()
        supabase.table("content_feedback").insert({
            "content_type": content_type,
            "platform": platform,
            "user_message": user_msg_before or "",
            "assistant_message": assistant_msg[:5000],
            "rating": rating,
            "feedback_note": latest["content"],
            "embedding": embedding,
        }).execute()
        print(f"Saved conversational feedback: {rating} - {latest['content'][:50]}")
    except Exception as e:
        print(f"Failed to save conversational feedback: {e}")


@router.post("/stream")
async def chat_stream(request: Request):
    """
    Stream chat completions with optional file attachments.

    Flow: Research (Perplexity) → RAG context → System prompt → Claude stream

    Expects JSON body with:
        messages: [{ role, content }]
        contentType: "caption" | "carousel" | "edm" | "reel_script"
        platform: "instagram" | "tiktok" | "youtube"
        files: [{ name, type, data (base64) }] (optional)
        sessionId: optional UUID
    """
    body = await request.json()
    messages = body.get("messages", [])
    content_type = body.get("contentType", "caption")
    platform = body.get("platform", "instagram")
    files = body.get("files", [])
    session_id = body.get("sessionId")

    if not messages:
        return StreamingResponse(
            iter(["Please send a message to get started."]),
            media_type="text/plain; charset=utf-8",
        )

    latest_user_message = messages[-1]["content"]

    # Auto-create session if none provided
    if not session_id:
        try:
            supabase = get_supabase_client()
            title = latest_user_message[:80] + ("..." if len(latest_user_message) > 80 else "")
            platform_map = {"instagram": 1, "tiktok": 2, "youtube": 3}
            content_type_map = {"caption": 1, "carousel": 2, "edm": 3, "reel_script": 4}
            result = supabase.table("chat_sessions").insert({
                "title": title,
                "content_type_id": content_type_map.get(content_type),
                "platform_id": platform_map.get(platform),
            }).execute()
            session_id = result.data[0]["id"]
        except Exception as e:
            print(f"Auto-create session failed: {e}")

    # Detect conversational feedback and save for future RAG
    _save_conversational_feedback(messages, content_type, platform)

    # Step 1: Research the topic via Perplexity (runs before streaming)
    research = research_topic(
        user_message=latest_user_message,
        content_type=content_type,
        platform=platform,
    )
    if research["success"]:
        print(f"Research complete: {len(research['findings'])} chars, {len(research['citations'])} citations")

    # Step 2: Build RAG context (viral examples + brand voice + feedback)
    rag_service = RAGService()
    rag_context = rag_service.get_rag_context(
        user_query=latest_user_message,
        content_type=content_type,
        platform=platform,
    )

    # Step 3: Build system prompt with all context
    system_prompt = build_system_prompt(rag_context, content_type, platform, research)

    # Step 4: Prepare messages for Claude
    claude_messages = []
    for i, m in enumerate(messages):
        if m["role"] not in ("user", "assistant"):
            continue

        # Only the latest user message gets file attachments
        is_latest_user = (i == len(messages) - 1) and m["role"] == "user"

        if is_latest_user and files:
            content = build_content_blocks(m["content"], files)
        else:
            content = m["content"]

        claude_messages.append({"role": m["role"], "content": content})

    # Step 5: Stream response (async for Vercel ASGI compatibility)
    async def generate():
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            yield "[Error: ANTHROPIC_API_KEY not set]"
            return

        client = anthropic.AsyncAnthropic(api_key=api_key)
        full_response = []

        try:
            async with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=claude_messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_response.append(text)
                    yield text
        except Exception as e:
            print(f"Streaming error: {type(e).__name__}: {e}")
            yield f"\n\n[Error: {type(e).__name__}: {str(e)}]"
            return

        # Save messages to database (best-effort)
        if session_id:
            try:
                supabase = get_supabase_client()
                supabase.table("chat_messages").insert({
                    "session_id": session_id,
                    "role": "user",
                    "content": latest_user_message,
                }).execute()
                supabase.table("chat_messages").insert({
                    "session_id": session_id,
                    "role": "assistant",
                    "content": "".join(full_response),
                    "model_used": "claude-sonnet-4-20250514",
                    "rag_context_used": bool(rag_context.get("viral_examples")),
                }).execute()
            except Exception as e:
                print(f"Error saving chat messages: {e}")

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": session_id or "",
        },
    )


@router.post("/feedback")
async def submit_feedback(request: Request):
    """
    Store user feedback on generated content for RAG improvement.

    Expects JSON body with:
        contentType: str
        platform: str
        userMessage: str (what the user asked)
        assistantMessage: str (what was generated)
        rating: "positive" | "negative"
        feedbackNote: str (optional)
    """
    body = await request.json()
    content_type = body.get("contentType", "caption")
    platform = body.get("platform", "instagram")
    user_message = body.get("userMessage", "")
    assistant_message = body.get("assistantMessage", "")
    rating = body.get("rating")
    feedback_note = body.get("feedbackNote")

    if rating not in ("positive", "negative"):
        return {"error": "Rating must be 'positive' or 'negative'"}
    if not assistant_message:
        return {"error": "assistantMessage is required"}

    # Generate embedding of the assistant's output for future similarity search
    try:
        embedding = generate_embedding(assistant_message[:2000])
    except Exception as e:
        print(f"Embedding generation failed for feedback: {e}")
        embedding = None

    supabase = get_supabase_client()
    record = {
        "content_type": content_type,
        "platform": platform,
        "user_message": user_message[:2000],
        "assistant_message": assistant_message[:5000],
        "rating": rating,
        "feedback_note": feedback_note,
        "embedding": embedding,
    }

    try:
        response = supabase.table("content_feedback").insert(record).execute()
        return {"success": True, "id": response.data[0]["id"]}
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return {"error": str(e)}


@router.post("/sessions")
async def create_session(request: Request):
    """Create a new chat session."""
    body = await request.json()
    supabase = get_supabase_client()

    platform_map = {"instagram": 1, "tiktok": 2, "youtube": 3}
    content_type_map = {"caption": 1, "carousel": 2, "edm": 3, "reel_script": 4}

    session = {
        "title": body.get("title", f"Chat {datetime.now().strftime('%b %d, %H:%M')}"),
        "content_type_id": content_type_map.get(body.get("content_type")),
        "platform_id": platform_map.get(body.get("platform")),
    }

    response = supabase.table("chat_sessions").insert(session).execute()
    return response.data[0]


@router.get("/sessions")
async def list_sessions():
    """List all chat sessions, most recent first."""
    supabase = get_supabase_client()
    response = (
        supabase.table("chat_sessions")
        .select("*")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return response.data


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get all messages for a chat session."""
    supabase = get_supabase_client()
    response = (
        supabase.table("chat_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return response.data
