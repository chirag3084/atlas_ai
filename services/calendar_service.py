"""Google Calendar API service for calendar operations."""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import config
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TOKEN_FILE = 'calendar_token.json'


def _get_credentials(chat_id: int) -> Optional[Credentials]:
    """Get or create OAuth credentials for a user."""
    token_path = f"tokens/calendar_{chat_id}.json"
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            return creds
    
    return None


def _save_credentials(chat_id: int, creds: Credentials) -> None:
    """Save OAuth credentials for a user."""
    os.makedirs('tokens', exist_ok=True)
    token_path = f"tokens/calendar_{chat_id}.json"
    with open(token_path, 'w') as token:
        token.write(creds.to_json())


def create_auth_url(chat_id: int) -> str:
    """Create OAuth authorization URL for a user."""
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [config.GOOGLE_REDIRECT_URI]
            }
        },
        SCOPES
    )
    flow.redirect_uri = config.GOOGLE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url


def exchange_code(chat_id: int, code: str) -> bool:
    """Exchange authorization code for credentials."""
    try:
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [config.GOOGLE_REDIRECT_URI]
                }
            },
            SCOPES
        )
        flow.redirect_uri = config.GOOGLE_REDIRECT_URI
        flow.fetch_token(code=code)
        _save_credentials(chat_id, flow.credentials)
        return True
    except Exception as e:
        logger.error(f"Failed to exchange code: {e}")
        return False


def get_events(chat_id: int, days: int = 7) -> List[Dict]:
    """Get calendar events for the next N days."""
    creds = _get_credentials(chat_id)
    if not creds:
        return []
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        now = datetime.utcnow().isoformat() + 'Z'
        time_max = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=time_max,
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted_events = []
        for event in events:
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Parse date/time
            start_time = start.get('dateTime', start.get('date'))
            end_time = end.get('dateTime', end.get('date'))
            
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start': start_time,
                'end': end_time,
                'location': event.get('location', ''),
                'status': event.get('status', '')
            })
        
        return formatted_events
    except Exception as e:
        logger.error(f"Failed to get calendar events: {e}")
        return []


def get_today_events(chat_id: int) -> List[Dict]:
    """Get today's calendar events."""
    creds = _get_credentials(chat_id)
    if not creds:
        return []
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        now = datetime.utcnow().isoformat() + 'Z'
        tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=tomorrow,
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted_events = []
        for event in events:
            start = event.get('start', {})
            end = event.get('end', {})
            
            start_time = start.get('dateTime', start.get('date'))
            end_time = end.get('dateTime', end.get('date'))
            
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start': start_time,
                'end': end_time,
                'location': event.get('location', ''),
                'status': event.get('status', '')
            })
        
        return formatted_events
    except Exception as e:
        logger.error(f"Failed to get today's events: {e}")
        return []


def is_authenticated(chat_id: int) -> bool:
    """Check if user is authenticated with Calendar."""
    return _get_credentials(chat_id) is not None
