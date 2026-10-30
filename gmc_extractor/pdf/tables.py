"""
gmc_extractor/pdf/tables.py
Extracts tables from a PDF page using:
1. PyMuPDF native page.find_tables() (accurate vector table extraction).
2. Layout-aware coordinate-based row reconstruction for separated key-value tables.
3. pdfplumber fallback.
Converts all extracted tables to GitHub-flavoured Markdown.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import fitz

logger = logging.getLogger(__name__)


def extract_tables_as_markdown(
    pdf_path: Path,
    page_num: int,
    fitz_page: Optional[fitz.Page] = None,
) -> list[str]:
    """
    Extract all tables from *page_num* (1-indexed) of *pdf_path*.
    Returns a list of markdown table strings.
    """
    tables_md: list[str] = []

    # ── Strategy 1: PyMuPDF find_tables ──────────────────────────────────────
    opened_doc = None
    try:
        page = fitz_page
        if page is None:
            opened_doc = fitz.open(str(pdf_path))
            if page_num < 1 or page_num > len(opened_doc):
                return []
            page = opened_doc[page_num - 1]

        found_tables = page.find_tables()
        if found_tables and found_tables.tables:
            for tab in found_tables.tables:
                extracted_rows = tab.extract()
                md = _table_to_markdown(extracted_rows)
                if md and len(md.strip()) > 20:
                    tables_md.append(md)

        # ── Strategy 2: Coordinate-based row reconstruction for key-value tables ─
        # Check if the text layer has separated label/value blocks
        raw_text = page.get_text("text")
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
        # Heuristic for scrambled page: many short consecutive label lines or consecutive numbers
        short_lines = sum(1 for ln in lines if len(ln.split()) <= 3)
        is_scrambled = len(lines) > 15 and (short_lines / len(lines)) > 0.45

        if is_scrambled or not tables_md:
            coord_md = reconstruct_words_to_markdown(page)
            if coord_md and len(coord_md.strip()) > 50:
                tables_md.append(coord_md)

    except Exception as exc:
        logger.warning("PyMuPDF table extraction failed on page %d: %s", page_num, exc)
    finally:
        if opened_doc:
            opened_doc.close()

    if tables_md:
        return tables_md

    # ── Strategy 3: pdfplumber fallback ─────────────────────────────────────
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            if page_num < 1 or page_num > len(pdf.pages):
                return []
            p = pdf.pages[page_num - 1]
            tables = p.extract_tables()
            if tables:
                return [_table_to_markdown(t) for t in tables if t]
    except Exception as exc:
        logger.warning("pdfplumber table extraction fallback failed on page %d: %s", page_num, exc)

    return []


def reconstruct_words_to_markdown(page: fitz.Page, y_tol: float = 3.5) -> str:
    """
    Reconstruct multi-column key-value rows from raw word bounding boxes.
    Sorts words vertically by y0 (with y_tol clustering) and horizontally by x0,
    then aligns labels with their corresponding values into markdown table rows.
    """
    try:
        words = page.get_text("words")
    except Exception:
        return ""

    if not words or len(words) < 10:
        return ""

    # Sort words primarily by y0, secondarily by x0
    words.sort(key=lambda w: (w[1], w[0]))

    rows: list[list[tuple[float, str]]] = []
    current_row: list[tuple[float, str]] = []
    current_y: Optional[float] = None

    for w in words:
        x0, y0, x1, y1, word = w[0], w[1], w[2], w[3], w[4]
        if current_y is None or abs(y0 - current_y) > y_tol:
            if current_row:
                current_row.sort(key=lambda item: item[0])
                rows.append(current_row)
            current_row = [(x0, word)]
            current_y = y0
        else:
            current_row.append((x0, word))
            current_y = (current_y + y0) / 2.0

    if current_row:
        current_row.sort(key=lambda item: item[0])
        rows.append(current_row)

    md_lines = ["| Item / Clause / Specification | Extracted Value / Limit |", "| --- | --- |"]
    for row in rows:
        if len(row) < 2:
            continue
        # Find horizontal gap between label and value
        widest_gap = 0
        split_idx = -1
        for i in range(len(row) - 1):
            gap = row[i + 1][0] - (row[i][0] + len(row[i][1]) * 5)
            if gap > widest_gap and gap > 18:
                widest_gap = gap
                split_idx = i + 1

        if split_idx > 0:
            left = " ".join(item[1] for item in row[:split_idx]).replace("|", "\\|").strip()
            right = " ".join(item[1] for item in row[split_idx:]).replace("|", "\\|").strip()
            if left and right:
                md_lines.append(f"| {left} | {right} |")

    return "\n".join(md_lines) if len(md_lines) > 2 else ""


def _table_to_markdown(table: list[list[str | None]]) -> str:
    """
    Convert a table (list of rows, each a list of cell strings)
    to a GitHub-flavoured Markdown table string.
    """
    if not table:
        return ""

    rows: list[list[str]] = []
    for raw_row in table:
        if raw_row is None:
            continue
        row = [_clean_cell(c) for c in raw_row]
        if any(c for c in row):  # Keep non-empty rows
            rows.append(row)

    if not rows:
        return ""

    n_cols = max(len(r) for r in rows)
    rows = [r + [""] * (n_cols - len(r)) for r in rows]

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
    return " ".join(str(cell).split()).replace("|", "\\|")
