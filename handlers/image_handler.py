"""Image handling for Telegram - vision analysis using Groq's multimodal models."""

import base64
import logging
import os
import tempfile

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from handlers.message_handler import process_user_message
from services import ai_service

logger = logging.getLogger(__name__)


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo:
        return

    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Get the largest photo (highest resolution)
    photo = update.message.photo[-1]
    telegram_file = await context.bot.get_file(photo.file_id)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await telegram_file.download_to_drive(tmp_path)
        
        # Convert image to base64 for API
        with open(tmp_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Analyze the image
        analysis = await ai_service.analyze_image(base64_image)
        
        if not analysis or not analysis.strip():
            await update.message.reply_text(
                "I couldn't quite make out what's in that image 🖼️ — mind trying again?"
            )
            return
        
        # Process the analysis as if it were a user message
        await process_user_message(update, context, f"[Image analysis: {analysis}]")
        
    except Exception as exc:
        logger.error(f"Image analysis failed: {exc}")
        await update.message.reply_text(
            "Couldn't process that image — mind trying again, or describing what you see?"
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
