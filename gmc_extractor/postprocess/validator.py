"""
gmc_extractor/postprocess/validator.py
Business rule validation for the ExtractionResult.
Violations become warnings, not crashes.

All logic is generic — no hardcoded carrier names, page numbers, or policy values.
"""
from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any, Optional

from gmc_extractor.postprocess.evidence_utils import (
    _POLICYHOLDER_MARKERS,
    find_best_evidence,
    _format_indian,
)

logger = logging.getLogger(__name__)


def validate_result(
    result_dict: dict,
    warnings: list[str],
    pages: Optional[list[Any]] = None,
) -> dict:
    """
    Run business rule checks on the extraction result dict.
    Appends warnings for any violations — never raises.
    """
    _check_policy_dates(result_dict, warnings)
    _check_si_tiers(result_dict, warnings)
    _check_premium(result_dict, warnings)
    _check_demographics(result_dict, warnings)
    _check_percentages(result_dict, warnings)
    _validate_previous_inception(result_dict)
    _validate_sum_insured(result_dict, pages)
    _validate_tpa(result_dict, pages)
    _validate_demographics_rules(result_dict, pages)
    _validate_maternity_metro(result_dict)
    _validate_not_covered_features(result_dict, pages)
    _check_premium_conflicts(result_dict, pages, warnings)
    _validate_disease_capping(result_dict, pages)
    _validate_copay_sublimits(result_dict, pages)
    _validate_waivers(result_dict, pages)
    _fix_waiting_period_days(result_dict)
    _fix_buf_eligibility_evidence(result_dict, pages)
    return result_dict


# ── Structural checks (unchanged) ────────────────────────────────────────────

def _check_policy_dates(result_dict: dict, warnings: list[str]) -> None:
    pd = result_dict.get("policy_details", {})
    start_str = pd.get("policy_start_date")
    end_str = pd.get("policy_end_date")
    tenure = pd.get("tenure_months")

    if start_str and end_str:
        try:
            start = date.fromisoformat(start_str)
            end = date.fromisoformat(end_str)
            if end <= start:
                warnings.append(
                    f"VALIDATION: Policy end date ({end_str}) is not after start date ({start_str})."
                )
            else:
                diff_months = (end.year - start.year) * 12 + (end.month - start.month)
                if tenure is not None and abs(diff_months - tenure) > 1:
                    warnings.append(
                        f"VALIDATION: Stated tenure ({tenure} months) differs from "
                        f"computed tenure ({diff_months} months) by more than 1 month."
                    )
                if not (10 <= diff_months <= 14):
                    warnings.append(
                        f"VALIDATION: Policy duration ({diff_months} months) is unusual "
                        f"for a GMC policy (expected ~12 months)."
                    )
        except ValueError as exc:
            warnings.append(f"VALIDATION: Could not parse policy dates: {exc}")


def _check_si_tiers(result_dict: dict, warnings: list[str]) -> None:
    tiers = result_dict.get("policy_details", {}).get("sum_insured_tiers", [])
    amounts = [t.get("amount") for t in tiers if isinstance(t, dict) and t.get("amount") is not None]
    if len(amounts) > 1 and amounts != sorted(amounts):
        warnings.append(
            f"VALIDATION: Sum insured tiers are not in ascending order: {amounts}"
        )


def _check_premium(result_dict: dict, warnings: list[str]) -> None:
    pd = result_dict.get("policy_details", {})
    excl = pd.get("premium_excluding_gst")
    incl = pd.get("premium_including_gst")
    if excl is not None and incl is not None and incl < excl:
        warnings.append(
            f"VALIDATION: Premium including GST ({incl}) is less than "
            f"excluding GST ({excl}). Possible data error."
        )


def _check_demographics(result_dict: dict, warnings: list[str]) -> None:
    demo = result_dict.get("demographics", {})
    employees = demo.get("num_employees")
    total_stated = demo.get("total_lives_stated")
    total_computed = demo.get("total_lives_computed")

    if employees is not None and total_stated is not None and total_stated < employees:
        warnings.append(
            f"VALIDATION: Total lives ({total_stated}) is less than "
            f"number of employees ({employees})."
        )

    if demo.get("count_mismatch"):
        warnings.append(
            f"VALIDATION: Demographics mismatch — stated total ({total_stated}) "
            f"!= computed total ({total_computed})."
        )


