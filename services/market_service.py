"""
Live stock/index/crypto prices and company fundamentals via yfinance.

yfinance calls are synchronous and hit the network, so every public
function here should be called with asyncio.to_thread from handlers to
avoid blocking the bot's event loop.
"""

from typing import Any, Dict, Optional

import yfinance as yf

# Common names/tickers people actually type -> the yfinance symbol that
# resolves them. Not exhaustive — anything not in this map is passed
# through as-is (assumed to already be a valid ticker, e.g. "AAPL").
ALIASES = {
    "nifty": "^NSEI",
    "nifty50": "^NSEI",
    "nifty 50": "^NSEI",
    "sensex": "^BSESN",
    "reliance": "RELIANCE.NS",
    "ril": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "hdfcbank": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "sbi": "SBIN.NS",
    "wipro": "WIPRO.NS",
    "tata motors": "TATAMOTORS.NS",
    "adani enterprises": "ADANIENT.NS",
    "bitcoin": "BTC-USD",
    "btc": "BTC-USD",
    "ethereum": "ETH-USD",
    "eth": "ETH-USD",
    "apple": "AAPL",
    "tesla": "TSLA",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "nvidia": "NVDA",
    "meta": "META",
}


def resolve_symbol(query: str) -> str:
    key = query.strip().lower()
    return ALIASES.get(key, query.strip().upper())


def get_quote(query: str) -> Dict[str, Any]:
    """Current price, day change %, and 52-week range for a symbol or alias."""
    symbol = resolve_symbol(query)
    ticker = yf.Ticker(symbol)

    try:
        fast = ticker.fast_info
        price = fast.get("lastPrice") or fast.get("last_price")
        prev_close = fast.get("previousClose") or fast.get("previous_close")
        year_high = fast.get("yearHigh") or fast.get("year_high")
        year_low = fast.get("yearLow") or fast.get("year_low")
        currency = fast.get("currency", "")
    except Exception:
        price = prev_close = year_high = year_low = None
        currency = ""

    if price is None:
        # fast_info can be sparse for some symbols — fall back to .info
        info = ticker.info or {}
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose")
        year_high = info.get("fiftyTwoWeekHigh")
        year_low = info.get("fiftyTwoWeekLow")
        currency = info.get("currency", currency)

    if price is None:
        return {"symbol": symbol, "found": False}

    change_pct = None
    if price is not None and prev_close:
        change_pct = round(((price - prev_close) / prev_close) * 100, 2)

    return {
        "symbol": symbol,
        "found": True,
        "price": round(price, 2) if price is not None else None,
        "previous_close": round(prev_close, 2) if prev_close else None,
        "change_pct": change_pct,
        "year_high": round(year_high, 2) if year_high else None,
        "year_low": round(year_low, 2) if year_low else None,
        "currency": currency,
    }


def get_fundamentals(query: str) -> Dict[str, Any]:
    """Deep company research: valuation, dividend, sector, analyst consensus."""
    symbol = resolve_symbol(query)
    ticker = yf.Ticker(symbol)

    try:
        info = ticker.info or {}
    except Exception:
        return {"symbol": symbol, "found": False}

    if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
        return {"symbol": symbol, "found": False}

    summary = info.get("longBusinessSummary", "")
    if summary and len(summary) > 500:
        summary = summary[:500].rsplit(" ", 1)[0] + "…"

    return {
        "symbol": symbol,
        "found": True,
        "name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "pe_ratio": info.get("trailingPE"),
        "dividend_yield": (
            round(info["dividendYield"] * 100, 2) if info.get("dividendYield") else None
        ),
        "market_cap": info.get("marketCap"),
        "analyst_consensus": info.get("recommendationKey"),
        "num_analyst_opinions": info.get("numberOfAnalystOpinions"),
        "target_mean_price": info.get("targetMeanPrice"),
        "business_summary": summary,
        "currency": info.get("currency"),
    }