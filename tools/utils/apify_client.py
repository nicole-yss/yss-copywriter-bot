"""Shared Apify client configuration."""

import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()


def get_apify_client() -> ApifyClient:
    """Return a configured Apify client."""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise ValueError("APIFY_API_TOKEN must be set in .env")
    return ApifyClient(token)
