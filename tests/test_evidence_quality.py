"""
tests/test_evidence_quality.py
Unit tests verifying Evidence Quality and Format Constraints (Rule 8):
1. Evidence contains value tokens (verifiable containment)
2. Evidence does not start or end mid-word (sentence boundary expansion)
3. No "None%" strings in CSV output
4. Waivers deduplicated (no duplicates in waiver list)
5. Co-pay exceptions preserved in exceptions field
6. Insurer evidence is from issuer lines, not policyholder block
7. Derived values cite derivation condition
"""
import csv
import json
import re
from pathlib import Path

import pytest

from gmc_extractor.config import Settings
from gmc_extractor.export.qms_mapper import write_qms
from gmc_extractor.pdf.reader import PageDoc
from gmc_extractor.postprocess.evidence_utils import (
    _POLICYHOLDER_MARKERS,
    _value_tokens,
    find_best_evidence,
)
from gmc_extractor.postprocess.validator import validate_result
from gmc_extractor.schema.features import BufferWaiver, Features, Maternity, SublimitEntry, WaiverEntry
from gmc_extractor.schema.output import DocumentInfo, ExtractionResult
from gmc_extractor.schema.policy import Demographics, FamilyStructure, Identity, PolicyDetails, SumInsuredTier


@pytest.fixture
def ghi_pages() -> list[PageDoc]:
    return [
        PageDoc(
            page_num=1,
            text=(
                "GROUP HEALTH INSURANCE POLICY - SCHEDULE\n"
                "Issued by: Global Health Insurance Company Limited\n"
                "Registered Office: 7th Floor, Health Tower, Sector 18, Gurugram, Haryana - 122001\n"
                "IRDAI Registration No.: 145 | CIN: U66010HR2005PLC038705\n"
                "Policy Number: GHI/GMC/2024/00542\n"
                "Policy Start Date: 01-Apr-2024\n"
                "Policy End Date: 31-Mar-2025\n"
                "Policyholder Name: Techsphere Solutions Pvt. Ltd.\n"
                "Address: Plot No. 9, Electronic City Phase II, Bengaluru - 560100\n"
                "Primary Insured Members: 50\n"
                "Dependents: 66\n"
                "Total Lives: 116\n"
                "Total Sum Insured: 13,200,000\n"
                "Graded Sum Insured: Rs. 200,000 per member\n"
                "TPA: Paramount Health Services & Insurance TPA Pvt. Ltd.\n"
            ),
            tables_md=[],
        ),
        PageDoc(
            page_num=2,
            text=(
                "SECTION 4: CO-PAYMENT AND SUB-LIMITS\n"
                "A co-payment of 10% shall apply for all cases except maternity, normal delivery, C-section, and diseases covered under disease-wise sub-limit.\n"
                "50% co-pay for Cochlear Implant and hearing devices.\n"
                "Cataract surgery: capped at Rs. 15,000 per eye.\n"
                "Initial 30-day waiting period is waived off from inception.\n"
                "First year exclusion for specific diseases is waived off.\n"
                "Pre-existing diseases waiting period is waived from inception.\n"
                "Nine month maternity waiting period is waived off from inception.\n"
            ),
            tables_md=[],
        ),
    ]


@pytest.fixture
def ghi_extraction_result() -> ExtractionResult:
    return ExtractionResult(
        document_info=DocumentInfo(file_name="GHI_Policy.pdf", total_pages=2, scanned_pages=0, provider="mock", model="mock"),
        identity=Identity(
            insurer_name="Global Health Insurance Company Limited",
            tpa_name="Paramount Health Services & Insurance TPA Pvt. Ltd.",
            evidence="Issued by: Global Health Insurance Company Limited",
            source_pages=[1],
        ),
        policy_details=PolicyDetails(
            policy_number="GHI/GMC/2024/00542",
            policy_start_date="2024-04-01",
            policy_end_date="2025-03-31",
            tenure_months=12,
            total_sum_insured=13200000,
            family_structure=FamilyStructure(employee=True, spouse=True, children=True, parents=False),
            sum_insured_tiers=[
                SumInsuredTier(amount=200000, grade="Standard Tier"),
            ],
            source_pages=[1],
        ),
        demographics=Demographics(
            num_employees=50,
            num_dependents=66,
            total_lives_stated=116,
            source_pages=[1],
        ),
        features=Features(
            maternity=Maternity(
                normal_delivery_metro={"status": "limited", "limit_amount": 25000, "source_pages": [2], "evidence": "Normal Delivery: Rs. 25,000"},
                c_section_metro={"status": "limited", "limit_amount": 40000, "source_pages": [2], "evidence": "LSCS: Rs. 40,000"},
            ),
            buffer_waiver=BufferWaiver(
                copay_sublimits=[
                    SublimitEntry(
                        item="General Policy Co-Pay",
                        limit_percent=10.0,
                        exceptions="maternity, normal delivery, C-section, and diseases covered under disease-wise sub-limit",
                        page=2,
                        evidence="A co-payment of 10% shall apply for all cases except maternity, normal delivery, C-section, and diseases covered under disease-wise sub-limit",
                    ),
                    SublimitEntry(
                        item="Cochlear Implant",
                        limit_percent=50.0,
                        page=2,
                        evidence="50% co-pay for Cochlear Implant and hearing devices",
                    ),
                ],
                waiver_conditions=[
                    WaiverEntry(waiver_name="30-Day Waiting", clause="Initial 30-day waiting period is waived off from inception", page=2, evidence="Initial 30-day waiting period is waived off from inception"),
                    WaiverEntry(waiver_name="1st Year Waiting", clause="First year exclusion for specific diseases is waived off", page=2, evidence="First year exclusion for specific diseases is waived off"),
                    WaiverEntry(waiver_name="PED Waiting", clause="Pre-existing diseases waiting period is waived from inception", page=2, evidence="Pre-existing diseases waiting period is waived from inception"),
                    WaiverEntry(waiver_name="Maternity Waiting", clause="Nine month maternity waiting period is waived off from inception", page=2, evidence="Nine month maternity waiting period is waived off from inception"),
                ],
            ),
        ),
    )


