"""
gmc_extractor/pdf/cleaner.py
Cleans extracted page text:
- Removes repeated headers and footers (lines appearing on 3+ pages).
- Fixes soft-hyphenation (word- \\nbreak -> wordbreak).
- Collapses excessive whitespace.
- Preserves [PAGE n] markers added by reader.py.
"""
from __future__ import annotations

import logging
import re
from collections import Counter

from gmc_extractor.pdf.reader import PageDoc

logger = logging.getLogger(__name__)

# How many pages a line must appear on to be considered a header/footer
_REPEAT_THRESHOLD = 3

# Regex patterns for section headings
_HEADING_PATTERNS = [
    re.compile(r"^\s*(ANNEXURE|ENDORSEMENT|SCHEDULE|ADDENDUM|RIDER|AMENDMENT)\b", re.I),
    re.compile(r"^\s*[IVX]+\.\s+[A-Z]"),          # Roman numeral headings
    re.compile(r"^\s*\d+(\.\d+)*\s+[A-Z][A-Z ]{3,}"),  # Numbered ALL CAPS
    re.compile(r"^[A-Z][A-Z &/\-]{5,}$"),          # ALL CAPS line
    re.compile(r"^\s*(?:SPECIAL CONDITIONS?|TERMS? AND CONDITIONS?)\b", re.I),
]


def clean_pages(pages: list[PageDoc]) -> list[PageDoc]:
    """
    Clean all pages in place: remove repeated headers/footers,
    fix hyphenation, normalise whitespace, detect headings.

    Args:
        pages: List of PageDoc objects from the PDF reader.

    Returns:
        The same list, modified in place, for chaining.
    """
    repeated = _find_repeated_lines(pages)
    for page in pages:
        text = page.ocr_text if page.is_scanned and page.ocr_text else page.text
        text = _remove_repeated_lines(text, repeated)
        text = _fix_hyphenation(text)
        text = _normalise_whitespace(text)
        headings = _detect_headings(text)

        if page.is_scanned and page.ocr_text:
            page.ocr_text = text
        else:
            page.text = text

        page.headings = headings

    return pages


_PROTECTED_BENEFIT_TOKENS = {
    "sum insured", "room rent", "maternity", "waiting period",
    "pre-existing", "day care", "ambulance", "premium", "rupees",
    "lakh", "deductible", "co-pay", "copay", "annexure", "schedule",
}


def _find_repeated_lines(pages: list[PageDoc]) -> set[str]:
    """Identify lines that appear verbatim on 3+ pages (headers/footers)."""
    line_counts: Counter[str] = Counter()
    for page in pages:
        text = page.ocr_text if page.is_scanned and page.ocr_text else page.text
        seen_on_this_page: set[str] = set()
        for line in text.splitlines():
            stripped = line.strip()
            if len(stripped) > 4 and stripped not in seen_on_this_page:
                line_counts[stripped] += 1
                seen_on_this_page.add(stripped)

    repeated = {
        line for line, cnt in line_counts.items()
        if cnt >= _REPEAT_THRESHOLD
        and not any(tok in line.lower() for tok in _PROTECTED_BENEFIT_TOKENS)
    }
    if repeated:
        logger.debug("Suppressing %d repeated header/footer lines", len(repeated))
    return repeated


def _remove_repeated_lines(text: str, repeated: set[str]) -> str:
    """Remove lines identified as repeated headers/footers."""
    lines = [
        ln for ln in text.splitlines()
        if ln.strip() not in repeated
    ]
    return "\n".join(lines)


def _fix_hyphenation(text: str) -> str:
    """
    Re-join words broken across lines by soft hyphenation.
    e.g. "hospi-\\ntalization" -> "hospitalization"
    """
    return re.sub(r"-\n(\w)", r"\1", text)


def _normalise_whitespace(text: str) -> str:
    """
    Collapse runs of blank lines to a single blank line,
    and strip trailing spaces from each line.
    """
    # Strip trailing spaces per line
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _detect_headings(text: str) -> list[str]:
    """
    Detect section headings in the cleaned text using heuristic patterns.

    Returns a list of heading strings found in this page.
    """
    headings: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) < 4:
            continue
        for pattern in _HEADING_PATTERNS:
            if pattern.match(stripped):
                headings.append(stripped)
                break
    return headings
