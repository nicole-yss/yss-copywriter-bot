"""Scraping job management endpoints."""

from fastapi import APIRouter, BackgroundTasks, Request
from tools.utils.supabase_client import get_supabase_client
from backend.services.scraping_service import create_scrape_job, run_scrape_job

router = APIRouter()


@router.post("/jobs")
async def start_scrape_job(request: Request, background_tasks: BackgroundTasks):
    """
    Start a new scraping job. Runs in background.

    Body:
        platform: "instagram" | "tiktok" | "youtube"
        job_type: "viral_research" | "brand_analysis" | "competitor"
        search_terms: ["hashtag1", "hashtag2"] (for viral/competitor)
        target_handles: ["handle"] (for brand_analysis/competitor)
        max_results: 100
    """
    body = await request.json()

    platform = body.get("platform", "instagram")
    job_type = body.get("job_type", "viral_research")
    search_terms = body.get("search_terms")
    target_handles = body.get("target_handles")
    max_results = body.get("max_results", 100)

    job_id = create_scrape_job(platform, job_type, search_terms, target_handles, max_results)

    background_tasks.add_task(
        run_scrape_job,
        job_id=job_id,
        platform=platform,
        job_type=job_type,
        search_terms=search_terms,
        target_handles=target_handles,
        max_results=max_results,
    )

    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs")
async def list_scrape_jobs(limit: int = 20):
    """List recent scraping jobs."""
    supabase = get_supabase_client()
    response = (
        supabase.table("scrape_jobs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data


@router.get("/jobs/{job_id}")
async def get_scrape_job_status(job_id: str):
    """Check status of a scraping job."""
    supabase = get_supabase_client()
    response = (
        supabase.table("scrape_jobs")
        .select("*")
        .eq("id", job_id)
        .execute()
    )
    if response.data:
        return response.data[0]
    return {"error": "Job not found"}


@router.post("/brand-analysis")
async def trigger_brand_analysis(background_tasks: BackgroundTasks):
    """Trigger brand voice analysis (runs in background)."""
    from tools.analyze_brand_voice import analyze_brand_voice

    background_tasks.add_task(analyze_brand_voice)
    return {"status": "started", "message": "Brand voice analysis running in background"}
