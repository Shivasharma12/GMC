"""
gmc_extractor/schema/output.py
Top-level ExtractionResult model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from gmc_extractor.schema.features import Features
from gmc_extractor.schema.policy import Demographics, Identity, PolicyDetails


class DocumentInfo(BaseModel):
    """Metadata about the processed PDF and the pipeline run."""
    file_name: str
    total_pages: int
    scanned_pages: int
    provider: str
    model: str
    run_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )
    failed_groups: list[str] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class ExtractionResult(BaseModel):
    """
    Top-level output of the GMC extraction pipeline for a single PDF.

    Fields that could not be found are left as None or not_mentioned.
    Never invent values — if absent, leave null.
    """
    document_info: DocumentInfo
    identity: Identity = Field(default_factory=Identity)
    policy_details: PolicyDetails = Field(default_factory=PolicyDetails)
    demographics: Demographics = Field(default_factory=Demographics)
    features: Features = Field(default_factory=Features)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal issues, low-confidence fields, grounding failures, etc.",
    )
