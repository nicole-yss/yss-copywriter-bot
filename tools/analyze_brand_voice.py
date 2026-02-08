"""
Brand voice analysis tool.

Scrapes @yoursalonsupport Instagram posts, then uses Claude to
extract a structured brand voice profile.

Usage:
    python tools/analyze_brand_voice.py
    python tools/analyze_brand_voice.py --ig-limit 30

Outputs:
    Stores brand_voice_profiles record in Supabase.
    Writes analysis to .tmp/brand_voice_analysis.json
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.scrape_instagram import scrape_profile as scrape_ig_profile
from tools.generate_embeddings import generate_embedding
from tools.utils.claude_client import get_claude_client
from tools.utils.supabase_client import get_supabase_client


BRAND_VOICE_ANALYSIS_PROMPT = """You are a brand strategist analyzing the voice and tone of a social media brand.

Analyze the following Instagram content from @yoursalonsupport (YSS - Your Salon Support, a creative agency that builds Hair Clubs, social strategies, and marketing systems for salons).

Instagram post captions:
{content_samples}

Provide a detailed brand voice analysis as valid JSON with this exact structure:

{{
    "tone_attributes": {{
        "authoritative": <0.0-1.0>,
        "warm": <0.0-1.0>,
        "professional": <0.0-1.0>,
        "playful": <0.0-1.0>,
        "urgent": <0.0-1.0>,
        "inspirational": <0.0-1.0>,
        "educational": <0.0-1.0>,
        "exclusive": <0.0-1.0>
    }},
    "vocabulary_patterns": {{
        "power_words": ["list of frequently used impactful words"],
        "industry_jargon": ["salon-specific terms used"],
        "avoided_words": ["words/phrases the brand never uses"],
        "signature_phrases": ["recurring brand phrases"]
    }},
    "sentence_structure": {{
        "avg_word_count": <number>,
        "style": "short_punchy | flowing | mixed",
        "uses_fragments": <boolean>,
        "uses_questions": <boolean>,
        "uses_commands": <boolean>
    }},
    "emoji_usage": {{
        "frequency": "none | minimal | moderate | heavy",
        "preferred_emojis": ["list of emojis if used"],
        "placement": "beginning | end | inline | none"
    }},
    "hashtag_strategy": {{
        "avg_count": <number>,
        "types": ["branded", "niche", "trending"],
        "placement": "inline | end | first_comment"
    }},
    "cta_patterns": {{
        "styles": ["list of CTA formats used"],
        "frequency": "every_post | most_posts | occasional"
    }},
    "overall_personality": "A 2-3 sentence summary of the brand voice personality",
    "writing_guidelines": "A detailed paragraph of specific do's and don'ts for writing as this brand"
}}

Return ONLY valid JSON, no other text."""


def analyze_brand_voice(ig_limit: int = 30):
    """Run the full brand voice analysis pipeline (Instagram only)."""

    # Step 1: Scrape Instagram posts
    print("Step 1: Scraping @yoursalonsupport Instagram posts...")
    ig_posts = scrape_ig_profile("yoursalonsupport", limit=ig_limit)
    captions = [p.get("caption", "") for p in ig_posts if p.get("caption")]
    print(f"  Got {len(captions)} captions")

    # Step 2: Analyze with Claude
    print("Step 2: Analyzing brand voice with Claude...")
    client = get_claude_client()

    content_samples = "\n\n---\n\n".join(captions[:20])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": BRAND_VOICE_ANALYSIS_PROMPT.format(
                    content_samples=content_samples,
                ),
            }
        ],
    )

    analysis_text = response.content[0].text

    # Step 3: Parse JSON
    try:
        analysis = json.loads(analysis_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        start = analysis_text.find("{")
        end = analysis_text.rfind("}") + 1
        if start >= 0 and end > start:
            analysis = json.loads(analysis_text[start:end])
        else:
            raise ValueError(f"Could not parse JSON from Claude response: {analysis_text[:200]}")

    print("  Brand voice analysis complete")

    # Step 4: Generate embedding
    print("Step 3: Generating analysis embedding...")
    analysis_prose = analysis.get("overall_personality", "") + "\n\n" + analysis.get(
        "writing_guidelines", ""
    )
    embedding = generate_embedding(analysis_prose)

    # Step 5: Store in Supabase
    print("Step 4: Storing in Supabase...")
    supabase = get_supabase_client()

    record = {
        "brand_name": "YourSalonSupport",
        "brand_handle": "@yoursalonsupport",
        "tone_attributes": analysis.get("tone_attributes"),
        "vocabulary_patterns": analysis.get("vocabulary_patterns"),
        "sentence_structure": analysis.get("sentence_structure"),
        "emoji_usage": analysis.get("emoji_usage"),
        "hashtag_strategy": analysis.get("hashtag_strategy"),
        "cta_patterns": analysis.get("cta_patterns"),
        "analysis_text": analysis_prose,
        "analysis_embedding": embedding,
        "source_posts_count": len(captions),
        "source_urls": ["https://instagram.com/yoursalonsupport"],
    }

    supabase.table("brand_voice_profiles").insert(record).execute()
    print("  Stored brand voice profile in Supabase")

    # Save to .tmp
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    filepath = os.path.join(tmp_dir, "brand_voice_analysis.json")
    with open(filepath, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"  Analysis saved to {filepath}")

    return analysis


def main():
    parser = argparse.ArgumentParser(description="Brand voice analysis tool (Instagram only)")
    parser.add_argument("--ig-limit", type=int, default=30, help="Instagram posts to analyze")
    args = parser.parse_args()

    analysis = analyze_brand_voice(ig_limit=args.ig_limit)

    print("\n=== Brand Voice Summary ===")
    print(f"Personality: {analysis.get('overall_personality', 'N/A')}")
    print(f"\nTone: {json.dumps(analysis.get('tone_attributes', {}), indent=2)}")


if __name__ == "__main__":
    main()
