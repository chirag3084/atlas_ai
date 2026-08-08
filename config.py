import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Primary model: fast, used for almost every reply (<300ms target).
GROQ_MODEL_PRIMARY = os.environ.get("GROQ_MODEL_PRIMARY", "llama-3.1-8b-instant")
# Fallback: used if the primary call fails/errors, or for PDF summarization
# where deeper reasoning over a long document matters more than latency.
GROQ_MODEL_FALLBACK = os.environ.get("GROQ_MODEL_FALLBACK", "llama-3.3-70b-versatile")
GROQ_WHISPER_MODEL = os.environ.get("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")
GROQ_VISION_MODEL = os.environ.get("GROQ_VISION_MODEL", "llava-v1.5-7b-4096-preview")

DB_PATH = os.environ.get("DB_PATH", "atlas.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")
BRIEFING_HOUR = int(os.environ.get("BRIEFING_HOUR", "8"))
BRIEFING_MINUTE = int(os.environ.get("BRIEFING_MINUTE", "0"))

PORT = int(os.environ.get("PORT", "8080"))
# Render's free web service tier sleeps after inactivity — set this to the
# bot's own public URL (e.g. https://your-app.onrender.com/health) and a
# background task will ping it every 10 minutes to keep it awake.
SELF_PING_URL = os.environ.get("SELF_PING_URL", "")

MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "10"))
MAX_PDF_CHARS = int(os.environ.get("MAX_PDF_CHARS", "15000"))