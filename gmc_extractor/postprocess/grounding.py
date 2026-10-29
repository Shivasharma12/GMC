"""
gmc_extractor/postprocess/grounding.py
Verifies that numeric values and evidence quotes returned by the LLM
actually appear in the retrieved source text.
Uses rapidfuzz for fuzzy quote matching.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from rapidfuzz import fuzz

from gmc_extractor.pdf.reader import PageDoc

logger = logging.getLogger(__name__)

# Minimum fuzzy match score for evidence quotes (0-100)
_EVIDENCE_MATCH_THRESHOLD = 65
# Confidence penalty for failed grounding
_GROUNDING_PENALTY = 0.25


def ground_result(
    result_dict: dict[str, Any],
    pages: list[PageDoc],
    warnings: list[str],
) -> dict[str, Any]:
    """
    Walk the result dict and verify grounding for all FeatureValue-like
    sub-dicts. Lowers confidence on failures and appends warnings.
    NEVER deletes values.

    Args:
        result_dict: The extraction result dict (model.model_dump()).
        pages: All PDF pages (for full-text lookup).
        warnings: Mutable warnings list.

    Returns:
        Modified result dict with updated confidence values.
    """
    # Build a lookup of page_num -> text
    page_texts: dict[int, str] = {p.page_num: p.full_text for p in pages}
    _ground_recursive(result_dict, page_texts, warnings, path="")
    return result_dict


def _ground_recursive(
    obj: Any,
    page_texts: dict[int, str],
    warnings: list[str],
    path: str,
) -> None:
    """Recursively ground all FeatureValue-like dicts."""
    if not isinstance(obj, dict):
        return

    # Check if this looks like a FeatureValue (has evidence + source_pages + confidence)
    if "evidence" in obj and "source_pages" in obj and "confidence" in obj:
        _ground_feature_value(obj, page_texts, warnings, path)
        return

    # Recurse into all dict values
    for k, v in obj.items():
        if isinstance(v, dict):
            _ground_recursive(v, page_texts, warnings, f"{path}.{k}" if path else k)
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    _ground_recursive(item, page_texts, warnings, f"{path}.{k}[{i}]")


def _ground_feature_value(
    fv: dict[str, Any],
    page_texts: dict[int, str],
    warnings: list[str],
    path: str,
) -> None:
    """Ground a single FeatureValue dict."""
    source_pages: list[int] = fv.get("source_pages", [])
    evidence: str | None = fv.get("evidence")
    limit_amount: int | None = fv.get("limit_amount")
    confidence: float = fv.get("confidence", 0.0)

    # Build source text from cited pages
    source_text = " ".join(page_texts.get(pn, "") for pn in source_pages)

    grounding_ok = True

    # ── Check evidence quote ──────────────────────────────────────────────
    if evidence and source_text:
        score = fuzz.partial_ratio(evidence.lower(), source_text.lower())
        if score < _EVIDENCE_MATCH_THRESHOLD:
            msg = (
                f"Grounding FAIL [{path}]: evidence quote not found in source pages "
                f"(score={score}). Evidence: '{evidence[:80]}...'"
            )
            logger.warning(msg)
            warnings.append(msg)
            grounding_ok = False

    # ── Check numeric amount ──────────────────────────────────────────────
    if limit_amount is not None and source_text:
        # Look for the number (with common formatting variants) in source
        if not _number_in_text(limit_amount, source_text):
            msg = (
                f"Grounding FAIL [{path}]: limit_amount={limit_amount} "
                f"not found in cited pages {source_pages}."
            )
            logger.warning(msg)
            warnings.append(msg)
            grounding_ok = False

    # Apply penalty
    if not grounding_ok:
        new_conf = max(0.0, confidence - _GROUNDING_PENALTY)
        fv["confidence"] = new_conf
        if "conditions" not in fv:
            fv["conditions"] = []
        fv["conditions"].append("WARNING: grounding check failed — value may be inaccurate")


def _number_in_text(amount: int, text: str) -> bool:
    """
    Check if *amount* (in rupees) appears in *text* in any common format.
    Handles: "500000", "5,00,000", "5 lakh", "5L".
    """
    # Plain integer
    if str(amount) in text.replace(",", ""):
        return True

    # Indian comma format
    formatted = _format_indian(amount)
    if formatted in text:
        return True

    # Lakh representation
    if amount >= 100_000 and amount % 100_000 == 0:
        lakhs = amount // 100_000
        for variant in [f"{lakhs} lakh", f"{lakhs} lac", f"{lakhs}L", f"{lakhs} L"]:
            if variant.lower() in text.lower():
                return True

    # Crore representation
    if amount >= 10_000_000 and amount % 10_000_000 == 0:
        crores = amount // 10_000_000
        for variant in [f"{crores} crore", f"{crores} cr"]:
            if variant.lower() in text.lower():
                return True

    return False


def _format_indian(n: int) -> str:
    """Format an integer in Indian comma notation (e.g. 500000 -> '5,00,000')."""
    s = str(n)
    if len(s) <= 3:
        return s
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return result
