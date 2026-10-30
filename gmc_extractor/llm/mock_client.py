"""
gmc_extractor/llm/mock_client.py
Mock LLM client for offline testing and evaluation without an API key.
Returns schema-valid JSON responses using generic synthetic data.
No values from real sample policies are hardcoded here.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from gmc_extractor.llm.base import LLMClient

logger = logging.getLogger(__name__)


class MockLLMClient(LLMClient):
    """Mock LLM client returning realistic, generic responses for offline testing."""

    def __init__(self, model: str = "mock-model") -> None:
        self._model = model

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model

    def ask_json(self, system: str, prompt: str) -> dict[str, Any]:
        """Match group based on prompt task heading and return generic mock data."""
        p = prompt.lower()

        # Check by task or group identifier
        if "extract the insurer name and tpa" in p or "group: identity" in p or '"insurer_name"' in p:
            # Check if an insurer name appears in the prompt text
            insurer = "Generic Health Insurance Ltd."
            tpa = "Standard Healthcare TPA Pvt. Ltd."
            m_ins = re.search(r"(?:issued by|insurer)[:\s]+([A-Za-z0-9\s]+(?:Insurance|Assurance)[^,\n\.\r]*)", prompt, re.IGNORECASE)
            if m_ins:
                insurer = m_ins.group(1).strip()
            return {
                "insurer_name": insurer,
                "tpa_name": tpa,
                "source_pages": [1],
                "confidence": 0.95,
            }

        elif "extract policy-level details" in p or "group: policy_details" in p or '"policy_start_date"' in p:
            pol_num = "MOCK/GMC/2024/001"
            m_pol = re.search(r"policy\s*(?:no|number)[:\s]+([A-Za-z0-9\/\-_]+)", prompt, re.IGNORECASE)
            if m_pol:
                pol_num = m_pol.group(1).strip()
            return {
                "policy_number": pol_num,
                "previous_inception_date": "2023-04-01",
                "policy_start_date": "2024-04-01",
                "policy_end_date": "2025-03-31",
                "tenure_months": 12,
                "premium_excluding_gst": 1000000,
                "premium_including_gst": 1180000,
                "family_structure": {
                    "employee": True,
                    "spouse": True,
                    "children": True,
                    "parents": True,
                    "parents_in_law": False,
                    "conditions": ["1+3 Family Floater", "up to 2 dependent Children"],
                },
                "sum_insured_tiers": [
                    {"amount": 300000, "grade_or_category": "Grade B"},
                    {"amount": 500000, "grade_or_category": "Grade A"},
                ],
                "source_pages": [1],
                "confidence": 0.95,
                "conditions": [],
            }

        elif "extract the number of insured members" in p or "group: demographics" in p or '"num_employees"' in p:
            return {
                "num_employees": 100,
                "num_spouses": 80,
                "num_children": 120,
                "num_parents": 40,
                "total_lives_stated": 340,
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
                "limit_text": "1% of Sum Insured per day, max Rs. 5,000",
                "conditions": ["Single Private AC Room"],
                "source_pages": [1],
                "evidence": "Room rent limit is 1% of Sum Insured up to Rs 5,000 per day",
                "confidence": 0.95,
            }
            return {
                "room_rent": fv,
                "icu_charges": {
                    "status": "limited",
                    "limit_amount": 10000,
                    "limit_percent_of_si": 2.0,
                    "limit_days": None,
                    "limit_text": "2% of Sum Insured per day, max Rs. 10,000",
                    "conditions": [],
                    "source_pages": [1],
                    "evidence": "ICU charges covered up to 2% of Sum Insured per day, max Rs. 10,000",
                    "confidence": 0.95,
                },
                "pre_hospitalization_days": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": 30,
                    "limit_text": "30 days prior to admission",
                    "conditions": [],
                    "source_pages": [1],
                    "evidence": "Pre-hospitalization expenses covered for 30 days prior to admission",
                    "confidence": 0.95,
                },
                "post_hospitalization_days": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": 60,
                    "limit_text": "60 days from discharge",
                    "conditions": [],
                    "source_pages": [1],
                    "evidence": "Post-hospitalization expenses covered for 60 days from discharge",
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
                "source_pages": [1],
                "evidence": "Normal delivery limit: Rs. 50,000 in metro cities",
                "confidence": 0.95,
            }
            return {
                "nine_month_waiting_period": {
                    "status": "waived_off",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": "Waived off from Day 1",
                    "conditions": [],
                    "source_pages": [1],
                    "evidence": "Maternity waiting period of 9 months is waived off from Day 1",
                    "confidence": 0.95,
                },
                "baby_day_one_cover": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": "Covered from birth",
                    "conditions": [],
                    "source_pages": [1],
                    "evidence": "Baby Day One cover is included from birth",
                    "confidence": 0.95,
                },
                "vaccination_cover": {
                    "status": "covered",
                    "limit_amount": 5000,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["First year only"],
                    "source_pages": [1],
                    "evidence": "Newborn vaccination covered up to Rs. 5,000",
                    "confidence": 0.95,
                },
                "normal_delivery_metro": base_mat,
                "normal_delivery_non_metro": {
                    **base_mat,
                    "limit_amount": 40000,
                    "evidence": "Normal delivery limit: Rs. 40,000 in non-metro cities",
                },
                "c_section_metro": {
                    **base_mat,
                    "limit_amount": 75000,
                    "evidence": "C-Section delivery limit: Rs. 75,000 in metro cities",
                },
                "c_section_non_metro": {
                    **base_mat,
                    "limit_amount": 60000,
                    "evidence": "C-Section delivery limit: Rs. 60,000 in non-metro cities",
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
                "source_pages": [1],
                "evidence": "Initial waiting periods are waived off under this policy",
                "confidence": 0.95,
            }
            return {
                "thirty_day_waiting": wv,
                "first_year_waiting": {
                    **wv,
                    "evidence": "1st year waiting period for specified illnesses is waived off",
                },
                "second_year_waiting": {
                    **wv,
                    "evidence": "2nd year waiting period for specified illnesses is waived off",
                },
                "ped_waiting": {
                    **wv,
                    "evidence": "Pre-existing diseases waiting period is waived off from inception",
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
                "source_pages": [1],
                "evidence": "All day care procedures requiring less than 24 hours hospitalization are covered",
                "confidence": 0.95,
            }
            return {
                "day_care": fv,
                "opd": {
                    **fv,
                    "limit_amount": 10000,
                    "evidence": "OPD consultations covered up to Rs. 10,000 per family",
                },
                "teleconsultation": {
                    **fv,
                    "evidence": "Unlimited teleconsultations available via mobile app",
                },
                "pharmacy_discount": {
                    **fv,
                    "limit_percent_of_si": 10.0,
                    "evidence": "10% discount on medicines at network pharmacies",
                },
                "domiciliary_hospitalization": {
                    **fv,
                    "limit_percent_of_si": 20.0,
                    "conditions": ["When treatment exceeds 3 days"],
                    "evidence": "Domiciliary hospitalization covered up to 20% of Sum Insured",
                },
                "annual_health_checkup": {
                    **fv,
                    "conditions": ["Employee and spouse"],
                    "evidence": "Annual health checkup for employee and spouse",
                },
                "modern_treatment": {
                    **fv,
                    "evidence": "Modern treatments covered up to Sum Insured",
                },
            }

        elif "extract bariatric" in p or "group: other_benefits_b" in p or '"bariatric"' in p:
            fv = {
                "status": "covered",
                "limit_amount": 150000,
                "limit_percent_of_si": None,
                "limit_days": None,
                "limit_text": None,
                "conditions": ["BMI > 35"],
                "source_pages": [1],
                "evidence": "Bariatric surgery covered up to Rs. 1,50,000 when BMI > 35",
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
                    "source_pages": [1],
                    "evidence": "In-patient psychiatric treatment covered up to Sum Insured",
                    "confidence": 0.95,
                },
                "ayush": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": 100.0,
                    "limit_days": None,
                    "limit_text": "100% of Sum Insured",
                    "conditions": ["In registered hospitals"],
                    "source_pages": [1],
                    "evidence": "AYUSH treatment covered up to 100% of Sum Insured",
                    "confidence": 0.95,
                },
                "lgbtq": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Recognized under spouse definition"],
                    "source_pages": [1],
                    "evidence": "Same-sex partners recognized under spouse definition",
                    "confidence": 0.95,
                },
                "live_in_partner": {
                    "status": "covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Recognized under spouse definition"],
                    "source_pages": [1],
                    "evidence": "Live-in partners recognized under spouse definition",
                    "confidence": 0.95,
                },
                "organ_donor_expenses": {
                    "status": "covered",
                    "limit_amount": 500000,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": [],
                    "source_pages": [1],
                    "evidence": "Organ donor in-patient hospitalization covered up to Rs. 5,00,000",
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
                    "source_pages": [1],
                    "evidence": "Infertility treatment covered up to Rs. 1,00,000",
                    "confidence": 0.95,
                },
                "surrogacy": {
                    "status": "not_covered",
                    "limit_amount": None,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": "Not covered",
                    "conditions": [],
                    "source_pages": [1],
                    "evidence": "Surrogacy expenses are not covered",
                    "confidence": 0.95,
                },
                "ambulance_charges": {
                    "status": "covered",
                    "limit_amount": 2500,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Per episode"],
                    "source_pages": [1],
                    "evidence": "Road ambulance charges covered up to Rs. 2,500",
                    "confidence": 0.95,
                },
                "air_ambulance": {
                    "status": "covered",
                    "limit_amount": 100000,
                    "limit_percent_of_si": None,
                    "limit_days": None,
                    "limit_text": None,
                    "conditions": ["Per policy year"],
                    "source_pages": [1],
                    "evidence": "Air ambulance covered up to Rs. 1,00,000",
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
                    "source_pages": [1],
                    "evidence": "Corporate floater buffer of Rs. 25,00,000 is available",
                    "confidence": 0.95,
                },
                "corporate_buffer_eligibility": "Employees and dependents after exhaustion of base sum insured, with HR approval",
                "disease_wise_capping": [
                    {"disease": "Cataract surgery", "limit_amount": 40000, "limit_text": "Rs. 40,000 per eye", "conditions": ["Per eye"], "page": 1, "evidence": "Cataract surgery capped at Rs. 40,000 per eye"},
                    {"disease": "Joint replacement", "limit_amount": 150000, "limit_text": "Rs. 1,50,000 per joint", "conditions": ["Per joint"], "page": 1, "evidence": "Joint replacement surgery capped at Rs. 1,50,000 per joint"},
                    {"disease": "Hernia surgery", "limit_amount": 50000, "limit_text": "Rs. 50,000", "conditions": [], "page": 1, "evidence": "Hernia surgery capped at Rs. 50,000"},
                    {"disease": "Cancer of Specified Severity", "limit_amount": 500000, "limit_text": "Rs. 5,00,000", "conditions": ["Diagnosis confirmed by oncologist"], "page": 1, "evidence": "Cancer of Specified Severity covered under corporate floater up to Rs. 5,00,000"},
                    {"disease": "Myocardial Infarction (First Heart Attack)", "limit_amount": 500000, "limit_text": "Rs. 5,00,000", "conditions": [], "page": 1, "evidence": "Myocardial Infarction covered under corporate floater up to Rs. 5,00,000"},
                    {"disease": "Stroke Resulting in Permanent Symptoms", "limit_amount": 500000, "limit_text": "Rs. 5,00,000", "conditions": [], "page": 1, "evidence": "Stroke Resulting in Permanent Symptoms covered under corporate floater up to Rs. 5,00,000"},
                    {"disease": "Major Organ / Bone Marrow Transplant", "limit_amount": 500000, "limit_text": "Rs. 5,00,000", "conditions": [], "page": 1, "evidence": "Major Organ or Bone Marrow Transplant covered under corporate floater up to Rs. 5,00,000"},
                    {"disease": "Coronary Artery Bypass Graft", "limit_amount": 500000, "limit_text": "Rs. 5,00,000", "conditions": [], "page": 1, "evidence": "Coronary Artery Bypass Graft covered under corporate floater up to Rs. 5,00,000"},
                    {"disease": "Kidney Failure Requiring Regular Dialysis", "limit_amount": 500000, "limit_text": "Rs. 5,00,000", "conditions": [], "page": 1, "evidence": "Kidney Failure Requiring Regular Dialysis covered under corporate floater up to Rs. 5,00,000"},
                    {"disease": "Multiple Sclerosis with Persisting Symptoms", "limit_amount": 500000, "limit_text": "Rs. 5,00,000", "conditions": [], "page": 1, "evidence": "Multiple Sclerosis with Persisting Symptoms covered under corporate floater up to Rs. 5,00,000"},
                    {"disease": "Aorta Graft Surgery", "limit_amount": 500000, "limit_text": "Rs. 5,00,000", "conditions": [], "page": 1, "evidence": "Aorta Graft Surgery covered under corporate floater up to Rs. 5,00,000"},
                    {"disease": "End Stage Liver Disease", "limit_amount": 500000, "limit_text": "Rs. 5,00,000", "conditions": [], "page": 1, "evidence": "End Stage Liver Disease covered under corporate floater up to Rs. 5,00,000"},
                ],
                "waiver_conditions": [
                    {
                        "waiver_name": "30-Day Initial Waiting Period",
                        "clause": "30-day initial waiting period is waived from the date of inception",
                        "page": 1,
                        "evidence": "30-day initial waiting period is waived from the date of inception",
                    },
                    {
                        "waiver_name": "1st Year Specific Disease Waiting Period",
                        "clause": "First year waiting period for specified diseases is waived off",
                        "page": 1,
                        "evidence": "First year waiting period for specified diseases is waived off",
                    },
                    {
                        "waiver_name": "2nd Year Specific Disease Waiting Period",
                        "clause": "Second year waiting period for specific diseases is waived off",
                        "page": 1,
                        "evidence": "Second year waiting period for specific diseases is waived off",
                    },
                    {
                        "waiver_name": "Pre-Existing Disease (PED) Waiting Period",
                        "clause": "Pre-existing diseases waiting period is waived from inception for all insured members",
                        "page": 1,
                        "evidence": "Pre-existing diseases waiting period is waived from inception for all insured members",
                    },
                    {
                        "waiver_name": "Maternity 9-Month Waiting Period",
                        "clause": "Nine month maternity waiting period is waived off from the date of inception",
                        "page": 1,
                        "evidence": "Nine month maternity waiting period is waived off from the date of inception",
                    },
                ],
                "copay_sublimits": [
                    {
                        "item": "General Policy Co-Pay",
                        "type": "copay",
                        "percent": 10.0,
                        "amount": None,
                        "applies_to": "All cases under this policy",
                        "exceptions": "maternity, normal delivery, C-section, and disease-wise sub-limit cases",
                        "page": 1,
                        "evidence": "A co-payment of 10% shall apply for all cases except maternity, normal delivery, C-section, and diseases covered under disease-wise sub-limit",
                    }
                ],
                "source_pages": [1],
                "confidence": 0.95,
            }

        return {}
