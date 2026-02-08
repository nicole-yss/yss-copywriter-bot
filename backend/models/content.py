"""Pydantic models for content endpoints."""

from pydantic import BaseModel


class RateContentRequest(BaseModel):
    rating: int
    feedback: str | None = None


class GeneratedContentResponse(BaseModel):
    id: str
    content_type: str | None = None
    platform: str | None = None
    title: str | None = None
    body: str
    hashtags: list[str] | None = None
    cta: str | None = None
    hook: str | None = None
    rating: int | None = None
    is_favorite: bool = False
    created_at: str | None = None
