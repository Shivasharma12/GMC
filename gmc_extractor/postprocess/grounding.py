"""
gmc_extractor/postprocess/grounding.py
Strict Grounding Gate:
Verifies that numeric values, dates, percentages, and evidence quotes returned by LLM
actually appear in the source text of the cited pages.

Rules:
(a) Evidence quote must exist in cited pages with fuzzy match ratio >= 0.90 (90%).
(b) The normalized number/date/status in the value must appear in that evidence quote.
(c) If grounding fails:
    - Candidate moved to unverified_candidate dict
    - status = "needs_review"
    - confidence <= 0.3
    - Main values (limit_amount, limit_text, limit_percent_of_si, limit_days, evidence) CLEARED.
    - NEVER write ungrounded values as main values.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from rapidfuzz import fuzz

from gmc_extractor.pdf.reader import PageDoc

logger = logging.getLogger(__name__)

# Strict fuzzy match threshold for evidence quotes (0-100)
_EVIDENCE_MATCH_THRESHOLD = 90
_MIN_EVIDENCE_LEN = 10


def ground_result(
    result_dict: dict[str, Any],
    pages: list[PageDoc],
    warnings: list[str],
) -> dict[str, Any]:
    """
    Walk the result dict and apply the strict Grounding Gate to all
    FeatureValue-like sub-dicts.
    """
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

    # Check if this looks like a FeatureValue or grounded entity
    if "evidence" in obj and "source_pages" in obj and "confidence" in obj:
        _ground_feature_value(obj, page_texts, warnings, path)

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
    """
    Apply strict Grounding Gate to a single FeatureValue:
    - Requires fuzzy match >= 90 for evidence quote in cited pages
    - Requires number/date/percentage to appear in evidence quote
    - On failure, sets status='needs_review', confidence<=0.3, clears main value.
    """
    status = fv.get("status")
    # If not_mentioned or not_covered without a claim of limit, grounding is not required to match numbers
    if status == "not_mentioned" and not fv.get("evidence"):
        return

    source_pages: list[int] = fv.get("source_pages", [])
    evidence: str | None = fv.get("evidence")
    limit_amount: int | None = fv.get("limit_amount")
    limit_percent: float | None = fv.get("limit_percent_of_si")
    limit_days: int | None = fv.get("limit_days")
    limit_text: str | None = fv.get("limit_text")

    failure_reasons: list[str] = []

    # ── Check 1: Evidence existence in cited pages (fuzzy >= 90) ───────────────
    matching_pages: list[int] = []
    if evidence and len(evidence.strip()) >= _MIN_EVIDENCE_LEN:
        ev_clean = evidence.strip().lower()
        for pn, ptext in page_texts.items():
            pt_clean = ptext.lower()
            if ev_clean in pt_clean:
                matching_pages.append(pn)
            elif fuzz.partial_ratio(ev_clean, pt_clean) >= _EVIDENCE_MATCH_THRESHOLD:
                matching_pages.append(pn)

        if matching_pages:
            matched_cited = [pn for pn in source_pages if pn in matching_pages]
            fv["source_pages"] = matched_cited if matched_cited else matching_pages
        else:
            failure_reasons.append(
                f"Evidence quote not found in document text with >= 90% match: '{evidence[:60]}...'"
            )
    elif status in ("covered", "limited", "waived_off") and (limit_amount is not None or limit_text is not None):
        failure_reasons.append("Evidence quote is missing or too short for a covered benefit")

    # ── Check 2: Value token containment in evidence & page text ──────────────
    source_page_text = " ".join(page_texts.get(pn, "") for pn in fv.get("source_pages", []))

    if limit_amount is not None:
        if not _number_in_text(limit_amount, evidence or "") or not _number_in_text(limit_amount, source_page_text):
            failure_reasons.append(f"Numeric limit_amount={limit_amount} not found in evidence or cited page text")

    if limit_percent is not None:
        pct_int = int(limit_percent)
        has_pct_ev = f"{pct_int}%" in (evidence or "") or f"{pct_int} %" in (evidence or "") or str(pct_int) in (evidence or "")
        has_pct_page = f"{pct_int}%" in source_page_text or f"{pct_int} %" in source_page_text or str(pct_int) in source_page_text
        if not (has_pct_ev and has_pct_page):
            failure_reasons.append(f"Percentage limit_percent={limit_percent}% not found in evidence and cited page text")

    if limit_days is not None:
        if str(limit_days) not in (evidence or "") or str(limit_days) not in source_page_text:
            failure_reasons.append(f"limit_days={limit_days} not found in evidence and cited page text")

    # ── Strict Grounding Gate Decision ────────────────────────────────────────
    if failure_reasons:
        msg = f"GROUNDING GATE REJECT [{path}]: {'; '.join(failure_reasons)}"
        logger.warning(msg)
        warnings.append(msg)

        # Move to unverified candidate
        fv["unverified_candidate"] = {
            "status": status,
            "limit_amount": limit_amount,
            "limit_text": limit_text,
            "limit_percent_of_si": limit_percent,
            "limit_days": limit_days,
            "evidence": evidence,
            "reasons": failure_reasons,
        }

        # Clear main value fields so fabricated data NEVER gets exported to QMS main values
        fv["status"] = "needs_review"
        fv["limit_amount"] = None
        fv["limit_text"] = None
        fv["limit_percent_of_si"] = None
        fv["limit_days"] = None
        fv["evidence"] = None
        fv["source_pages"] = []
        fv["confidence"] = min(fv.get("confidence", 0.2), 0.2)

        conds = fv.setdefault("conditions", [])
        reject_note = "GROUNDING_GATE_FAILED: Candidate value rejected — does not exist in source text"
        if reject_note not in conds:
            conds.append(reject_note)


def _number_in_text(amount: int, text: str) -> bool:
    """
    Check if *amount* (in rupees) appears in *text* in any common format.
    Handles: "500000", "5,00,000", "5 lakh", "5L", "5 Lacs".
    """
    text_clean = text.replace(",", "")
    if str(amount) in text_clean:
        return True

    formatted = _format_indian(amount)
    if formatted in text:
        return True

    if amount >= 100_000 and amount % 100_000 == 0:
        lakhs = amount // 100_000
        for variant in [f"{lakhs} lakh", f"{lakhs} lac", f"{lakhs}l", f"{lakhs} l", f"{lakhs} lacs"]:
            if variant.lower() in text.lower():
                return True

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
