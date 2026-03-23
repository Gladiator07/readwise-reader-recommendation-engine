# /// script
# requires-python = ">=3.11"
# dependencies = ["requests>=2.28.0"]
# ///

"""Fetch articles from Readwise Reader API and export to markdown files."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests

SCRIPT_DIR = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = SCRIPT_DIR / "data"


def fetch_reader_documents(location=None, updated_after=None):
    """Fetch documents from Readwise Reader API with pagination."""
    token = os.environ["READWISE_TOKEN"]
    full_data = []
    next_page_cursor = None

    while True:
        params = {}
        if next_page_cursor:
            params["pageCursor"] = next_page_cursor
        if updated_after:
            params["updatedAfter"] = updated_after
        if location:
            params["location"] = location

        response = requests.get(
            url="https://readwise.io/api/v3/list/",
            params=params,
            headers={"Authorization": f"Token {token}"},
        )
        response.raise_for_status()

        data = response.json()
        full_data.extend(data["results"])

        next_page_cursor = data.get("nextPageCursor")
        if not next_page_cursor:
            break

    return full_data


def process_article(doc):
    """Keep only relevant fields for recommendation matching."""
    url = doc.get("source_url") or doc.get("url") or ""
    domain = urlparse(url).netloc if url else "unknown"

    return {
        "title": doc.get("title") or "Untitled",
        "author": doc.get("author") or "Unknown",
        "summary": (doc.get("summary") or "No summary")[:200],  # Truncate for table
        "tags": ", ".join((doc.get("tags") or {}).keys()) or "None",
        "url": doc.get("url") or "",
        "reading_time": doc.get("reading_time") or "Unknown",
        "domain": domain or "unknown",
    }


def export_to_markdown(docs, output_file, title):
    """Export documents to a single markdown file with table structure."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    articles = [process_article(doc) for doc in docs]

    lines = [
        f"# {title}",
        f"",
        f"**Total articles: {len(articles)}**",
        f"",
        f"| # | Title | Author | Domain | Reading Time | Tags | Summary |",
        f"|---|-------|--------|--------|--------------|------|---------|",
    ]

    for i, article in enumerate(articles, 1):
        # Escape pipe characters in content
        title_clean = article["title"].replace("|", "\\|")[:60]
        author_clean = article["author"].replace("|", "\\|")[:30]
        summary_clean = article["summary"].replace("|", "\\|").replace("\n", " ")[:100]
        tags_clean = article["tags"].replace("|", "\\|")[:50]

        line = f"| {i} | [{title_clean}]({article['url']}) | {author_clean} | {article['domain']} | {article['reading_time']} | {tags_clean} | {summary_clean} |"
        lines.append(line)

    with open(output_file, "w") as f:
        f.write("\n".join(lines))

    print(f"Exported {len(articles)} articles to {output_file}")


def main():
    print("Fetching Readwise Reader articles...")
    print(f"Data directory: {DATA_DIR}")

    print("\n--- Fetching 'new' location ---")
    new_docs = fetch_reader_documents(location="new")
    export_to_markdown(new_docs, DATA_DIR / "new.md", "Inbox Articles (New)")

    print("\n--- Fetching 'later' location ---")
    later_docs = fetch_reader_documents(location="later")
    export_to_markdown(later_docs, DATA_DIR / "later.md", "Later Articles")

    print("\n--- Fetching 'archive' location (last 14 days) ---")
    two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()
    archive_docs = fetch_reader_documents(location="archive", updated_after=two_weeks_ago)
    export_to_markdown(archive_docs, DATA_DIR / "recent.md", "Recently Archived (Last 14 Days)")

    print("\nDone!")


if __name__ == "__main__":
    main()
