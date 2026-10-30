"""
gmc_extractor/postprocess/normalizer.py
Normalises amounts, percentages, days/months/years, and dates
from common Indian insurance document formats.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ── Amount patterns ───────────────────────────────────────────────────────────

# Indian number format: 5,00,000 or 500000
_INDIAN_NUMBER = re.compile(r"(?:Rs\.?\s*|INR\s*|₹\s*)?(\d+(?:,\d+)*(?:\.\d+)?)\b")
_LAKH_PATTERN = re.compile(
    r"(?:Rs\.?\s*|INR\s*|₹\s*)?(\d+(?:\.\d+)?)\s*(?:lakh|lac|lakhs|lacs)\b", re.I
)
_CRORE_PATTERN = re.compile(
    r"(?:Rs\.?\s*|INR\s*|₹\s*)?(\d+(?:\.\d+)?)\s*(?:crore|cr)\b", re.I
)
_L_SHORTHAND = re.compile(
    r"(?:Rs\.?\s*|INR\s*|₹\s*)?(\d+(?:\.\d+)?)\s*L\b"
)

# ── Date patterns ─────────────────────────────────────────────────────────────

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}

# DD/MM/YYYY or DD-MM-YYYY
_DATE_DMY_NUM = re.compile(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})")
# DD-Mon-YY or DD Month YYYY or DD-Month-YYYY
_DATE_DMY_ALPHA = re.compile(
    r"(\d{1,2})(?:st|nd|rd|th)?[\s\-]+([A-Za-z]+)[\s,\-]+(\d{2,4})",
    re.I,
)
# Month DD, YYYY or Mon DD, YYYY (e.g. April 26, 2024)
_DATE_MDY_ALPHA = re.compile(
    r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,\s*(\d{2,4})",
    re.I,
)
# YYYY-MM-DD (already ISO)
_DATE_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")

# ── Days / months / years ─────────────────────────────────────────────────────

_DAYS_PATTERN = re.compile(r"(\d+)\s*days?\b", re.I)
_MONTHS_PATTERN = re.compile(r"(\d+)\s*months?\b", re.I)
_YEARS_PATTERN = re.compile(r"(\d+)\s*years?\b", re.I)

# ── Percent ───────────────────────────────────────────────────────────────────

_PCT_OF_SI = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*(?:of\s+(?:sum\s+insured|SI|SA))?", re.I)


def parse_amount(text: str) -> Optional[int]:
    """
    Parse a rupee amount from a string like:
    - "Rs. 5,00,000" → 500000
    - "₹ 7.5 L" → 750000
    - "1 crore" → 10000000
    - "INR 5 Lacs" → 500000
    - "500000" → 500000

    Returns integer in rupees, or None if not parseable.
    """
    text = text.strip()

    # Crore
    m = _CRORE_PATTERN.search(text)
    if m:
        return int(float(m.group(1)) * 10_000_000)

    # Lakh
    m = _LAKH_PATTERN.search(text)
    if m:
        return int(float(m.group(1)) * 100_000)

    # L shorthand (e.g. 7.5 L)
    m = _L_SHORTHAND.search(text)
    if m:
        return int(float(m.group(1)) * 100_000)

    # Indian number format or plain integer
    m = _INDIAN_NUMBER.search(text)
    if m:
        # Remove commas and convert
        raw = m.group(1).replace(",", "")
        try:
            return int(float(raw))
        except ValueError:
            return None

    return None


def parse_percent(text: str) -> Optional[float]:
    """
    Parse a percentage value (e.g. "1% of SI" → 1.0, "2.5%" → 2.5).
    Returns float 0-100, or None.
    """
    m = _PCT_OF_SI.search(text)
    if m:
        return float(m.group(1))
    return None


def parse_days(text: str) -> Optional[int]:
    """
    Parse a duration in days from text.
    - "30 days" → 30
    - "2 months" → 60
    - "1 year" → 365
    """
    m = _DAYS_PATTERN.search(text)
    if m:
        return int(m.group(1))
    m = _MONTHS_PATTERN.search(text)
    if m:
        return int(m.group(1)) * 30
    m = _YEARS_PATTERN.search(text)
    if m:
        return int(m.group(1)) * 365
    return None


def parse_date(text: str) -> Optional[str]:
    """
    Parse a date from common Indian insurance document formats.
    Returns ISO yyyy-mm-dd string or None.

    Supported formats:
    - "26th April 2024" → "2024-04-26"
    - "26/04/2024" → "2024-04-26"
    - "26-Apr-24" → "2024-04-26"
    - "2024-04-26" → "2024-04-26"
    """
    text = text.strip()

    # Already ISO
    m = _DATE_ISO.search(text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # DD-Mon-YY or DD Month YYYY
    m = _DATE_DMY_ALPHA.search(text)
    if m:
        day = int(m.group(1))
        month_str = m.group(2).lower()[:3]
        year = int(m.group(3))
        if year < 100:
            year += 2000
        month = _MONTHS.get(month_str)
        if month:
            return f"{year:04d}-{month:02d}-{day:02d}"

    # Month DD, YYYY (e.g. April 26, 2024)
    m = _DATE_MDY_ALPHA.search(text)
    if m:
        month_str = m.group(1).lower()[:3]
        day = int(m.group(2))
        year = int(m.group(3))
        if year < 100:
            year += 2000
        month = _MONTHS.get(month_str)
        if month and 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}"

    # DD/MM/YYYY or DD-MM-YYYY
    m = _DATE_DMY_NUM.search(text)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}"

    return None


def normalise_amount_text(text: str) -> Optional[int]:
    """Attempt to normalise an amount string, returning None if not parseable."""
    return parse_amount(text)
