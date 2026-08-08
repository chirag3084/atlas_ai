"""Voice note handling for Telegram."""

import logging
import os
import tempfile

from telegram import Update
from telegram.ext import ContextTypes

from handlers.message_handler import process_user_message
from services import ai_service

logger = logging.getLogger(__name__)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice:
        return

    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    voice = update.message.voice
    telegram_file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await telegram_file.download_to_drive(tmp_path)
        transcript = await ai_service.transcribe_voice(tmp_path)
    except Exception as exc:
        logger.error(f"Voice transcription failed: {exc}")
        await update.message.reply_text(
            "Couldn't quite catch that voice note 🎤 — mind trying again, or just typing it?"
        )
        return
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if not transcript or not transcript.strip():
        await update.message.reply_text("I heard silence there — could you try that again?")
        return

    await process_user_message(update, context, transcript)
