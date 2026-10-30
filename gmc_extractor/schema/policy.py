"""
gmc_extractor/schema/policy.py
Pydantic models for identity, policy details, and demographics.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator

from gmc_extractor.schema.common import FeatureValue


# ── Identity ──────────────────────────────────────────────────────────────────

class Identity(BaseModel):
    """Insurer and TPA identification."""
    insurer_name: Optional[str] = Field(default=None, description="Name of the insurance company.")
    tpa_name: Optional[str] = Field(default=None, description="Name of the Third Party Administrator (TPA).")
    source_pages: list[int] = Field(default_factory=list)
    evidence: Optional[str] = Field(default=None, description="Short verbatim evidence quote from document.")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ── Policy Details ────────────────────────────────────────────────────────────

class FamilyStructure(BaseModel):
    """Which family members are covered under this policy."""
    employee: bool = Field(default=False)
    spouse: bool = Field(default=False)
    children: bool = Field(default=False)
    parents: bool = Field(default=False)
    parents_in_law: bool = Field(default=False)
    conditions: list[str] = Field(default_factory=list, description="Any conditions on family coverage.")


class SumInsuredTier(BaseModel):
    """A single sum-insured tier with optional grade/category mapping."""
    amount: int = Field(description="Sum insured amount in INR.")
    grade_or_category: Optional[str] = Field(
        default=None, description="Employee grade or category this tier applies to."
    )


class PolicyDetails(BaseModel):
    """Core policy metadata."""
    policy_number: Optional[str] = Field(default=None)
    previous_inception_date: Optional[str] = Field(
        default=None, description="Previous year inception/renewal date (ISO yyyy-mm-dd)."
    )
    policy_start_date: Optional[str] = Field(
        default=None, description="Policy start date (ISO yyyy-mm-dd)."
    )
    policy_end_date: Optional[str] = Field(
        default=None, description="Policy end date (ISO yyyy-mm-dd)."
    )
    tenure_months: Optional[int] = Field(
        default=None, description="Policy tenure in months."
    )
    premium_excluding_gst: Optional[int] = Field(
        default=None, description="Net premium (INR, excluding GST)."
    )
    premium_including_gst: Optional[int] = Field(
        default=None, description="Gross premium (INR, including GST)."
    )
    family_structure: FamilyStructure = Field(default_factory=FamilyStructure)
    sum_insured_tiers: list[SumInsuredTier] = Field(
        default_factory=list,
        description="All sum-insured tiers (ascending order).",
    )
    total_sum_insured: Optional[int] = Field(
        default=None,
        description="Aggregate/total policy Sum Insured if explicitly stated.",
    )
    source_pages: list[int] = Field(default_factory=list)
    evidence: Optional[str] = Field(default=None, description="Short verbatim evidence quote from document.")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    conditions: list[str] = Field(default_factory=list)


# ── Demographics ──────────────────────────────────────────────────────────────

class Demographics(BaseModel):
    """Census / member count data."""
    num_employees: Optional[int] = Field(default=None)
    num_dependents: Optional[int] = Field(
        default=None, description="Total dependents when stated as an aggregate count."
    )
    num_spouses: Optional[int] = Field(default=None)
    num_children: Optional[int] = Field(default=None)
    num_parents: Optional[int] = Field(default=None, description="Parents + parents-in-law combined.")
    total_lives_stated: Optional[int] = Field(
        default=None, description="Total lives as explicitly stated in the document."
    )
    total_lives_computed: Optional[int] = Field(
        default=None, description="Sum of employees + dependents or members."
    )
    count_mismatch: bool = Field(
        default=False,
        description="True if stated total does not match computed total.",
    )
    source_pages: list[int] = Field(default_factory=list)
    evidence: Optional[str] = Field(default=None, description="Short verbatim evidence quote from document.")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    conditions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _compute_total(self) -> "Demographics":
        """Auto-compute total_lives and flag mismatch."""
        if self.total_lives_computed is None:
            if self.num_employees is not None and self.num_dependents is not None:
                self.total_lives_computed = self.num_employees + self.num_dependents
            else:
                parts = [self.num_employees, self.num_spouses, self.num_children, self.num_parents]
                if any(v is not None for v in parts):
                    self.total_lives_computed = sum(v for v in parts if v is not None)
        if (
            self.total_lives_stated is not None
            and self.total_lives_computed is not None
            and self.total_lives_stated != self.total_lives_computed
        ):
            self.count_mismatch = True
        return self
