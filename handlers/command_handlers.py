from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import db.database as db
from handlers import menu_handlers
from services import ai_service

WELCOME_TEXT = """👋 Hey, I'm *Atlas* — your financial analyst on Telegram.

I can:
📈 Give you live prices for stocks, indices, and crypto — "What's the Reliance share price?"
🔎 Pull up company research — P/E, dividend yield, sector, analyst consensus
📰 Explain market moves with real news — "Why is Nifty falling today?"
📑 Summarize earnings reports — just upload a PDF
🎤 Take voice notes instead of typing
🖼️ Analyze images of charts and financial documents
📬 Check your Gmail inbox and read emails
📅 View your Google Calendar events
☀️ Send you a morning briefing at 8 AM IST — or run /briefing anytime
🎛️ Interactive menus for easy navigation

Just talk to me like you would a sharp friend who happens to know markets. What's on your mind?

_I share market data and general information — not personalized investment advice._"""

HELP_TEXT = """*Commands*
/start — intro and what I can do
/help — this message
/menu — show interactive menu
/briefing — get a market briefing right now

*Gmail Commands*
/gmail_auth — authenticate with Gmail
/gmail_code <code> — complete Gmail authentication
/gmail_inbox [count] — show recent emails (default: 5)
/gmail_read <number> — read full email content

*Calendar Commands*
/calendar_auth — authenticate with Google Calendar
/calendar_code <code> — complete Calendar authentication
/calendar_today — show today's events
/calendar_week [days] — show upcoming events (default: 7 days)

*Or just talk to me* — ask about a stock price, company fundamentals, market news, upload a PDF earnings report, send a voice note, or share an image.

You can also say things like:
- "Show me the menu"
- "Check my emails"
- "What's on my calendar today?"
- "Give me a market briefing"
- "Latest news"
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await db.touch_user(chat_id)
    await update.message.reply_text(WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN)
    await menu_handlers.show_main_menu(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the interactive menu."""
    await menu_handlers.show_main_menu(update, context)


async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    text = await ai_service.build_briefing()
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(text)
