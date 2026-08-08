from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import db.database as db
from services import ai_service

WELCOME_TEXT = """👋 Hey, I'm *Atlas* — your financial analyst on Telegram.

I can:
📈 Give you live prices for stocks, indices, and crypto — "What's the Reliance share price?"
🔎 Pull up company research — P/E, dividend yield, sector, analyst consensus
📰 Explain market moves with real news — "Why is Nifty falling today?"
📑 Summarize earnings reports — just upload a PDF
🎤 Take voice notes instead of typing
☀️ Send you a morning briefing at 8 AM IST — or run /briefing anytime

Just talk to me like you would a sharp friend who happens to know markets. What's on your mind?

_I share market data and general information — not personalized investment advice._"""

HELP_TEXT = """*Commands*
/start — intro and what I can do
/help — this message
/briefing — get a market briefing right now

*Or just talk to me* — ask about a stock price, company fundamentals, market news, upload a PDF earnings report, or send a voice note."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await db.touch_user(chat_id)
    await update.message.reply_text(WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)


async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    text = await ai_service.build_briefing()
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(text)
