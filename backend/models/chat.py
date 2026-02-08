"""Pydantic models for chat endpoints."""

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    contentType: str = "caption"
    platform: str = "instagram"
    sessionId: str | None = None


class CreateSessionRequest(BaseModel):
    title: str | None = None
    content_type: str | None = None
    platform: str | None = None
