"""
YSS Content Copywriter - FastAPI Application

Entry point for the backend server.
Run with: uvicorn backend.main:app --reload --port 8000
"""

import os
import sys

# Add project root to path so tools/ imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import chat, content, scraping, reports

app = FastAPI(
    title="YSS Content Copywriter API",
    description="AI-powered social media content generation for YourSalonSupport",
    version="1.0.0",
)

# CORS - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
app.include_router(scraping.router, prefix="/api/v1/scraping", tags=["Scraping"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "yss-content-copywriter"}


@app.get("/api/v1/platforms")
async def list_platforms():
    """List available platforms."""
    return [
        {"id": 1, "name": "instagram", "display_name": "Instagram"},
        {"id": 2, "name": "tiktok", "display_name": "TikTok"},
        {"id": 3, "name": "youtube", "display_name": "YouTube"},
    ]


@app.get("/api/v1/content-types")
async def list_content_types():
    """List available content types."""
    return [
        {"id": 1, "name": "caption", "display_name": "Caption"},
        {"id": 2, "name": "carousel", "display_name": "Carousel Post"},
        {"id": 3, "name": "edm", "display_name": "EDM Copy"},
        {"id": 4, "name": "reel_script", "display_name": "Reel Script"},
    ]
