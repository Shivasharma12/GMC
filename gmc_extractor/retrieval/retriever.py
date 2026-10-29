"""
gmc_extractor/retrieval/retriever.py
Retrieves the most relevant pages for a given field group using BM25 scores,
annexure/structural page boosting, neighbour inclusion, and a character budget.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from gmc_extractor.pdf.reader import PageDoc
from gmc_extractor.retrieval.indexer import PageIndex, _tokenise

logger = logging.getLogger(__name__)

# Default character budget per retrieval (keeps prompts within LLM context)
DEFAULT_CHAR_BUDGET = 24_000
# Default number of top pages to retrieve
DEFAULT_TOP_K = 8
# Structural page boost multiplier
_STRUCTURAL_BOOST = 1.5


def retrieve(
    index: PageIndex,
    keywords: dict[str, Any],
    group_key: str,
    top_k: int = DEFAULT_TOP_K,
    neighbor_window: int = 1,
    char_budget: int = DEFAULT_CHAR_BUDGET,
) -> list[PageDoc]:
    """
    Retrieve the most relevant pages for *group_key* from the index.

    Strategy:
    1. Build a combined query from primary keywords + synonyms for the group.
    2. Score all pages with BM25.
    3. Apply structural-page boost.
    4. Select top-k pages + their immediate neighbours (±neighbor_window).
    5. Trim to char_budget (most-relevant pages first).

    Args:
        index: The PageIndex built from the PDF.
        keywords: The full keywords config dict (from keywords.yaml).
        group_key: Key in the keywords dict for this field group.
        top_k: How many top-scoring pages to include.
        neighbor_window: Number of pages before/after each top page to include.
        char_budget: Maximum total characters to return.

    Returns:
        Ordered list of PageDoc objects (by page number), within budget.
    """
    group_kw = keywords.get(group_key, {})
    primary = group_kw.get("primary", [])
    synonyms = group_kw.get("synonyms", [])
    all_terms = primary + synonyms

    if not all_terms:
        logger.warning("No keywords found for group '%s'; returning first %d pages", group_key, top_k)
        return index.pages[:top_k]

    # Build query tokens from all terms
    query_text = " ".join(all_terms)
    query_tokens = _tokenise(query_text)

    # BM25 scores
    raw_scores = index.scores(query_tokens)

    # Apply structural boost
    boosted: list[tuple[float, int]] = []
    for i, score in enumerate(raw_scores):
        page_num = index.pages[i].page_num
        if page_num in index.structural_pages:
            score *= _STRUCTURAL_BOOST
        boosted.append((score, i))

    # Sort by score descending
    boosted.sort(reverse=True)

    # Collect top-k page indices (0-indexed)
    top_indices: set[int] = set()
    for _, idx in boosted[:top_k]:
        top_indices.add(idx)
        # Add neighbours
        for delta in range(-neighbor_window, neighbor_window + 1):
            neighbour = idx + delta
            if 0 <= neighbour < len(index.pages):
                top_indices.add(neighbour)

    # Sort by page order
    selected_indices = sorted(top_indices)
    selected_pages = [index.pages[i] for i in selected_indices]

    # Apply character budget (greedily add pages, most-relevant first)
    # Build a priority order (top-k first, neighbours second)
    priority_page_nums = {index.pages[i].page_num: rank for rank, (_, i) in enumerate(boosted[:top_k])}

    def _priority(p: PageDoc) -> int:
        return priority_page_nums.get(p.page_num, 9999)

    selected_pages_sorted_by_priority = sorted(selected_pages, key=_priority)

    kept: list[PageDoc] = []
    total_chars = 0
    for page in selected_pages_sorted_by_priority:
        size = len(page.full_text)
        if total_chars + size <= char_budget:
            kept.append(page)
            total_chars += size
        else:
            logger.debug(
                "Page %d dropped: char budget reached (%d/%d)",
                page.page_num, total_chars, char_budget,
            )
            break

    # Return in page-number order
    kept.sort(key=lambda p: p.page_num)
    logger.debug(
        "Group '%s': retrieved %d pages, %d chars",
        group_key, len(kept), total_chars,
    )
    return kept
