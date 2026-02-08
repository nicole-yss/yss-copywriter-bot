"""Content CRUD and browsing endpoints."""

from fastapi import APIRouter, Request
from tools.utils.supabase_client import get_supabase_client

router = APIRouter()

PLATFORM_MAP = {"instagram": 1, "tiktok": 2, "youtube": 3}
CONTENT_TYPE_MAP = {"caption": 1, "carousel": 2, "edm": 3, "reel_script": 4}


@router.get("/generated")
async def list_generated_content(
    content_type: str | None = None,
    platform: str | None = None,
    favorites_only: bool = False,
    limit: int = 20,
    offset: int = 0,
):
    """List previously generated content with optional filters."""
    supabase = get_supabase_client()
    query = supabase.table("generated_content").select("*")

    if content_type and content_type in CONTENT_TYPE_MAP:
        query = query.eq("content_type_id", CONTENT_TYPE_MAP[content_type])
    if platform and platform in PLATFORM_MAP:
        query = query.eq("platform_id", PLATFORM_MAP[platform])
    if favorites_only:
        query = query.eq("is_favorite", True)

    response = (
        query.order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return response.data


@router.post("/generated/{content_id}/rate")
async def rate_content(content_id: str, request: Request):
    """Rate generated content (1-5) and optionally provide feedback."""
    body = await request.json()
    supabase = get_supabase_client()

    update = {"rating": body.get("rating")}
    if body.get("feedback"):
        update["feedback"] = body["feedback"]

    response = (
        supabase.table("generated_content")
        .update(update)
        .eq("id", content_id)
        .execute()
    )
    return response.data[0] if response.data else {"error": "Not found"}


@router.post("/generated/{content_id}/favorite")
async def toggle_favorite(content_id: str):
    """Toggle favorite status on generated content."""
    supabase = get_supabase_client()

    # Fetch current state
    current = (
        supabase.table("generated_content")
        .select("is_favorite")
        .eq("id", content_id)
        .execute()
    )

    if not current.data:
        return {"error": "Not found"}

    new_state = not current.data[0]["is_favorite"]
    response = (
        supabase.table("generated_content")
        .update({"is_favorite": new_state})
        .eq("id", content_id)
        .execute()
    )
    return response.data[0]


@router.get("/viral")
async def list_viral_content(
    platform: str | None = None,
    min_virality: float = 0.0,
    limit: int = 20,
    offset: int = 0,
):
    """Browse the scraped viral content corpus."""
    supabase = get_supabase_client()
    query = (
        supabase.table("scraped_content")
        .select("id, platform_id, source_url, source_handle, content_text, content_type, likes_count, comments_count, shares_count, views_count, virality_score, hashtags, posted_at")
    )

    if platform and platform in PLATFORM_MAP:
        query = query.eq("platform_id", PLATFORM_MAP[platform])
    if min_virality > 0:
        query = query.gte("virality_score", min_virality)

    response = (
        query.order("virality_score", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return response.data
