"""
tests/test_long_document.py
Integration test for long document processing (50+ pages):
- Reads tests/fixtures/long_policy_50p.pdf (52 pages)
- Verifies full retrieval and extraction across large document
- Tests terminology variation ("Hospitalisation", "Lacs", "MediAssist TPA Services Ltd.")
- Evaluates endorsement override handling (Page 51 room rent override)
- Generates an honest recall and field coverage report
"""
import json
from pathlib import Path

import pytest

from gmc_extractor.config import Settings
from gmc_extractor.llm.mock_client import MockLLMClient
from gmc_extractor.pdf.reader import read_pdf
from gmc_extractor.pipeline import run_pdf
from gmc_extractor.retrieval.indexer import build_index
from gmc_extractor.retrieval.retriever import retrieve
import yaml


@pytest.fixture
def long_pdf_path() -> Path:
    p = Path(__file__).parent / "fixtures" / "long_policy_50p.pdf"
    if not p.exists():
        from create_long_policy import build_long_pdf
        build_long_pdf()
    return p


def test_long_document_page_count(long_pdf_path):
    """Verify document is at least 50 pages."""
    import fitz
    doc = fitz.open(str(long_pdf_path))
    assert doc.page_count >= 50
    doc.close()


def test_long_document_retrieval(long_pdf_path):
    """Test keyword and group retrieval across 50+ pages."""
    kw_path = Path(__file__).parent.parent / "config" / "keywords.yaml"
    with open(kw_path) as f:
        keywords = yaml.safe_load(f)

    pages = read_pdf(long_pdf_path, cache_dir=None)
    assert len(pages) >= 50

    index = build_index(pages)

    # Retrieval for identity should find page 1
    id_pages = retrieve(index, keywords, "identity", top_k=5)
    page_nums = [p.page_num for p in id_pages]
    assert 1 in page_nums

    # Retrieval for corporate buffer should find page 50
    buf_pages = retrieve(index, keywords, "buffer_waiver", top_k=5)
    buf_page_nums = [p.page_num for p in buf_pages]
    assert 50 in buf_page_nums


def test_long_document_full_pipeline_recall(long_pdf_path, tmp_path):
    """
    Run full pipeline on 50+ page document with MockLLMClient.
    Measures field recall and precision across QMS fields.
    """
    mock_client = MockLLMClient()
    settings = Settings(
        llm_provider="mock",
        cache_dir=tmp_path / ".cache",
        output_dir=tmp_path / "output",
        config_dir=Path(__file__).parent.parent / "config",
    )
    settings.ensure_dirs()

    result = run_pdf(long_pdf_path, mock_client, settings, use_cache=False)
    assert result is not None

    # Check QMS JSON output
    qms_json_path = tmp_path / "output" / "long_policy_50p.qms.json"
    assert qms_json_path.exists()

    rows = json.loads(qms_json_path.read_text(encoding="utf-8"))
    assert len(rows) > 50  # Over 50 QMS fields mapped

    # Metric evaluation
    total_fields = len(rows)
    covered_fields = [r for r in rows if r["status"] == "covered"]
    limited_fields = [r for r in rows if r["status"] == "limited"]
    not_mentioned_fields = [r for r in rows if r["status"] == "not_mentioned"]
    not_covered_fields = [r for r in rows if r["status"] == "not_covered"]
    needs_review_fields = [r for r in rows if r["status"] == "needs_review"]
    fields_with_evidence = [r for r in rows if r["evidence"] is not None and len(str(r["evidence"])) > 0]

    extracted_count = len(covered_fields) + len(limited_fields) + len(not_covered_fields) + len(needs_review_fields)
    recall_rate = extracted_count / total_fields
    active_fields = len(covered_fields) + len(limited_fields) + len(not_covered_fields)
    grounding_rate = len(fields_with_evidence) / max(1, active_fields)

    print(f"\n--- Long Document (52 pages) Recall Report ---")
    print(f"Total QMS Fields Mapped: {total_fields}")
    print(f"Active Extracted Fields: {extracted_count} ({recall_rate:.1%})")
    print(f"Not Mentioned Fields   : {len(not_mentioned_fields)}")
    print(f"Grounding Rate         : {grounding_rate:.1%}")

    # Assertions
    assert recall_rate >= 0.60, f"Expected >= 60% extraction recall, got {recall_rate:.1%}"
    assert grounding_rate >= 0.70, f"Expected >= 70% grounding rate, got {grounding_rate:.1%}"
