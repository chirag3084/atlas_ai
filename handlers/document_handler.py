"""PDF upload handling for Telegram."""

import asyncio
import logging
import os
import tempfile

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import db.database as db
from services import ai_service, pdf_service

logger = logging.getLogger(__name__)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.document:
        return

    document = update.message.document
    if document.mime_type != "application/pdf" and not document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text(
            "I can only read PDFs right now 📄 — try uploading the report as a .pdf."
        )
        return

    chat_id = update.effective_chat.id
    await db.touch_user(chat_id)
    await context.bot.send_chat_action(chat_id=chat_id, action="upload_document")
    status_msg = await update.message.reply_text("Reading through this now… 🔍")

    telegram_file = await context.bot.get_file(document.file_id)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await telegram_file.download_to_drive(tmp_path)
        text = await asyncio.to_thread(pdf_service.extract_text, tmp_path)

        if not text.strip():
            await status_msg.edit_text(
                "That PDF looks empty or scanned as images — I can only read selectable text right now."
            )
            return

        summary = await ai_service.summarize_pdf(text)
        await db.save_message(chat_id, "user", "[Uploaded PDF document]")
        await db.save_message(chat_id, "assistant", summary)
        await status_msg.edit_text(summary, parse_mode=ParseMode.MARKDOWN)
    except Exception as exc:
        logger.error(f"PDF handling failed: {exc}")
        await status_msg.edit_text("Couldn't process that PDF — mind trying again?")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
