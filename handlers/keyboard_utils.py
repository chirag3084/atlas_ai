"""Inline keyboard utilities for interactive menus and quick replies."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional, Tuple


def create_main_menu() -> InlineKeyboardMarkup:
    """Create the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📈 Market Data", callback_data="menu_market"),
            InlineKeyboardButton("📰 News", callback_data="menu_news"),
        ],
        [
            InlineKeyboardButton("📬 Gmail", callback_data="menu_gmail"),
            InlineKeyboardButton("📅 Calendar", callback_data="menu_calendar"),
        ],
        [
            InlineKeyboardButton("☀️ Briefing", callback_data="menu_briefing"),
            InlineKeyboardButton("❓ Help", callback_data="menu_help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_market_menu() -> InlineKeyboardMarkup:
    """Create market data submenu."""
    keyboard = [
        [
            InlineKeyboardButton("💹 Live Quote", callback_data="market_quote"),
            InlineKeyboardButton("🔍 Research", callback_data="market_research"),
        ],
        [
            InlineKeyboardButton("📊 Indices", callback_data="market_indices"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_news_menu() -> InlineKeyboardMarkup:
    """Create news submenu."""
    keyboard = [
        [
            InlineKeyboardButton("🇮🇳 Indian Markets", callback_data="news_india"),
            InlineKeyboardButton("🌍 Global Markets", callback_data="news_global"),
        ],
        [
            InlineKeyboardButton("🔥 Trending", callback_data="news_trending"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_gmail_menu() -> InlineKeyboardMarkup:
    """Create Gmail submenu."""
    keyboard = [
        [
            InlineKeyboardButton("📥 Inbox", callback_data="gmail_inbox"),
            InlineKeyboardButton("📧 Compose", callback_data="gmail_compose"),
        ],
        [
            InlineKeyboardButton("🔐 Auth", callback_data="gmail_auth"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_calendar_menu() -> InlineKeyboardMarkup:
    """Create Calendar submenu."""
    keyboard = [
        [
            InlineKeyboardButton("📅 Today", callback_data="calendar_today"),
            InlineKeyboardButton("📆 This Week", callback_data="calendar_week"),
        ],
        [
            InlineKeyboardButton("🔐 Auth", callback_data="calendar_auth"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_quick_reply_keyboard() -> ReplyKeyboardMarkup:
    """Create a quick reply keyboard for common actions."""
    keyboard = [
        [
            KeyboardButton("📈 Stock Price"),
            KeyboardButton("🔍 Company Info"),
        ],
        [
            KeyboardButton("📰 Market News"),
            KeyboardButton("☀️ Daily Briefing"),
        ],
        [
            KeyboardButton("📬 Check Gmail"),
            KeyboardButton("📅 Calendar"),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def create_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Create a yes/no confirmation keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ No", callback_data=f"cancel_{action}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_pagination_keyboard(prefix: str, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Create pagination keyboard for lists."""
    keyboard = []
    
    if current_page > 1:
        keyboard.append([InlineKeyboardButton("⬅️ Previous", callback_data=f"{prefix}_page_{current_page-1}")])
    
    keyboard.append([InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="page_info")])
    
    if current_page < total_pages:
        keyboard.append([InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}_page_{current_page+1}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(keyboard)


def create_stock_action_keyboard(symbol: str) -> InlineKeyboardMarkup:
    """Create action keyboard for stock interactions."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Chart", callback_data=f"stock_chart_{symbol}"),
            InlineKeyboardButton("🔍 Details", callback_data=f"stock_details_{symbol}"),
        ],
        [
            InlineKeyboardButton("📰 News", callback_data=f"stock_news_{symbol}"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_market"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_email_action_keyboard(email_id: str) -> InlineKeyboardMarkup:
    """Create action keyboard for email interactions."""
    keyboard = [
        [
            InlineKeyboardButton("📧 Reply", callback_data=f"email_reply_{email_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"email_delete_{email_id}"),
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="menu_gmail"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_time_range_keyboard() -> InlineKeyboardMarkup:
    """Create time range selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("1 Day", callback_data="time_1d"),
            InlineKeyboardButton("1 Week", callback_data="time_1w"),
        ],
        [
            InlineKeyboardButton("1 Month", callback_data="time_1m"),
            InlineKeyboardButton("3 Months", callback_data="time_3m"),
        ],
        [
            InlineKeyboardButton("1 Year", callback_data="time_1y"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
