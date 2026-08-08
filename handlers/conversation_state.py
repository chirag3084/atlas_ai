"""Conversation state management for multi-step interactions."""

import json
import logging
from typing import Any, Dict, Optional

import db.database as db

logger = logging.getLogger(__name__)

# Conversation states
STATE_NONE = "none"
STATE_AWAITING_GMAIL_CODE = "awaiting_gmail_code"
STATE_AWAITING_CALENDAR_CODE = "awaiting_calendar_code"
STATE_AWAITING_STOCK_SYMBOL = "awaiting_stock_symbol"
STATE_AWAITING_EMAIL_COMPOSE = "awaiting_email_compose"


async def set_user_state(chat_id: int, state: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Set the conversation state for a user."""
    profile = await db.get_profile(chat_id)
    profile["conversation_state"] = state
    if data:
        profile["conversation_data"] = data
    else:
        profile.pop("conversation_data", None)
    await db.update_profile(chat_id, profile)


async def get_user_state(chat_id: int) -> str:
    """Get the current conversation state for a user."""
    profile = await db.get_profile(chat_id)
    return profile.get("conversation_state", STATE_NONE)


async def get_user_state_data(chat_id: int) -> Dict[str, Any]:
    """Get the conversation state data for a user."""
    profile = await db.get_profile(chat_id)
    return profile.get("conversation_data", {})


async def clear_user_state(chat_id: int) -> None:
    """Clear the conversation state for a user."""
    profile = await db.get_profile(chat_id)
    profile.pop("conversation_state", None)
    profile.pop("conversation_data", None)
    await db.update_profile(chat_id, profile)


async def is_in_state(chat_id: int, state: str) -> bool:
    """Check if user is in a specific state."""
    return await get_user_state(chat_id) == state
