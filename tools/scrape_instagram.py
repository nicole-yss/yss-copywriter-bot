"""
Instagram scraping tool using Apify actors.

Usage:
    python tools/scrape_instagram.py --mode viral --hashtags "salonowner,hairstylist,salonmarketing" --limit 100
    python tools/scrape_instagram.py --mode brand --handle yoursalonsupport --limit 50

Modes:
    viral  - Search by hashtags for viral content in the salon niche
    brand  - Scrape a specific profile's posts for brand voice analysis

Outputs:
    Stores results in Supabase scraped_content table.
    Writes raw results to .tmp/instagram_scrape_{timestamp}.json
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
    """Scrape viral Instagram posts by hashtag."""
    client = get_apify_client()

    # Build hashtag URLs for direct scraping
    directUrls = [f"https://www.instagram.com/explore/tags/{tag}/" for tag in hashtags]

    run_input = {
        "directUrls": directUrls,
        "resultsType": "posts",
        "resultsLimit": limit,
        "searchType": "hashtag",
        "searchLimit": limit,
    }

    print(f"Starting Instagram hashtag scrape: {hashtags} (limit: {limit})")
    try:
        # Try with apify/instagram-scraper (more general)
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"Scraped {len(items)} posts")
        return items
    except Exception as e:
        print(f"Error with apify/instagram-scraper: {e}")
        print("Trying alternative approach...")
        
        # Fallback: scrape profiles that use these hashtags
        all_items = []
        for tag in hashtags[:3]:  # Limit to first 3 hashtags to avoid rate limits
            try:
                run_input_fallback = {
                    "hashtags": [tag],
                    "resultsLimit": limit // len(hashtags),
                }
                run = client.actor("voyager/instagram-hashtag-scraper").call(run_input=run_input_fallback)
                items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                all_items.extend(items)
                print(f"Scraped {len(items)} posts for #{tag}")
            except Exception as e2:
                print(f"Error scraping #{tag}: {e2}")
        
        return all_items


def scrape_profile(handle: str, limit: int = 50) -> list[dict]:
    """Scrape all posts from a specific Instagram profile."""
    client = get_apify_client()
    
    # Remove @ if present
    handle = handle.lstrip('@')

    # Use directUrls instead of usernames - more reliable
    run_input = {
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "posts",
        "resultsLimit": limit,
    }

    print(f"Starting Instagram profile scrape: @{handle} (limit: {limit})")
    
    # Log the run input for debugging
    print(f"Run input: {json.dumps(run_input, indent=2)}")
    
    try:
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        
        # Log run details
        print(f"Run ID: {run.get('id')}")
        print(f"Run status: {run.get('status')}")
        
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"Scraped {len(items)} posts from @{handle}")
        
        if not items:
            print("⚠️ No posts returned. Possible reasons:")
            print("  - Profile is private")
            print("  - Profile doesn't exist")
            print("  - Apify actor needs authentication/proxies")
            print("  - Rate limiting")
        
        return items
        
    except Exception as e:
        print(f"Error scraping @{handle}: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Try alternative approach with direct URL only
        try:
            print("Trying minimal configuration...")
            run_input_minimal = {
                "directUrls": [f"https://www.instagram.com/{handle}/"],
                "resultsLimit": limit,
            }
            run = client.actor("apify/instagram-scraper").call(run_input=run_input_minimal)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            print(f"✅ Alternative method worked! Scraped {len(items)} posts")
            return items
        except Exception as e2:
            print(f"❌ All methods failed: {e2}")
            return []


def compute_virality_score(post: dict) -> float:
    """Compute a weighted virality score from engagement metrics."""
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
    """Transform raw Apify Instagram data to our database schema."""
    content_type_map = {
        "Image": "post",
        "Video": "reel",
        "Sidecar": "carousel",
        "GraphImage": "post",
        "GraphVideo": "reel",
        "GraphSidecar": "carousel",
    }

    # Handle different field names from different scrapers
    post_type = raw_post.get("type") or raw_post.get("__typename", "") or raw_post.get("productType", "")
    caption = raw_post.get("caption") or raw_post.get("text", "") or ""
    
    # Extract username from various possible fields
    username = (
        raw_post.get("ownerUsername") or 
        raw_post.get("owner", {}).get("username") if isinstance(raw_post.get("owner"), dict) else None or
        raw_post.get("username", "")
    )
    
    # Extract URL
    url = raw_post.get("url", "")
    if not url and raw_post.get("shortCode"):
        url = f"https://www.instagram.com/p/{raw_post.get('shortCode')}/"
    
    transformed = {
        "platform_id": 1,  # Instagram
        "source_url": url,
        "source_handle": username,
        "content_text": caption,
        "content_type": content_type_map.get(post_type, "post"),
        "media_urls": [raw_post.get("displayUrl", "")] if raw_post.get("displayUrl") else [],
        "likes_count": raw_post.get("likesCount", 0) or raw_post.get("likes", 0) or 0,
        "comments_count": raw_post.get("commentsCount", 0) or raw_post.get("comments", 0) or 0,
        "shares_count": 0,
        "views_count": raw_post.get("videoViewCount", 0) or raw_post.get("views", 0) or 0,
        "saves_count": 0,
        "hashtags": raw_post.get("hashtags", []),
        "mentions": raw_post.get("mentions", []),
        "posted_at": raw_post.get("timestamp") or raw_post.get("date") or raw_post.get("takenAtTimestamp"),
        "scrape_job_id": scrape_job_id,
        "raw_data": raw_post,
    }

    transformed["virality_score"] = compute_virality_score(transformed)
    return transformed


def store_posts(posts: list[dict], scrape_job_id: str) -> int:
    """Transform and store posts in Supabase. Returns count stored."""
    supabase = get_supabase_client()
    stored = 0

    for raw_post in posts:
        caption = raw_post.get("caption") or raw_post.get("text", "")
        if not caption:
            continue

        transformed = transform_post(raw_post, scrape_job_id)

        try:
            supabase.table("scraped_content").insert(transformed).execute()
            stored += 1
        except Exception as e:
            print(f"Error storing post {raw_post.get('url', 'unknown')}: {e}")

    return stored


def save_raw_to_tmp(items: list[dict], mode: str) -> str:
    """Save raw scrape results to .tmp/ for reference."""
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(tmp_dir, f"instagram_{mode}_{timestamp}.json")

    with open(filepath, "w") as f:
        json.dump(items, f, indent=2, default=str)

    print(f"Raw results saved to {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Instagram scraping tool")
    parser.add_argument("--mode", required=True, choices=["viral", "brand"])
    parser.add_argument("--hashtags", help="Comma-separated hashtags (viral mode)")
    parser.add_argument("--handle", help="Instagram handle without @ (brand mode)")
    parser.add_argument("--limit", type=int, default=100, help="Max posts to scrape")
    args = parser.parse_args()

    scrape_job_id = f"ig_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if args.mode == "viral":
        if not args.hashtags:
            parser.error("--hashtags required for viral mode")
        hashtags = [h.strip() for h in args.hashtags.split(",")]
        items = scrape_by_hashtags(hashtags, args.limit)
    else:
        if not args.handle:
            parser.error("--handle required for brand mode")
        items = scrape_profile(args.handle, args.limit)

    if not items:
        print("No posts scraped. Exiting.")
        return

    save_raw_to_tmp(items, args.mode)
    stored = store_posts(items, scrape_job_id)
    print(f"Done. Stored {stored}/{len(items)} posts in Supabase.")


if __name__ == "__main__":
    main()