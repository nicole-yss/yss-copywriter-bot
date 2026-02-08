"""
Scraping service: Orchestrates scraping jobs.

Manages job lifecycle and delegates to WAT tools.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.utils.supabase_client import get_supabase_client

PLATFORM_MAP = {"instagram": 1, "tiktok": 2, "youtube": 3}


def create_scrape_job(platform: str, job_type: str, search_terms: list[str] | None,
                      target_handles: list[str] | None, max_results: int) -> str:
    """Create a scrape job record in the database."""
    supabase = get_supabase_client()

    job = {
        "platform_id": PLATFORM_MAP.get(platform),
        "job_type": job_type,
        "status": "pending",
        "search_terms": search_terms,
        "target_handles": target_handles,
        "max_results": max_results,
    }

    response = supabase.table("scrape_jobs").insert(job).execute()
    return response.data[0]["id"]


def run_scrape_job(job_id: str, platform: str, job_type: str,
                   search_terms: list[str] | None, target_handles: list[str] | None,
                   max_results: int):
    """Execute a scraping job (runs in background)."""
    supabase = get_supabase_client()

    # Mark as running
    supabase.table("scrape_jobs").update({
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
    }).eq("id", job_id).execute()

    try:
        results_count = 0

        if platform == "instagram":
            from tools.scrape_instagram import scrape_by_hashtags, scrape_profile, store_posts

            if job_type == "brand_analysis" and target_handles:
                items = scrape_profile(target_handles[0], max_results)
            elif search_terms:
                items = scrape_by_hashtags(search_terms, max_results)
            else:
                items = []

            results_count = store_posts(items, job_id)

        elif platform == "tiktok":
            from tools.scrape_tiktok import scrape_by_hashtags, scrape_profile, store_posts

            if target_handles:
                items = scrape_profile(target_handles[0], max_results)
            elif search_terms:
                items = scrape_by_hashtags(search_terms, max_results)
            else:
                items = []

            results_count = store_posts(items, job_id)

        elif platform == "youtube":
            from tools.scrape_youtube import scrape_by_search, scrape_channel, store_posts

            if target_handles:
                items = scrape_channel(target_handles[0], max_results)
            elif search_terms:
                items = scrape_by_search(search_terms, max_results)
            else:
                items = []

            results_count = store_posts(items, job_id)

        # Generate embeddings for new content
        from tools.generate_embeddings import backfill_unembedded_content
        backfill_unembedded_content()

        # Mark as completed
        supabase.table("scrape_jobs").update({
            "status": "completed",
            "results_count": results_count,
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", job_id).execute()

    except Exception as e:
        supabase.table("scrape_jobs").update({
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", job_id).execute()
        raise
