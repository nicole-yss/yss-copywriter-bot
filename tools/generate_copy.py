"""
Copy generation tool (standalone, CLI-based).

Usage:
    python tools/generate_copy.py --type caption --platform instagram --prompt "Post about salon growth tips"
    python tools/generate_copy.py --type carousel --platform instagram --prompt "5 ways to retain salon clients"
    python tools/generate_copy.py --type edm --prompt "Email about our new social media package"
    python tools/generate_copy.py --type reel_script --platform tiktok --prompt "Quick tip about salon booking systems"

Outputs:
    Prints generated copy to stdout.
    Stores in generated_content table.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.utils.claude_client import get_claude_client
from tools.utils.supabase_client import get_supabase_client
from tools.search_vectors import search_similar_content

# Import prompt building from backend
from backend.prompts.system_prompt import build_system_prompt
from backend.services.rag_service import RAGService

PLATFORM_MAP = {"instagram": 1, "tiktok": 2, "youtube": 3}
CONTENT_TYPE_MAP = {"caption": 1, "carousel": 2, "edm": 3, "reel_script": 4}


def generate_copy(content_type: str, platform: str, user_prompt: str) -> str:
    """Generate copy using RAG context and Claude."""

    # Get RAG context
    rag_service = RAGService()
    rag_context = rag_service.get_rag_context(
        user_query=user_prompt,
        content_type=content_type,
        platform=platform,
    )

    # Build system prompt
    system_prompt = build_system_prompt(rag_context, content_type, platform)

    # Generate with Claude
    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    generated_text = response.content[0].text

    # Store in Supabase
    supabase = get_supabase_client()
    rag_source_ids = [ex.get("id") for ex in rag_context.get("viral_examples", []) if ex.get("id")]

    record = {
        "content_type_id": CONTENT_TYPE_MAP.get(content_type),
        "platform_id": PLATFORM_MAP.get(platform),
        "body": generated_text,
        "prompt_used": user_prompt,
        "model_used": "claude-sonnet-4-20250514",
        "rag_sources": rag_source_ids if rag_source_ids else None,
    }

    supabase.table("generated_content").insert(record).execute()

    return generated_text


def main():
    parser = argparse.ArgumentParser(description="Copy generation tool")
    parser.add_argument("--type", required=True, choices=["caption", "carousel", "edm", "reel_script"])
    parser.add_argument("--platform", default="instagram", choices=["instagram", "tiktok", "youtube"])
    parser.add_argument("--prompt", required=True, help="What kind of content to generate")
    args = parser.parse_args()

    print(f"Generating {args.type} for {args.platform}...")
    print("=" * 60)

    copy = generate_copy(args.type, args.platform, args.prompt)
    print(copy)
    print("=" * 60)
    print("Copy saved to database.")


if __name__ == "__main__":
    main()
