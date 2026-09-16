"""
Sends notifications to Telegram: a formatted text message plus a screenshot.
"""
import html
import requests
from loguru import logger

from config import CONFIG

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _url(method: str) -> str:
    return TELEGRAM_API.format(token=CONFIG["TELEGRAM_TOKEN"], method=method)


def send_telegram_notification(details: list, screenshot_path: str = None):
    chat_id = CONFIG["TELEGRAM_CHAT_ID"]

    escaped_details = [html.escape(d) for d in details[:5]]
    bullet_list = "\n".join(f"• {d}" for d in escaped_details)

    message = (
        "🟢 <b>New CROUS Housing Listing(s)!</b>\n\n"
        f"{len(details)} new listing(s) detected:\n\n"
        f"{bullet_list}\n\n"
        f'<a href="{html.escape(CONFIG["TARGET_URL"])}">Open the search page</a>'
    )

    try:
        resp = requests.post(
            _url("sendMessage"),
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram text message: {e}")

    if screenshot_path:
        try:
            with open(screenshot_path, "rb") as photo:
                resp = requests.post(
                    _url("sendPhoto"),
                    data={"chat_id": chat_id, "caption": "📸 Latest screenshot"},
                    files={"photo": photo},
                    timeout=30,
                )
                resp.raise_for_status()
        except (requests.RequestException, OSError) as e:
            logger.error(f"Failed to send Telegram screenshot: {e}")


def send_telegram_text(text: str):
    """Utility for simple status/error messages (e.g. startup, repeated failures)."""
    try:
        resp = requests.post(
            _url("sendMessage"),
            json={"chat_id": CONFIG["TELEGRAM_CHAT_ID"], "text": text},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram status message: {e}")
