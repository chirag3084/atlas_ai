"""Groq LLM, Whisper transcription, and response formatting."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx

import config
from services import market_service, news_service

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

IMAGE_ANALYSIS_PROMPT = """You are Atlas — a financial analyst. Analyze this image and describe:
1. What type of content it shows (chart, document, screenshot, etc.)
2. Key financial data visible (prices, percentages, trends)
3. Any notable patterns or insights
4. If it's a chart, describe the trend and key levels
Keep it concise and factual. If the image is unclear or not financial-related, say so."""

SYSTEM_PROMPT = """You are Atlas — a warm, witty Indian financial analyst on Telegram.
You explain markets clearly, use light emojis, and sound like a smart friend — not a robot.
Keep replies concise (under 200 words unless summarizing a PDF).
Use ₹ for INR prices when relevant.
Never give personalized investment advice — share data and general information only.
If market data or news is provided in context, ground your answer in it."""

PDF_SUMMARY_PROMPT = """Summarize this financial document as an Executive Summary with these sections:
📑 Title (infer from content)
• Revenue (with YoY if available)
• Net Profit (with YoY if available)
• EBITDA (if mentioned)
• Key Risks
• Analyst Verdict (Bullish/Neutral/Bearish based on tone)
Use bullet points and emojis. Be factual — only state numbers present in the text."""


async def _groq_chat(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> str:
    model = model or config.GROQ_MODEL_PRIMARY
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.warning(f"Primary model failed ({model}): {exc}")
            if model != config.GROQ_MODEL_FALLBACK:
                return await _groq_chat(
                    messages,
                    model=config.GROQ_MODEL_FALLBACK,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            raise


async def transcribe_voice(file_path: str) -> str:
    headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(file_path, "rb") as audio_file:
            files = {"file": ("voice.ogg", audio_file, "audio/ogg")}
            data = {"model": config.GROQ_WHISPER_MODEL}
            resp = await client.post(GROQ_AUDIO_URL, headers=headers, files=files, data=data)
            resp.raise_for_status()
            return resp.json().get("text", "").strip()


async def analyze_image(base64_image: str) -> str:
    """Analyze an image using Groq's vision-capable models."""
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Use a vision-capable model (llava-v1.5-7b-4096-preview or similar)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": IMAGE_ANALYSIS_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ]
    
    payload = {
        "model": config.GROQ_VISION_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 500,
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.warning(f"Image analysis failed: {exc}")
            # Fallback: try with a different model or return error message
            return "I couldn't analyze this image. Please describe what you'd like to know about it."


async def summarize_pdf(text: str) -> str:
    messages = [
        {"role": "system", "content": PDF_SUMMARY_PROMPT},
        {"role": "user", "content": f"Document text:\n\n{text}"},
    ]
    return await _groq_chat(messages, model=config.GROQ_MODEL_FALLBACK, max_tokens=1200)


def _format_quote(q: Dict[str, Any]) -> str:
    if not q.get("found"):
        return f"No live quote found for {q.get('symbol', 'that symbol')}."
    sym = q["symbol"]
    price = q["price"]
    change = q.get("change_pct")
    curr = q.get("currency", "")
    prefix = "₹" if curr == "INR" else ("$" if curr == "USD" else "")
    change_str = f" ({'+' if change and change > 0 else ''}{change}% today)" if change is not None else ""
    range_str = ""
    if q.get("year_low") and q.get("year_high"):
        range_str = f" 52-week range: {prefix}{q['year_low']}–{prefix}{q['year_high']}."
    return f"{sym}: {prefix}{price}{change_str}.{range_str}"


def _format_fundamentals(f: Dict[str, Any]) -> str:
    if not f.get("found"):
        return f"No fundamentals found for {f.get('symbol', 'that symbol')}."
    cap = f.get("market_cap")
    cap_str = f"{cap / 1e7:.1f} Cr" if cap and f.get("currency") == "INR" else str(cap)
    return (
        f"Company: {f.get('name')} ({f['symbol']})\n"
        f"Sector: {f.get('sector')} / {f.get('industry')}\n"
        f"P/E: {f.get('pe_ratio')} | Dividend Yield: {f.get('dividend_yield')}%\n"
        f"Market Cap: {cap_str} | Analyst: {f.get('analyst_consensus')}\n"
        f"Summary: {f.get('business_summary', '')}"
    )


def _format_news(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "No recent headlines found."
    lines = ["Recent headlines:"]
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item.get('title')} ({item.get('source', '')})")
    return "\n".join(lines)


async def build_briefing() -> str:
    indices = await asyncio.gather(
        asyncio.to_thread(market_service.get_quote, "nifty"),
        asyncio.to_thread(market_service.get_quote, "sensex"),
    )
    headlines = await asyncio.to_thread(news_service.fetch_news, "Indian stock market", 5)
    context = "\n".join([_format_quote(q) for q in indices]) + "\n" + _format_news(headlines)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Write a morning market briefing for India. Include Nifty & Sensex levels, "
                f"day change, and top headlines. Context:\n{context}"
            ),
        },
    ]
    return await _groq_chat(messages, max_tokens=600)


async def generate_reply(
    user_text: str,
    *,
    chat_id: int,
    profile: Dict[str, Any],
    history: List[Dict[str, str]],
    intent: str,
    intent_data: Dict[str, Any],
) -> str:
    context_parts = []
    ticker = intent_data.get("ticker")

    if intent == "quote" and ticker:
        quote = await asyncio.to_thread(market_service.get_quote, ticker)
        context_parts.append(_format_quote(quote))
    elif intent == "research" and ticker:
        fund = await asyncio.to_thread(market_service.get_fundamentals, ticker)
        context_parts.append(_format_fundamentals(fund))
    elif intent == "news":
        query = intent_data.get("query", "stock market India")
        items = await asyncio.to_thread(news_service.fetch_news, query, 5)
        context_parts.append(_format_news(items))
        if ticker:
            quote = await asyncio.to_thread(market_service.get_quote, ticker)
            context_parts.append(_format_quote(quote))

    profile_str = json.dumps(profile) if profile else "{}"
    context_block = "\n".join(context_parts) if context_parts else "No extra market data fetched."

    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append(
        {
            "role": "system",
            "content": f"User profile (remember across sessions): {profile_str}\nContext data:\n{context_block}",
        }
    )
    for msg in history[-config.MAX_HISTORY_MESSAGES :]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_text})

    reply = await _groq_chat(messages)

    # Extract profile updates from conversation (simple heuristic)
    await _maybe_update_profile(chat_id, user_text, reply, profile)

    return reply


async def _maybe_update_profile(
    chat_id: int,
    user_text: str,
    reply: str,
    profile: Dict[str, Any],
) -> None:
    """Ask the model to extract durable user facts, merge into profile."""
    import db.database as db

    extract_prompt = (
        "From the user message below, extract ONLY durable facts to remember "
        "(name, role/job, interests, preferred stocks/sectors). "
        'Return JSON object with keys among: name, role, interests, notes. '
        "Return {} if nothing new. User message:\n"
        f"{user_text}"
    )
    try:
        raw = await _groq_chat(
            [{"role": "user", "content": extract_prompt}],
            temperature=0,
            max_tokens=150,
        )
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            updates = json.loads(raw[start:end])
            if isinstance(updates, dict) and updates:
                await db.update_profile(chat_id, updates)
    except Exception as exc:
        logger.debug(f"Profile extraction skipped: {exc}")
