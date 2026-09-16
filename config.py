"""
Central configuration, loaded from environment variables / .env file.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(
            f"[config] Missing required environment variable: {name}\n"
            f"Copy .env.example to .env and fill in your values."
        )
    return value


CONFIG = {
    "TARGET_URL": os.getenv(
        "TARGET_URL",
        "https://trouverunlogement.lescrous.fr/tools/47/search"
        "?bounds=2.224122_48.902156_2.4697602_48.8155755&locationName=Paris",
    ),
    "CHECK_INTERVAL_SECONDS": int(os.getenv("CHECK_INTERVAL_SECONDS", 60)),
    "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN"),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
    "HEADLESS": os.getenv("HEADLESS", "true").lower() == "true",
    "MAX_RETRIES": int(os.getenv("MAX_RETRIES", 3)),
    "PAGE_LOAD_WAIT_SECONDS": int(os.getenv("PAGE_LOAD_WAIT_SECONDS", 8)),
    "DB_PATH": os.getenv("DB_PATH", "seen_listings.sqlite3"),
}


def validate_config():
    """Call this at startup so missing Telegram creds fail fast with a clear message."""
    if not CONFIG["TELEGRAM_TOKEN"]:
        _require("TELEGRAM_TOKEN")
    if not CONFIG["TELEGRAM_CHAT_ID"]:
        _require("TELEGRAM_CHAT_ID")
    if CONFIG["CHECK_INTERVAL_SECONDS"] < 30:
        sys.exit(
            "[config] CHECK_INTERVAL_SECONDS is set below 30 seconds. "
            "Please use a more respectful polling interval (60s+ recommended)."
        )
