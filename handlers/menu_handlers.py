"""Interactive menu handlers with inline buttons and callback queries."""

import asyncio
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler

from handlers import keyboard_utils
from services import ai_service, market_service, news_service, gmail_service, calendar_service

logger = logging.getLogger(__name__)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main interactive menu."""
    if update.message:
        await update.message.reply_text(
            "🏠 **Main Menu**\n\nWhat would you like to do?",
            reply_markup=keyboard_utils.create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "🏠 **Main Menu**\n\nWhat would you like to do?",
            reply_markup=keyboard_utils.create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )


async def show_market_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show market data submenu."""
    query = update.callback_query
    await query.edit_message_text(
        "📈 **Market Data**\n\nSelect an option:",
        reply_markup=keyboard_utils.create_market_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def show_news_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show news submenu."""
    query = update.callback_query
    await query.edit_message_text(
        "📰 **News**\n\nSelect news category:",
        reply_markup=keyboard_utils.create_news_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def show_gmail_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show Gmail submenu."""
    query = update.callback_query
    await query.edit_message_text(
        "📬 **Gmail**\n\nSelect an option:",
        reply_markup=keyboard_utils.create_gmail_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def show_calendar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show Calendar submenu."""
    query = update.callback_query
    await query.edit_message_text(
        "📅 **Calendar**\n\nSelect an option:",
        reply_markup=keyboard_utils.create_calendar_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_briefing_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle briefing button click."""
    query = update.callback_query
    await query.answer("Generating briefing...")
    
    try:
        briefing = await ai_service.build_briefing()
        await query.edit_message_text(
            f"☀️ **Market Briefing**\n\n{briefing}",
            reply_markup=keyboard_utils.create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Briefing failed: {e}")
        await query.edit_message_text(
            "❌ Failed to generate briefing. Please try again.",
            reply_markup=keyboard_utils.create_main_menu()
        )


async def handle_help_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle help button click."""
    query = update.callback_query
    help_text = """❓ **Help**

**Quick Commands:**
/menu — Show this menu
/quote <symbol> — Get stock price
/research <symbol> — Get company info
/news <query> — Search news

**Natural Language:**
Just ask me anything! Try:
- "What's the Reliance share price?"
- "Show me Nifty performance"
- "Latest market news"
- "My calendar today"

**Features:**
📈 Market data & analysis
📰 Real-time news
📬 Gmail integration
📅 Google Calendar
📑 PDF analysis
🎤 Voice notes
🖼️ Image analysis"""

    await query.edit_message_text(
        help_text,
        reply_markup=keyboard_utils.create_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_market_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle market quote button - prompt for symbol."""
    query = update.callback_query
    await query.edit_message_text(
        "📈 **Stock Quote**\n\nPlease send the stock symbol (e.g., RELIANCE, TCS, INFY):",
        reply_markup=keyboard_utils.create_main_menu()
    )


async def handle_market_research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle market research button - prompt for symbol."""
    query = update.callback_query
    await query.edit_message_text(
        "🔍 **Company Research**\n\nPlease send the stock symbol for detailed analysis (e.g., RELIANCE, TCS):",
        reply_markup=keyboard_utils.create_main_menu()
    )


async def handle_market_indices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle market indices button - show major indices."""
    query = update.callback_query
    await query.answer("Fetching indices...")
    
    try:
        indices = await asyncio.to_thread(market_service.get_quote, "nifty")
        sensex = await asyncio.to_thread(market_service.get_quote, "sensex")
        
        message = f"📊 **Market Indices**\n\n"
        message += f"**NIFTY 50:** {indices.get('price', 'N/A')} ({indices.get('change_pct', 0):+.2f}%)\n"
        message += f"**SENSEX:** {sensex.get('price', 'N/A')} ({sensex.get('change_pct', 0):+.2f}%)\n"
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard_utils.create_market_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Indices failed: {e}")
        await query.edit_message_text(
            "❌ Failed to fetch indices. Please try again.",
            reply_markup=keyboard_utils.create_market_menu()
        )


async def handle_news_india(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle India news button."""
    query = update.callback_query
    await query.answer("Fetching Indian market news...")
    
    try:
        items = await asyncio.to_thread(news_service.fetch_news, "Indian stock market", 5)
        message = "🇮🇳 **Indian Market News**\n\n"
        
        for i, item in enumerate(items, 1):
            message += f"{i}. {item.get('title', 'No title')}\n"
            message += f"   {item.get('source', 'Unknown')}\n\n"
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard_utils.create_news_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"India news failed: {e}")
        await query.edit_message_text(
            "❌ Failed to fetch news. Please try again.",
            reply_markup=keyboard_utils.create_news_menu()
        )


async def handle_news_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle global news button."""
    query = update.callback_query
    await query.answer("Fetching global market news...")
    
    try:
        items = await asyncio.to_thread(news_service.fetch_news, "global stock market", 5)
        message = "🌍 **Global Market News**\n\n"
        
        for i, item in enumerate(items, 1):
            message += f"{i}. {item.get('title', 'No title')}\n"
            message += f"   {item.get('source', 'Unknown')}\n\n"
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard_utils.create_news_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Global news failed: {e}")
        await query.edit_message_text(
            "❌ Failed to fetch news. Please try again.",
            reply_markup=keyboard_utils.create_news_menu()
        )


async def handle_news_trending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle trending news button."""
    query = update.callback_query
    await query.answer("Fetching trending news...")
    
    try:
        items = await asyncio.to_thread(news_service.fetch_news, "trending stocks", 5)
        message = "🔥 **Trending News**\n\n"
        
        for i, item in enumerate(items, 1):
            message += f"{i}. {item.get('title', 'No title')}\n"
            message += f"   {item.get('source', 'Unknown')}\n\n"
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard_utils.create_news_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Trending news failed: {e}")
        await query.edit_message_text(
            "❌ Failed to fetch news. Please try again.",
            reply_markup=keyboard_utils.create_news_menu()
        )


async def handle_gmail_inbox_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Gmail inbox button."""
    query = update.callback_query
    chat_id = update.effective_chat.id
    
    if not gmail_service.is_authenticated(chat_id):
        await query.edit_message_text(
            "🔐 **Authentication Required**\n\nPlease authenticate with Gmail first using /gmail_auth",
            reply_markup=keyboard_utils.create_gmail_menu()
        )
        return
    
    await query.answer("Fetching inbox...")
    
    try:
        emails = gmail_service.get_emails(chat_id, max_results=5)
        
        if not emails:
            await query.edit_message_text(
                "📭 Your inbox is empty!",
                reply_markup=keyboard_utils.create_gmail_menu()
            )
            return
        
        message = f"📬 **Recent Emails ({len(emails)})**\n\n"
        for i, email in enumerate(emails, 1):
            from_name = email['from'].split('<')[0].strip() if '<' in email['from'] else email['from']
            message += f"{i}. {email['subject']}\n"
            message += f"   From: {from_name}\n\n"
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard_utils.create_gmail_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Gmail inbox failed: {e}")
        await query.edit_message_text(
            "❌ Failed to fetch emails. Please try again.",
            reply_markup=keyboard_utils.create_gmail_menu()
        )


async def handle_gmail_auth_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Gmail auth button."""
    query = update.callback_query
    chat_id = update.effective_chat.id
    
    if gmail_service.is_authenticated(chat_id):
        await query.edit_message_text(
            "✅ You're already authenticated with Gmail!",
            reply_markup=keyboard_utils.create_gmail_menu()
        )
        return
    
    try:
        auth_url = gmail_service.create_auth_url(chat_id)
        message = (
            "🔗 **Gmail Authentication**\n\n"
            "1. Click this link:\n"
            f"{auth_url}\n\n"
            "2. Sign in and grant permissions\n"
            "3. Copy the code and send: `/gmail_code <code>`"
        )
        await query.edit_message_text(
            message,
            reply_markup=keyboard_utils.create_gmail_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Gmail auth failed: {e}")
        await query.edit_message_text(
            "❌ Failed to create authorization URL.",
            reply_markup=keyboard_utils.create_gmail_menu()
        )


async def handle_calendar_today_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle calendar today button."""
    query = update.callback_query
    chat_id = update.effective_chat.id
    
    if not calendar_service.is_authenticated(chat_id):
        await query.edit_message_text(
            "🔐 **Authentication Required**\n\nPlease authenticate with Calendar first using /calendar_auth",
            reply_markup=keyboard_utils.create_calendar_menu()
        )
        return
    
    await query.answer("Fetching today's events...")
    
    try:
        events = calendar_service.get_today_events(chat_id)
        
        if not events:
            await query.edit_message_text(
                "📅 No events scheduled for today!",
                reply_markup=keyboard_utils.create_calendar_menu()
            )
            return
        
        message = f"📅 **Today's Events ({len(events)})**\n\n"
        for event in events:
            message += f"• {event['summary']}\n"
            if event['start']:
                message += f"  Time: {event['start']}\n"
            if event['location']:
                message += f"  Location: {event['location']}\n"
            message += "\n"
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard_utils.create_calendar_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Calendar today failed: {e}")
        await query.edit_message_text(
            "❌ Failed to fetch events. Please try again.",
            reply_markup=keyboard_utils.create_calendar_menu()
        )


async def handle_calendar_week_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle calendar week button."""
    query = update.callback_query
    chat_id = update.effective_chat.id
    
    if not calendar_service.is_authenticated(chat_id):
        await query.edit_message_text(
            "🔐 **Authentication Required**\n\nPlease authenticate with Calendar first using /calendar_auth",
            reply_markup=keyboard_utils.create_calendar_menu()
        )
        return
    
    await query.answer("Fetching week's events...")
    
    try:
        events = calendar_service.get_events(chat_id, days=7)
        
        if not events:
            await query.edit_message_text(
                "📅 No events scheduled for this week!",
                reply_markup=keyboard_utils.create_calendar_menu()
            )
            return
        
        message = f"📅 **This Week's Events ({len(events)})**\n\n"
        for event in events:
            message += f"• {event['summary']}\n"
            if event['start']:
                message += f"  Time: {event['start']}\n"
            message += "\n"
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard_utils.create_calendar_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Calendar week failed: {e}")
        await query.edit_message_text(
            "❌ Failed to fetch events. Please try again.",
            reply_markup=keyboard_utils.create_calendar_menu()
        )


async def handle_calendar_auth_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle calendar auth button."""
    query = update.callback_query
    chat_id = update.effective_chat.id
    
    if calendar_service.is_authenticated(chat_id):
        await query.edit_message_text(
            "✅ You're already authenticated with Calendar!",
            reply_markup=keyboard_utils.create_calendar_menu()
        )
        return
    
    try:
        auth_url = calendar_service.create_auth_url(chat_id)
        message = (
            "🔗 **Calendar Authentication**\n\n"
            "1. Click this link:\n"
            f"{auth_url}\n\n"
            "2. Sign in and grant permissions\n"
            "3. Copy the code and send: `/calendar_code <code>`"
        )
        await query.edit_message_text(
            message,
            reply_markup=keyboard_utils.create_calendar_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Calendar auth failed: {e}")
        await query.edit_message_text(
            "❌ Failed to create authorization URL.",
            reply_markup=keyboard_utils.create_calendar_menu()
        )


# Callback query mapping
CALLBACK_HANDLERS = {
    "menu_main": show_main_menu,
    "menu_market": show_market_menu,
    "menu_news": show_news_menu,
    "menu_gmail": show_gmail_menu,
    "menu_calendar": show_calendar_menu,
    "menu_briefing": handle_briefing_button,
    "menu_help": handle_help_button,
    "market_quote": handle_market_quote,
    "market_research": handle_market_research,
    "market_indices": handle_market_indices,
    "news_india": handle_news_india,
    "news_global": handle_news_global,
    "news_trending": handle_news_trending,
    "gmail_inbox": handle_gmail_inbox_button,
    "gmail_auth": handle_gmail_auth_button,
    "calendar_today": handle_calendar_today_button,
    "calendar_week": handle_calendar_week_button,
    "calendar_auth": handle_calendar_auth_button,
}


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline buttons."""
    query = update.callback_query
    callback_data = query.data
    
    if not callback_data:
        await query.answer("Invalid callback")
        return
    
    # Handle pagination
    if "_page_" in callback_data:
        parts = callback_data.split("_page_")
        prefix = parts[0]
        page = int(parts[1])
        # Handle pagination logic here
        await query.answer(f"Page {page}")
        return
    
    # Handle stock actions
    if callback_data.startswith("stock_"):
        # Handle stock-specific actions
        await query.answer("Stock action")
        return
    
    # Handle email actions
    if callback_data.startswith("email_"):
        # Handle email-specific actions
        await query.answer("Email action")
        return
    
    # Handle confirmations
    if callback_data.startswith("confirm_"):
        action = callback_data.replace("confirm_", "")
        await query.answer(f"Confirmed: {action}")
        return
    
    if callback_data.startswith("cancel_"):
        action = callback_data.replace("cancel_", "")
        await query.answer(f"Cancelled: {action}")
        await show_main_menu(update, context)
        return
    
    # Handle menu navigation
    handler = CALLBACK_HANDLERS.get(callback_data)
    if handler:
        await handler(update, context)
    else:
        await query.answer("Unknown action")
        await show_main_menu(update, context)
