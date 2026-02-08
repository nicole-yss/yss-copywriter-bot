"""
TikTok scraping tool using Apify actors.

Usage:
    python tools/scrape_tiktok.py --mode viral --hashtags "salontok,salonowner,beautybusiness" --limit 100
    python tools/scrape_tiktok.py --mode profile --handle yoursalonsupport --limit 50

Outputs:
    Stores results in Supabase scraped_content table.
    Writes raw results to .tmp/tiktok_scrape_{timestamp}.json
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.utils.apify_client import get_apify_client
from tools.utils.supabase_client import get_supabase_client


def scrape_by_hashtags(hashtags: list[str], limit: int = 100) -> list[dict]:
    """Scrape viral TikTok posts by hashtag."""
    client = get_apify_client()

    run_input = {
        "hashtags": hashtags,
        "resultsPerPage": limit,
    }

    print(f"Starting TikTok hashtag scrape: {hashtags} (limit: {limit})")
    run = client.actor("clockworks/tiktok-hashtag-scraper").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"Scraped {len(items)} TikTok videos")
    return items


def scrape_profile(handle: str, limit: int = 50) -> list[dict]:
    """Scrape videos from a specific TikTok profile."""
    client = get_apify_client()

    run_input = {
        "profiles": [handle],
        "resultsPerPage": limit,
    }

    print(f"Starting TikTok profile scrape: @{handle} (limit: {limit})")
    run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"Scraped {len(items)} videos from @{handle}")
    return items


def compute_virality_score(post: dict) -> float:
    """Compute a weighted virality score."""
    likes = post.get("likes_count", 0) or 0
    comments = post.get("comments_count", 0) or 0
    shares = post.get("shares_count", 0) or 0
    saves = post.get("saves_count", 0) or 0
    views = post.get("views_count", 0) or 0

    engagement = likes + (comments * 2) + (shares * 3) + (saves * 4)
    if views > 0:
        return round(engagement / views, 6)
    elif likes > 0:
        return round(engagement / (likes * 10), 6)
    return 0.0


def transform_post(raw_post: dict, scrape_job_id: str) -> dict:
    """Transform raw Apify TikTok data to our schema."""
    author = raw_post.get("authorMeta", {})
    hashtag_list = [h.get("name", "") for h in raw_post.get("hashtags", [])]

    transformed = {
        "platform_id": 2,  # TikTok
        "source_url": raw_post.get("webVideoUrl", ""),
        "source_handle": author.get("name", ""),
        "content_text": raw_post.get("text", ""),
        "content_type": "video",
        "media_urls": [raw_post.get("videoUrl", "")] if raw_post.get("videoUrl") else [],
        "likes_count": raw_post.get("diggCount", 0),
        "comments_count": raw_post.get("commentCount", 0),
        "shares_count": raw_post.get("shareCount", 0),
        "views_count": raw_post.get("playCount", 0),
        "saves_count": raw_post.get("collectCount", 0),
        "hashtags": hashtag_list,
        "mentions": raw_post.get("mentions", []),
        "posted_at": raw_post.get("createTimeISO"),
        "scrape_job_id": scrape_job_id,
        "raw_data": raw_post,
    }

    transformed["virality_score"] = compute_virality_score(transformed)
    return transformed


def store_posts(posts: list[dict], scrape_job_id: str) -> int:
    """Transform and store posts in Supabase."""
    supabase = get_supabase_client()
    stored = 0

    for raw_post in posts:
        if not raw_post.get("text"):
            continue

        transformed = transform_post(raw_post, scrape_job_id)

        try:
            supabase.table("scraped_content").insert(transformed).execute()
            stored += 1
        except Exception as e:
            print(f"Error storing TikTok video: {e}")

    return stored


def save_raw_to_tmp(items: list[dict], mode: str) -> str:
    """Save raw results to .tmp/."""
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(tmp_dir, f"tiktok_{mode}_{timestamp}.json")

    with open(filepath, "w") as f:
        json.dump(items, f, indent=2, default=str)

    print(f"Raw results saved to {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="TikTok scraping tool")
    parser.add_argument("--mode", required=True, choices=["viral", "profile"])
    parser.add_argument("--hashtags", help="Comma-separated hashtags (viral mode)")
    parser.add_argument("--handle", help="TikTok handle (profile mode)")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    scrape_job_id = f"tt_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if args.mode == "viral":
        if not args.hashtags:
            parser.error("--hashtags required for viral mode")
        hashtags = [h.strip() for h in args.hashtags.split(",")]
        items = scrape_by_hashtags(hashtags, args.limit)
    else:
        if not args.handle:
            parser.error("--handle required for profile mode")
        items = scrape_profile(args.handle, args.limit)

    save_raw_to_tmp(items, args.mode)
    stored = store_posts(items, scrape_job_id)
    print(f"Done. Stored {stored}/{len(items)} TikTok videos in Supabase.")


if __name__ == "__main__":
    main()
