import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_STRING_SESSION = os.getenv("TELEGRAM_STRING_SESSION", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0")) if os.getenv("ADMIN_TELEGRAM_ID") else None
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OUR_SERVICES_DESCRIPTION = os.getenv(
    "OUR_SERVICES_DESCRIPTION",
    "Розробка сайтів, Telegram-ботів, веб-сервісів, парсерів, автоматизація бізнесу, скрипти."
)
