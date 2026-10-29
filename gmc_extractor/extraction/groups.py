"""
gmc_extractor/extraction/groups.py
Declarative list of GroupSpec objects defining each extraction group.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from pydantic import BaseModel

from gmc_extractor.schema.features import (
    BufferWaiver,
    InfertilityAmbulance,
    Maternity,
    OtherBenefitsA,
    OtherBenefitsB,
    RoomHospitalization,
    WaitingPeriods,
)
from gmc_extractor.schema.policy import Demographics, Identity, PolicyDetails


@dataclass
class GroupSpec:
    """
    Declarative specification for one extraction group.

    Attributes:
        name: Short identifier matching group_prompts and keywords keys.
        keyword_key: Key in keywords.yaml for retrieval.
        model: Pydantic model class to parse the LLM output into.
        description: Human-readable description (used in reports).
    """
    name: str
    keyword_key: str
    model: Type[BaseModel]
    description: str


# Ordered list of all extraction groups.
# Order matters: identity and policy_details are first (useful for context).
ALL_GROUPS: list[GroupSpec] = [
    GroupSpec(
        name="identity",
        keyword_key="identity",
        model=Identity,
        description="Insurer name and TPA name",
    ),
    GroupSpec(
        name="policy_details",
        keyword_key="policy_details",
        model=PolicyDetails,
        description="Policy dates, tenure, premium, family structure, SI tiers",
    ),
    GroupSpec(
        name="demographics",
        keyword_key="demographics",
        model=Demographics,
        description="Member census (employees, spouses, children, parents, total lives)",
    ),
    GroupSpec(
        name="room_hospitalization",
        keyword_key="room_hospitalization",
        model=RoomHospitalization,
        description="Room rent, ICU charges, pre/post-hospitalisation days",
    ),
    GroupSpec(
        name="maternity",
        keyword_key="maternity",
        model=Maternity,
        description="Maternity waiting period, delivery limits, baby cover, vaccination",
    ),
    GroupSpec(
        name="waiting_periods",
        keyword_key="waiting_periods",
        model=WaitingPeriods,
        description="30-day, 1st year, 2nd year, PED waiting periods",
    ),
    GroupSpec(
        name="other_benefits_a",
        keyword_key="other_benefits_a",
        model=OtherBenefitsA,
        description="Day care, OPD, teleconsultation, pharmacy, domiciliary, health check, modern treatment",
    ),
    GroupSpec(
        name="other_benefits_b",
        keyword_key="other_benefits_b",
        model=OtherBenefitsB,
        description="Bariatric, psychiatric, AYUSH, LGBTQ+, live-in partner, organ donor",
    ),
    GroupSpec(
        name="infertility_ambulance",
        keyword_key="infertility_ambulance",
        model=InfertilityAmbulance,
        description="Infertility treatment, surrogacy, road and air ambulance",
    ),
    GroupSpec(
        name="buffer_waiver",
        keyword_key="buffer_waiver",
        model=BufferWaiver,
        description="Corporate buffer, disease-wise capping, waiver conditions",
    ),
]
