"""Pydantic models for scraping endpoints."""

from pydantic import BaseModel


class CreateScrapeJobRequest(BaseModel):
    platform: str  # 'instagram', 'tiktok', 'youtube'
    job_type: str = "viral_research"  # 'viral_research', 'brand_analysis', 'competitor'
    search_terms: list[str] | None = None
    target_handles: list[str] | None = None
    max_results: int = 100


class ScrapeJobResponse(BaseModel):
    id: str
    platform: str
    job_type: str
    status: str
    results_count: int = 0
    error_message: str | None = None
    created_at: str | None = None
