"""
tests/test_grounding.py
Unit tests for the grounding module.
"""
import pytest
from gmc_extractor.pdf.reader import PageDoc
from gmc_extractor.postprocess.grounding import ground_result, _number_in_text, _format_indian


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
        result = {"room_rent": self._make_feature_value(500000, "Room rent limit Rs. 5,00,000 per day")}
        warnings = []
        out = ground_result(result, pages, warnings)
        # Confidence should not be penalised
        assert out["room_rent"]["confidence"] >= 0.85
        # No grounding warnings
        grounding_warns = [w for w in warnings if "Grounding FAIL" in w]
        assert len(grounding_warns) == 0

    def test_wrong_amount_triggers_warning(self):
        pages = [make_page(1, "Room rent limit Rs. 3,00,000 per day.")]
        result = {"room_rent": self._make_feature_value(500000, "Room rent limit Rs. 5,00,000", page=1)}
        warnings = []
        out = ground_result(result, pages, warnings)
        grounding_warns = [w for w in warnings if "Grounding FAIL" in w]
        assert len(grounding_warns) >= 1

    def test_missing_evidence_quote_triggers_warning(self):
        pages = [make_page(1, "Completely unrelated content on this page.")]
        result = {"maternity": self._make_feature_value(50000, "Normal delivery Rs. 50,000 metro", page=1)}
        warnings = []
        ground_result(result, pages, warnings)
        grounding_warns = [w for w in warnings if "Grounding FAIL" in w]
        assert len(grounding_warns) >= 1

    def test_value_never_deleted_on_fail(self):
        pages = [make_page(1, "No relevant content here.")]
        result = {"mat": self._make_feature_value(50000, "Delivery Rs. 50,000", page=1)}
        warnings = []
        out = ground_result(result, pages, warnings)
        # Value must still be present
        assert out["mat"]["limit_amount"] == 50000