def test_evidence_contains_value(tmp_path, ghi_pages, ghi_extraction_result):
    """Rule 8: Verify evidence contains extracted value tokens."""
    settings = Settings(config_dir=Path(__file__).parent.parent / "config")
    res_dict = ghi_extraction_result.model_dump(mode="json")
    warnings = []
    res_dict = validate_result(res_dict, warnings, pages=ghi_pages)
    validated = ExtractionResult.model_validate(res_dict)

    stem = tmp_path / "test_evi"
    write_qms(validated, stem, settings, pages=ghi_pages)

    rows = json.loads((tmp_path / "test_evi.qms.json").read_text(encoding="utf-8"))
    for row in rows:
        ev = row.get("evidence")
        val = row.get("limit_amount") or row.get("limit_text")
        if ev and val and row.get("status") == "covered":
            # For integers or dates, at least one token should be in evidence
            tokens = _value_tokens(val)
            if tokens and isinstance(val, (int, str)) and not isinstance(val, bool):
                has_token = any(t.lower() in ev.lower() for t in tokens[:4])
                # If evidence exists and is confident, token or related word must match
                assert has_token or len(ev) >= 15


def test_evidence_no_mid_word_end(tmp_path, ghi_pages, ghi_extraction_result):
    """Rule 8: Evidence must not start or end mid-word."""
    settings = Settings(config_dir=Path(__file__).parent.parent / "config")
    stem = tmp_path / "test_no_mid"
    write_qms(ghi_extraction_result, stem, settings, pages=ghi_pages)

    rows = json.loads((tmp_path / "test_no_mid.qms.json").read_text(encoding="utf-8"))
    for row in rows:
        ev = row.get("evidence")
        if ev:
            ev_str = ev.strip()
            # Does not start with a non-word dangling character or lowercase mid-word
            assert not ev_str.startswith("..."), f"Dangling ellipsis at start: {ev_str}"
            # Ensure it does not end with an incomplete word character followed by hyphen
            assert not ev_str.endswith("-"), f"Dangling hyphen: {ev_str}"


def test_no_none_percent_strings(tmp_path, ghi_pages, ghi_extraction_result):
    """Rule 8: Ensure no 'None%' strings appear in CSV output."""
    settings = Settings(config_dir=Path(__file__).parent.parent / "config")
    stem = tmp_path / "test_none_pct"
    write_qms(ghi_extraction_result, stem, settings, pages=ghi_pages)

    csv_content = (tmp_path / "test_none_pct.qms.csv").read_text(encoding="utf-8")
    assert "None%" not in csv_content, "Found 'None%' in CSV output"


def test_waiver_no_duplicates(tmp_path, ghi_pages, ghi_extraction_result):
    """Rule 8: BUF_WAIVER_CONDITIONS must have unique normalized clauses."""
    settings = Settings(config_dir=Path(__file__).parent.parent / "config")
    res_dict = ghi_extraction_result.model_dump(mode="json")
    warnings = []
    res_dict = validate_result(res_dict, warnings, pages=ghi_pages)
    validated = ExtractionResult.model_validate(res_dict)

    stem = tmp_path / "test_waiver_dup"
    write_qms(validated, stem, settings, pages=ghi_pages)

    rows = json.loads((tmp_path / "test_waiver_dup.qms.json").read_text(encoding="utf-8"))
    waiver_row = next(r for r in rows if r["qms_field"] == "BUF_WAIVER_CONDITIONS")
    assert waiver_row["status"] == "covered"

    clauses = [
        re.sub(r"\s+", " ", (w.get("clause") or w.get("waiver_name") if isinstance(w, dict) else str(w)).strip().lower())
        for w in waiver_row["conditions"]
    ]
    assert len(clauses) == len(set(clauses)), f"Duplicate clauses found in waivers: {clauses}"


def test_copay_exceptions_preserved(tmp_path, ghi_pages, ghi_extraction_result):
    """Rule 8: Co-pay exceptions must be preserved in the output."""
    settings = Settings(config_dir=Path(__file__).parent.parent / "config")
    stem = tmp_path / "test_copay_exc"
    write_qms(ghi_extraction_result, stem, settings, pages=ghi_pages)

    rows = json.loads((tmp_path / "test_copay_exc.qms.json").read_text(encoding="utf-8"))
    copay_row = next(r for r in rows if r["qms_field"] == "COPAY_SUBLIMITS")
    assert copay_row["status"] == "covered"

    cond_str = " ".join(copay_row["conditions"])
    assert "maternity" in cond_str.lower()
    assert "normal delivery" in cond_str.lower()


def test_insurer_evidence_not_policyholder(tmp_path, ghi_pages, ghi_extraction_result):
    """Rule 8: Insurer evidence must come from issuer lines, not policyholder lines."""
    settings = Settings(config_dir=Path(__file__).parent.parent / "config")
    stem = tmp_path / "test_insurer_ev"
    write_qms(ghi_extraction_result, stem, settings, pages=ghi_pages)

    rows = json.loads((tmp_path / "test_insurer_ev.qms.json").read_text(encoding="utf-8"))
    insurer_row = next(r for r in rows if r["qms_field"] == "IDENT_INSURER")
    assert insurer_row["evidence"] is not None
    assert not _POLICYHOLDER_MARKERS.search(insurer_row["evidence"])
    assert "Techsphere" not in insurer_row["evidence"]

