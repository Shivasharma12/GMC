"""
tests/test_grounding.py
Unit tests for the strict Grounding Gate module.
Enforces:
- Fuzzy quote containment >= 90%
- Value token containment in evidence
- Rejected ungrounded values moved to unverified_candidate with status 'needs_review'
- Main values in QMS output kept empty for rejected candidates
"""
import json
from pathlib import Path
import pytest

from gmc_extractor.config import Settings
from gmc_extractor.export.qms_mapper import write_qms
from gmc_extractor.pdf.reader import PageDoc
from gmc_extractor.postprocess.grounding import (
    ground_result,
    _number_in_text,
    _format_indian,
)
from gmc_extractor.schema.common import FeatureValue
from gmc_extractor.schema.features import Features, RoomHospitalization
from gmc_extractor.schema.output import DocumentInfo, ExtractionResult
from gmc_extractor.schema.policy import Identity, PolicyDetails


def make_page(num: int, text: str) -> PageDoc:
    return PageDoc(page_num=num, text=text, tables_md=[])


class TestFormatIndian:
    def test_small(self):
        assert _format_indian(500) == "500"

    def test_lakh(self):
        assert _format_indian(500000) == "5,00,000"

    def test_crore(self):
        assert _format_indian(10000000) == "1,00,00,000"

    def test_10k(self):
        assert _format_indian(10000) == "10,000"


class TestNumberInText:
    def test_plain_int(self):
        assert _number_in_text(500000, "room rent limit 500000 per day") is True

    def test_indian_comma(self):
        assert _number_in_text(500000, "limit Rs. 5,00,000") is True

    def test_lakh_word(self):
        assert _number_in_text(500000, "Rs. 5 lakh per year") is True

    def test_not_found(self):
        assert _number_in_text(999999, "room rent limit 500000 per day") is False

    def test_crore(self):
        assert _number_in_text(10_000_000, "buffer of 1 crore") is True


class TestGroundResult:
    def _make_feature_value(self, amount, evidence, page=1):
        return {
            "status": "limited",
            "limit_amount": amount,
            "limit_percent_of_si": None,
            "limit_days": None,
            "limit_text": None,
            "conditions": [],
            "source_pages": [page],
            "evidence": evidence,
            "confidence": 0.9,
        }

    def test_good_grounding_no_penalty(self):
        pages = [make_page(1, "Room rent limit Rs. 5,00,000 per day for single room.")]
        result = {"room_rent": self._make_feature_value(500000, "Room rent limit Rs. 5,00,000 per day for single room.", page=1)}
        warnings = []
        out = ground_result(result, pages, warnings)
        assert out["room_rent"]["confidence"] >= 0.85
        assert out["room_rent"]["status"] == "limited"
        assert out["room_rent"]["limit_amount"] == 500000

    def test_wrong_amount_triggers_grounding_gate(self):
        pages = [make_page(1, "Room rent limit Rs. 3,00,000 per day.")]
        result = {"room_rent": self._make_feature_value(500000, "Room rent limit Rs. 5,00,000 per day", page=1)}
        warnings = []
        out = ground_result(result, pages, warnings)
        # Main value cleared, candidate moved to unverified_candidate
        assert out["room_rent"]["status"] == "needs_review"
        assert out["room_rent"]["limit_amount"] is None
        assert out["room_rent"]["confidence"] <= 0.3
        assert "unverified_candidate" in out["room_rent"]
        assert out["room_rent"]["unverified_candidate"]["limit_amount"] == 500000

    def test_missing_evidence_quote_triggers_grounding_gate(self):
        pages = [make_page(1, "Completely unrelated content on this page.")]
        result = {"maternity": self._make_feature_value(50000, "Normal delivery Rs. 50,000 metro", page=1)}
        warnings = []
        out = ground_result(result, pages, warnings)
        assert out["maternity"]["status"] == "needs_review"
        assert out["maternity"]["limit_amount"] is None
        assert out["maternity"]["confidence"] <= 0.3

    def test_grounding_gate_rejects_hallucination_in_qms_export(self, tmp_path):
        """
        Rule 3 test: When a value fails grounding, assert the QMS main value is empty
        and status is 'needs_review'.
        """
        # Document text has NO mention of OPD
        pages = [make_page(1, "Only inpatient care is covered under this policy.")]

        # Create extraction result with a fabricated OPD amount
        fab_result = ExtractionResult(
            document_info=DocumentInfo(file_name="test.pdf", total_pages=1, scanned_pages=0, provider="mock", model="mock"),
            features=Features(
                room_hospitalization=RoomHospitalization(
                    room_rent=FeatureValue(
                        status="limited",
                        limit_amount=99999,
                        evidence="Fabricated quote not present in document",
                        source_pages=[1],
                        confidence=0.95,
                    )
                )
            ),
        )

        res_dict = fab_result.model_dump(mode="json")
        warnings = []
        res_dict = ground_result(res_dict, pages, warnings)
        validated = ExtractionResult.model_validate(res_dict)

        settings = Settings(config_dir=Path(__file__).parent.parent / "config")
        stem = tmp_path / "test_gate"
        write_qms(validated, stem, settings, pages=pages)

        # Check QMS JSON output
        qms_json = json.loads((tmp_path / "test_gate.qms.json").read_text(encoding="utf-8"))
        room_row = next(r for r in qms_json if r["qms_field"] == "ROOM_RENT")

        # ASSERTION: Main value MUST be empty and status must be 'needs_review'
        assert room_row["status"] == "needs_review"
        assert room_row["limit_amount"] is None
        assert room_row["evidence"] is None
        assert room_row["confidence"] <= 0.3

        # Candidate must be preserved in unverified_candidate
        assert "unverified_candidate" in room_row
        assert room_row["unverified_candidate"]["limit_amount"] == 99999
