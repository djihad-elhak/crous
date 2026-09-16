"""
Parses the CROUS search results page to determine whether listings exist,
and extracts whatever detail text is available for each one.

Note: trouverunlogement.lescrous.fr is a JS-rendered Angular app, and its
internal CSS class names can change between deployments. This module uses a
layered strategy: try a few plausible "listing card" selectors first, and
fall back to a generic text-scan so the bot still detects availability even
if the markup shifts (it just won't extract fine detail in that case).
"""
import re
from bs4 import BeautifulSoup
from loguru import logger

NEGATIVE_PHRASES = [
    "aucun logement trouvé",
    "aucun résultat",
    "0 logement",
]

POSITIVE_PHRASES = [
    "logement trouvé",
    "logements trouvés",
    "résidence",
]

# Best-effort selectors for individual listing cards. Update these if you
# inspect the live page and find more accurate class/data-attribute names.
CARD_SELECTORS = [
    "[class*='fr-card']",
    "[class*='result-item']",
    "[class*='listing-card']",
    "article",
]


def has_listings(page_source: str) -> bool:
    soup = BeautifulSoup(page_source, "html.parser")
    text = soup.get_text(separator=" ").strip().lower()
    text = re.sub(r"\s+", " ", text)

    if any(phrase in text for phrase in NEGATIVE_PHRASES):
        return False

    if any(phrase in text for phrase in POSITIVE_PHRASES):
        return True

    # Fallback: if we can find plausible listing cards with real content,
    # treat that as a positive signal even without matching phrase text.
    cards = _find_cards(soup)
    return len(cards) > 0


def _find_cards(soup: BeautifulSoup):
    for selector in CARD_SELECTORS:
        cards = soup.select(selector)
        # Filter out tiny/empty elements that aren't really listing cards
        cards = [c for c in cards if len(c.get_text(strip=True)) > 20]
        if cards:
            return cards
    return []


def extract_listing_details(page_source: str) -> list:
    """
    Returns a list of short human-readable strings, one per detected listing,
    e.g. "Résidence Bara - T1 - 450€/mois". Falls back to a generic message
    if the page structure doesn't match known patterns.
    """
    soup = BeautifulSoup(page_source, "html.parser")
    cards = _find_cards(soup)

    if not cards:
        return ["Listings detected — open the link to view details."]

    details = []
    for card in cards[:10]:
        text = card.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        if len(text) > 150:
            text = text[:150].rsplit(" ", 1)[0] + "..."
        if text:
            details.append(text)

    return details or ["Listings detected — open the link to view details."]
