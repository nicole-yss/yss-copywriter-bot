"""Shared Voyage AI client configuration for embeddings."""

import os
import voyageai
from dotenv import load_dotenv

load_dotenv()

VOYAGE_MODEL = "voyage-3.5"
EMBEDDING_DIMENSIONS = 1024
BATCH_SIZE = 128

_client: voyageai.Client | None = None


def get_voyage_client() -> voyageai.Client:
    """Return a configured Voyage AI client (singleton)."""
    global _client
    if _client is None:
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise ValueError("VOYAGE_API_KEY must be set in .env")
        _client = voyageai.Client(api_key=api_key)
    return _client