def _check_percentages(result_dict: dict, warnings: list[str]) -> None:
    _walk_check_pct(result_dict, warnings, path="")


def _walk_check_pct(obj: object, warnings: list[str], path: str) -> None:
    if isinstance(obj, dict):
        pct = obj.get("limit_percent_of_si")
        if pct is not None and isinstance(pct, (int, float)):
            if not (0 <= pct <= 100):
                warnings.append(
                    f"VALIDATION: limit_percent_of_si={pct} out of range [0, 100] at {path}"
                )
        for k, v in obj.items():
            _walk_check_pct(v, warnings, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _walk_check_pct(item, warnings, f"{path}[{i}]")


# ── Business rules ────────────────────────────────────────────────────────────

def _validate_previous_inception(result_dict: dict) -> None:
    """
    Treat the uploaded document as the previous/expiring year policy unless
    the text says otherwise. Populate previous_inception_date with policy_start_date.
    """
    pd = result_dict.get("policy_details")
    if not isinstance(pd, dict):
        return

    prev = pd.get("previous_inception_date")
    start = pd.get("policy_start_date")
    conds = pd.setdefault("conditions", [])

    if not prev and start:
        pd["previous_inception_date"] = start
        rule_note = "Treated uploaded document start date as previous inception date per expiring policy baseline rule"
        if rule_note not in conds:
            conds.append(rule_note)


def _validate_sum_insured(result_dict: dict, pages: Optional[list[Any]] = None) -> None:
    """Ensure Total Sum Insured and SI Tiers are captured generically from document text."""
    pd = result_dict.get("policy_details")
    if not isinstance(pd, dict):
        return

    # Total Sum Insured
    if pd.get("total_sum_insured") is None and pages:
        for p in pages:
            m = re.search(r"Total\s+Sum\s+Insured\s*[:\s]+([\d,]+)", p.full_text, re.IGNORECASE)
            if m:
                try:
                    amt = int(m.group(1).replace(",", ""))
                    pd["total_sum_insured"] = amt
                    break
                except ValueError:
                    pass

    # Sum Insured Tiers (generic: any table with graded/tiered SI amounts)
    tiers = pd.get("sum_insured_tiers", [])
    if not tiers and pages:
        for p in pages:
            m = re.search(
                r"(?:Graded\s+Sum\s+[Ii]nsured|Sum\s+Insured\s*(?:Tiers|Options|Slabs)?)\s*[:\s]+([^\n\r.]+)",
                p.full_text, re.IGNORECASE
            )
            if m:
                clause = m.group(1)
                found_amts = [int(x.replace(",", "")) for x in re.findall(r"Rs\.?\s*([\d,]+)", clause, re.IGNORECASE)]
                if not found_amts:
                    # Try Lacs/Lakhs
                    for lakh_m in re.finditer(r"([\d.]+)\s*(?:lakh|lac|lacs)s?", clause, re.IGNORECASE):
                        try:
                            found_amts.append(int(float(lakh_m.group(1)) * 100_000))
                        except ValueError:
                            pass
                if found_amts:
                    sorted_amts = sorted(list(set(found_amts)))
                    pd["sum_insured_tiers"] = [{"amount": a, "grade_or_category": "Graded Sum Insured"} for a in sorted_amts]
                    break


def _validate_tpa(result_dict: dict, pages: Optional[list[Any]] = None) -> None:
    """
    When claims are handled by the insurer itself and no third-party TPA is named,
    ensure status is 'not_covered'. If a real TPA is named, keep it.
    Never use a sales channel / intermediary / broker as TPA.
    Rule 1f: For in-house TPA, cite the claims-servicing line.
    """
    ident = result_dict.get("identity")
    if not isinstance(ident, dict):
        return

    tpa = ident.get("tpa_name")
    is_in_house = False
    if not tpa or str(tpa).strip().lower() in ("none", "direct", "in-house", "self", "n/a", "null", ""):
        is_in_house = True
    elif re.search(r"\b(direct|broker|intermediary|agent|sales\s+channel)\b", str(tpa), re.IGNORECASE):
        is_in_house = True

    if is_in_house:
        ident["tpa_name"] = None
        conds = ident.setdefault("conditions", [])
        in_house_note = "None (claims handled in-house by insurer)"
        if in_house_note not in conds:
            conds.append(in_house_note)

        # Rule 1f: find claims-servicing line as evidence
        if pages:
            ev, pgs = find_best_evidence(
                "claims",
                pages,
                extra_queries=["Claims", "Assistance", "servicing", "helpdesk", "cashless", "toll free"],
                require_claims_context=True,
            )
            if ev:
                ident["evidence"] = ev
                ident["source_pages"] = pgs


def _validate_demographics_rules(result_dict: dict, pages: Optional[list[Any]] = None) -> None:
    """
    Fill total_lives_computed when employees + dependents are known.
    When member census/annexure is not present, flag note.
    Derives dependents = total - employees when total and employees are grounded.
    """
    demo = result_dict.get("demographics")
    if not isinstance(demo, dict):
        return

    emp = demo.get("num_employees")
    dep = demo.get("num_dependents")
    total_stated = demo.get("total_lives_stated")
    conds = demo.setdefault("conditions", [])

    # Try to extract employees from page text if missing
    if emp is None and pages:
        for p in pages:
            m = re.search(r"(?:Total\s+no\s+of\s+employees|Primary\s+Insured\s+Members|Employees)\s*(?:/Primary Members)?\s*[:\|\s]+(\d+)\b", p.full_text, re.IGNORECASE)
            if m:
                try:
                    emp = int(m.group(1))
                    demo["num_employees"] = emp
                    break
                except ValueError:
                    pass

    # Try to extract total lives from page text if missing
    if total_stated is None and pages:
        for p in pages:
            m = re.search(r"(?:Total\s+no\s+of\s+Insured\s+Members|Total\s+Lives|Total\s+Members)\s*[:\|\s]+(\d+)\b", p.full_text, re.IGNORECASE)
            if m:
                try:
                    total_stated = int(m.group(1))
                    demo["total_lives_stated"] = total_stated
                    break
                except ValueError:
                    pass

    # Try to extract dependents from page text if missing
    if dep is None and pages:
        for p in pages:
            m = re.search(r"\bDependents\s*[:\|\s]+(\d+)\b", p.full_text, re.IGNORECASE)
            if m:
                try:
                    dep = int(m.group(1))
                    demo["num_dependents"] = dep
                    break
                except ValueError:
                    pass

    # Derive dependents = total - employees when total and employees are known
    if dep is None and total_stated is not None and emp is not None and total_stated >= emp:
        dep = total_stated - emp
        demo["num_dependents"] = dep
        conds.append(f"Derived: dependents ({dep}) computed from total lives ({total_stated}) - employees ({emp})")

    if emp is not None and dep is not None:
        demo["total_lives_computed"] = emp + dep

    # No individual breakdown → note annexure absent
    if demo.get("num_spouses") is None and demo.get("num_children") is None and demo.get("num_parents") is None:
        annex_note = "member-wise annexure not present in document"
        if annex_note not in conds:
            conds.append(annex_note)


def _validate_not_covered_features(result_dict: dict, pages: Optional[list[Any]] = None) -> None:
    """
    Handle 'NA' / 'Not Covered' cells:
    - Corporate Floater 'Not Covered' with limit 'NA' -> BUF_AMOUNT status: not_covered, limit: None
    - OPD Coverage 'Not Covered' -> OPD status: not_covered, limit: None
    """
    if not pages:
        return

    full_doc = "\n".join(p.full_text for p in pages)

    # Corporate floater check
    if re.search(r"Corporate\s+Floater\s*(?:Limit)?\s*[:\|\s]+(?:Not\s+Covered|NA|Nil)\b", full_doc, re.IGNORECASE):
        bw = result_dict.setdefault("features", {}).setdefault("buffer_waiver", {})
        cba = bw.setdefault("corporate_buffer_amount", {})
        cba["status"] = "not_covered"
        cba["limit_amount"] = None
        cba["limit_text"] = "Not Covered"
        conds = cba.setdefault("conditions", [])
        not_cov_note = "Corporate Floater explicitly Not Covered in policy schedule"
        if not_cov_note not in conds:
            conds.append(not_cov_note)

    # OPD Coverage check
    if re.search(r"OPD\s*(?:Coverage|Treatment)?\s*[:\|\s]+(?:Not\s+Covered|NA|Nil)\b", full_doc, re.IGNORECASE):
        ob_a = result_dict.setdefault("features", {}).setdefault("other_benefits_a", {})
        opd = ob_a.setdefault("opd", {})
        opd["status"] = "not_covered"
        opd["limit_amount"] = None
        opd["limit_text"] = "Not Covered"
        conds = opd.setdefault("conditions", [])
        not_cov_note = "OPD Coverage explicitly Not Covered in policy schedule"
        if not_cov_note not in conds:
            conds.append(not_cov_note)


def _check_premium_conflicts(result_dict: dict, pages: Optional[list[Any]] = None, warnings: Optional[list[str]] = None) -> None:
    """
    Detect conflicts: e.g. Gross premium in Schedule table vs Premium Receipt.
    Keep schedule value as primary, record other as alternative, add warning.
    """
    if not pages:
        return

    premiums_found = []
    for p in pages:
        # Match Gross Premium with page source
        for m in re.finditer(r"(?:Gross\s+premium|Total\s+Gross\s+Premium)\s*(?:\(Rs\.?\))?\s*[:\|\s]+(?:Rs\.?\s*)?([\d,]+(?:\.\d+)?)", p.full_text, re.IGNORECASE):
            try:
                amt = int(float(m.group(1).replace(",", "")))
                if amt > 1000 and amt not in [x[0] for x in premiums_found]:
                    premiums_found.append((amt, p.page_num, m.group(0).strip()))
            except ValueError:
                pass

    if len(premiums_found) >= 2:
        schedule_val = premiums_found[0][0]
        alt_val = premiums_found[1][0]
        if schedule_val != alt_val:
            pd = result_dict.setdefault("policy_details", {})
            pd["premium_including_gst"] = schedule_val
            conds = pd.setdefault("conditions", [])
            conflict_msg = (
                f"Conflict detected: Schedule (p. {premiums_found[0][1]}) states Gross Premium Rs. {schedule_val:,}, "
                f"while Receipt/Section (p. {premiums_found[1][1]}) states Rs. {alt_val:,}."
            )
            if conflict_msg not in conds:
                conds.append(conflict_msg)
            if warnings is not None:
                warnings.append(conflict_msg)


def _validate_disease_capping(result_dict: dict, pages: Optional[list[Any]] = None) -> None:
    """
    Extract procedure-wise cap list found in document text.
    Captures procedure, amount, qualifiers without inventing items.
    """
    if not pages:
        return

    bw = result_dict.setdefault("features", {}).setdefault("buffer_waiver", {})
    existing_caps = bw.get("disease_wise_capping", [])
    if existing_caps and len(existing_caps) > 5:
        return

    found_caps = []
    for p in pages:
        # Search for Disease wise capping block
        m = re.search(r"Disease\s+wise\s+capping\s*[:\|\s]+([^\n\r]+(?:\n[^\n\r]+){0,5})", p.full_text, re.IGNORECASE)
        if m:
            block = m.group(1)
            items = re.split(r",(?=\s*[A-Z])", block)
            for it in items:
                m_proc = re.search(r"^(.*?)\s*[-:]\s*(\d[\d,]*)\s*$", it.strip())
                if m_proc:
                    proc_name = m_proc.group(1).strip()
                    amt = int(m_proc.group(2).replace(",", ""))
                    found_caps.append({
                        "disease": proc_name,
                        "limit_amount": amt,
                        "limit_text": f"Rs. {_format_indian(amt)}",
                        "conditions": [],
                        "page": p.page_num,
                        "evidence": it.strip()[:150],
                    })
    if found_caps:
        bw["disease_wise_capping"] = found_caps


def _validate_maternity_metro(result_dict: dict) -> None:
    """
    If no metro/non-metro distinction: set both to single limit.
    Keep ONLY ONE condition: the standard note.
    Remove duplicates like 'Same limit for metro and non-metro'.
    """
    feats = result_dict.get("features", {})
    mat = feats.get("maternity")
    if not isinstance(mat, dict):
        return

    single_note = "No metro/non-metro distinction stated in policy; single limit applies"
    # These are redundant synonyms that should be removed
    redundant = {
        "same limit for metro and non-metro",
        "same limit applies",
        "same limit for both metro and non-metro",
    }

    for metro_key, non_metro_key in [
        ("normal_delivery_metro", "normal_delivery_non_metro"),
        ("c_section_metro", "c_section_non_metro"),
    ]:
        nm = mat.get(metro_key)
        nnm = mat.get(non_metro_key)
        if isinstance(nm, dict) and isinstance(nnm, dict):
            limit = nm.get("limit_amount") or nnm.get("limit_amount")
            if limit:
                nm["limit_amount"] = limit
                nnm["limit_amount"] = limit
                nm["status"] = "limited"
                nnm["status"] = "limited"
                for fv in (nm, nnm):
                    conds = fv.setdefault("conditions", [])
                    # Remove redundant duplicates
                    fv["conditions"] = [
                        c for c in conds
                        if c.lower() not in redundant
                    ]
                    if single_note not in fv["conditions"]:
                        fv["conditions"].append(single_note)


def _validate_copay_sublimits(result_dict: dict, pages: Optional[list[Any]] = None) -> None:
    """
    COPAY_SUBLIMITS: ONLY co-pay clauses and procedure/disease-wise caps.
    NOT room rent, ICU, maternity, ambulance (those live in their own fields).
    Each item: {item, type, percent, amount, applies_to, exceptions, page, evidence}
    No "None%" strings.
    """
    bw = result_dict.setdefault("features", {}).setdefault("buffer_waiver", {})

    # Build a clean list from scratch using only proper co-pay / cap clauses
    copay_list: list[dict] = []
    seen_evidence: set[str] = set()

    # ── 1. Scan existing copay_sublimits (LLM-supplied), validate and enrich ──
    existing = bw.get("copay_sublimits", [])
    for item in existing:
        if not isinstance(item, dict):
            continue
        # Check it looks like a real copay/sublimit, not a basic benefit field
        item_name = (item.get("item") or "").lower()
        # Skip items that are just limit fields already captured elsewhere
        if any(x in item_name for x in (
            "room rent", "icu charge", "ambulance", "normal delivery",
            "c section", "c-section", "pre hosp", "post hosp",
        )):
            continue

        pct = item.get("limit_percent")
        amt = item.get("limit_amount")
        ev = item.get("evidence") or ""

        # Remove "None%" artifacts
        lt = item.get("limit_text") or ""
        if lt == "None%" or lt.strip() == "None%":
            lt = f"{pct}% of Sum Insured" if pct else (f"Rs. {_format_indian(amt)}" if amt else None)
            item["limit_text"] = lt

        entry = {
            "item": item.get("item", "Co-Pay / Sub-Limit"),
            "type": item.get("type", "sublimit"),
            "percent": pct,
            "amount": amt,
            "applies_to": item.get("applies_to") or item.get("conditions", [None])[0] if item.get("conditions") else None,
            "exceptions": item.get("exceptions") or _extract_exceptions(ev),
            "page": item.get("page"),
            "evidence": ev if ev and len(ev) >= 12 else None,
        }
        ev_key = (ev or "").lower()[:80]
        if ev_key not in seen_evidence:
            seen_evidence.add(ev_key)
            copay_list.append(entry)

    # ── 2. Scan page text for generic co-pay / cap patterns ──────────────────
    if pages:
        # Pattern 1: "X% co-pay / co-payment shall apply ..."
        copay_pct_re = re.compile(
            r"(\d+(?:\.\d+)?)\s*%\s*co-?pay(?:ment)?\s+(?:shall\s+)?(?:apply|be\s+payable|applicable)"
            r"(?:[^.]*(?:except|excluding|other\s+than)[^.]*)?",
            re.IGNORECASE,
        )
        # Pattern 2: "50% co-pay for <device/procedure>"
        copay_for_re = re.compile(
            r"(\d+(?:\.\d+)?)\s*%\s*co-?pay(?:ment)?\s+(?:for|on)\s+([^.;\n]{5,250})",
            re.IGNORECASE,
        )
        # Pattern 3: "Sub-limit / capped at Rs. X for ..."
        sublimit_re = re.compile(
            r"(?:sub-?limit(?:ed)?|capped?\s+at)\s+(?:Rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(?:for|on|of)?\s*([^.;\n]{5,250})?",
            re.IGNORECASE,
        )
        # Pattern 4: "X% of Sum Insured for <procedure>"
        pct_si_re = re.compile(
            r"(\d+(?:\.\d+)?)\s*%\s+of\s+(?:the\s+)?Sum\s+Insured\s+(?:for|on|towards)\s+([^.;\n]{5,250})",
            re.IGNORECASE,
        )

        for p in pages:
            text = p.full_text

            for pat, entry_type, pct_group, item_group in [
                (copay_pct_re, "copay", 1, None),
                (copay_for_re, "copay", 1, 2),
                (sublimit_re, "sublimit", None, 2),
                (pct_si_re, "cap", 1, 2),
            ]:
                for m in pat.finditer(text):
                    # Expand to full sentence
                    sent_start = text.rfind("\n", 0, m.start())
                    sent_start = sent_start + 1 if sent_start >= 0 else 0
                    sent_end = text.find("\n", m.end())
                    if sent_end < 0:
                        sent_end = len(text)
                    sentence = text[sent_start:sent_end].strip()

                    if len(sentence) < 12:
                        sentence = m.group(0).strip()
                    if len(sentence) < 12:
                        continue

                    ev_key = sentence.lower()[:80]
                    if ev_key in seen_evidence:
                        continue
                    seen_evidence.add(ev_key)

                    pct = float(m.group(pct_group)) if pct_group and m.group(pct_group) else None
                    item_txt = m.group(item_group).strip() if item_group and m.group(item_group) else "General Policy"
                    exceptions = _extract_exceptions(sentence)

                    copay_list.append({
                        "item": item_txt[:120],
                        "type": entry_type,
                        "percent": pct,
                        "amount": None,
                        "applies_to": sentence[:200],
                        "exceptions": exceptions,
                        "page": p.page_num,
                        "evidence": sentence[:300],
                    })

    bw["copay_sublimits"] = copay_list


def _extract_exceptions(text: str) -> Optional[str]:
    """Extract exception clause text from a co-pay sentence."""
    if not text:
        return None
    m = re.search(
        r"(?:except|excluding|other\s+than|save\s+for|not\s+applicable\s+(?:for|to))\s+([^.;\n]{5,120})",
        text, re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return None


def _validate_waivers(result_dict: dict, pages: Optional[list[Any]] = None) -> None:
    """
    BUF_WAIVER_CONDITIONS = real JSON list, de-duplicated, containing ONLY actual
    waivers/relaxations. Each entry: {waiver_name, clause, page, evidence}.
    Removes general boilerplate like "applicable unless specifically waived or amended".
    """
    bw = result_dict.setdefault("features", {}).setdefault("buffer_waiver", {})
    waiver_list: list[dict] = []
    seen_clauses: set[str] = set()  # normalized whitespace keys for dedup

    # Boilerplate phrases to exclude
    _BOILERPLATE = re.compile(
        r"(?:applicable\s+unless\s+specifically|"
        r"terms\s*[&and]+\s*conditions\s+are\s+applicable|"
        r"below\s+terms|policy\s+terms\s+and\s+conditions|"
        r"general\s+terms)",
        re.IGNORECASE,
    )

    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip()).lower()

    def _add(name: str, clause: str, page: Optional[int], ev: Optional[str]) -> None:
        clean = (clause or ev or "").strip()
        if not clean or len(clean) < 12:
            return
        # Skip boilerplate
        if _BOILERPLATE.search(clean):
            return
        key = _norm(clean)
        if key in seen_clauses:
            return
        seen_clauses.add(key)
        waiver_list.append({
            "waiver_name": name,
            "clause": clean,
            "page": page,
            "evidence": ev or clean,
        })

    # ── From structured waiting period fields ──────────────────────────────
    wp = result_dict.get("features", {}).get("waiting_periods", {})
    if isinstance(wp, dict):
        wp_map = [
            ("thirty_day_waiting", "30-Day Initial Waiting Period"),
            ("first_year_waiting", "1st Year Specific Disease Waiting Period"),
            ("second_year_waiting", "2nd Year Specific Disease Waiting Period"),
            ("ped_waiting", "Pre-Existing Diseases (PED) Waiting Period"),
        ]
        for key, label in wp_map:
            fv = wp.get(key)
            if isinstance(fv, dict) and fv.get("status") == "waived_off":
                pg = fv.get("source_pages", [None])[0] if fv.get("source_pages") else None
                ev = fv.get("evidence")
                if ev:
                    _add(label, ev, pg, ev)

    # ── From maternity waiting period ─────────────────────────────────────
    mat = result_dict.get("features", {}).get("maternity", {})
    if isinstance(mat, dict):
        fv = mat.get("nine_month_waiting_period")
        if isinstance(fv, dict) and fv.get("status") == "waived_off":
            pg = fv.get("source_pages", [None])[0] if fv.get("source_pages") else None
            ev = fv.get("evidence")
            if ev:
                _add("Maternity 9-Month Waiting Period", ev, pg, ev)

    # ── Scan pages for waiver sentences ───────────────────────────────────
    if pages:
        waiver_re = re.compile(
            r"[^.\n;]{5,}(?:\bwaived\b|\bwaiver\b|\bdeleted\b|\bnot\s+applicable\b|\bno\s+waiting\s+period\b)[^.\n;]{0,150}",
            re.IGNORECASE,
        )
        for p in pages:
            for m in waiver_re.finditer(p.full_text):
                sent = m.group(0).strip()
                if _BOILERPLATE.search(sent):
                    continue
                if len(sent) < 15:
                    continue
                _add("Policy Clause Waiver", sent, p.page_num, sent)

    bw["waiver_conditions"] = waiver_list


def _fix_waiting_period_days(result_dict: dict) -> None:
    """
    Rule 6: For waived_off or applied waiting periods, leave limit_days empty
    unless the document explicitly states a number of days for THAT period.
    Remove auto-filled generic day values (30, 365, 730) that weren't extracted.
    """
    wp = result_dict.get("features", {}).get("waiting_periods", {})
    if not isinstance(wp, dict):
        return

    # Mapping: field -> expected stated day value
    expected_days = {
        "thirty_day_waiting": 30,
        "first_year_waiting": 365,
        "second_year_waiting": 730,
    }

    for key, default_days in expected_days.items():
        fv = wp.get(key)
        if not isinstance(fv, dict):
            continue
        status = fv.get("status")
        days = fv.get("limit_days")
        evidence = fv.get("evidence") or ""
        # If limit_days is the "generic" assumed value but evidence doesn't mention it,
        # clear it (rule: leave empty unless stated)
        if days is not None:
            if status in ("waived_off",) and str(days) not in evidence:
                fv["limit_days"] = None


def _fix_buf_eligibility_evidence(result_dict: dict, pages: Optional[list[Any]] = None) -> None:
    """
    Rule 3: BUF_ELIGIBILITY must always carry source_pages and evidence.
    """
    bw = result_dict.get("features", {}).get("buffer_waiver", {})
    if not isinstance(bw, dict):
        return

    eligibility = bw.get("corporate_buffer_eligibility")
    if not eligibility or not pages:
        return

    # If it's a plain string, search for evidence in pages
    ev, pgs = find_best_evidence(eligibility, pages, extra_queries=["buffer", "floater", "eligibility", "corporate"])
    if ev:
        # Store as structured dict if it's still a raw string
        bw["corporate_buffer_eligibility_evidence"] = ev
        bw["corporate_buffer_eligibility_pages"] = pgs
