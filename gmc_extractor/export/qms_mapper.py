"""
gmc_extractor/export/qms_mapper.py
Maps the nested ExtractionResult to flat QMS rows (JSON + CSV)
using config/qms_mapping.yaml.
Generic logic only — no hardcoded policy values, page numbers, or insurer names.
"""
from __future__ import annotations

import csv
import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Any, Optional

from rapidfuzz import fuzz

from gmc_extractor.config import Settings
from gmc_extractor.postprocess.evidence_utils import find_best_evidence, fix_evidence_for_row
from gmc_extractor.schema.output import ExtractionResult

logger = logging.getLogger(__name__)

_CSV_COLUMNS = [
    "qms_field",
    "label",
    "status",
    "limit_amount",
    "limit_text",
    "limit_percent_of_si",
    "limit_days",
    "conditions",
    "source_pages",
    "evidence",
    "confidence",
]


def write_qms(
    result: ExtractionResult,
    output_stem: Path,
    settings: Settings,
    pages: Optional[list[Any]] = None,
) -> None:
    """
    Write flat QMS JSON and CSV files from the ExtractionResult.

    Args:
        result: The completed ExtractionResult.
        output_stem: Path stem (without extension), e.g. output/policy.
        settings: Global settings (for QMS mapping config).
        pages: Optional list of PageDoc objects for text grounding.
    """
    mapping: dict[str, Any] = settings.qms_mapping
    result_dict = result.model_dump(mode="json")

    rows: list[dict[str, Any]] = []
    for internal_path, meta in mapping.items():
        value = _get_nested(result_dict, internal_path)
        row = _make_row(internal_path, meta, value, root_dict=result_dict, pages=pages)
        rows.append(row)

    # Write JSON
    json_path = output_stem.parent / (output_stem.name + ".qms.json")
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Written QMS JSON: %s", json_path)

    # Write CSV
    csv_path = output_stem.parent / (output_stem.name + ".qms.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            csv_row = {k: _csv_value(row.get(k)) for k in _CSV_COLUMNS}
            writer.writerow(csv_row)
    logger.info("Written QMS CSV: %s", csv_path)


def _get_nested(data: dict, dotpath: str) -> Any:
    """Traverse a nested dict using dot-notation path. Returns None if not found."""
    parts = dotpath.split(".")
    obj = data
    for part in parts:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
        if obj is None:
            return None
    return obj


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


def _find_quote_in_pages(query: Any, pages: Optional[list[Any]]) -> tuple[Optional[str], list[int]]:
    """
    Generic search for a query string, integer, or date across document pages.
    Returns (verbatim_sentence, [page_num]) if found.
    """
    if not pages or query is None:
        return None, []

    s_query = str(query).strip()
    if not s_query or s_query.lower() in ("none", "null", "false", "true"):
        return None, []

    variants: list[str] = [s_query]

    # Handle numeric representations
    if isinstance(query, (int, float)) or (isinstance(query, str) and query.isdigit()):
        val = int(query)
        variants.append(f"{val:,}")
        variants.append(_format_indian(val))

    # Handle date representations (e.g. 2022-04-02 -> 02-Apr-2022, 02-April-2022, etc.)
    if isinstance(query, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", query):
        try:
            d = date.fromisoformat(query)
            variants.append(d.strftime("%d-%b-%Y"))
            variants.append(d.strftime("%d-%B-%Y"))
            variants.append(d.strftime("%d/%m/%Y"))
            variants.append(d.strftime("%d-%m-%Y"))
            variants.append(f"{d.day:02d}-{d.strftime('%b')}-{d.year}")
            variants.append(f"{d.day} {d.strftime('%b')} {d.year}")
        except ValueError:
            pass

    # Normalized text variants (e.g. Limited -> Ltd.)
    if "limited" in s_query.lower():
        variants.append(re.sub(r"(?i)\blimited\b", "Ltd.", s_query))
        variants.append(re.sub(r"(?i)\bltd\.\b", "Limited", s_query))

    for p in pages:
        ptext = p.full_text
        for v in variants:
            escaped = re.escape(v)
            m = re.search(rf"([^\n.;]{{0,60}}\b{escaped}\b[^\n.;]{{0,60}})", ptext, re.IGNORECASE)
            if m:
                quote = m.group(1).strip()
                if len(quote) >= len(v):
                    return quote, [p.page_num]

    # Fuzzy match fallback against sentences/lines in pages
    for p in pages:
        for line in p.full_text.splitlines():
            line_str = line.strip()
            if len(line_str) < 5:
                continue
            for v in variants:
                if fuzz.partial_ratio(v.lower(), line_str.lower()) >= 65:
                    return line_str, [p.page_num]

    return None, []


def _make_row(
    internal_path: str,
    meta: dict,
    value: Any,
    root_dict: Optional[dict] = None,
    pages: Optional[list[Any]] = None,
) -> dict[str, Any]:
    """Build a single QMS output row from a mapping entry and its value."""
    qms_field = meta.get("qms_field", internal_path)
    label = meta.get("label", internal_path)

    row: dict[str, Any] = {
        "qms_field": qms_field,
        "label": label,
        "status": None,
        "limit_amount": None,
        "limit_text": None,
        "limit_percent_of_si": None,
        "limit_days": None,
        "conditions": [],
        "source_pages": [],
        "evidence": None,
        "confidence": None,
    }

    # ── SPECIAL HANDLING 0: Insurer Name (IDENT_INSURER) ───────────────────
    if qms_field == "IDENT_INSURER":
        if value:
            row["status"] = "covered"
            row["limit_text"] = str(value)
            ev, pgs = find_best_evidence(
                str(value),
                pages,
                require_issuer_context=True,
                exclude_policyholder=True,
                extra_queries=["issued by", "insurer", "insurance company", "registered office", "on behalf of", "authorized signatory"],
            )
            row["evidence"] = ev
            row["source_pages"] = pgs
            row["confidence"] = 1.0 if ev else 0.5
            return row
        else:
            row["status"] = "not_mentioned"
            return row

    # ── SPECIAL HANDLING 1: TPA (IDENT_TPA) ──────────────────────────────────
    if qms_field == "IDENT_TPA":
        is_in_house = False
        if not value or str(value).strip().lower() in ("none", "direct", "in-house", "self", "n/a", "null"):
            is_in_house = True
        elif re.search(r"\b(direct|broker|intermediary|agent|sales\s+channel)\b", str(value), re.IGNORECASE):
            is_in_house = True

        if is_in_house:
            row["status"] = "not_covered"
            row["limit_text"] = "None (claims handled in-house by insurer)"
            row["conditions"] = ["None (claims handled in-house by insurer)"]
            ev, pgs = find_best_evidence("claims", pages, extra_queries=["Claims", "Assistance", "servicing", "helpdesk", "cashless", "toll free"], require_claims_context=True)
            row["evidence"] = ev
            row["source_pages"] = pgs
            row["confidence"] = 1.0 if ev else 0.5
            return row
        else:
            row["status"] = "covered"
            row["limit_text"] = str(value)
            ev, pgs = find_best_evidence(str(value), pages, extra_queries=["TPA", "third party administrator"])
            row["evidence"] = ev
            row["source_pages"] = pgs
            row["confidence"] = 1.0 if ev else 0.5
            return row

    # ── SPECIAL HANDLING 2: Sum Insured Tiers (POL_SI_TIERS) ─────────────────
    if qms_field == "POL_SI_TIERS":
        if isinstance(value, list) and value:
            amounts: list[int] = []
            grades: list[str] = []
            tier_pages: set[int] = set()
            tier_evidences: list[str] = []

            for item in value:
                if isinstance(item, dict):
                    amt = item.get("amount")
                    grd = item.get("grade_or_category") or item.get("category") or item.get("grade")
                    pgs = item.get("source_pages", [])
                    ev = item.get("evidence")
                else:
                    amt = getattr(item, "amount", None)
                    grd = getattr(item, "grade_or_category", None) or getattr(item, "category", None)
                    pgs = getattr(item, "source_pages", [])
                    ev = getattr(item, "evidence", None)

                if amt is not None:
                    amounts.append(int(amt))
                if grd:
                    grades.append(str(grd))
                if pgs:
                    tier_pages.update(pgs)
                if ev:
                    tier_evidences.append(str(ev))

            sorted_amounts = sorted(list(set(amounts)))
            row["status"] = "covered" if sorted_amounts else "not_mentioned"
            row["limit_text"] = sorted_amounts
            row["conditions"] = list(dict.fromkeys(grades))

            if tier_evidences:
                row["evidence"] = "; ".join(tier_evidences)
                row["source_pages"] = sorted(list(tier_pages))
            else:
                ev, pgs = find_best_evidence("graded sum insured", pages, extra_queries=["sum insured", "SI tiers", "graded"])
                row["evidence"] = ev
                row["source_pages"] = pgs

            row["confidence"] = 1.0 if row["evidence"] else 0.5
            return row
        else:
            row["status"] = "not_mentioned"
            return row

    # ── SPECIAL HANDLING 3: Total Sum Insured (POL_TOTAL_SUM_INSURED) ────────
    if qms_field == "POL_TOTAL_SUM_INSURED":
        if value is not None and isinstance(value, (int, float)):
            row["status"] = "covered"
            row["limit_amount"] = int(value)
            ev, pgs = find_best_evidence(int(value), pages, extra_queries=["total sum insured"])
            row["evidence"] = ev
            row["source_pages"] = pgs
            row["confidence"] = 1.0 if ev else 0.5
            return row
        else:
            row["status"] = "not_mentioned"
            return row

    # ── SPECIAL HANDLING 4: Previous Year Inception (POL_PREV_INCEPTION) ────
    if qms_field == "POL_PREV_INCEPTION":
        if value:
            row["status"] = "covered"
            row["limit_text"] = str(value)
            cond_note = "Treated uploaded document start date as previous inception date per expiring policy baseline rule"
            row["conditions"] = [cond_note]
            ev, pgs = find_best_evidence(str(value), pages, extra_queries=["policy period", "start date", "inception date", "period of insurance"])
            row["evidence"] = ev
            row["source_pages"] = pgs
            row["confidence"] = 1.0 if ev else 0.5
            return row
        else:
            row["status"] = "not_mentioned"
            return row

    # ── SPECIAL HANDLING 5: Demographics (Absence of census breakdown) ───────
    if qms_field in ("DEM_SPOUSES", "DEM_CHILDREN", "DEM_PARENTS"):
        if value is None:
            row["status"] = "not_mentioned"
            row["conditions"] = ["member-wise annexure not present in document"]
            row["confidence"] = None
            row["evidence"] = None
            row["source_pages"] = []
            return row

    if qms_field == "DEM_DEPENDENTS":
        if value is not None:
            row["status"] = "covered"
            row["limit_amount"] = int(value)
            ev, pgs = find_best_evidence("dependents", pages, extra_queries=["Dependents", str(int(value)) if value else ""])
            row["evidence"] = ev
            row["source_pages"] = pgs
            row["confidence"] = 1.0 if ev else 0.5
            return row
        else:
            row["status"] = "not_mentioned"
            return row

    if qms_field == "DEM_TOTAL_COMPUTED":
        if value is not None:
            row["status"] = "covered"
            row["limit_amount"] = int(value)
            row["conditions"] = ["Computed from employee + dependent counts"]
            ev, pgs = find_best_evidence("primary insured", pages, extra_queries=["total", "members", "primary insured members"])
            row["evidence"] = ev
            row["source_pages"] = pgs
            row["confidence"] = 1.0 if ev else 0.5
            return row
        else:
            row["status"] = "not_mentioned"
            return row

    # ── SPECIAL HANDLING 6: Co-Pay and Sub-Limits (COPAY_SUBLIMITS) ──────────
    if qms_field == "COPAY_SUBLIMITS":
        if isinstance(value, list) and value:
            row["status"] = "covered"
            row["limit_text"] = value  # Keep real list in JSON
            conds_list = []
            for s in value:
                if isinstance(s, dict):
                    item_name = s.get("item") or "Co-Pay / Sub-Limit"
                    pct = s.get("percent") or s.get("limit_percent")
                    amt = s.get("amount") or s.get("limit_amount")
                    lt = s.get("limit_text")
                    exc = s.get("exceptions")
                    exc_str = f" (except: {exc})" if exc else ""
                    if pct is not None:
                        conds_list.append(f"{item_name}: {pct}% co-pay{exc_str}")
                    elif amt is not None:
                        conds_list.append(f"{item_name}: Rs. {_format_indian(amt)}{exc_str}")
                    elif lt and lt != "None%":
                        conds_list.append(f"{item_name}: {lt}{exc_str}")
                    else:
                        conds_list.append(f"{item_name}{exc_str}")
            row["conditions"] = conds_list
            row["source_pages"] = sorted(list({s.get("page") for s in value if isinstance(s, dict) and s.get("page")}))
            evs = [s.get("evidence") for s in value if isinstance(s, dict) and s.get("evidence")]
            row["evidence"] = "; ".join(evs)[:300] if evs else None
            row["confidence"] = 1.0 if row["evidence"] else 0.5
            return row
        else:
            row["status"] = "not_mentioned"
            return row

    # ── SPECIAL HANDLING 7: Waiver Conditions (BUF_WAIVER_CONDITIONS) ────────
    if qms_field == "BUF_WAIVER_CONDITIONS":
        if isinstance(value, list) and value:
            row["status"] = "covered"
            row["limit_text"] = [
                w.get("clause") or w.get("waiver_name") if isinstance(w, dict) else str(w)
                for w in value
            ]
            row["conditions"] = value  # Keep real list in JSON
            row["source_pages"] = sorted(list({w.get("page") for w in value if isinstance(w, dict) and w.get("page")}))
            evs = [w.get("evidence") for w in value if isinstance(w, dict) and w.get("evidence")]
            row["evidence"] = "; ".join(evs)[:300] if evs else None
            row["confidence"] = 1.0 if row["evidence"] else 0.5
            return row
        else:
            row["status"] = "not_mentioned"
            return row

    # ── DEFAULT VALUE PARSING ────────────────────────────────────────────────
    if value is None:
        row["status"] = "not_mentioned"
        return row

    # FeatureValue-like dict
    if isinstance(value, dict) and "status" in value:
        row["status"] = value.get("status")
        row["limit_amount"] = value.get("limit_amount")
        row["limit_text"] = value.get("limit_text")
        row["limit_percent_of_si"] = value.get("limit_percent_of_si")
        row["limit_days"] = value.get("limit_days")
        row["conditions"] = value.get("conditions", [])
        row["source_pages"] = value.get("source_pages", [])
        row["evidence"] = value.get("evidence")
        row["confidence"] = value.get("confidence")

        # Strict Grounding Gate enforcement
        if row.get("status") == "needs_review":
            row["limit_amount"] = None
            row["limit_text"] = None
            row["limit_percent_of_si"] = None
            row["limit_days"] = None
            row["evidence"] = None
            row["source_pages"] = []
            row["confidence"] = min(row.get("confidence") or 0.2, 0.2)
            if value.get("unverified_candidate"):
                row["unverified_candidate"] = value.get("unverified_candidate")
            return row

        # Ground evidence quote if empty or missing pages
        if pages and (not row["evidence"] or not row["source_pages"]):
            query_val = row["limit_amount"] or row["limit_text"]
            ev, pgs = find_best_evidence(query_val, pages)
            if ev:
                row["evidence"] = ev
                row["source_pages"] = pgs

        # Requirement 4: Rows with empty evidence must not get confidence 1.0
        if not row.get("evidence"):
            row["source_pages"] = []
            if row.get("confidence") is not None and row["confidence"] >= 0.8:
                row["confidence"] = 0.5

    # Scalar value (bool, int, str, date, list)
    else:
        if isinstance(value, bool):
            row["status"] = "covered" if value else "not_covered"
            row["limit_text"] = str(value)
            if not value and internal_path.startswith("policy_details.family_structure"):
                conds = row.setdefault("conditions", [])
                derived_fam = "Derived: not covered per family definition in policy"
                if derived_fam not in conds:
                    conds.append(derived_fam)
        elif isinstance(value, int):
            row["limit_amount"] = value
            row["status"] = "covered"
            if internal_path == "policy_details.tenure_months" or qms_field == "POL_TENURE":
                conds = row.setdefault("conditions", [])
                derived_ten = "Derived from policy start and end dates"
                if derived_ten not in conds:
                    conds.append(derived_ten)
        elif isinstance(value, str):
            row["limit_text"] = value
            row["status"] = "covered" if value else "not_mentioned"
        elif isinstance(value, list):
            row["limit_text"] = value
            row["status"] = "covered" if value else "not_mentioned"

        # Inherit parent group metadata if present
        if root_dict:
            parts = internal_path.split(".")
            parent_key = parts[0]
            parent = root_dict.get(parent_key)
            if isinstance(parent, dict):
                if not row["source_pages"]:
                    row["source_pages"] = parent.get("source_pages", [])
                if row["evidence"] is None:
                    row["evidence"] = parent.get("evidence")
                if parent.get("confidence") is not None:
                    row["confidence"] = parent.get("confidence")

        # Search pages for verbatim evidence and exact page
        ev, pgs = find_best_evidence(value, pages)
        if not ev and isinstance(value, bool):
            # For family structure booleans, search for family structure line
            ev, pgs = find_best_evidence("family structure", pages, extra_queries=["definition of family", "dependents", "members"])

        if ev:
            row["evidence"] = ev
            row["source_pages"] = pgs
            row["confidence"] = 1.0
        elif not row.get("evidence"):
            row["source_pages"] = []
            row["confidence"] = 0.5  # Requirement 4: never 1.0 if empty evidence

    return row


def _csv_value(v: Any) -> str:
    """Convert a value to a clean CSV-safe string."""
    if v is None:
        return ""
    if isinstance(v, list):
        items: list[str] = []
        for x in v:
            if isinstance(x, dict):
                parts = []
                for key in ("waiver_name", "item", "type", "disease", "clause", "percent", "amount", "limit_text", "limit_percent", "limit_amount", "exceptions", "page"):
                    val = x.get(key)
                    if val is not None and str(val).strip():
                        parts.append(f"{val}")
                items.append(" | ".join(parts) if parts else str(x))
            else:
                items.append(str(x))
        return "; ".join(items)
    return str(v)
