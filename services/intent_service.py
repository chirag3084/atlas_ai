"""Lightweight intent detection for routing user messages."""

import re
from typing import Any, Dict, Optional, Tuple

from services.market_service import ALIASES

STOCK_PATTERNS = [
    r"\b(price|quote|trading at|share price|stock price|how much is|current price|what's the price)\b",
    r"\b(nifty|sensex|btc|bitcoin|ethereum|crypto)\b",
]
RESEARCH_PATTERNS = [
    r"\b(fundamental|p/e|pe ratio|dividend|market cap|analyst|consensus|research|overview|details)\b",
    r"\b(tell me about|deep dive|company profile|what do you know about|explain)\b",
]
NEWS_PATTERNS = [
    r"\b(news|headline|why is|why are|falling|rising|crash|surge|market move|latest|what's happening)\b",
    r"\b(what happened|market update|breaking news)\b",
]
GMAIL_PATTERNS = [
    r"\b(email|emails|gmail|inbox|check mail|read email|unread)\b",
    r"\b(any new emails|email notification)\b",
]
CALENDAR_PATTERNS = [
    r"\b(calendar|schedule|appointment|meeting|event|today's schedule|what's on my calendar)\b",
    r"\b(do i have any|upcoming events|my schedule)\b",
]
MENU_PATTERNS = [
    r"\b(menu|options|what can you do|help menu|show menu|main menu)\b",
    r"\b(start over|go back|home)\b",
]
BRIEFING_PATTERNS = [
    r"\b(briefing|morning briefing|daily update|market summary|catch me up)\b",
    r"\b(what's moving the market|market overview)\b",
]


def _extract_ticker(text: str) -> Optional[str]:
    lower = text.lower()
    for alias in sorted(ALIASES.keys(), key=len, reverse=True):
        if alias in lower:
            return alias
    match = re.search(r"\b([A-Z]{2,10}(?:\.NS|\.BO)?)\b", text)
    if match:
        return match.group(1)
    return None


def detect_intent(text: str) -> Tuple[str, Dict[str, Any]]:
    lower = text.lower()
    ticker = _extract_ticker(text)

    # Check for menu requests
    if any(re.search(p, lower) for p in MENU_PATTERNS):
        return "menu", {}

    # Check for briefing requests
    if any(re.search(p, lower) for p in BRIEFING_PATTERNS):
        return "briefing", {}

    # Check for Gmail requests
    if any(re.search(p, lower) for p in GMAIL_PATTERNS):
        return "gmail", {}

    # Check for Calendar requests
    if any(re.search(p, lower) for p in CALENDAR_PATTERNS):
        return "calendar", {}

    # Check for news requests
    if any(re.search(p, lower) for p in NEWS_PATTERNS):
        query = ticker or "stock market India"
        return "news", {"query": query, "ticker": ticker}

    # Check for research requests
    if any(re.search(p, lower) for p in RESEARCH_PATTERNS) and ticker:
        return "research", {"ticker": ticker}

    # Check for quote requests
    if any(re.search(p, lower) for p in STOCK_PATTERNS) or ticker:
        if ticker:
            return "quote", {"ticker": ticker}

    return "chat", {"ticker": ticker}
