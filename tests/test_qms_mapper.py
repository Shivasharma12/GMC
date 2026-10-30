"""
tests/test_qms_mapper.py
Unit tests verifying the 9 specific QMS extraction & mapping gap fixes:
1. POL_SI_TIERS (sorted ascending integers) & POL_TOTAL_SUM_INSURED
2. POL_PREV_INCEPTION with policy start date baseline rule
3. DEM_DEPENDENTS, DEM_TOTAL_COMPUTED, and "member-wise annexure not present in document"
4. Verbatim evidence quotes, exact source pages, and confidence penalty if empty
5. Metro / Non-metro single limit normalization with standard condition
6. COPAY_SUBLIMITS generic list
7. BUF_WAIVER_CONDITIONS real list of waiver objects
8. Removal of duplicate ROOM_RENT_PCT and ROOM_ICU_PCT rows
9. IDENT_TPA in-house handling ("not_covered" + "None (claims handled in-house by insurer)")
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gmc_extractor.config import Settings
from gmc_extractor.export.qms_mapper import write_qms
from gmc_extractor.pdf.reader import PageDoc
from gmc_extractor.postprocess.validator import validate_result
from gmc_extractor.schema.features import BufferWaiver, Features, Maternity, SublimitEntry, WaiverEntry
from gmc_extractor.schema.output import DocumentInfo, ExtractionResult
from gmc_extractor.schema.policy import Demographics, FamilyStructure, Identity, PolicyDetails, SumInsuredTier


@pytest.fixture
def sample_pages() -> list[PageDoc]:
    return [
        PageDoc(
            page_num=1,
            text=(
                "Policy Certificate - Group Care 360\n"
                "Policy No: 41201895\n"
                "Policy Period - Start Date 00:00 hrs 02-Apr-2022\n"
                "Policy Period - End Date Midnight 01-Apr-2023\n"
                "Premium Details: Premium 349,469 Total Premium 412,373\n"
                "Details of Insured: Primary Insured Members: 115, Dependents: 32, Total: 147\n"
                "For details of each insured refer to 'Annexure A'\n"
                "Details of Cover: Total Sum Insured : 51,900,000\n"
                "Intermediary Details: Care Health Insurance Ltd. Code: Direct\n"
                "for Claims & Assistance: Call 1800 -102-4488\n"
            ),
            tables_md=[],
        ),
        PageDoc(
            page_num=2,
            text=(
                "Graded Sum insured: Rs. 300,000 and Rs. 500,000\n"
                "Family Structure : Self + Spouse + 2 Dependent children\n"
                "Pre-existing diseases are covered for existing members.\n"
                "30 Days Wait Period condition is waived for all members.\n"
                "First & Second year exclusion condition for specific diseases is waived.\n"
                "Maximum Limit for Maternity claims is Rs. 50,000 for Normal and Rs. 50,000 for LSCS.\n"
                "9 month waiting period in respect of maternity claims waived.\n"
                "Modern treatments, psychiatric treatments and Bariatric Surgery covered upto 50% of the Sum Insured.\n"
            ),
            tables_md=[],
        ),
    ]


@pytest.fixture
def mock_extraction_result() -> ExtractionResult:
    return ExtractionResult(
        document_info=DocumentInfo(file_name="1.Policy Copy.pdf", total_pages=2, scanned_pages=0, provider="mock", model="mock"),
        identity=Identity(
            insurer_name="Care Health Insurance Limited",
            tpa_name="Direct",  # Sales intermediary, should be converted to in-house
            evidence="Care Health Insurance Ltd. Code: Direct",
            source_pages=[1],
        ),
        policy_details=PolicyDetails(
            policy_number="41201895",
            policy_start_date="2022-04-02",
            policy_end_date="2023-04-01",
            premium_excluding_gst=349469,
            premium_including_gst=412373,
            total_sum_insured=51900000,
            family_structure=FamilyStructure(employee=True, spouse=True, children=True),
            sum_insured_tiers=[
                SumInsuredTier(amount=500000, grade="Grade A"),
                SumInsuredTier(amount=300000, grade="Grade B"),
            ],
            source_pages=[1, 2],
        ),
        demographics=Demographics(
            num_employees=115,
            num_dependents=32,
            total_lives_stated=147,
            source_pages=[1],
        ),
        features=Features(
            maternity=Maternity(
                normal_delivery_metro={"status": "limited", "limit_amount": 50000, "source_pages": [2], "evidence": "Normal: Rs. 50,000"},
                c_section_metro={"status": "limited", "limit_amount": 50000, "source_pages": [2], "evidence": "LSCS: Rs. 50,000"},
            ),
            buffer_waiver=BufferWaiver(
                copay_sublimits=[
                    SublimitEntry(
                        item="Modern treatments, psychiatric & Bariatric Surgery",
                        limit_percent=50.0,
                        limit_text="50% of the Sum Insured",
                        page=2,
                        evidence="Modern treatments, psychiatric treatments and Bariatric Surgery covered upto 50% of the Sum Insured",
                    )
                ],
                waiver_conditions=[
                    WaiverEntry(waiver_name="30 Days Wait Period", clause="30 Days Wait Period condition is waived", page=2, evidence="30 Days Wait Period condition is waived"),
                    WaiverEntry(waiver_name="1st & 2nd Year Exclusion", clause="First & Second year exclusion condition is waived", page=2, evidence="First & Second year exclusion condition is waived"),
                    WaiverEntry(waiver_name="9 Month Maternity", clause="9 month waiting period in respect of maternity claims waived", page=2, evidence="9 month waiting period in respect of maternity claims waived"),
                ],
            ),
        ),
    )


def test_gap_fixes_in_qms_export(tmp_path, sample_pages, mock_extraction_result):
    settings = Settings(config_dir=Path(__file__).parent.parent / "config")
    warnings: list[str] = []

    # 1. Run validator
    res_dict = mock_extraction_result.model_dump(mode="json")
    res_dict = validate_result(res_dict, warnings, pages=sample_pages)
    validated_res = ExtractionResult.model_validate(res_dict)

    # 2. Write QMS files
    stem = tmp_path / "1.Policy Copy"
    write_qms(validated_res, stem, settings, pages=sample_pages)

    # Read back JSON
    qms_json_file = tmp_path / "1.Policy Copy.qms.json"
    assert qms_json_file.exists()
    rows = json.loads(qms_json_file.read_text(encoding="utf-8"))
    row_map = {r["qms_field"]: r for r in rows}

    # ── Gap 1: Sum Insured Tiers & Total Sum Insured ─────────────────────────
    assert "POL_SI_TIERS" in row_map
    si_tier_row = row_map["POL_SI_TIERS"]
    assert si_tier_row["status"] == "covered"
    assert si_tier_row["limit_text"] == [300000, 500000]  # Sorted ascending integers
    assert si_tier_row["evidence"] is not None

    assert "POL_TOTAL_SUM_INSURED" in row_map
    total_si_row = row_map["POL_TOTAL_SUM_INSURED"]
    assert total_si_row["status"] == "covered"
    assert total_si_row["limit_amount"] == 51900000

    # ── Gap 2: Previous Inception Date Baseline Rule ─────────────────────────
    assert "POL_PREV_INCEPTION" in row_map
    prev_inc = row_map["POL_PREV_INCEPTION"]
    assert prev_inc["status"] == "covered"
    assert prev_inc["limit_text"] == "2022-04-02"
    assert any("expiring policy baseline rule" in c for c in prev_inc["conditions"])

    # ── Gap 3: Demographics Dependents & Annexure Note ───────────────────────
    assert "DEM_DEPENDENTS" in row_map
    assert row_map["DEM_DEPENDENTS"]["limit_amount"] == 32
    assert row_map["DEM_TOTAL_COMPUTED"]["limit_amount"] == 147

    # Spouses/children/parents should be not_mentioned with annexure note
    for dem_field in ("DEM_SPOUSES", "DEM_CHILDREN", "DEM_PARENTS"):
        assert row_map[dem_field]["status"] == "not_mentioned"
        assert any("member-wise annexure not present" in c for c in row_map[dem_field]["conditions"])

    # ── Gap 4: Grounding & Confidence Penalty for Empty Evidence ─────────────
    for field_key in ("IDENT_INSURER", "POL_NUMBER", "POL_START_DATE", "POL_PREMIUM_EXCL_GST"):
        r = row_map[field_key]
        assert r["evidence"] is not None and len(r["evidence"]) > 0
        assert len(r["source_pages"]) > 0
        assert r["confidence"] == 1.0

    # ── Gap 5: Metro / Non-Metro Single Limit ────────────────────────────────
    mat_metro = row_map["MAT_NORMAL_METRO"]
    mat_non_metro = row_map["MAT_NORMAL_NON_METRO"]
    assert mat_metro["limit_amount"] == 50000
    assert mat_non_metro["limit_amount"] == 50000
    assert any("No metro/non-metro distinction" in c for c in mat_metro["conditions"])
    assert any("No metro/non-metro distinction" in c for c in mat_non_metro["conditions"])

    # ── Gap 6: Co-Pay and Sub-Limits Generic List ────────────────────────────
    assert "COPAY_SUBLIMITS" in row_map
    copay_row = row_map["COPAY_SUBLIMITS"]
    assert copay_row["status"] == "covered"
    assert isinstance(copay_row["limit_text"], list)
    assert any("Modern treatments" in c for c in copay_row["conditions"])

    # ── Gap 7: Waiver Conditions Real List ───────────────────────────────────
    assert "BUF_WAIVER_CONDITIONS" in row_map
    waiver_row = row_map["BUF_WAIVER_CONDITIONS"]
    assert waiver_row["status"] == "covered"
    assert isinstance(waiver_row["conditions"], list)
    assert len(waiver_row["conditions"]) >= 3

    # ── Gap 8: No duplicate room rows ────────────────────────────────────────
    assert "ROOM_RENT_PCT" not in row_map
    assert "ROOM_ICU_PCT" not in row_map

    # ── Gap 9: In-House Claims / TPA ─────────────────────────────────────────
    assert "IDENT_TPA" in row_map
    tpa_row = row_map["IDENT_TPA"]
    assert tpa_row["status"] == "not_covered"
    assert tpa_row["limit_text"] == "None (claims handled in-house by insurer)"
    assert tpa_row["evidence"] is not None
