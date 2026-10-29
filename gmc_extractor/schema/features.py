"""
gmc_extractor/schema/features.py
Pydantic models for the 8 benefit-feature groups.
Every field uses FeatureValue for consistency.
Metro/non-metro pairs are explicit named fields.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from gmc_extractor.schema.common import FeatureValue


# ── Room / Hospitalization ────────────────────────────────────────────────────

class RoomHospitalization(BaseModel):
    """Room rent, ICU, and hospitalization day limits."""
    room_rent: FeatureValue = Field(default_factory=FeatureValue)
    icu_charges: FeatureValue = Field(default_factory=FeatureValue)
    pre_hospitalization_days: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Pre-hospitalisation coverage period.",
    )
    post_hospitalization_days: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Post-hospitalisation coverage period.",
    )


# ── Maternity ─────────────────────────────────────────────────────────────────

class Maternity(BaseModel):
    """Maternity benefits including delivery limits and baby cover."""
    nine_month_waiting_period: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Status of the standard 9-month maternity waiting period.",
    )
    baby_day_one_cover: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Cover for newborn from day one.",
    )
    vaccination_cover: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Baby vaccination benefit.",
    )
    normal_delivery_metro: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Normal delivery limit in metro cities.",
    )
    normal_delivery_non_metro: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Normal delivery limit in non-metro cities.",
    )
    c_section_metro: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Caesarean delivery limit in metro cities.",
    )
    c_section_non_metro: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Caesarean delivery limit in non-metro cities.",
    )


# ── Waiting Periods ───────────────────────────────────────────────────────────

class WaitingPeriods(BaseModel):
    """All waiting-period clauses."""
    thirty_day_waiting: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Standard 30-day initial waiting period.",
    )
    first_year_waiting: FeatureValue = Field(
        default_factory=FeatureValue,
        description="1st-year specific disease waiting period.",
    )
    second_year_waiting: FeatureValue = Field(
        default_factory=FeatureValue,
        description="2nd-year specific disease waiting period.",
    )
    ped_waiting: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Pre-existing disease (PED) waiting period.",
    )


# ── Other Benefits A ─────────────────────────────────────────────────────────

class OtherBenefitsA(BaseModel):
    """Day care, OPD, teleconsultation, pharmacy, domiciliary, health check, modern treatment."""
    day_care: FeatureValue = Field(default_factory=FeatureValue)
    opd: FeatureValue = Field(default_factory=FeatureValue)
    teleconsultation: FeatureValue = Field(default_factory=FeatureValue)
    pharmacy_discount: FeatureValue = Field(default_factory=FeatureValue)
    domiciliary_hospitalization: FeatureValue = Field(default_factory=FeatureValue)
    annual_health_checkup: FeatureValue = Field(default_factory=FeatureValue)
    modern_treatment: FeatureValue = Field(default_factory=FeatureValue)


# ── Other Benefits B ─────────────────────────────────────────────────────────

class OtherBenefitsB(BaseModel):
    """Bariatric, psychiatric, AYUSH, LGBTQ+, live-in partner, organ donor."""
    bariatric: FeatureValue = Field(default_factory=FeatureValue)
    psychiatric: FeatureValue = Field(default_factory=FeatureValue)
    ayush: FeatureValue = Field(default_factory=FeatureValue)
    lgbtq: FeatureValue = Field(default_factory=FeatureValue)
    live_in_partner: FeatureValue = Field(default_factory=FeatureValue)
    organ_donor_expenses: FeatureValue = Field(default_factory=FeatureValue)


# ── Infertility / Ambulance ───────────────────────────────────────────────────

class InfertilityAmbulance(BaseModel):
    """Infertility treatment, surrogacy, ambulance charges."""
    infertility_treatment: FeatureValue = Field(default_factory=FeatureValue)
    surrogacy: FeatureValue = Field(default_factory=FeatureValue)
    ambulance_charges: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Road ambulance charges.",
    )
    air_ambulance: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Air/helicopter ambulance charges.",
    )


# ── Buffer / Waiver ───────────────────────────────────────────────────────────

class DiseaseCapEntry(BaseModel):
    """A single disease → limit mapping for disease-wise capping."""
    disease: str
    limit_amount: Optional[int] = None
    limit_text: Optional[str] = None


class BufferWaiver(BaseModel):
    """Corporate buffer limit, disease-wise capping, and waiver conditions."""
    corporate_buffer_amount: FeatureValue = Field(
        default_factory=FeatureValue,
        description="Corporate buffer / top-up pool limit.",
    )
    corporate_buffer_eligibility: Optional[str] = Field(
        default=None,
        description="Who can access the corporate buffer and under what conditions.",
    )
    disease_wise_capping: list[DiseaseCapEntry] = Field(
        default_factory=list,
        description="List of disease → limit mappings.",
    )
    waiver_conditions: list[str] = Field(
        default_factory=list,
        description="Conditions under which waivers apply.",
    )
    source_pages: list[int] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ── Feature Container ─────────────────────────────────────────────────────────

class Features(BaseModel):
    """All benefit feature groups bundled together."""
    room_hospitalization: RoomHospitalization = Field(default_factory=RoomHospitalization)
    maternity: Maternity = Field(default_factory=Maternity)
    waiting_periods: WaitingPeriods = Field(default_factory=WaitingPeriods)
    other_benefits_a: OtherBenefitsA = Field(default_factory=OtherBenefitsA)
    other_benefits_b: OtherBenefitsB = Field(default_factory=OtherBenefitsB)
    infertility_ambulance: InfertilityAmbulance = Field(default_factory=InfertilityAmbulance)
    buffer_waiver: BufferWaiver = Field(default_factory=BufferWaiver)
