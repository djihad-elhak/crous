"""
Fetches the CROUS search page using plain Selenium (Chrome).

Deliberately NOT using anti-detection / stealth tooling - this is a simple,
polite polling client with reasonable delays between checks.
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

from config import CONFIG


def get_driver():
    options = Options()
    if CONFIG["HEADLESS"]:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=fr-FR")
    # A normal, current desktop Chrome user agent - not spoofing anything unusual
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    try:
        # Selenium >= 4.6 finds/downloads a matching driver by itself (works on
        # GitHub Actions runners and on Windows).
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        logger.warning(f"Selenium Manager failed ({e}), falling back to webdriver-manager")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver


def fetch_page(driver) -> str:
    """Loads the target URL and waits for the results container to render."""
    driver.get(CONFIG["TARGET_URL"])

    try:
        WebDriverWait(driver, CONFIG["PAGE_LOAD_WAIT_SECONDS"]).until(
            lambda d: len(d.find_elements(By.TAG_NAME, "body")[0].text.strip()) > 0
        )
    except TimeoutException:
        logger.warning("Page body took a while to populate, continuing anyway.")

    # Small extra buffer for any async content (search results load via AJAX)
    time.sleep(3)
    return driver.page_source
