"""
CROUS Housing Monitor - entry point.

Polls the CROUS search page on a schedule. When new listings appear that
haven't been alerted on before, sends a Telegram notification with details
and a screenshot.
"""
import argparse
import time
import schedule
from loguru import logger

from config import CONFIG, validate_config
from scraper import get_driver, fetch_page
from analyzer import has_listings, extract_listing_details
from notifier import send_telegram_notification, send_telegram_text
from storage import init_db, filter_new
from utils import ensure_dirs, screenshot_filename

CONSECUTIVE_FAILURES = 0
FAILURE_ALERT_THRESHOLD = 5


def job():
    global CONSECUTIVE_FAILURES
    driver = None
    try:
        driver = get_driver()
        html_source = fetch_page(driver)

        if has_listings(html_source):
            details = extract_listing_details(html_source)
            new_details = filter_new(details)

            if new_details:
                logger.success(f"🎉 {len(new_details)} new listing(s) found!")
                path = screenshot_filename()
                driver.save_screenshot(path)
                send_telegram_notification(new_details, path)
            else:
                logger.info("Listings present but already alerted on previously.")
        else:
            logger.info("No housing found yet...")

        CONSECUTIVE_FAILURES = 0

    except Exception as e:
        CONSECUTIVE_FAILURES += 1
        logger.error(f"Job failed ({CONSECUTIVE_FAILURES} in a row): {e}")
        if CONSECUTIVE_FAILURES == FAILURE_ALERT_THRESHOLD:
            send_telegram_text(
                f"⚠️ CROUS monitor has failed {CONSECUTIVE_FAILURES} checks in a "
                f"row. Last error: {e}"
            )
    finally:
        if driver:
            driver.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")
    parser.add_argument(
        "--duration", type=int, default=0,
        help="Keep polling for N seconds then exit (0 = forever). Used by GitHub Actions.",
    )
    args = parser.parse_args()

    validate_config()
    ensure_dirs("screenshots", "logs")

    logger.add(
        "logs/crous_{time:YYYY-MM-DD}.log", rotation="10 MB", level="INFO"
    )

    logger.info("🚀 CROUS housing monitor started")
    logger.info(f"Polling every {CONFIG['CHECK_INTERVAL_SECONDS']}s")
    logger.info(f"Target URL: {CONFIG['TARGET_URL']}")

    init_db()

    # Run once immediately, then on the schedule
    job()
    if args.once:
        return

    schedule.every(CONFIG["CHECK_INTERVAL_SECONDS"]).seconds.do(job)
    deadline = time.time() + args.duration if args.duration else None

    while deadline is None or time.time() < deadline:
        schedule.run_pending()
        time.sleep(1)
    logger.info("Duration reached, exiting cleanly.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
