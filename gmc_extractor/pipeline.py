"""
gmc_extractor/pipeline.py
Orchestrates the full GMC extraction pipeline for one PDF.
Also provides a batch mode for processing a folder of PDFs.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from gmc_extractor.config import Settings
from gmc_extractor.export.json_writer import write_json, write_report
from gmc_extractor.export.qms_mapper import write_qms
from gmc_extractor.extraction.groups import ALL_GROUPS
from gmc_extractor.extraction.runner import extract_group
from gmc_extractor.llm.base import LLMClient
from gmc_extractor.pdf.cleaner import clean_pages
from gmc_extractor.pdf.reader import read_pdf
from gmc_extractor.postprocess.confidence import compute_overall_confidence
from gmc_extractor.postprocess.grounding import ground_result
from gmc_extractor.postprocess.validator import validate_result
from gmc_extractor.retrieval.indexer import build_index
from gmc_extractor.schema.output import DocumentInfo, ExtractionResult

logger = logging.getLogger(__name__)


def run_pdf(
    pdf_path: Path,
    client: LLMClient,
    settings: Settings,
    use_cache: bool = True,
) -> ExtractionResult:
    """
    Run the full extraction pipeline on a single PDF.

    Args:
        pdf_path: Path to the PDF file.
        client: Configured LLM client.
        settings: Global settings.
        use_cache: Whether to use page-level cache.

    Returns:
        A fully populated ExtractionResult.
    """
    pdf_path = Path(pdf_path)
    warnings: list[str] = []

    logger.info("=" * 60)
    logger.info("Processing: %s", pdf_path.name)

    # ── 1. READ ──────────────────────────────────────────────────────────────
    cache_dir = settings.cache_dir if use_cache else None
    pages = read_pdf(pdf_path, cache_dir=cache_dir, ocr_available=True)
    total_pages = len(pages)
    scanned_pages = sum(1 for p in pages if p.is_scanned)

    # ── 2. CLEAN ─────────────────────────────────────────────────────────────
    pages = clean_pages(pages)

    # ── 3. INDEX ─────────────────────────────────────────────────────────────
    index = build_index(pages)

    # ── 4. EXTRACT per group ─────────────────────────────────────────────────
    doc_info = DocumentInfo(
        file_name=pdf_path.name,
        total_pages=total_pages,
        scanned_pages=scanned_pages,
        provider=client.provider_name,
        model=client.model_name,
    )
    result = ExtractionResult(document_info=doc_info)

    for spec in ALL_GROUPS:
        logger.info("Extracting group: %s", spec.name)
        try:
            group_result = extract_group(
                spec=spec,
                index=index,
                keywords=settings.keywords,
                client=client,
                warnings=warnings,
            )
            # Assign to the correct field on the result
            _assign_group(result, spec.name, group_result)
        except Exception as exc:
            msg = f"Group '{spec.name}' failed with unexpected error: {exc}"
            logger.error(msg, exc_info=True)
            warnings.append(msg)

    # ── 5. POSTPROCESS ───────────────────────────────────────────────────────
    result_dict = result.model_dump(mode="json")
    result_dict = ground_result(result_dict, pages, warnings)
    result_dict = validate_result(result_dict, warnings)
    overall_conf = compute_overall_confidence(result_dict)

    # Reconstruct result from the post-processed dict
    result_dict["overall_confidence"] = overall_conf
    result_dict["warnings"] = warnings
    result = ExtractionResult.model_validate(result_dict)

    # ── 6. EXPORT ────────────────────────────────────────────────────────────
    stem = settings.output_dir / pdf_path.stem
    write_json(result, stem.with_suffix(".json"))
    write_qms(result, stem, settings)
    write_report(result, stem.parent / (stem.name + ".report.md"))

    logger.info(
        "Done: %s | confidence=%.0f%% | warnings=%d",
        pdf_path.name, overall_conf * 100, len(warnings)
    )
    return result


def run_batch(
    folder: Path,
    client: LLMClient,
    settings: Settings,
    use_cache: bool = True,
) -> list[ExtractionResult]:
    """
    Process all PDF files in *folder*.

    Args:
        folder: Directory containing PDF files.
        client: Configured LLM client.
        settings: Global settings.
        use_cache: Whether to use page-level cache.

    Returns:
        List of ExtractionResult objects (one per PDF).
    """
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        logger.warning("No PDF files found in %s", folder)
        return []

    logger.info("Found %d PDFs in %s", len(pdfs), folder)
    results: list[ExtractionResult] = []

    for pdf_path in pdfs:
        try:
            result = run_pdf(pdf_path, client, settings, use_cache=use_cache)
            results.append(result)
        except RuntimeError as exc:
            # Max requests reached
            logger.error("Stopping batch: %s", exc)
            break
        except Exception as exc:
            logger.error("Failed to process %s: %s", pdf_path.name, exc, exc_info=True)

    return results


# ── Internal helpers ──────────────────────────────────────────────────────────

def _assign_group(result: ExtractionResult, group_name: str, group_result: object) -> None:
    """Assign the extracted group model to the correct field on ExtractionResult."""
    from gmc_extractor.schema.policy import Identity, PolicyDetails, Demographics
    from gmc_extractor.schema.features import (
        RoomHospitalization, Maternity, WaitingPeriods,
        OtherBenefitsA, OtherBenefitsB, InfertilityAmbulance, BufferWaiver,
    )

    mapping = {
        "identity": "identity",
        "policy_details": "policy_details",
        "demographics": "demographics",
        "room_hospitalization": ("features", "room_hospitalization"),
        "maternity": ("features", "maternity"),
        "waiting_periods": ("features", "waiting_periods"),
        "other_benefits_a": ("features", "other_benefits_a"),
        "other_benefits_b": ("features", "other_benefits_b"),
        "infertility_ambulance": ("features", "infertility_ambulance"),
        "buffer_waiver": ("features", "buffer_waiver"),
    }

    target = mapping.get(group_name)
    if target is None:
        return

    if isinstance(target, str):
        setattr(result, target, group_result)
    elif isinstance(target, tuple):
        parent_attr, child_attr = target
        parent = getattr(result, parent_attr)
        setattr(parent, child_attr, group_result)
