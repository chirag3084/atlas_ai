"""Core text message pipeline — shared by Telegram and web UI."""

import logging
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import db.database as db
from handlers import menu_handlers
from services import ai_service, intent_service

logger = logging.getLogger(__name__)


async def process_user_message(
    update: Optional[Update],
    context: Optional[ContextTypes.DEFAULT_TYPE],
    text: str,
    *,
    chat_id: Optional[int] = None,
) -> str:
    """Handle a user message and return the assistant reply."""
    if chat_id is None:
        if update and update.effective_chat:
            chat_id = update.effective_chat.id
        else:
            raise ValueError("chat_id required when update is not provided")

    await db.touch_user(chat_id)
    await db.save_message(chat_id, "user", text)

    if update and context:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    profile = await db.get_profile(chat_id)
    history = await db.recent_messages(chat_id)
    intent, intent_data = intent_service.detect_intent(text)

    # Handle special intents that don't need AI
    if intent == "menu":
        if update and context:
            await menu_handlers.show_main_menu(update, context)
        return "Menu shown"
    
    if intent == "briefing":
        try:
            briefing = await ai_service.build_briefing()
            if update and update.message:
                await update.message.reply_text(briefing, parse_mode=ParseMode.MARKDOWN)
            await db.save_message(chat_id, "assistant", briefing)
            return briefing
        except Exception as exc:
            logger.error(f"Briefing failed: {exc}")
            reply = "Failed to generate briefing. Please try again."
            if update and update.message:
                await update.message.reply_text(reply)
            return reply
    
    if intent == "gmail":
        if update and context:
            await menu_handlers.show_gmail_menu(update, context)
        return "Gmail menu shown"
    
    if intent == "calendar":
        if update and context:
            await menu_handlers.show_calendar_menu(update, context)
        return "Calendar menu shown"

    try:
        reply = await ai_service.generate_reply(
            text,
            chat_id=chat_id,
            profile=profile,
            history=history,
            intent=intent,
            intent_data=intent_data,
        )
    except Exception as exc:
        logger.error(f"AI reply failed: {exc}")
        reply = "Something went wrong on my end — give me a sec and try again? 🙏"

    await db.save_message(chat_id, "assistant", reply)

    if update and update.message:
        try:
            await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(reply)

    return reply


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    await process_user_message(update, context, update.message.text.strip())
