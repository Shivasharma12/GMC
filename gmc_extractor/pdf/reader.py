"""
gmc_extractor/pdf/reader.py
Reads a PDF and returns a list of PageDoc objects.
Uses PyMuPDF for text extraction and page rendering,
and pdfplumber for table detection.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Minimum characters of text for a page to be considered "text-selectable"
_MIN_TEXT_CHARS = 30


@dataclass
class PageDoc:
    """Holds all content extracted from a single PDF page."""

    page_num: int                        # 1-indexed
    text: str                            # raw text from PyMuPDF
    tables_md: list[str]                 # each table rendered as markdown
    is_scanned: bool = False             # True if text was too sparse
    ocr_text: Optional[str] = None       # OCR result for scanned pages
    headings: list[str] = field(default_factory=list)  # detected section headings

    @property
    def full_text(self) -> str:
        """Combined text + OCR + tables, with PAGE marker."""
        parts = [f"[PAGE {self.page_num}]"]
        body = (self.ocr_text or self.text).strip()
        if body:
            parts.append(body)
        for tbl in self.tables_md:
            if tbl.strip():
                parts.append(tbl)
        return "\n".join(parts)


def read_pdf(
    pdf_path: Path,
    cache_dir: Optional[Path] = None,
    ocr_available: bool = True,
) -> list[PageDoc]:
    """
    Extract all pages from *pdf_path* as PageDoc objects.

    Results are cached to *cache_dir*/<stem>/pages.json so reruns are instant.

    Args:
        pdf_path: Path to the PDF file.
        cache_dir: Directory for caching extracted pages. None disables cache.
        ocr_available: Whether pytesseract is importable and ready.

    Returns:
        Ordered list of PageDoc (1-indexed page numbers).
    """
    import fitz  # PyMuPDF

    from gmc_extractor.pdf.tables import extract_tables_as_markdown
    from gmc_extractor.pdf.ocr import ocr_page

    pdf_path = Path(pdf_path)
    cache_path: Optional[Path] = None

    if cache_dir is not None:
        cache_path = cache_dir / pdf_path.stem / "pages.json"
        if cache_path.exists():
            logger.debug("Loading page cache from %s", cache_path)
            return _load_cache(cache_path)

    logger.info("Reading PDF: %s", pdf_path.name)
    doc = fitz.open(str(pdf_path))
    pages: list[PageDoc] = []

    for fitz_page in doc:
        page_num = fitz_page.number + 1  # 1-indexed
        text = fitz_page.get_text("text")  # type: ignore[attr-defined]
        is_scanned = len(text.strip()) < _MIN_TEXT_CHARS

        tables_md = extract_tables_as_markdown(pdf_path, page_num, fitz_page=fitz_page)

        ocr_text: Optional[str] = None
        if is_scanned and ocr_available:
            ocr_text = ocr_page(fitz_page)

        page = PageDoc(
            page_num=page_num,
            text=text,
            tables_md=tables_md,
            is_scanned=is_scanned,
            ocr_text=ocr_text,
        )
        pages.append(page)
        logger.debug("Page %d: %d chars, scanned=%s", page_num, len(text), is_scanned)

    doc.close()
    logger.info("Read %d pages (%d scanned)", len(pages), sum(p.is_scanned for p in pages))

    if cache_path is not None:
        _save_cache(cache_path, pages)

    return pages


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _save_cache(path: Path, pages: list[PageDoc]) -> None:
    """Serialise pages to JSON cache."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "page_num": p.page_num,
            "text": p.text,
            "tables_md": p.tables_md,
            "is_scanned": p.is_scanned,
            "ocr_text": p.ocr_text,
            "headings": p.headings,
        }
        for p in pages
    ]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.debug("Cached pages to %s", path)


def _load_cache(path: Path) -> list[PageDoc]:
    """Deserialise pages from JSON cache."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        PageDoc(
            page_num=d["page_num"],
            text=d["text"],
            tables_md=d["tables_md"],
            is_scanned=d["is_scanned"],
            ocr_text=d.get("ocr_text"),
            headings=d.get("headings", []),
        )
        for d in data
    ]
