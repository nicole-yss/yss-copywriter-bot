"""
RAG service: Retrieves relevant context for content generation.

Combines:
1. Vector search of viral content (scraped_content)
2. Brand voice profile (brand_voice_profiles)
3. User feedback from previous generations (content_feedback)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.search_vectors import search_similar_content
from tools.generate_embeddings import generate_embedding
from tools.utils.supabase_client import get_supabase_client

PLATFORM_MAP = {"instagram": 1, "tiktok": 2, "youtube": 3}


class RAGService:
    def __init__(self):
        self.supabase = get_supabase_client()

    def get_rag_context(
        self,
        user_query: str,
        content_type: str = "caption",
        platform: str | None = None,
        max_examples: int = 5,
    ) -> dict:
        """
        Build the full RAG context for a generation request.

        Returns dict with:
            - viral_examples: Top matching viral content
            - brand_voice: Brand voice profile dict
            - positive_feedback: Liked generations to emulate
            - negative_feedback: Disliked generations to avoid
        """
        # 1. Vector search for relevant viral content
        platform_id = PLATFORM_MAP.get(platform) if platform else None
        try:
            viral_examples = search_similar_content(
                query=user_query,
                match_count=max_examples,
                match_threshold=0.3,
                platform_filter=platform_id,
            )
        except Exception as e:
            print(f"Vector search failed (corpus may be empty): {e}")
            viral_examples = []

        # 2. Fetch latest brand voice profile
        try:
            brand_voice_response = (
                self.supabase.table("brand_voice_profiles")
                .select("*")
                .eq("brand_name", "YourSalonSupport")
                .order("analyzed_at", desc=True)
                .limit(1)
                .execute()
            )
            brand_voice = brand_voice_response.data[0] if brand_voice_response.data else None
        except Exception as e:
            print(f"Brand voice fetch failed: {e}")
            brand_voice = None

        # 3. Fetch relevant feedback for RAG improvement
        positive_feedback = []
        negative_feedback = []
        try:
            query_embedding = generate_embedding(user_query)
            positive_feedback = self._search_feedback(
                query_embedding, content_type, rating="positive", limit=3
            )
            negative_feedback = self._search_feedback(
                query_embedding, content_type, rating="negative", limit=2
            )
        except Exception as e:
            print(f"Feedback search failed: {e}")

        return {
            "viral_examples": viral_examples,
            "brand_voice": brand_voice,
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
        }

    def _search_feedback(
        self,
        query_embedding: list[float],
        content_type: str,
        rating: str,
        limit: int = 3,
    ) -> list[dict]:
        """Search content_feedback table for similar rated content."""
        try:
            response = self.supabase.rpc(
                "match_feedback",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.3,
                    "match_count": limit,
                    "filter_rating": rating,
                    "filter_content_type": content_type,
                },
            ).execute()
            return response.data or []
        except Exception as e:
            print(f"Feedback RPC failed: {e}")
            return []
