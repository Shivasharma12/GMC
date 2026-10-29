"""
tests/test_schema.py
Unit tests for the Pydantic schema models.
"""
import pytest
from pydantic import ValidationError

from gmc_extractor.schema.common import FeatureValue, FeatureStatus
from gmc_extractor.schema.policy import Demographics, PolicyDetails, SumInsuredTier
from gmc_extractor.schema.features import Maternity, WaitingPeriods, RoomHospitalization
from gmc_extractor.schema.output import ExtractionResult, DocumentInfo


class TestFeatureValue:
    def test_default_status_is_not_mentioned(self):
        fv = FeatureValue()
        assert fv.status == FeatureStatus.not_mentioned

    def test_valid_statuses(self):
        for s in ("covered", "not_covered", "waived_off", "applied", "limited", "not_mentioned"):
            fv = FeatureValue(status=s)
            assert fv.status.value == s

    def test_confidence_range(self):
        fv = FeatureValue(confidence=0.85)
        assert fv.confidence == 0.85

    def test_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            FeatureValue(confidence=1.5)

    def test_evidence_stored(self):
        fv = FeatureValue(evidence="Normal delivery Rs. 50,000")
        assert fv.evidence == "Normal delivery Rs. 50,000"

    def test_conditions_list(self):
        fv = FeatureValue(conditions=["Up to 2 children", "Metro only"])
        assert len(fv.conditions) == 2


class TestDemographics:
    def test_auto_compute_total(self):
        d = Demographics(num_employees=100, num_spouses=80, num_children=50, num_parents=20)
        assert d.total_lives_computed == 250

    def test_mismatch_flagged(self):
        d = Demographics(
            num_employees=100,
            num_spouses=80,
            num_children=50,
            num_parents=20,
            total_lives_stated=999,
        )
        assert d.count_mismatch is True

    def test_no_mismatch_when_correct(self):
        d = Demographics(
            num_employees=100,
            num_spouses=80,
            num_children=50,
            num_parents=20,
            total_lives_stated=250,
        )
        assert d.count_mismatch is False


class TestSumInsuredTier:
    def test_valid_tier(self):
        t = SumInsuredTier(amount=500000, grade_or_category="Grade A")
        assert t.amount == 500000

    def test_no_grade(self):
        t = SumInsuredTier(amount=300000)
        assert t.grade_or_category is None


class TestExtractionResult:
    def test_create_result(self):
        doc_info = DocumentInfo(
            file_name="test.pdf",
            total_pages=50,
            scanned_pages=0,
            provider="gemini",
            model="gemini-2.0-flash-lite",
        )
        result = ExtractionResult(document_info=doc_info)
        assert result.document_info.file_name == "test.pdf"
        assert result.overall_confidence == 0.0
        assert result.warnings == []

    def test_features_defaults(self):
        doc_info = DocumentInfo(
            file_name="test.pdf",
            total_pages=10,
            scanned_pages=0,
            provider="test",
            model="test",
        )
        result = ExtractionResult(document_info=doc_info)
        assert result.features.maternity.nine_month_waiting_period.status == FeatureStatus.not_mentioned

    def test_json_serializable(self):
        import json
        doc_info = DocumentInfo(
            file_name="test.pdf",
            total_pages=10,
            scanned_pages=0,
            provider="test",
            model="test",
        )
        result = ExtractionResult(document_info=doc_info)
        data = result.model_dump(mode="json")
        # Should be JSON serializable
        json_str = json.dumps(data)
        assert "test.pdf" in json_str


class TestWaitingPeriods:
    def test_waived_off_status(self):
        wp = WaitingPeriods(
            thirty_day_waiting=FeatureValue(status="waived_off", limit_days=30)
        )
        assert wp.thirty_day_waiting.status == FeatureStatus.waived_off

    def test_applied_status(self):
        wp = WaitingPeriods(
            ped_waiting=FeatureValue(status="applied", limit_days=1095)
        )
        assert wp.ped_waiting.status == FeatureStatus.applied


class TestMaternity:
    def test_metro_non_metro(self):
        m = Maternity(
            normal_delivery_metro=FeatureValue(status="limited", limit_amount=50000),
            normal_delivery_non_metro=FeatureValue(status="limited", limit_amount=35000),
        )
        assert m.normal_delivery_metro.limit_amount == 50000
        assert m.normal_delivery_non_metro.limit_amount == 35000
