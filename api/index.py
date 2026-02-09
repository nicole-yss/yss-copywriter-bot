"""
Vercel serverless entry point for the FastAPI backend.

Vercel's Python Runtime picks up this file and serves the FastAPI app.
"""

from backend.main import app
