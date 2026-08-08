"""Gmail API service for email operations."""

import logging
import os
from typing import Dict, List, Optional

import config
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_FILE = 'gmail_token.json'
CREDENTIALS_FILE = 'credentials.json'


def _get_credentials(chat_id: int) -> Optional[Credentials]:
    """Get or create OAuth credentials for a user."""
    token_path = f"tokens/gmail_{chat_id}.json"
    
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
    token_path = f"tokens/gmail_{chat_id}.json"
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


def get_emails(chat_id: int, max_results: int = 10) -> List[Dict]:
    """Get recent emails for a user."""
    creds = _get_credentials(chat_id)
    if not creds:
        return []
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(
            userId='me', 
            maxResults=max_results
        ).execute()
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me', 
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
            emails.append({
                'id': msg['id'],
                'from': headers.get('From', 'Unknown'),
                'subject': headers.get('Subject', 'No Subject'),
                'date': headers.get('Date', ''),
                'snippet': msg_data.get('snippet', '')
            })
        
        return emails
    except Exception as e:
        logger.error(f"Failed to get emails: {e}")
        return []


def get_email_body(chat_id: int, message_id: str) -> Optional[str]:
    """Get full email body."""
    creds = _get_credentials(chat_id)
    if not creds:
        return None
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        msg = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract email body from payload
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    import base64
                    body = part['body']['data']
                    return base64.urlsafe_b64decode(body).decode('utf-8')
        
        return None
    except Exception as e:
        logger.error(f"Failed to get email body: {e}")
        return None


def is_authenticated(chat_id: int) -> bool:
    """Check if user is authenticated with Gmail."""
    return _get_credentials(chat_id) is not None
