"""
gmc_extractor/pdf/tables.py
Extracts tables from a PDF page using pdfplumber and converts them
to GitHub-flavoured Markdown. Handles merged cells and split tables.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_tables_as_markdown(pdf_path: Path, page_num: int) -> list[str]:
    """
    Extract all tables from *page_num* (1-indexed) of *pdf_path*.

    Args:
        pdf_path: Path to the PDF file.
        page_num: 1-indexed page number.

    Returns:
        List of markdown strings, one per table found on the page.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber not installed; skipping table extraction.")
        return []

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            if page_num < 1 or page_num > len(pdf.pages):
                return []
            page = pdf.pages[page_num - 1]
            tables = page.extract_tables()
            if not tables:
                return []
            return [_table_to_markdown(t) for t in tables if t]
    except Exception as exc:
        logger.warning("Table extraction failed on page %d: %s", page_num, exc)
        return []


def _table_to_markdown(table: list[list[str | None]]) -> str:
    """
    Convert a pdfplumber table (list of rows, each a list of cell strings)
    to a GitHub-flavoured Markdown table string.

    None cells are replaced with empty strings.
    Multi-line cell content is collapsed to spaces.
    """
    if not table:
        return ""

    # Normalise cells
    rows: list[list[str]] = []
    for raw_row in table:
        if raw_row is None:
            continue
        row = [_clean_cell(c) for c in raw_row]
        rows.append(row)

    if not rows:
        return ""

    # Determine column count
    n_cols = max(len(r) for r in rows)
    # Pad short rows
    rows = [r + [""] * (n_cols - len(r)) for r in rows]

    # Build markdown
    lines: list[str] = []
    header = rows[0]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * n_cols) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def _clean_cell(cell: str | None) -> str:
    """Normalise a table cell value."""
    if cell is None:
        return ""
    # Collapse newlines / multiple spaces
    return " ".join(str(cell).split()).replace("|", "\\|")
