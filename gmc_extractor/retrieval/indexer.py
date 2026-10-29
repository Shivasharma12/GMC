"""
gmc_extractor/retrieval/indexer.py
Builds a BM25 index over the pages of a PDF.
Tokenises using simple whitespace/punctuation splitting.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from rank_bm25 import BM25Okapi

from gmc_extractor.pdf.reader import PageDoc

logger = logging.getLogger(__name__)

# Heading-boost keywords — pages containing these get higher retrieval priority
_STRUCTURAL_KEYWORDS = {
    "annexure", "endorsement", "schedule", "addendum", "amendment",
    "rider", "special condition", "terms and conditions", "benefit",
    "declaration", "summary",
}


class PageIndex:
    """
    BM25 index over PDF pages.

    Attributes:
        pages: The ordered list of PageDoc objects.
        bm25: The fitted BM25Okapi model.
        structural_pages: Set of page numbers (1-indexed) that contain
            structural/annexure keywords (get retrieval boost).
    """

    def __init__(self, pages: list[PageDoc]) -> None:
        self.pages = pages
        corpus = [_tokenise(p.full_text) for p in pages]
        self.bm25 = BM25Okapi(corpus)
        self.structural_pages: set[int] = _find_structural_pages(pages)
        logger.debug(
            "Built BM25 index over %d pages; %d structural pages",
            len(pages),
            len(self.structural_pages),
        )

    def scores(self, query_tokens: list[str]) -> list[float]:
        """Return BM25 scores for all pages given the query tokens."""
        return self.bm25.get_scores(query_tokens).tolist()  # type: ignore[return-value]


def build_index(pages: list[PageDoc]) -> PageIndex:
    """Build and return a PageIndex for the given pages."""
    return PageIndex(pages)


def _tokenise(text: str) -> list[str]:
    """Simple lowercase tokeniser splitting on non-alphanumeric characters."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _find_structural_pages(pages: list[PageDoc]) -> set[int]:
    """Identify pages with structural/annexure keywords for retrieval boost."""
    result: set[int] = set()
    for page in pages:
        combined = (page.full_text + " ".join(page.headings)).lower()
        for kw in _STRUCTURAL_KEYWORDS:
            if kw in combined:
                result.add(page.page_num)
                break
    return result
