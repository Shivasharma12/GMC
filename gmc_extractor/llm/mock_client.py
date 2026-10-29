"""
gmc_extractor/llm/mock_client.py
Mock LLM client for offline testing and evaluation without an API key.
Returns schema-valid JSON responses aligned with sample GMC policies.
"""
from __future__ import annotations

import logging
from typing import Any

from gmc_extractor.llm.base import LLMClient

logger = logging.getLogger(__name__)


class MockLLMClient(LLMClient):
    """Mock LLM client returning realistic, grounded responses for offline testing."""

    def __init__(self, model: str = "mock-model") -> None:
        self._model = model

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model

    def ask_json(self, system: str, prompt: str) -> dict[str, Any]:
        """Match group based on prompt task heading and return mock data."""
        p = prompt.lower()

        # Check by task or group identifier
        if "extract the insurer name and tpa" in p or "group: identity" in p or '"insurer_name"' in p:
            return {
                "insurer_name": "Star Health and Allied Insurance Company Limited",
                "tpa_name": "Medi Assist Insurance TPA Private Limited",
                "source_pages": [1],
                "confidence": 0.95,
            }

        elif "extract policy-level details" in p or "group: policy_details" in p or '"policy_start_date"' in p:
            return {
                "policy_number": "STAR/GMC/2024/09841",
                "previous_inception_date": "2023-04-01",
                "policy_start_date": "2024-04-01",
                "policy_end_date": "2025-03-31",
                "tenure_months": 12,
                "premium_excluding_gst": 1250000,
                "premium_including_gst": 1475000,
                "family_structure": {
                    "employee": True,
                    "spouse": True,
                    "children": True,
                    "parents": True,
                    "parents_in_law": True,
                    "conditions": ["1+5 Family Floater", "up to 2 dependent Children"],
                },
                "sum_insured_tiers": [
                    {"amount": 300000, "grade_or_category": "Grade B (Management)"},
                    {"amount": 500000, "grade_or_category": "Grade A (Executive)"},
                ],
                "source_pages": [1],
                "confidence": 0.95,
                "conditions": [],
            }

        elif "extract the number of insured members" in p or "group: demographics" in p or '"num_employees"' in p:
            return {
                "num_employees": 150,
                "num_spouses": 120,
                "num_children": 180,
                "num_parents": 50,
                "total_lives_stated": 500,
                "source_pages": [2],
                "confidence": 0.98,
                "conditions": [],
            }

        elif "extract room rent limits" in p or "group: room_hospitalization" in p or '"room_rent"' in p:
            fv = {
                "status": "limited",
                "limit_amount": 5000,
                "limit_percent_of_si": 1.0,
                "limit_days": None,
                "limit_text": "1% of Sum Insured per day, subject to max Rs. 5,000",
                "conditions": ["Single Private AC Room", "Proportionate deduction will apply"],
                "source_pages": [3],
                "evidence": "Room Rent is covered up to 1% of Sum Insured per day, subject to a maximum of Rs. 5,000 per day",
                "confidence": 0.95,
            }
            return {
                "room_rent": fv,
                "icu_charges": {
                    "status": "limited",
                    "limit_amount": 10000,
                    "limit_percent_of_si": 2.0,
                    "limit_days": None,
                    "limit_text": "2% of Sum Insured per day, subject to max Rs. 10,000",
                    "conditions": [],
                    "source_pages": [3],
                    "evidence": "ICU charges are covered up to 2% of Sum Insured per day, subject to maximum Rs. 10,000 per day.",
                    "confidence": 0.95,
                },
                "pre_hospitalization_days": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": 30,
                    "limit_text": "30 days prior to admission",
                    "conditions": [],
                    "source_pages": [3],
                    "evidence": "Pre-hospitalization medical expenses: Covered for 30 days prior to the date of admission.",
                    "confidence": 0.95,
                },
                "post_hospitalization_days": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": 60,
                    "limit_text": "60 days from discharge",
                    "conditions": [],
                    "source_pages": [3],
                    "evidence": "Post-hospitalization medical expenses: Covered for 60 days from the date of discharge.",
                    "confidence": 0.95,
                },
            }

        elif "extract maternity benefits" in p or "group: maternity" in p or '"normal_delivery_metro"' in p:
            base_mat = {
                "status": "covered",
                "limit_amount": 50000,
                "limit_percent_of_si": None,
                "limit_days": None,
                "limit_text": None,
                "conditions": ["Restricted to first 2 living children"],
                "source_pages": [4],
                "evidence": "Normal Delivery limit: Rs. 50,000 in Metro cities",
                "confidence": 0.95,
            }
            return {
                "nine_month_waiting_period": {
                    "status": "waived_off",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": "Waived off from Day 1",
                    "conditions": ["All employees and spouses"],
                    "source_pages": [4],
                    "evidence": "Maternity waiting period of 9 months is waived off from Day 1",
                    "confidence": 0.95,
                },
                "baby_day_one_cover": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": "Covered from birth up to normal delivery limit",
                    "conditions": [],
                    "source_pages": [4],
                    "evidence": "Baby Day One cover is included from birth",
                    "confidence": 0.95,
                },
                "vaccination_cover": {
                    "status": "covered",
                    "limit_amount": 5000,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Within the first year"],
                    "source_pages": [4],
                    "evidence": "Newborn vaccination cover is covered up to Rs. 5,000",
                    "confidence": 0.95,
                },
                "normal_delivery_metro": base_mat,
                "normal_delivery_non_metro": {
                    **base_mat,
                    "limit_amount": 40000,
                    "evidence": "Rs. 40,000 in Non-Metro cities",
                },
                "c_section_metro": {
                    **base_mat,
                    "limit_amount": 75000,
                    "evidence": "Caesarean (C-Section) delivery limit: Rs. 75,000 in Metro cities",
                },
                "c_section_non_metro": {
                    **base_mat,
                    "limit_amount": 60000,
                    "evidence": "Rs. 60,000 in Non-Metro cities",
                },
            }

        elif "extract waiting period terms" in p or "group: waiting_periods" in p or '"thirty_day_waiting"' in p:
            wv = {
                "status": "waived_off",
                "limit_amount": None,
                "limit_percent_of_si": None,
                "limit_days": None,
                "limit_text": "Waived off from Day 1",
                "conditions": [],
                "source_pages": [5],
                "evidence": "The standard 30-day initial waiting period is waived off under this Group policy.",
                "confidence": 0.95,
            }
            return {
                "thirty_day_waiting": wv,
                "first_year_waiting": {
                    **wv,
                    "evidence": "Waiting period of 1st and 2nd year for specified illnesses / treatments is waived off.",
                },
                "second_year_waiting": {
                    **wv,
                    "evidence": "Waiting period of 1st and 2nd year for specified illnesses / treatments is waived off.",
                },
                "ped_waiting": {
                    **wv,
                    "evidence": "Pre-existing diseases waiting period is waived off from inception of cover.",
                },
            }

        elif "extract day care" in p or "group: other_benefits_a" in p or '"day_care"' in p:
            fv = {
                "status": "covered",
                "limit_amount": None,
                "limit_percent_of_si": None,
                "limit_days": None,
                "limit_text": None,
                "conditions": [],
                "source_pages": [6],
                "evidence": "All day care procedures requiring less than 24 hours hospitalization due to advanced technology are covered.",
                "confidence": 0.95,
            }
            return {
                "day_care": fv,
                "opd": {
                    **fv,
                    "limit_amount": 10000,
                    "evidence": "OPD consultations and diagnostics are covered up to Rs. 10,000 per family",
                },
                "teleconsultation": {
                    **fv,
                    "evidence": "Unlimited free audio/video consultations available via dedicated insurer mobile application.",
                },
                "pharmacy_discount": {
                    **fv,
                    "limit_percent_of_si": 10.0,
                    "evidence": "Up to 10% discount on prescribed medicines across network partner pharmacies.",
                },
                "domiciliary_hospitalization": {
                    **fv,
                    "limit_percent_of_si": 20.0,
                    "conditions": ["When treatment exceeds 3 days"],
                    "evidence": "DOMICILIARY HOSPITALIZATION: Covered up to 20% of Sum Insured",
                },
                "annual_health_checkup": {
                    **fv,
                    "conditions": ["Employee and spouse"],
                    "evidence": "Free annual preventive health check-up package for employee and spouse.",
                },
                "modern_treatment": {
                    **fv,
                    "evidence": "robotic surgery, stem cell therapy covered up to Sum Insured.",
                },
            }

        elif "extract bariatric" in p or "group: other_benefits_b" in p or '"bariatric"' in p:
            fv = {
                "status": "covered",
                "limit_amount": 150000,
                "limit_percent_of_si": None,
                "limit_days": None,
                "limit_text": None,
                "conditions": ["BMI is greater than 35"],
                "source_pages": [7],
                "evidence": "Covered up to Rs. 1,50,000 for morbid obesity when BMI is greater than 35.",
                "confidence": 0.95,
            }
            return {
                "bariatric": fv,
                "psychiatric": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": "Up to Sum Insured",
                    "conditions": [],
                    "source_pages": [7],
                    "evidence": "In-patient psychiatric treatment covered up to Sum Insured.",
                    "confidence": 0.95,
                },
                "ayush": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": 100.0,
                    "limit_days": None,
                    "limit_text": "100% of Sum Insured",
                    "conditions": ["In registered hospitals"],
                    "source_pages": [7],
                    "evidence": "treatments covered up to 100% of Sum Insured in registered hospitals.",
                    "confidence": 0.95,
                },
                "lgbtq": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Recognized under spouse definition"],
                    "source_pages": [7],
                    "evidence": "Same-sex partners and live-in partners recognized as dependents under spouse definition.",
                    "confidence": 0.95,
                },
                "live_in_partner": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Recognized under spouse definition"],
                    "source_pages": [7],
                    "evidence": "Same-sex partners and live-in partners recognized as dependents under spouse definition.",
                    "confidence": 0.95,
                },
                "organ_donor_expenses": {
                    "status": "covered",
                    "limit_amount": 500000,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": [],
                    "source_pages": [7],
                    "evidence": "In-patient hospitalization expenses of donor covered up to Rs. 5,00,000.",
                    "confidence": 0.95,
                },
            }

        elif "extract infertility treatment" in p or "group: infertility_ambulance" in p or '"infertility_treatment"' in p:
            return {
                "infertility_treatment": {
                    "status": "limited",
                    "limit_amount": 100000,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Per family"],
                    "source_pages": [7],
                    "evidence": "Infertility investigation and procedures covered up to Rs. 1,00,000",
                    "confidence": 0.95,
                },
                "surrogacy": {
                    "status": "not_covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": "Not covered",
                    "conditions": [],
                    "source_pages": [7],
                    "evidence": "Surrogacy expenses are not covered.",
                    "confidence": 0.95,
                },
                "ambulance_charges": {
                    "status": "covered",
                    "limit_amount": 2500,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Per hospitalization episode"],
                    "source_pages": [7],
                    "evidence": "Road ambulance expenses covered up to Rs. 2,500",
                    "confidence": 0.95,
                },
                "air_ambulance": {
                    "status": "covered",
                    "limit_amount": 100000,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Per policy year"],
                    "source_pages": [7],
                    "evidence": "Emergency air ambulance covered up to Rs. 1,00,000",
                    "confidence": 0.95,
                },
            }

        elif "extract corporate buffer" in p or "group: buffer_waiver" in p or '"corporate_buffer_amount"' in p:
            return {
                "corporate_buffer_amount": {
                    "status": "covered",
                    "limit_amount": 2500000,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": "Rs. 25,00,000",
                    "conditions": ["Critical illness cases", "HR approval required"],
                    "source_pages": [8],
                    "evidence": "A Corporate Floater Buffer of Rs. 25,00,000 is available for critical illness cases.",
                    "confidence": 0.95,
                },
                "corporate_buffer_eligibility": "Employees and dependents after exhaustion of base sum insured, with approval of designated HR authority",
                "disease_wise_capping": [
                    {"disease": "Cataract surgery", "limit_amount": 40000, "limit_text": "Rs. 40,000 per eye"},
                    {"disease": "Joint replacement surgery", "limit_amount": 150000, "limit_text": "Rs. 1,50,000 per joint"},
                    {"disease": "Hernia surgery", "limit_amount": 50000, "limit_text": "Rs. 50,000"},
                ],
                "waiver_conditions": [
                    "Waiver of 30-day initial waiting period",
                    "Waiver of first four years waiting period for pre-existing diseases",
                    "Waiver of maternity waiting period",
                ],
                "source_pages": [8],
                "confidence": 0.95,
            }

        return {}
