"""
Embedding generation tool using Voyage AI.

Usage:
    python tools/generate_embeddings.py --text "some text to embed"
    python tools/generate_embeddings.py --batch --unembedded

Modes:
    --text        Embed a single text string, print the vector
    --batch       Find all scraped_content rows without embeddings and generate them
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.utils.voyage_client import get_voyage_client, VOYAGE_MODEL, BATCH_SIZE
from tools.utils.supabase_client import get_supabase_client


def generate_embedding(text: str, input_type: str = "document") -> list[float]:
    """Generate a single embedding vector."""
    client = get_voyage_client()
    result = client.embed([text], model=VOYAGE_MODEL, input_type=input_type)
    return result.embeddings[0]


def generate_embeddings_batch(texts: list[str], input_type: str = "document") -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    client = get_voyage_client()
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        print(f"  Embedding batch {i // BATCH_SIZE + 1} ({len(batch)} texts)...")
        result = client.embed(batch, model=VOYAGE_MODEL, input_type=input_type)
        all_embeddings.extend(result.embeddings)

    return all_embeddings


def backfill_unembedded_content():
    """Find scraped_content without embeddings and generate them."""
    supabase = get_supabase_client()

    response = (
        supabase.table("scraped_content")
        .select("id, content_text")
        .is_("embedding", "null")
        .not_.is_("content_text", "null")
        .limit(500)
        .execute()
    )

    rows = response.data
    if not rows:
        print("No unembedded content found.")
        return 0

    print(f"Found {len(rows)} unembedded content items. Generating embeddings...")

    texts = [row["content_text"] for row in rows]
    embeddings = generate_embeddings_batch(texts)

    updated = 0
    for row, embedding in zip(rows, embeddings):
        try:
            supabase.table("scraped_content").update({"embedding": embedding}).eq(
                "id", row["id"]
            ).execute()
            updated += 1
        except Exception as e:
            print(f"Error updating embedding for {row['id']}: {e}")

    print(f"Generated embeddings for {updated}/{len(rows)} content items.")
    return updated


def main():
    parser = argparse.ArgumentParser(description="Embedding generation tool")
    parser.add_argument("--text", help="Single text to embed")
    parser.add_argument("--batch", action="store_true", help="Batch mode")
    parser.add_argument(
        "--unembedded",
        action="store_true",
        help="Process unembedded content (use with --batch)",
    )
    args = parser.parse_args()

    if args.text:
        embedding = generate_embedding(args.text)
        print(f"Embedding dimensions: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    elif args.batch and args.unembedded:
        backfill_unembedded_content()
    else:
        parser.error("Provide --text for single embedding or --batch --unembedded for batch mode")


if __name__ == "__main__":
    main()
