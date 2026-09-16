"""
Tiny SQLite-backed store so we don't send a duplicate Telegram alert every
single poll cycle while the same listings are still up - only on new ones.
"""
import sqlite3
import hashlib
from contextlib import contextmanager

from config import CONFIG


def _hash_detail(detail: str) -> str:
    return hashlib.sha256(detail.encode("utf-8")).hexdigest()


@contextmanager
def _connect():
    conn = sqlite3.connect(CONFIG["DB_PATH"])
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_listings (
                hash TEXT PRIMARY KEY,
                detail TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def filter_new(details: list) -> list:
    """Given a list of listing-detail strings, return only the ones we haven't
    already alerted on, and record them as seen."""
    new_items = []
    with _connect() as conn:
        for detail in details:
            h = _hash_detail(detail)
            row = conn.execute(
                "SELECT 1 FROM seen_listings WHERE hash = ?", (h,)
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO seen_listings (hash, detail) VALUES (?, ?)",
                    (h, detail),
                )
                new_items.append(detail)
    return new_items
