"""
Website scraping tool for brand voice analysis.

Crawls a website and extracts text content for analysis.

Usage:
    python tools/scrape_website.py --url https://yoursalonsupport.com --max-pages 10

Outputs:
    Returns extracted text content.
    Writes raw results to .tmp/website_scrape_{timestamp}.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from bs4 import BeautifulSoup


def extract_text_from_html(html: str, url: str) -> dict:
    """Extract meaningful text content from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Extract title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Extract meta description
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"]

    # Extract headings
    headings = []
    for tag in ["h1", "h2", "h3"]:
        for h in soup.find_all(tag):
            text = h.get_text(strip=True)
            if text:
                headings.append({"level": tag, "text": text})

    # Extract paragraph text
    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text and len(text) > 20:
            paragraphs.append(text)

    # Extract links for crawling
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(url, href)
        if urlparse(full_url).netloc == urlparse(url).netloc:
            links.append(full_url)

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "headings": headings,
        "paragraphs": paragraphs,
        "internal_links": list(set(links)),
    }


def crawl_website(base_url: str, max_pages: int = 10) -> list[dict]:
    """Crawl a website starting from base_url, up to max_pages."""
    visited = set()
    to_visit = [base_url]
    results = []

    client = httpx.Client(
        follow_redirects=True,
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        },
    )

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)

        # Normalize URL
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

        if normalized in visited:
            continue

        try:
            print(f"Crawling: {url}")
            response = client.get(url)
            response.raise_for_status()

            if "text/html" not in response.headers.get("content-type", ""):
                continue

            page_data = extract_text_from_html(response.text, url)
            results.append(page_data)
            visited.add(normalized)

            # Add internal links to queue
            for link in page_data["internal_links"]:
                link_normalized = urlparse(link)
                link_key = f"{link_normalized.scheme}://{link_normalized.netloc}{link_normalized.path}".rstrip("/")
                if link_key not in visited:
                    to_visit.append(link)

        except Exception as e:
            print(f"Error crawling {url}: {e}")
            visited.add(normalized)

    client.close()
    return results


def combine_text(pages: list[dict]) -> str:
    """Combine all extracted text into a single string for analysis."""
    sections = []

    for page in pages:
        page_text = f"--- Page: {page['title']} ({page['url']}) ---\n"

        if page["meta_description"]:
            page_text += f"Description: {page['meta_description']}\n"

        for h in page["headings"]:
            prefix = "#" * int(h["level"][1])
            page_text += f"{prefix} {h['text']}\n"

        for p in page["paragraphs"]:
            page_text += f"{p}\n"

        sections.append(page_text)

    return "\n\n".join(sections)


def save_raw_to_tmp(pages: list[dict]) -> str:
    """Save crawl results to .tmp/."""
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(tmp_dir, f"website_scrape_{timestamp}.json")

    with open(filepath, "w") as f:
        json.dump(pages, f, indent=2, default=str)

    print(f"Raw results saved to {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Website scraping tool")
    parser.add_argument("--url", required=True, help="Base URL to crawl")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to crawl")
    args = parser.parse_args()

    pages = crawl_website(args.url, args.max_pages)
    save_raw_to_tmp(pages)

    combined = combine_text(pages)
    print(f"\nCrawled {len(pages)} pages. Total text length: {len(combined)} chars")
    print("\n--- Combined Text Preview (first 1000 chars) ---")
    print(combined[:1000])


if __name__ == "__main__":
    main()
