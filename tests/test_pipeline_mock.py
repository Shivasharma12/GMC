"""
tests/test_pipeline_mock.py
Full pipeline integration test using a mocked LLM client.
No real API key is needed.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gmc_extractor.llm.base import LLMClient
from gmc_extractor.schema.output import ExtractionResult


# ── Mock LLM that returns plausible JSON for every group ─────────────────────

class MockLLMClient(LLMClient):
    """Mock LLM client that returns deterministic JSON responses."""

    def __init__(self):
        self._call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-model"

    def ask_json(self, system: str, prompt: str) -> dict:
        self._call_count += 1
        # Determine which group is being extracted from the prompt
        if "insurer_name" in prompt or "tpa_name" in prompt:
            return {
                "insurer_name": "Test General Insurance Ltd.",
                "tpa_name": "TestTPA Services",
                "source_pages": [1],
                "confidence": 0.9,
            }
        elif "policy_start_date" in prompt:
            return {
                "policy_number": "GRP/TEST/2024/001",
                "previous_inception_date": "2023-04-01",
                "policy_start_date": "2024-04-01",
                "policy_end_date": "2025-03-31",
                "tenure_months": 12,
                "premium_excluding_gst": 1800000,
                "premium_including_gst": 2124000,
                "family_structure": {
                    "employee": True,
                    "spouse": True,
                    "children": True,
                    "parents": False,
                    "parents_in_law": False,
                    "conditions": [],
                },
                "sum_insured_tiers": [
                    {"amount": 300000, "grade_or_category": "Grade B"},
                    {"amount": 500000, "grade_or_category": "Grade A"},
                ],
                "source_pages": [3],
                "confidence": 0.88,
                "conditions": [],
            }
        elif "num_employees" in prompt:
            return {
                "num_employees": 450,
                "num_spouses": 380,
                "num_children": 620,
                "num_parents": 210,
                "total_lives_stated": 1660,
                "source_pages": [7],
                "confidence": 0.92,
                "conditions": [],
            }
        elif "room_rent" in prompt:
            fv = lambda: {
                "status": "limited",
                "limit_amount": None,
                "limit_percent_of_si": 1.0,
                "limit_days": None,
                "limit_text": "1% of SI per day",
                "conditions": [],
                "source_pages": [12],
                "evidence": "Room rent: 1% of SI",
                "confidence": 0.9,
            }
            return {
                "room_rent": fv(),
                "icu_charges": {**fv(), "limit_percent_of_si": 2.0, "limit_text": "2% of SI"},
                "pre_hospitalization_days": {**fv(), "limit_percent_of_si": None, "limit_days": 30, "limit_text": None},
                "post_hospitalization_days": {**fv(), "limit_percent_of_si": None, "limit_days": 60, "limit_text": None},
            }
        elif "nine_month_waiting" in prompt or "normal_delivery" in prompt:
            fv = {
                "status": "limited",
                "limit_amount": 50000,
                "limit_percent_of_si": None,
                "limit_days": None,
                "limit_text": None,
                "conditions": [],
                "source_pages": [18],
                "evidence": "Normal delivery: Rs. 50,000",
                "confidence": 0.85,
            }
            return {
                "nine_month_waiting_period": {**fv, "status": "waived_off", "limit_amount": None},
                "baby_day_one_cover": {**fv, "status": "covered", "limit_amount": None},
                "vaccination_cover": {**fv, "limit_amount": 5000},
                "normal_delivery_metro": fv,
                "normal_delivery_non_metro": {**fv, "limit_amount": 35000},
                "c_section_metro": {**fv, "limit_amount": 75000},
                "c_section_non_metro": {**fv, "limit_amount": 55000},
            }
        elif "thirty_day_waiting" in prompt:
            fv = {
                "status": "waived_off",
                "limit_amount": None,
                "limit_percent_of_si": None,
                "limit_days": 30,
                "limit_text": None,
                "conditions": [],
                "source_pages": [22],
                "evidence": "30-day waiting: waived",
                "confidence": 0.9,
            }
            return {
                "thirty_day_waiting": fv,
                "first_year_waiting": {**fv, "status": "applied"},
                "second_year_waiting": {**fv, "status": "applied"},
                "ped_waiting": {**fv, "status": "waived_off"},
            }
        elif "day_care" in prompt:
            fv = {
                "status": "covered",
                "limit_amount": None,
                "limit_percent_of_si": None,
                "limit_days": None,
                "limit_text": "All procedures",
                "conditions": [],
                "source_pages": [28],
                "evidence": "Day care: all procedures covered",
                "confidence": 0.85,
            }
            return {
                "day_care": fv,
                "opd": {**fv, "limit_amount": 3000, "limit_text": None},
                "teleconsultation": fv,
                "pharmacy_discount": fv,
                "domiciliary_hospitalization": fv,
                "annual_health_checkup": {**fv, "limit_amount": 2500},
                "modern_treatment": fv,
            }
        elif "bariatric" in prompt:
            fv = {
                "status": "limited",
                "limit_amount": 200000,
                "limit_percent_of_si": None,
                "limit_days": None,
                "limit_text": None,
                "conditions": [],
                "source_pages": [33],
                "evidence": "Bariatric: Rs. 2,00,000",
                "confidence": 0.8,
            }
            return {
                "bariatric": fv,
                "psychiatric": {**fv, "limit_amount": None, "status": "covered"},
                "ayush": {**fv, "limit_amount": 15000},
                "lgbtq": {**fv, "status": "covered", "limit_amount": None},
                "live_in_partner": {**fv, "status": "covered", "limit_amount": None},
                "organ_donor_expenses": {**fv, "status": "covered", "limit_amount": None},
            }
        elif "infertility" in prompt or "ambulance" in prompt:
            fv = {
                "status": "limited",
                "limit_amount": 100000,
                "limit_percent_of_si": None,
                "limit_days": None,
                "limit_text": None,
                "conditions": [],
                "source_pages": [38],
                "evidence": "Infertility: Rs. 1,00,000",
                "confidence": 0.8,
            }
            return {
                "infertility_treatment": fv,
                "surrogacy": {**fv, "status": "not_covered", "limit_amount": None},
                "ambulance_charges": {**fv, "limit_amount": 2000},
                "air_ambulance": {**fv, "limit_amount": 500000},
            }
        elif "corporate_buffer" in prompt or "disease_wise" in prompt:
            return {
                "corporate_buffer_amount": {
                    "status": "covered",
                    "limit_amount": 1000000,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": "Rs. 10,00,000",
                    "conditions": [],
                    "source_pages": [45],
                    "evidence": "Corporate buffer: Rs. 10,00,000",
                    "confidence": 0.85,
                },
                "corporate_buffer_eligibility": "All employees after SI exhausted",
                "disease_wise_capping": [
                    {"disease": "Cataract", "limit_amount": 30000, "limit_text": "Rs. 30,000 per eye"},
                ],
                "waiver_conditions": ["Co-pay waived for senior employees"],
                "source_pages": [45],
                "confidence": 0.82,
            }
        # Default fallback
        return {}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_client():
    return MockLLMClient()


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal synthetic PDF for testing."""
    try:
        import fitz
        pdf_path = tmp_path / "test_policy.pdf"
        doc = fitz.open()
        for i in range(5):
            page = doc.new_page()
            page.insert_text(
                (50, 50 + i * 20),
                f"Page {i+1}: Group Mediclaim Policy. Room rent 1% of SI. Maternity Rs. 50,000. TPA: TestTPA.",
            )
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path
    except ImportError:
        pytest.skip("PyMuPDF not installed")


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPipelineMock:
    def test_mock_llm_returns_dict(self, mock_client):
        """MockLLMClient returns non-empty dicts."""
        result = mock_client.ask_json("system", "Extract insurer_name and tpa_name from the text.")
        assert isinstance(result, dict)
        assert "insurer_name" in result

    def test_extraction_group_with_mock(self, mock_client, sample_pdf):
        """Run a single extraction group with the mock client."""
        from gmc_extractor.pdf.reader import read_pdf
        from gmc_extractor.pdf.cleaner import clean_pages
        from gmc_extractor.retrieval.indexer import build_index
        from gmc_extractor.extraction.groups import ALL_GROUPS
        from gmc_extractor.extraction.runner import extract_group
        import yaml
        from pathlib import Path

        # Load real keywords
        keywords_path = Path(__file__).parent.parent / "config" / "keywords.yaml"
        with open(keywords_path) as f:
            keywords = yaml.safe_load(f)

        pages = read_pdf(sample_pdf, cache_dir=None)
        pages = clean_pages(pages)
        index = build_index(pages)

        identity_spec = next(s for s in ALL_GROUPS if s.name == "identity")
        warnings = []
        result = extract_group(identity_spec, index, keywords, mock_client, warnings)

        assert result is not None

    def test_full_pipeline_mock(self, mock_client, sample_pdf, tmp_path):
        """Run the full pipeline with a mock LLM and verify outputs are created."""
        from gmc_extractor.config import Settings
        from gmc_extractor.pipeline import run_pdf

        settings = Settings(
            llm_provider="mock",
            cache_dir=tmp_path / ".cache",
            output_dir=tmp_path / "output",
        )
        settings.ensure_dirs()

        result = run_pdf(sample_pdf, mock_client, settings, use_cache=False)

        assert isinstance(result, ExtractionResult)
        assert result.document_info.file_name == "test_policy.pdf"

        # Verify output files exist
        stem = settings.output_dir / "test_policy"
        assert (settings.output_dir / "test_policy.json").exists()
        assert (settings.output_dir / "test_policy.qms.json").exists()
        assert (settings.output_dir / "test_policy.qms.csv").exists()
        assert (settings.output_dir / "test_policy.report.md").exists()

    def test_output_json_structure(self, mock_client, sample_pdf, tmp_path):
        """Verify the output JSON has the expected top-level keys."""
        from gmc_extractor.config import Settings
        from gmc_extractor.pipeline import run_pdf

        settings = Settings(
            llm_provider="mock",
            cache_dir=tmp_path / ".cache",
            output_dir=tmp_path / "output",
        )
        settings.ensure_dirs()

        result = run_pdf(sample_pdf, mock_client, settings, use_cache=False)
        data = result.model_dump(mode="json")

        assert "document_info" in data
        assert "identity" in data
        assert "policy_details" in data
        assert "demographics" in data
        assert "features" in data
        assert "overall_confidence" in data
        assert "warnings" in data

    def test_failed_group_does_not_crash_pipeline(self, sample_pdf, tmp_path):
        """A group that raises an exception should not crash the whole pipeline."""
        from gmc_extractor.config import Settings
        from gmc_extractor.pipeline import run_pdf

        class FailingClient(MockLLMClient):
            def ask_json(self, system, prompt):
                raise ConnectionError("Simulated LLM failure")

        settings = Settings(
            llm_provider="mock",
            cache_dir=tmp_path / ".cache",
            output_dir=tmp_path / "output",
        )
        settings.ensure_dirs()

        result = run_pdf(sample_pdf, FailingClient(), settings, use_cache=False)
        # Should still produce a result (with warnings)
        assert isinstance(result, ExtractionResult)
        assert len(result.warnings) > 0

    def test_qms_csv_has_headers(self, mock_client, sample_pdf, tmp_path):
        """QMS CSV should have the expected column headers."""
        import csv
        from gmc_extractor.config import Settings
        from gmc_extractor.pipeline import run_pdf

        settings = Settings(
            llm_provider="mock",
            cache_dir=tmp_path / ".cache",
            output_dir=tmp_path / "output",
        )
        settings.ensure_dirs()

        run_pdf(sample_pdf, mock_client, settings, use_cache=False)

        csv_path = settings.output_dir / "test_policy.qms.csv"
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        assert "qms_field" in headers
        assert "label" in headers
        assert "status" in headers
        assert "confidence" in headers
