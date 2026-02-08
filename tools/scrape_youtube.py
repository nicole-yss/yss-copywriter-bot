"""
YouTube scraping tool using Apify actors.

Usage:
    python tools/scrape_youtube.py --mode search --terms "salon marketing tips,salon business growth" --limit 50
    python tools/scrape_youtube.py --mode channel --handle yoursalonsupport --limit 30

Outputs:
    Stores results in Supabase scraped_content table.
    Writes raw results to .tmp/youtube_scrape_{timestamp}.json
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.utils.apify_client import get_apify_client
from tools.utils.supabase_client import get_supabase_client


def scrape_by_search(search_terms: list[str], limit: int = 50) -> list[dict]:
    """Search YouTube for videos matching terms."""
    client = get_apify_client()

    run_input = {
        "searchKeywords": search_terms,
        "maxResults": limit,
    }

    print(f"Starting YouTube search scrape: {search_terms} (limit: {limit})")
    run = client.actor("streamers/youtube-scraper").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"Scraped {len(items)} YouTube videos")
    return items


def scrape_channel(handle: str, limit: int = 30) -> list[dict]:
    """Scrape videos from a specific YouTube channel."""
    client = get_apify_client()

    run_input = {
        "startUrls": [{"url": f"https://www.youtube.com/@{handle}"}],
        "maxResults": limit,
    }

    print(f"Starting YouTube channel scrape: @{handle} (limit: {limit})")
    run = client.actor("streamers/youtube-channel-scraper").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"Scraped {len(items)} videos from @{handle}")
    return items


def compute_virality_score(post: dict) -> float:
    """Compute virality score for YouTube content."""
    likes = post.get("likes_count", 0) or 0
    comments = post.get("comments_count", 0) or 0
    views = post.get("views_count", 0) or 0

    engagement = likes + (comments * 2)
    if views > 0:
        return round(engagement / views, 6)
    elif likes > 0:
        return round(engagement / (likes * 10), 6)
    return 0.0


def transform_post(raw_post: dict, scrape_job_id: str) -> dict:
    """Transform raw Apify YouTube data to our schema."""
    description = raw_post.get("description", "") or ""
    title = raw_post.get("title", "") or ""
    content_text = f"{title}\n\n{description}".strip()

    transformed = {
        "platform_id": 3,  # YouTube
        "source_url": raw_post.get("url", ""),
        "source_handle": raw_post.get("channelName", ""),
        "content_text": content_text,
        "content_type": "video",
        "media_urls": [raw_post.get("thumbnailUrl", "")] if raw_post.get("thumbnailUrl") else [],
        "likes_count": raw_post.get("likes", 0),
        "comments_count": raw_post.get("commentsCount", 0),
        "shares_count": 0,
        "views_count": raw_post.get("viewCount", 0),
        "saves_count": 0,
        "hashtags": raw_post.get("hashtags", []),
        "mentions": [],
        "posted_at": raw_post.get("date"),
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
        content = raw_post.get("title", "") or raw_post.get("description", "")
        if not content:
            continue

        transformed = transform_post(raw_post, scrape_job_id)

        try:
            supabase.table("scraped_content").insert(transformed).execute()
            stored += 1
        except Exception as e:
            print(f"Error storing YouTube video: {e}")

    return stored


def save_raw_to_tmp(items: list[dict], mode: str) -> str:
    """Save raw results to .tmp/."""
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(tmp_dir, f"youtube_{mode}_{timestamp}.json")

    with open(filepath, "w") as f:
        json.dump(items, f, indent=2, default=str)

    print(f"Raw results saved to {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="YouTube scraping tool")
    parser.add_argument("--mode", required=True, choices=["search", "channel"])
    parser.add_argument("--terms", help="Comma-separated search terms (search mode)")
    parser.add_argument("--handle", help="YouTube channel handle (channel mode)")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    scrape_job_id = f"yt_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if args.mode == "search":
        if not args.terms:
            parser.error("--terms required for search mode")
        terms = [t.strip() for t in args.terms.split(",")]
        items = scrape_by_search(terms, args.limit)
    else:
        if not args.handle:
            parser.error("--handle required for channel mode")
        items = scrape_channel(args.handle, args.limit)

    save_raw_to_tmp(items, args.mode)
    stored = store_posts(items, scrape_job_id)
    print(f"Done. Stored {stored}/{len(items)} YouTube videos in Supabase.")


if __name__ == "__main__":
    main()
