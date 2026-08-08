"""
FastAPI application: health checks, web UI, REST API, and Telegram bot lifecycle.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters
 
import config
import db.database as db
import scheduler as scheduler_module
from handlers import command_handlers, google_handlers, menu_handlers
from handlers.document_handler import handle_document
from handlers.image_handler import handle_image
from handlers.message_handler import handle_text, process_user_message
from handlers.voice_handler import handle_voice
from services import ai_service, market_service, news_service

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
PING_INTERVAL_SECONDS = 10 * 60

_telegram_app: Optional[Application] = None
_self_ping_task: Optional[asyncio.Task] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: int = Field(default=0, description="Web demo session id (stored as chat_id)")


class ChatResponse(BaseModel):
    reply: str
    session_id: int


async def _self_ping_loop() -> None:
    if not config.SELF_PING_URL:
        logger.info("SELF_PING_URL not set — skipping keep-alive pinger.")
        return
    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            await asyncio.sleep(PING_INTERVAL_SECONDS)
            try:
                resp = await client.get(config.SELF_PING_URL)
                logger.info(f"Self-ping -> {resp.status_code}")
            except Exception as exc:
                logger.warning(f"Self-ping failed: {exc}")


def _build_telegram_app() -> Application:
    application = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )
    application.add_handler(CommandHandler("start", command_handlers.start))
    application.add_handler(CommandHandler("help", command_handlers.help_command))
    application.add_handler(CommandHandler("menu", command_handlers.menu_command))
    application.add_handler(CommandHandler("briefing", command_handlers.briefing_command))
    
    # Gmail commands
    application.add_handler(CommandHandler("gmail_auth", google_handlers.gmail_auth))
    application.add_handler(CommandHandler("gmail_code", google_handlers.gmail_code))
    application.add_handler(CommandHandler("gmail_inbox", google_handlers.gmail_inbox))
    application.add_handler(CommandHandler("gmail_read", google_handlers.gmail_read))
    
    # Calendar commands
    application.add_handler(CommandHandler("calendar_auth", google_handlers.calendar_auth))
    application.add_handler(CommandHandler("calendar_code", google_handlers.calendar_code))
    application.add_handler(CommandHandler("calendar_today", google_handlers.calendar_today))
    application.add_handler(CommandHandler("calendar_week", google_handlers.calendar_week))
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(menu_handlers.handle_callback_query))
    
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


async def _run_telegram_polling(application: Application) -> None:
    await application.initialize()
    await application.start()
    scheduler_module.start_scheduler(application)
    logger.info("Telegram bot polling started.")
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _telegram_app, _self_ping_task

    if not config.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — AI features will fail until configured.")

    await db.init_db()
    logger.info("Database initialized.")

    if config.TELEGRAM_BOT_TOKEN:
        _telegram_app = _build_telegram_app()
        asyncio.create_task(_run_telegram_polling(_telegram_app))
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot disabled.")

    _self_ping_task = asyncio.create_task(_self_ping_loop())
    logger.info("Atlas FastAPI is ready.")
    yield

    if _self_ping_task:
        _self_ping_task.cancel()
    await db.close_db()
    logger.info("Shutting down Atlas.")


app = FastAPI(
    title="Atlas — AI Financial Assistant",
    description="Telegram bot + web UI for live markets, news, and PDF intelligence.",
    version="1.0.0",
    lifespan=lifespan,
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": "atlas",
    }


@app.get("/")
async def index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Atlas API is running. Open /docs for API reference."}


@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(body: ChatRequest):
    chat_id = body.session_id or 900_000_001
    try:
        reply = await process_user_message(None, None, body.message.strip(), chat_id=chat_id)
    except Exception as exc:
        logger.error(f"Web chat failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to generate reply") from exc
    return ChatResponse(reply=reply, session_id=chat_id)


@app.get("/api/briefing")
async def api_briefing():
    try:
        return {"briefing": await ai_service.build_briefing()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/quote/{symbol}")
async def api_quote(symbol: str):
    quote = await asyncio.to_thread(market_service.get_quote, symbol)
    if not quote.get("found"):
        raise HTTPException(status_code=404, detail=f"No quote for {symbol}")
    return quote


@app.get("/api/research/{symbol}")
async def api_research(symbol: str):
    data = await asyncio.to_thread(market_service.get_fundamentals, symbol)
    if not data.get("found"):
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")
    return data


@app.get("/api/news")
async def api_news(q: str = "Indian stock market", limit: int = 5):
    items = await asyncio.to_thread(news_service.fetch_news, q, min(limit, 10))
    return {"query": q, "items": items}


@app.post("/api/pdf")
async def api_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a PDF file.")

    import os
    import tempfile

    from services import pdf_service

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        text = await asyncio.to_thread(pdf_service.extract_text, tmp_path)
        if not text.strip():
            raise HTTPException(status_code=400, detail="PDF has no extractable text.")
        summary = await ai_service.summarize_pdf(text)
        return {"summary": summary}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
