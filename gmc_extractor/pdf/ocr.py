"""
gmc_extractor/pdf/ocr.py
Optional OCR fallback using pytesseract + Pillow.
Only called for scanned (image-only) pages.
Renders pages via PyMuPDF — no poppler dependency.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_TESSERACT_AVAILABLE: bool | None = None  # lazily determined


def _check_tesseract() -> bool:
    """Return True if pytesseract and tesseract binary are available."""
    global _TESSERACT_AVAILABLE
    if _TESSERACT_AVAILABLE is not None:
        return _TESSERACT_AVAILABLE
    try:
        import pytesseract  # noqa: F401
        pytesseract.get_tesseract_version()
        _TESSERACT_AVAILABLE = True
    except Exception:
        logger.warning(
            "Tesseract not found. OCR fallback disabled. "
            "Install Tesseract-OCR and ensure it is on your PATH to enable OCR."
        )
        _TESSERACT_AVAILABLE = False
    return _TESSERACT_AVAILABLE


def ocr_page(fitz_page: Any, dpi: int = 200) -> str | None:
    """
    Render a PyMuPDF page and run Tesseract OCR on it.

    Args:
        fitz_page: A ``fitz.Page`` object (PyMuPDF).
        dpi: Resolution for rendering (higher = better OCR, slower).

    Returns:
        Extracted text string, or None if OCR is unavailable.
    """
    if not _check_tesseract():
        return None

    try:
        import pytesseract
        from PIL import Image
        import io

        # Render page to a pixmap at the given DPI
        zoom = dpi / 72.0
        mat = __import__("fitz").Matrix(zoom, zoom)
        pix = fitz_page.get_pixmap(matrix=mat, alpha=False)  # type: ignore[attr-defined]

        # Convert pixmap to PIL Image
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))

        # Run OCR with English language (expandable via config)
        text: str = pytesseract.image_to_string(img, lang="eng")
        return text
    except Exception as exc:
        logger.warning("OCR failed on page: %s", exc)
        return None
