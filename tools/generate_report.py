"""
Report generation tool.

Generates analytics reports by analyzing scraped content, generated content,
and brand voice data.

Usage:
    python tools/generate_report.py --type content_audit
    python tools/generate_report.py --type competitor_analysis
    python tools/generate_report.py --type strategy

Outputs:
    Stores report in Supabase reports table.
    Writes markdown report to .tmp/reports/
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.utils.claude_client import get_claude_client
from tools.utils.supabase_client import get_supabase_client


REPORT_PROMPTS = {
    "content_audit": {
        "title": "Content Performance Audit",
        "prompt": """Analyze the following data about the salon industry social media landscape.

Viral Content from the Salon Niche (top performing posts):
{viral_data}

Generated Content History for YSS:
{generated_data}

Brand Voice Profile:
{brand_voice}

Produce a comprehensive Content Performance Audit report in markdown covering:

1. **Executive Summary** - Key findings in 3-4 bullet points
2. **Viral Content Analysis** - What patterns make salon content go viral (hooks, formats, topics, timing)
3. **Content Gap Analysis** - Topics and formats that perform well in the niche but YSS hasn't covered
4. **Engagement Benchmarks** - Average metrics for top content, what "good" looks like
5. **Top Content Themes** - The 5-7 most engaging content themes in the salon niche
6. **Recommendations** - 5-10 specific, actionable recommendations for YSS's content strategy
7. **Quick Wins** - 3 things that can be implemented this week

Be data-driven. Reference specific examples from the data. Be specific, not generic.""",
    },
    "competitor_analysis": {
        "title": "Competitive Landscape Analysis",
        "prompt": """Analyze the following scraped content from salon industry social media accounts.

Top Performing Content by Account:
{viral_data}

Produce a Competitive Landscape Analysis report in markdown covering:

1. **Executive Summary** - Key competitive insights
2. **Top Accounts** - Who are the top performers in salon social media and why
3. **Content Strategy Patterns** - How competitors post (frequency, formats, themes)
4. **Engagement Tactics** - Specific techniques that drive high engagement
5. **Hashtag Strategies** - What hashtags top performers use and how
6. **Content Gaps** - What competitors are NOT covering (opportunity for YSS)
7. **Differentiation Opportunities** - How YSS can stand out from the crowd
8. **Threat Assessment** - Competitors whose strategies could impact YSS

Be specific. Name accounts, reference specific posts, and provide actionable insights.""",
    },
    "strategy": {
        "title": "Content Strategy Recommendations",
        "prompt": """Based on all available data, create a content strategy for YourSalonSupport.

Brand Voice Profile:
{brand_voice}

Viral Content Trends in Salon Niche:
{viral_data}

Current Generated Content:
{generated_data}

Produce a Content Strategy Report in markdown covering:

1. **Executive Summary** - Strategy direction in 3 sentences
2. **Content Pillars** - 4-5 content themes/pillars with descriptions and example post ideas
3. **Platform Strategy**
   - Instagram: posting cadence, best formats, optimal times
   - TikTok: content approach, trending formats, hashtag strategy
   - YouTube: content types, SEO approach
4. **Format Mix** - Recommended split between reels, carousels, single posts, stories
5. **Hook Formulas** - 10 proven hook templates customized for salon content
6. **Monthly Content Calendar** - A template week with specific content slots
7. **KPIs & Success Metrics** - What to measure and target benchmarks
8. **30-60-90 Day Plan** - Phased rollout strategy

Make every recommendation specific to the salon/beauty industry. Include example post ideas.""",
    },
}


def gather_report_data(report_type: str) -> dict:
    """Gather all necessary data from Supabase for report generation."""
    supabase = get_supabase_client()
    data = {}

    # Viral content (always needed)
    viral = (
        supabase.table("scraped_content")
        .select(
            "content_text, source_handle, platform_id, likes_count, comments_count, "
            "shares_count, views_count, virality_score, hashtags, content_type, posted_at"
        )
        .order("virality_score", desc=True)
        .limit(50)
        .execute()
    )
    data["viral_data"] = json.dumps(viral.data[:30], indent=2, default=str) if viral.data else "No viral data collected yet."

    # Generated content (for audit and strategy)
    if report_type in ("content_audit", "strategy"):
        generated = (
            supabase.table("generated_content")
            .select("body, content_type_id, platform_id, rating, is_favorite, created_at")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        data["generated_data"] = json.dumps(generated.data[:20], indent=2, default=str) if generated.data else "No generated content yet."
    else:
        data["generated_data"] = "N/A"

    # Brand voice (for audit and strategy)
    if report_type in ("content_audit", "strategy"):
        voice = (
            supabase.table("brand_voice_profiles")
            .select("tone_attributes, vocabulary_patterns, sentence_structure, emoji_usage, hashtag_strategy, cta_patterns, analysis_text")
            .eq("brand_name", "YourSalonSupport")
            .order("analyzed_at", desc=True)
            .limit(1)
            .execute()
        )
        data["brand_voice"] = json.dumps(voice.data[0], indent=2) if voice.data else "Brand voice not yet analyzed."
    else:
        data["brand_voice"] = "N/A"

    return data


def generate_report(report_type: str) -> dict:
    """Generate a report using Claude and store it in Supabase."""
    if report_type not in REPORT_PROMPTS:
        raise ValueError(f"Unknown report type: {report_type}. Choose from: {list(REPORT_PROMPTS.keys())}")

    config = REPORT_PROMPTS[report_type]
    print(f"Generating {config['title']}...")

    # Gather data
    data = gather_report_data(report_type)

    # Generate with Claude
    client = get_claude_client()
    prompt = config["prompt"].format(**data)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    report_content = response.content[0].text

    # Extract summary (first paragraph or executive summary)
    lines = report_content.split("\n")
    summary_lines = []
    for line in lines:
        if line.strip() and not line.startswith("#"):
            summary_lines.append(line.strip())
            if len(summary_lines) >= 3:
                break
    summary = " ".join(summary_lines)

    # Store in Supabase
    supabase = get_supabase_client()
    record = {
        "report_type": report_type,
        "title": config["title"],
        "summary": summary[:500],
        "full_content": report_content,
        "data": {"viral_count": len(data.get("viral_data", "")), "generated_at": datetime.utcnow().isoformat()},
    }

    result = supabase.table("reports").insert(record).execute()
    print(f"Report stored in Supabase: {result.data[0]['id']}")

    # Save to .tmp
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "reports")
    os.makedirs(tmp_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(tmp_dir, f"{report_type}_{timestamp}.md")
    with open(filepath, "w") as f:
        f.write(report_content)
    print(f"Report saved to {filepath}")

    return {"id": result.data[0]["id"], "title": config["title"], "filepath": filepath}


def main():
    parser = argparse.ArgumentParser(description="Report generation tool")
    parser.add_argument("--type", required=True, choices=list(REPORT_PROMPTS.keys()))
    args = parser.parse_args()

    result = generate_report(args.type)
    print(f"\nReport generated: {result['title']}")
    print(f"File: {result['filepath']}")


if __name__ == "__main__":
    main()
