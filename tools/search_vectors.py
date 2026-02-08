"""
Vector similarity search tool.

Usage:
    python tools/search_vectors.py --query "salon marketing caption ideas" --limit 10
    python tools/search_vectors.py --query "hair stylist tips" --platform instagram --limit 5

Returns the most similar scraped content based on semantic search.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.generate_embeddings import generate_embedding
from tools.utils.supabase_client import get_supabase_client

PLATFORM_MAP = {"instagram": 1, "tiktok": 2, "youtube": 3}


def search_similar_content(
    query: str,
    match_count: int = 10,
    match_threshold: float = 0.5,
    platform_filter: int | None = None,
) -> list[dict]:
    """
    Search for similar content using vector similarity.

    Uses input_type="query" for asymmetric search (query vs documents).
    """
    query_embedding = generate_embedding(query, input_type="query")

    supabase = get_supabase_client()
    response = supabase.rpc(
        "match_content",
        {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
            "filter_platform_id": platform_filter,
        },
    ).execute()

    return response.data


def main():
    parser = argparse.ArgumentParser(description="Vector similarity search")
    parser.add_argument("--query", required=True, help="Search query text")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--platform", choices=["instagram", "tiktok", "youtube"])
    args = parser.parse_args()

    platform_id = PLATFORM_MAP.get(args.platform) if args.platform else None

    results = search_similar_content(
        query=args.query,
        match_count=args.limit,
        match_threshold=args.threshold,
        platform_filter=platform_id,
    )

    print(f"\nFound {len(results)} similar content items:\n")
    for i, r in enumerate(results, 1):
        platform_name = {1: "Instagram", 2: "TikTok", 3: "YouTube"}.get(r["platform_id"], "Unknown")
        print(f"{i}. [{platform_name}] @{r['source_handle']} (similarity: {r['similarity']:.3f})")
        preview = (r["content_text"] or "")[:150]
        print(f"   {preview}...")
        print(f"   Virality: {r['virality_score']:.4f} | URL: {r['source_url']}")
        print()


if __name__ == "__main__":
    main()
