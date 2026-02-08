"""
Research service using Perplexity API.

Searches the web for relevant salon/beauty industry trends, insights,
and data before content generation. Gracefully degrades if no API key is set.
"""

import os
import httpx


PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


def get_research_query(user_message: str, content_type: str, platform: str) -> str:
    """Build a targeted research query from the user's message."""
    content_label = {
        "caption": "Instagram caption",
        "carousel": "carousel post",
        "edm": "email marketing",
        "reel_script": "short-form video/reel",
    }.get(content_type, "social media content")

    return (
        f"What are the latest trends, strategies, and insights about "
        f'"{user_message}" in the salon and beauty industry? '
        f"Focus on what's working for {content_label} content on {platform} right now. "
        f"Include any relevant statistics, viral formats, or engagement patterns."
    )


def research_topic(
    user_message: str,
    content_type: str = "caption",
    platform: str = "instagram",
) -> dict:
    """
    Research a topic using Perplexity API before content generation.

    Returns dict with:
        - findings: str (synthesized research text)
        - citations: list[str] (source URLs if available)
        - success: bool
    """
    api_key = os.getenv("PERPLEXITY_API_KEY", "")

    if not api_key:
        return {"findings": "", "citations": [], "success": False}

    query = get_research_query(user_message, content_type, platform)

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                PERPLEXITY_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a salon and beauty industry research assistant. "
                                "Provide concise, actionable insights. Focus on current trends, "
                                "data points, and what's working on social media right now. "
                                "Keep your response under 400 words."
                            ),
                        },
                        {"role": "user", "content": query},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()

        findings = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])

        return {
            "findings": findings,
            "citations": citations if isinstance(citations, list) else [],
            "success": True,
        }

    except Exception as e:
        print(f"Perplexity research failed: {e}")
        return {"findings": "", "citations": [], "success": False}
