"""
Sends the morning briefing to every known user at a fixed local time
(default 8:00 AM IST) using APScheduler running inside the bot's own
asyncio event loop.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.constants import ParseMode
from telegram.ext import Application

import config
import db.database as db
from services import ai_service

logger = logging.getLogger(__name__)


async def _send_daily_briefings(application: Application) -> None:
    chat_ids = await db.all_chat_ids()
    if not chat_ids:
        return

    text = await ai_service.build_briefing()
    logger.info(f"Sending daily briefing to {len(chat_ids)} user(s).")

    for chat_id in chat_ids:
        try:
            await application.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to send briefing to {chat_id}: {exc}")


def start_scheduler(application: Application) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    scheduler.add_job(
        _send_daily_briefings,
        trigger=CronTrigger(hour=config.BRIEFING_HOUR, minute=config.BRIEFING_MINUTE),
        args=[application],
        id="daily_briefing",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"Daily briefing scheduled for {config.BRIEFING_HOUR:02d}:{config.BRIEFING_MINUTE:02d} {config.TIMEZONE}."
    )
    return scheduler