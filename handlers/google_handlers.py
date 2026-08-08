"""Gmail and Google Calendar command handlers for Telegram."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from services import gmail_service, calendar_service

logger = logging.getLogger(__name__)


async def gmail_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Authenticate with Gmail - sends OAuth URL."""
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    
    if gmail_service.is_authenticated(chat_id):
        await update.message.reply_text("✅ You're already authenticated with Gmail!")
        return
    
    try:
        auth_url = gmail_service.create_auth_url(chat_id)
        message = (
            "🔗 **Gmail Authentication Required**\n\n"
            "To link your Gmail account, follow these steps:\n\n"
            "1. Click this authorization link:\n"
            f"{auth_url}\n\n"
            "2. Sign in to your Google account and grant permissions\n"
            "3. Copy the authorization code from the page\n"
            "4. Send it to me with: `/gmail_code <your_code>`"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Gmail auth failed: {e}")
        await update.message.reply_text("❌ Failed to create authorization URL. Please check your Google credentials.")


async def gmail_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exchange Gmail authorization code for credentials."""
    if not update.message or not context.args:
        await update.message.reply_text("Usage: /gmail_code <authorization_code>")
        return
    
    chat_id = update.effective_chat.id
    code = context.args[0]
    
    if gmail_service.exchange_code(chat_id, code):
        await update.message.reply_text("✅ Gmail authentication successful! You can now use Gmail commands.")
    else:
        await update.message.reply_text("❌ Failed to authenticate. Please check the code and try again.")


async def gmail_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent emails from inbox."""
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    
    if not gmail_service.is_authenticated(chat_id):
        await update.message.reply_text("❌ Please authenticate first with /gmail_auth")
        return
    
    try:
        # Get limit from args or default to 5
        limit = int(context.args[0]) if context.args else 5
        emails = gmail_service.get_emails(chat_id, max_results=min(limit, 20))
        
        if not emails:
            await update.message.reply_text("📭 No emails found in your inbox.")
            return
        
        message = f"📬 **Recent {len(emails)} Emails**\n\n"
        for i, email in enumerate(emails, 1):
            from_name = email['from'].split('<')[0].strip() if '<' in email['from'] else email['from']
            message += f"{i}. **{email['subject']}**\n"
            message += f"   From: {from_name}\n"
            message += f"   Date: {email['date'][:16] if email['date'] else 'Unknown'}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Gmail inbox failed: {e}")
        await update.message.reply_text("❌ Failed to fetch emails. Please try again.")


async def gmail_read(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Read full email content."""
    if not update.message or not context.args:
        await update.message.reply_text("Usage: /gmail_read <email_number>")
        return
    
    chat_id = update.effective_chat.id
    
    if not gmail_service.is_authenticated(chat_id):
        await update.message.reply_text("❌ Please authenticate first with /gmail_auth")
        return
    
    try:
        # Get emails first to find the one requested
        emails = gmail_service.get_emails(chat_id, max_results=20)
        email_num = int(context.args[0])
        
        if email_num < 1 or email_num > len(emails):
            await update.message.reply_text(f"❌ Invalid email number. Please use 1-{len(emails)}")
            return
        
        email = emails[email_num - 1]
        body = gmail_service.get_email_body(chat_id, email['id'])
        
        if body:
            # Truncate if too long
            if len(body) > 3000:
                body = body[:3000] + "\n\n... (message truncated)"
            
            message = f"📧 **{email['subject']}**\n"
            message += f"From: {email['from']}\n"
            message += f"Date: {email['date']}\n\n"
            message += f"{body}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Could not fetch email body. The email might be empty or in an unsupported format.")
    except Exception as e:
        logger.error(f"Gmail read failed: {e}")
        await update.message.reply_text("❌ Failed to read email. Please try again.")


async def calendar_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Authenticate with Google Calendar - sends OAuth URL."""
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    
    if calendar_service.is_authenticated(chat_id):
        await update.message.reply_text("✅ You're already authenticated with Google Calendar!")
        return
    
    try:
        auth_url = calendar_service.create_auth_url(chat_id)
        message = (
            "🔗 **Google Calendar Authentication Required**\n\n"
            "To link your Calendar account, follow these steps:\n\n"
            "1. Click this authorization link:\n"
            f"{auth_url}\n\n"
            "2. Sign in to your Google account and grant permissions\n"
            "3. Copy the authorization code from the page\n"
            "4. Send it to me with: `/calendar_code <your_code>`"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Calendar auth failed: {e}")
        await update.message.reply_text("❌ Failed to create authorization URL. Please check your Google credentials.")


async def calendar_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exchange Calendar authorization code for credentials."""
    if not update.message or not context.args:
        await update.message.reply_text("Usage: /calendar_code <authorization_code>")
        return
    
    chat_id = update.effective_chat.id
    code = context.args[0]
    
    if calendar_service.exchange_code(chat_id, code):
        await update.message.reply_text("✅ Google Calendar authentication successful! You can now use Calendar commands.")
    else:
        await update.message.reply_text("❌ Failed to authenticate. Please check the code and try again.")


async def calendar_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show today's calendar events."""
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    
    if not calendar_service.is_authenticated(chat_id):
        await update.message.reply_text("❌ Please authenticate first with /calendar_auth")
        return
    
    try:
        events = calendar_service.get_today_events(chat_id)
        
        if not events:
            await update.message.reply_text("📅 No events scheduled for today!")
            return
        
        message = f"📅 **Today's Events ({len(events)})**\n\n"
        for event in events:
            message += f"• **{event['summary']}**\n"
            if event['start']:
                message += f"  Time: {event['start']}\n"
            if event['location']:
                message += f"  Location: {event['location']}\n"
            if event['description']:
                message += f"  Note: {event['description'][:100]}...\n"
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Calendar today failed: {e}")
        await update.message.reply_text("❌ Failed to fetch calendar events. Please try again.")


async def calendar_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show calendar events for the next week."""
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    
    if not calendar_service.is_authenticated(chat_id):
        await update.message.reply_text("❌ Please authenticate first with /calendar_auth")
        return
    
    try:
        # Get days from args or default to 7
        days = int(context.args[0]) if context.args else 7
        events = calendar_service.get_events(chat_id, days=min(days, 30))
        
        if not events:
            await update.message.reply_text(f"📅 No events scheduled for the next {days} days!")
            return
        
        message = f"📅 **Upcoming Events ({len(events)})**\n\n"
        for event in events:
            message += f"• **{event['summary']}**\n"
            if event['start']:
                message += f"  Time: {event['start']}\n"
            if event['location']:
                message += f"  Location: {event['location']}\n"
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Calendar week failed: {e}")
        await update.message.reply_text("❌ Failed to fetch calendar events. Please try again.")
