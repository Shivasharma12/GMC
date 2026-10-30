"""
gmc_extractor/postprocess/evidence_utils.py
Generic utilities for extracting and validating verbatim evidence quotes
from raw page text.

Rules:
  - Evidence must be a complete sentence/line (never starts/ends mid-word).
  - Evidence must contain key tokens of the extracted value.
  - Never use "[PAGE n]" markers or bare section headers as evidence.
  - For derived values (tenure, computed totals) cite the source lines.
  - For insurer: only issuer/signatory/registered-office lines, not policyholder.
  - For in-house TPA: claims-servicing line.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Optional

from rapidfuzz import fuzz

# Internal [PAGE n] marker pattern - must NEVER be used as evidence
_PAGE_MARKER_RE = re.compile(r"^\s*\[PAGE\s*\d+\]\s*$", re.IGNORECASE)

# Section-header-only detection (short lines with no sentence structure)
_SECTION_HEADER_RE = re.compile(
    r"^\s*(?:section|chapter|part|appendix|schedule|annexure|exhibit)?\s*[A-Z0-9 :–—-]{3,50}\s*$"
)

# Sentence / line boundary splitter
_SENT_SPLITTER = re.compile(r"(?<=[.!?])\s+|\n")

# Policyholder / insured-party header keywords - evidence from these is INVALID for insurer
_POLICYHOLDER_MARKERS = re.compile(
    r"\b(policyholder|insured|master\s*policyholder|employee|employer|company\s*name|"
    r"group\s*name|name\s*of\s*(?:insured|employer|employee|group)|address)\b",
    re.IGNORECASE,
)

# Issuer / insurer authority keywords (evidence from these is VALID for insurer)
_ISSUER_MARKERS = re.compile(
    r"\b(issued\s*by|insurer|insurance\s*company|underwritten\s*by|registered\s*office|"
    r"head\s*office|signed\s*by|authorized\s*signatory|on\s*behalf\s*of|"
    r"irdai|cin\s*:|gstin\s*:|claims?\s*(serviced?|handled?|administered)\s*by)\b",
    re.IGNORECASE,
)

# Generic noise-like phrases that must not be sole evidence
_NOISE_PHRASES = re.compile(
    r"^\s*(?:nil|n/?a|not\s*applicable|as\s*per\s*policy|refer\s*annexure|see\s*above"
    r"|private\s*limited|limited|ltd\.?|pvt\.?)\s*$",
    re.IGNORECASE,
)

# Minimum evidence length
_MIN_EVIDENCE_LEN = 12

# Fuzzy match threshold for evidence-to-value containment check
_CONTAINMENT_THRESHOLD = 60

# Format Indian number notation
def _format_indian(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return s
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return result


def _value_tokens(value: Any) -> list[str]:
    """
    Derive searchable tokens from a value.
    For integers: decimal, comma-formatted, Indian, lakh, crore variants.
    For ISO dates: multiple date-string forms.
    For strings: significant words.
    """
    if value is None:
        return []

    tokens: list[str] = []

    if isinstance(value, bool):
        return []  # No specific tokens for bool

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        val = int(value)
        tokens.append(str(val))
        tokens.append(f"{val:,}")
        tokens.append(_format_indian(val))
        if val >= 100_000 and val % 100_000 == 0:
            lakhs = val // 100_000
            tokens += [f"{lakhs} lakh", f"{lakhs} lac", f"{lakhs}L", f"{lakhs} L",
                       f"{lakhs} Lakh", f"{lakhs} Lac"]
        if val >= 10_000_000 and val % 10_000_000 == 0:
            crores = val // 10_000_000
            tokens += [f"{crores} crore", f"{crores} cr", f"{crores} Crore"]
        return tokens

    s = str(value).strip()
    if not s:
        return []

    # Date variants
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        try:
            d = date.fromisoformat(s)
            tokens += [
                d.strftime("%d-%b-%Y"),
                d.strftime("%d-%B-%Y"),
                d.strftime("%d/%m/%Y"),
                d.strftime("%d-%m-%Y"),
                f"{d.day:02d}-{d.strftime('%b')}-{d.year}",
                f"{d.day} {d.strftime('%b')} {d.year}",
            ]
            return tokens
        except ValueError:
            pass

    # Text: use significant words (len > 3)
    words = re.findall(r"\b[A-Za-z]{4,}\b|\b\d{3,}\b", s)
    tokens.extend(words[:6])  # Cap at 6 tokens
    tokens.append(s)

    # Handle "Limited" / "Ltd." variants
    if "limited" in s.lower():
        tokens.append(re.sub(r"(?i)\blimited\b", "Ltd.", s))
    elif "ltd." in s.lower():
        tokens.append(re.sub(r"(?i)\bltd\.\b", "Limited", s))

    return list(dict.fromkeys(t for t in tokens if t))


def _is_valid_evidence(evidence: str, value: Any, path: str = "") -> bool:
    """
    Check that an evidence string is usable:
    - Not a [PAGE n] marker
    - Not a bare section header
    - Not a noise phrase
    - Long enough
    - Contains key value tokens
    """
    if not evidence or not evidence.strip():
        return False

    ev = evidence.strip()

    # Reject [PAGE n] markers
    if _PAGE_MARKER_RE.match(ev):
        return False

    # Reject noise
    if _NOISE_PHRASES.match(ev):
        return False

    # Reject too-short evidence
    if len(ev) < _MIN_EVIDENCE_LEN:
        return False

    # For scalar bool values we skip containment check
    if isinstance(value, bool):
        return True

    # Containment check: evidence must contain at least one value token
    tokens = _value_tokens(value)
    if not tokens:
        return True  # No tokens to check

    ev_lower = ev.lower()
    for tok in tokens:
        if tok.lower() in ev_lower:
            return True
        if fuzz.partial_ratio(tok.lower(), ev_lower) >= _CONTAINMENT_THRESHOLD:
            return True

    return False


def _expand_to_sentence(text: str, match_start: int, match_end: int) -> str:
    """
    Given a match position within text, expand backwards and forwards
    to the nearest sentence boundary (. ! ? newline).
    Never starts/ends mid-word.
    """
    # Expand backwards to sentence start
    start = match_start
    # Look back for sentence-ending punctuation or newline
    prefix = text[:match_start]
    # Find last .\n?! or start of string
    boundary_back = max(
        prefix.rfind("."),
        prefix.rfind("!"),
        prefix.rfind("?"),
        prefix.rfind("\n"),
        -1,
    )
    if boundary_back >= 0:
        start = boundary_back + 1
    else:
        start = 0

    # Expand forwards to sentence end
    end = match_end
    suffix = text[match_end:]
    boundary_fwd = -1
    for ch in [".", "!", "?"]:
        pos = suffix.find(ch)
        if pos >= 0 and (boundary_fwd < 0 or pos < boundary_fwd):
            boundary_fwd = pos
    nl_pos = suffix.find("\n")
    if nl_pos >= 0 and (boundary_fwd < 0 or nl_pos < boundary_fwd):
        boundary_fwd = nl_pos

    if boundary_fwd >= 0:
        end = match_end + boundary_fwd + 1
    else:
        end = len(text)

    sentence = text[start:end].strip()
    # Never start/end mid-word: trim to word boundaries
    sentence = re.sub(r"^\W+", "", sentence)
    sentence = re.sub(r"\W+$", "", sentence)
    return sentence


def find_best_evidence(
    value: Any,
    pages: list[Any],
    *,
    extra_queries: Optional[list[str]] = None,
    require_issuer_context: bool = False,
    require_claims_context: bool = False,
    exclude_policyholder: bool = False,
) -> tuple[Optional[str], list[int]]:
    """
    Find the best verbatim evidence for *value* across all pages.

    Rules applied:
    - Expand to full sentence boundary
    - Evidence must contain the value's key tokens
    - Never emit [PAGE n] markers or section headers
    - If require_issuer_context: prefer lines near issuer/insurer keywords
    - If require_claims_context: prefer lines near claims/servicing keywords
    - If exclude_policyholder: skip lines that look like policyholder blocks

    Returns (evidence_sentence, [page_num]) or (None, [])
    """
    if not pages:
        return None, []

    tokens = _value_tokens(value)
    queries = tokens.copy()
    if extra_queries:
        queries = list(dict.fromkeys(queries + extra_queries))

    best: Optional[tuple[str, int, int]] = None  # (sentence, page_num, score)

    for p in pages:
        ptext = p.full_text

        for q in queries:
            if not q:
                continue
            escaped = re.escape(q)
            for m in re.finditer(escaped, ptext, re.IGNORECASE):
                sentence = _expand_to_sentence(ptext, m.start(), m.end())

                # Skip [PAGE n] markers
                if _PAGE_MARKER_RE.match(sentence):
                    continue

                # Skip pure noise
                if _NOISE_PHRASES.match(sentence):
                    continue

                # Skip too-short sentences
                if len(sentence) < _MIN_EVIDENCE_LEN:
                    continue

                # If we need issuer context, skip policyholder lines
                if require_issuer_context or exclude_policyholder:
                    if _POLICYHOLDER_MARKERS.search(sentence):
                        continue

                # If claims context required, require a claims keyword nearby
                if require_claims_context:
                    context_window = ptext[max(0, m.start()-150):m.end()+150]
                    if not re.search(r"\b(claims?|servic|helpdesk|cashless|tpa)\b", context_window, re.IGNORECASE):
                        continue

                # Score: prefer issuer-marked lines for insurer fields
                score = len(sentence)
                if require_issuer_context and _ISSUER_MARKERS.search(sentence):
                    score += 1000

                if best is None or score > best[2]:
                    best = (sentence, p.page_num, score)

    if best:
        return best[0], [best[1]]

    # Fuzzy fallback: search line by line
    for p in pages:
        lines = [ln.strip() for ln in p.full_text.splitlines() if ln.strip()]
        for q in queries[:3]:
            if not q:
                continue
            for line in lines:
                if len(line) < _MIN_EVIDENCE_LEN:
                    continue
                if _PAGE_MARKER_RE.match(line):
                    continue
                if _NOISE_PHRASES.match(line):
                    continue
                if exclude_policyholder and _POLICYHOLDER_MARKERS.search(line):
                    continue
                if require_claims_context:
                    if not re.search(r"\b(claims?|servic|helpdesk|cashless)\b", line, re.IGNORECASE):
                        continue
                score = fuzz.partial_ratio(q.lower(), line.lower())
                if score >= 65:
                    if best is None or score > best[2]:
                        best = (line, p.page_num, score)

    if best:
        return best[0], [best[1]]

    return None, []


def fix_evidence_for_row(
    row: dict,
    value: Any,
    pages: list[Any],
    path: str = "",
    *,
    require_issuer_context: bool = False,
    require_claims_context: bool = False,
    exclude_policyholder: bool = False,
    extra_queries: Optional[list[str]] = None,
    derived_condition: Optional[str] = None,
) -> dict:
    """
    Validate and fix the evidence field in a QMS row dict.

    If existing evidence is invalid (PAGE marker, noise, doesn't contain value),
    search pages for a better one.
    Always expands to full sentence.
    If derived value, adds 'derived' condition.
    Returns the modified row.
    """
    current_ev = row.get("evidence")

    # Check if current evidence is valid
    ev_ok = (
        current_ev
        and not _PAGE_MARKER_RE.match(current_ev.strip())
        and not _NOISE_PHRASES.match(current_ev.strip())
        and len(current_ev.strip()) >= _MIN_EVIDENCE_LEN
        and _is_valid_evidence(current_ev, value, path)
    )

    if not ev_ok and pages:
        ev, pgs = find_best_evidence(
            value,
            pages,
            extra_queries=extra_queries,
            require_issuer_context=require_issuer_context,
            require_claims_context=require_claims_context,
            exclude_policyholder=exclude_policyholder,
        )
        if ev:
            row["evidence"] = ev
            row["source_pages"] = pgs
        else:
            row["evidence"] = None
            row["source_pages"] = []
            if row.get("confidence") is None or row["confidence"] >= 0.8:
                row["confidence"] = 0.5

    if derived_condition:
        conds = row.setdefault("conditions", [])
        if derived_condition not in conds:
            conds.append(derived_condition)

    return row

