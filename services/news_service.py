"""
Real-time headlines via Google News RSS — no API key required.
"""

from typing import Any, Dict, List
from urllib.parse import quote_plus

import feedparser


def _feed_url(query: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"


def fetch_news(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Synchronous network call — wrap with asyncio.to_thread from handlers."""
    feed = feedparser.parse(_feed_url(query))
    results = []
    for entry in feed.entries[:limit]:
        results.append(
            {
                "title": getattr(entry, "title", ""),
                "link": getattr(entry, "link", ""),
                "published": getattr(entry, "published", ""),
                "source": getattr(getattr(entry, "source", None), "title", "") if hasattr(entry, "source") else "",
            }
        )
    return results