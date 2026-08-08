"""Lightweight intent detection for routing user messages."""

import re
from typing import Any, Dict, Optional, Tuple

from services.market_service import ALIASES

STOCK_PATTERNS = [
    r"\b(price|quote|trading at|share price|stock price|how much is|current price)\b",
    r"\b(nifty|sensex|btc|bitcoin|ethereum)\b",
]
RESEARCH_PATTERNS = [
    r"\b(fundamental|p/e|pe ratio|dividend|market cap|analyst|consensus|research|overview)\b",
    r"\b(tell me about|deep dive|company profile)\b",
]
NEWS_PATTERNS = [
    r"\b(news|headline|why is|why are|falling|rising|crash|surge|market move)\b",
    r"\bwhat happened\b",
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

    if any(re.search(p, lower) for p in NEWS_PATTERNS):
        query = ticker or "stock market India"
        return "news", {"query": query, "ticker": ticker}

    if any(re.search(p, lower) for p in RESEARCH_PATTERNS) and ticker:
        return "research", {"ticker": ticker}

    if any(re.search(p, lower) for p in STOCK_PATTERNS) or ticker:
        if ticker:
            return "quote", {"ticker": ticker}

    return "chat", {"ticker": ticker}
