"""
gmc_extractor/schema/common.py
Shared enums and the FeatureValue model used by every benefit/feature field.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FeatureStatus(str, Enum):
    """Possible status values for any extracted feature."""
    covered = "covered"
    not_covered = "not_covered"
    waived_off = "waived_off"
    applied = "applied"
    limited = "limited"
    not_mentioned = "not_mentioned"


class FeatureValue(BaseModel):
    """
    Universal model for a single insurance benefit / feature.

    All monetary amounts are in Indian Rupees (integers).
    Percentages are floats (0-100). Days are integers.
    """

    status: FeatureStatus = Field(
        default=FeatureStatus.not_mentioned,
        description="Whether this feature is covered, waived, applied, etc.",
    )
    limit_amount: Optional[int] = Field(
        default=None,
        description="Monetary limit in INR (e.g. 500000 for Rs. 5 lakh).",
    )
    limit_percent_of_si: Optional[float] = Field(
        default=None,
        description="Limit as a percentage of Sum Insured (0-100).",
    )
    limit_days: Optional[int] = Field(
        default=None,
        description="Limit expressed in number of days.",
    )
    limit_text: Optional[str] = Field(
        default=None,
        description=(
            "Original wording when limit cannot be expressed numerically "
            "(e.g. 'up to SI', 'as per hospital tariff')."
        ),
    )
    conditions: list[str] = Field(
        default_factory=list,
        description=(
            "Conditions, exceptions, sub-limits, or nested conditions. "
            "Preserve all; do not drop."
        ),
    )
    source_pages: list[int] = Field(
        default_factory=list,
        description="1-indexed page numbers from which this was extracted.",
    )
    evidence: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Short verbatim quote from the document (max 300 chars).",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score (0-1).",
    )

    model_config = {"populate_by_name": True}
