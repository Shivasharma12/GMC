"""
gmc_extractor/prompts/groups.py
Per-group extraction prompts with schema descriptions and GENERIC invented few-shot examples.
None of the examples are from real sample PDFs.
"""
from __future__ import annotations

import json

# ── FeatureValue JSON schema description (inline) ─────────────────────────────
_FV_SCHEMA = """{
  "status": "covered|not_covered|waived_off|applied|limited|not_mentioned",
  "limit_amount": <int in INR or null>,
  "limit_percent_of_si": <float 0-100 or null>,
  "limit_days": <int or null>,
  "limit_text": <string with original wording if not expressible numerically, or null>,
  "conditions": [<list of condition strings>],
  "source_pages": [<list of 1-indexed page numbers>],
  "evidence": "<short verbatim quote max 300 chars or null>",
  "confidence": <float 0.0-1.0>
}"""


# ── Group prompt templates ─────────────────────────────────────────────────────

GROUP_PROMPTS: dict[str, str] = {}


# 1. identity
GROUP_PROMPTS["identity"] = f"""
TASK: Extract the insurer name and TPA (Third Party Administrator) name.

The insurer is the company that issued/underwrites the policy. It may appear:
- On the cover page or header
- In the policy schedule or certificate
- In page footers
- As "ABC General Insurance Co. Ltd." or similar

The TPA manages claims. It may appear as:
- "Claims administered by XYZ TPA Services"
- "Third Party Administrator: XYZ"
- "TPA: XYZ Health Services"

Return JSON with this exact structure:
{{
  "insurer_name": "<string or null>",
  "tpa_name": "<string or null>",
  "source_pages": [<list of page numbers>],
  "confidence": <float 0.0-1.0>
}}

EXAMPLE (invented, not from any real document):
Input text: "[PAGE 1] GROUP MEDICLAIM POLICY\\nIssued by: Horizon General Insurance Limited\\nClaims administered by: MediAssist Healthcare Services Ltd.\\nPolicy No: GRP/2024/001"
Output:
{{"insurer_name": "Horizon General Insurance Limited", "tpa_name": "MediAssist Healthcare Services Ltd.", "source_pages": [1], "confidence": 0.98}}

---
DOCUMENT TEXT:
"""


# 2. policy_details
GROUP_PROMPTS["policy_details"] = f"""
TASK: Extract policy dates, tenure, premium, family structure, and sum-insured tiers.

FIELDS TO EXTRACT:
- policy_number: Policy/master policy number
- previous_inception_date: Previous year inception or renewal date (ISO yyyy-mm-dd)
- policy_start_date: Current policy start/commencement date (ISO yyyy-mm-dd)
- policy_end_date: Current policy expiry date (ISO yyyy-mm-dd)
- tenure_months: Duration in months (compute from dates if explicitly stated)
- premium_excluding_gst: Net premium in INR (int)
- premium_including_gst: Gross premium in INR (int)
- family_structure: {{employee, spouse, children, parents, parents_in_law}} (bool each), conditions: list
- sum_insured_tiers: list of {{amount: int, grade_or_category: str or null}}

NOTES:
- If only one premium figure is given, put it in premium_excluding_gst and leave the other null.
- Sum insured tiers must be in ascending order.
- Dates must be ISO yyyy-mm-dd format.

Return JSON:
{{
  "policy_number": null,
  "previous_inception_date": null,
  "policy_start_date": null,
  "policy_end_date": null,
  "tenure_months": null,
  "premium_excluding_gst": null,
  "premium_including_gst": null,
  "family_structure": {{"employee": false, "spouse": false, "children": false, "parents": false, "parents_in_law": false, "conditions": []}},
  "sum_insured_tiers": [],
  "source_pages": [],
  "confidence": 0.0,
  "conditions": []
}}

EXAMPLE (invented):
Input: "[PAGE 3] Policy Period: 01-April-2024 to 31-March-2025 (12 months)\\nPremium (excl. GST): Rs. 18,45,000\\nPremium (incl. GST): Rs. 21,77,100\\nFamily: Employee + Spouse + 2 Children (up to age 25)\\nSum Insured Tiers: Grade A: Rs. 5,00,000; Grade B: Rs. 3,00,000"
Output:
{{
  "policy_number": null,
  "previous_inception_date": null,
  "policy_start_date": "2024-04-01",
  "policy_end_date": "2025-03-31",
  "tenure_months": 12,
  "premium_excluding_gst": 1845000,
  "premium_including_gst": 2177100,
  "family_structure": {{"employee": true, "spouse": true, "children": true, "parents": false, "parents_in_law": false, "conditions": ["Children covered up to age 25", "Maximum 2 children"]}},
  "sum_insured_tiers": [{{"amount": 300000, "grade_or_category": "Grade B"}}, {{"amount": 500000, "grade_or_category": "Grade A"}}],
  "source_pages": [3],
  "confidence": 0.93,
  "conditions": []
}}

---
DOCUMENT TEXT:
"""


# 3. demographics
GROUP_PROMPTS["demographics"] = """
TASK: Extract the number of insured members (census data).

FIELDS:
- num_employees: Number of employee/principal members
- num_spouses: Number of spouses covered
- num_children: Number of children covered
- num_parents: Number of parents + parents-in-law covered (combined)
- total_lives_stated: Total lives as explicitly stated in the document
- source_pages, confidence, conditions

IMPORTANT:
- If a total is stated, copy it to total_lives_stated. Do NOT compute it yourself.
- If individual counts allow a sum, that goes in total_lives_computed (computed by the system, not you).
- If counts appear in a table, read each cell carefully.

Return JSON:
{
  "num_employees": null,
  "num_spouses": null,
  "num_children": null,
  "num_parents": null,
  "total_lives_stated": null,
  "source_pages": [],
  "confidence": 0.0,
  "conditions": []
}

EXAMPLE (invented):
Input: "[PAGE 7] MEMBER CENSUS\\n| Category | Count |\\n|---|---|\\n| Employees | 450 |\\n| Spouses | 380 |\\n| Children | 620 |\\n| Parents | 210 |\\n| Total Lives | 1660 |"
Output:
{"num_employees": 450, "num_spouses": 380, "num_children": 620, "num_parents": 210, "total_lives_stated": 1660, "source_pages": [7], "confidence": 0.97, "conditions": []}

---
DOCUMENT TEXT:
"""


# 4. room_hospitalization
GROUP_PROMPTS["room_hospitalization"] = f"""
TASK: Extract room rent limits, ICU charges, pre- and post-hospitalisation days.

For EACH field, return a FeatureValue object:
{_FV_SCHEMA}

KEY NOTES:
- Room rent may be expressed as: "% of SI per day", "₹ X per day", "single private AC room", or "as per actuals".
- ICU charges are often a higher % of SI or a fixed rupee limit.
- Pre-hospitalisation: days before admission (e.g., 30 days, 60 days).
- Post-hospitalisation: days after discharge (e.g., 60 days, 90 days).
- "Proportionate deduction" = if a higher room is taken, all charges are reduced proportionately — add this to conditions.

Return JSON:
{{
  "room_rent": <FeatureValue>,
  "icu_charges": <FeatureValue>,
  "pre_hospitalization_days": <FeatureValue>,
  "post_hospitalization_days": <FeatureValue>
}}

EXAMPLE (invented):
Input: "[PAGE 12] Room Rent: 1% of Sum Insured per day (single private AC room). ICU: 2% of Sum Insured per day. Pre-hospitalisation: 30 days. Post-hospitalisation: 60 days."
Output:
{{
  "room_rent": {{"status": "limited", "limit_amount": null, "limit_percent_of_si": 1.0, "limit_days": null, "limit_text": "1% of SI per day", "conditions": ["Single private AC room", "Proportionate deduction applies if higher category room is taken"], "source_pages": [12], "evidence": "Room Rent: 1% of Sum Insured per day (single private AC room)", "confidence": 0.95}},
  "icu_charges": {{"status": "limited", "limit_amount": null, "limit_percent_of_si": 2.0, "limit_days": null, "limit_text": "2% of SI per day", "conditions": [], "source_pages": [12], "evidence": "ICU: 2% of Sum Insured per day", "confidence": 0.95}},
  "pre_hospitalization_days": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": 30, "limit_text": null, "conditions": [], "source_pages": [12], "evidence": "Pre-hospitalisation: 30 days", "confidence": 0.98}},
  "post_hospitalization_days": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": 60, "limit_text": null, "conditions": [], "source_pages": [12], "evidence": "Post-hospitalisation: 60 days", "confidence": 0.98}}
}}

---
DOCUMENT TEXT:
"""


# 5. maternity
GROUP_PROMPTS["maternity"] = f"""
TASK: Extract maternity benefits.

For EACH field, return a FeatureValue object:
{_FV_SCHEMA}

FIELDS:
- nine_month_waiting_period: Is the 9-month maternity waiting period waived_off or applied?
- baby_day_one_cover: Is the newborn covered from day 1? (status + conditions)
- vaccination_cover: Baby vaccination benefit (status + limit_amount)
- normal_delivery_metro: Limit for normal delivery in metro cities
- normal_delivery_non_metro: Limit for normal delivery in non-metro cities
- c_section_metro: Limit for C-section in metro cities
- c_section_non_metro: Limit for C-section in non-metro cities

METRO vs NON-METRO: These must go in the correct named fields. If only one limit is given for all locations, put it in both metro and non-metro fields with a condition "Same limit for metro and non-metro".
NUMBER OF CHILDREN: If a limit is mentioned (e.g., "up to 2 deliveries"), add it to conditions.

Return JSON with exactly these 7 keys.

EXAMPLE (invented):
Input: "[PAGE 18] Maternity Benefit: Covered. 9-month waiting waived for all members. Normal delivery: Rs. 50,000 (metro) / Rs. 35,000 (non-metro). Caesarean: Rs. 75,000 (metro) / Rs. 55,000 (non-metro). New born baby covered from day 1. Vaccination covered up to Rs. 5,000."
Output:
{{
  "nine_month_waiting_period": {{"status": "waived_off", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": null, "conditions": ["9-month waiting waived for all members"], "source_pages": [18], "evidence": "9-month waiting waived for all members", "confidence": 0.96}},
  "baby_day_one_cover": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": "covered from day 1", "conditions": [], "source_pages": [18], "evidence": "New born baby covered from day 1", "confidence": 0.97}},
  "vaccination_cover": {{"status": "limited", "limit_amount": 5000, "limit_percent_of_si": null, "limit_days": null, "limit_text": null, "conditions": [], "source_pages": [18], "evidence": "Vaccination covered up to Rs. 5,000", "confidence": 0.95}},
  "normal_delivery_metro": {{"status": "limited", "limit_amount": 50000, "limit_percent_of_si": null, "limit_days": null, "limit_text": null, "conditions": [], "source_pages": [18], "evidence": "Normal delivery: Rs. 50,000 (metro)", "confidence": 0.97}},
  "normal_delivery_non_metro": {{"status": "limited", "limit_amount": 35000, "limit_percent_of_si": null, "limit_days": null, "limit_text": null, "conditions": [], "source_pages": [18], "evidence": "Normal delivery: Rs. 35,000 (non-metro)", "confidence": 0.97}},
  "c_section_metro": {{"status": "limited", "limit_amount": 75000, "limit_percent_of_si": null, "limit_days": null, "limit_text": null, "conditions": [], "source_pages": [18], "evidence": "Caesarean: Rs. 75,000 (metro)", "confidence": 0.96}},
  "c_section_non_metro": {{"status": "limited", "limit_amount": 55000, "limit_percent_of_si": null, "limit_days": null, "limit_text": null, "conditions": [], "source_pages": [18], "evidence": "Caesarean: Rs. 55,000 (non-metro)", "confidence": 0.96}}
}}

---
DOCUMENT TEXT:
"""


# 6. waiting_periods
GROUP_PROMPTS["waiting_periods"] = f"""
TASK: Extract all waiting period clauses from the policy.

For EACH field, return a FeatureValue object:
{_FV_SCHEMA}

FIELDS:
- thirty_day_waiting: 30-day initial waiting period (applied / waived_off)
- first_year_waiting: 1st-year specific disease waiting period (applied / waived_off / not_covered)
- second_year_waiting: 2nd-year specific disease waiting period
- ped_waiting: Pre-existing disease (PED) waiting period

For waiting_period fields:
- status = "waived_off" if the waiting period is removed/not applicable
- status = "applied" if the waiting period applies as stated
- status = "not_covered" if the disease category is excluded entirely
- limit_days = number of days of the waiting period (e.g., 30, 365, 730)
- conditions = any conditions, disease lists, or exceptions

EXAMPLE (invented):
Input: "[PAGE 22] Waiting Periods: 30-day initial waiting period: WAIVED for all members. 1st Year: Applicable (listed diseases). 2nd year exclusion: Applicable. Pre-existing diseases: Covered from day 1 (PED waiting period waived)."
Output:
{{
  "thirty_day_waiting": {{"status": "waived_off", "limit_amount": null, "limit_percent_of_si": null, "limit_days": 30, "limit_text": null, "conditions": ["Waived for all members"], "source_pages": [22], "evidence": "30-day initial waiting period: WAIVED for all members", "confidence": 0.97}},
  "first_year_waiting": {{"status": "applied", "limit_amount": null, "limit_percent_of_si": null, "limit_days": 365, "limit_text": null, "conditions": ["Applies to listed diseases per policy schedule"], "source_pages": [22], "evidence": "1st Year: Applicable (listed diseases)", "confidence": 0.88}},
  "second_year_waiting": {{"status": "applied", "limit_amount": null, "limit_percent_of_si": null, "limit_days": 730, "limit_text": null, "conditions": [], "source_pages": [22], "evidence": "2nd year exclusion: Applicable", "confidence": 0.87}},
  "ped_waiting": {{"status": "waived_off", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": null, "conditions": ["PED covered from day 1"], "source_pages": [22], "evidence": "Pre-existing diseases: Covered from day 1 (PED waiting period waived)", "confidence": 0.96}}
}}

---
DOCUMENT TEXT:
"""


# 7. other_benefits_a
GROUP_PROMPTS["other_benefits_a"] = f"""
TASK: Extract day care, OPD, teleconsultation, pharmacy discount, domiciliary hospitalisation, annual health check-up, and modern treatment benefits.

For EACH field, return a FeatureValue object:
{_FV_SCHEMA}

FIELDS:
- day_care: Day care procedures / treatments (limit or "all IRDA-listed procedures")
- opd: Out-patient department benefit (limit_amount per year or per visit)
- teleconsultation: Tele/e-consultation benefit
- pharmacy_discount: Medicine / pharmacy discount (e.g., "15% discount")
- domiciliary_hospitalization: Treatment at home benefit
- annual_health_checkup: Annual preventive health check benefit
- modern_treatment: Advanced/robotic/laser/gene therapy treatments

EXAMPLE (invented):
Input: "[PAGE 28] Day Care: All IRDA-approved day care procedures covered. OPD: Rs. 3,000 per annum. Teleconsultation: Unlimited consultations via app. Pharmacy: 10% discount at network pharmacies. Domiciliary: Up to 10% of SI. Annual Health Check: Rs. 2,500 per employee per year. Modern Treatment: Covered up to SI."
Output:
{{
  "day_care": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": "All IRDA-approved day care procedures", "conditions": [], "source_pages": [28], "evidence": "All IRDA-approved day care procedures covered", "confidence": 0.96}},
  "opd": {{"status": "limited", "limit_amount": 3000, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Rs. 3,000 per annum", "conditions": [], "source_pages": [28], "evidence": "OPD: Rs. 3,000 per annum", "confidence": 0.97}},
  "teleconsultation": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Unlimited consultations via app", "conditions": [], "source_pages": [28], "evidence": "Teleconsultation: Unlimited consultations via app", "confidence": 0.95}},
  "pharmacy_discount": {{"status": "limited", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": "10% discount at network pharmacies", "conditions": ["Network pharmacies only"], "source_pages": [28], "evidence": "Pharmacy: 10% discount at network pharmacies", "confidence": 0.94}},
  "domiciliary_hospitalization": {{"status": "limited", "limit_amount": null, "limit_percent_of_si": 10.0, "limit_days": null, "limit_text": "Up to 10% of SI", "conditions": [], "source_pages": [28], "evidence": "Domiciliary: Up to 10% of SI", "confidence": 0.93}},
  "annual_health_checkup": {{"status": "limited", "limit_amount": 2500, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Rs. 2,500 per employee per year", "conditions": ["Per employee, per year"], "source_pages": [28], "evidence": "Annual Health Check: Rs. 2,500 per employee per year", "confidence": 0.97}},
  "modern_treatment": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Covered up to SI", "conditions": [], "source_pages": [28], "evidence": "Modern Treatment: Covered up to SI", "confidence": 0.94}}
}}

---
DOCUMENT TEXT:
"""


# 8. other_benefits_b
GROUP_PROMPTS["other_benefits_b"] = f"""
TASK: Extract bariatric surgery, psychiatric/mental health, AYUSH, LGBTQ+, live-in partner, and organ donor benefit details.

For EACH field, return a FeatureValue object:
{_FV_SCHEMA}

FIELDS:
- bariatric: Bariatric / obesity surgery benefit
- psychiatric: Psychiatric / mental health treatment
- ayush: AYUSH treatments (Ayurveda, Yoga, Unani, Siddha, Homeopathy)
- lgbtq: LGBTQ+ partner cover
- live_in_partner: Live-in / domestic partner cover
- organ_donor_expenses: Organ donor hospitalisation expenses

EXAMPLE (invented):
Input: "[PAGE 33] Bariatric Surgery: Covered up to Rs. 2,00,000 (BMI ≥ 40 or ≥ 35 with comorbidities). Psychiatric: Covered as per IRDAI mental health guidelines, up to SI. AYUSH: Rs. 15,000 per annum. LGBTQ+ and live-in partners: Covered same as spouse. Organ Donor: Donor hospitalisation expenses covered up to SI."
Output:
{{
  "bariatric": {{"status": "limited", "limit_amount": 200000, "limit_percent_of_si": null, "limit_days": null, "limit_text": null, "conditions": ["BMI ≥ 40 or ≥ 35 with comorbidities"], "source_pages": [33], "evidence": "Bariatric Surgery: Covered up to Rs. 2,00,000 (BMI ≥ 40 or ≥ 35 with comorbidities)", "confidence": 0.96}},
  "psychiatric": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Up to SI, as per IRDAI mental health guidelines", "conditions": ["As per IRDAI mental health guidelines"], "source_pages": [33], "evidence": "Psychiatric: Covered as per IRDAI mental health guidelines, up to SI", "confidence": 0.95}},
  "ayush": {{"status": "limited", "limit_amount": 15000, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Rs. 15,000 per annum", "conditions": [], "source_pages": [33], "evidence": "AYUSH: Rs. 15,000 per annum", "confidence": 0.97}},
  "lgbtq": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Covered same as spouse", "conditions": [], "source_pages": [33], "evidence": "LGBTQ+ and live-in partners: Covered same as spouse", "confidence": 0.94}},
  "live_in_partner": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Covered same as spouse", "conditions": [], "source_pages": [33], "evidence": "LGBTQ+ and live-in partners: Covered same as spouse", "confidence": 0.93}},
  "organ_donor_expenses": {{"status": "covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Up to SI", "conditions": ["Donor hospitalisation expenses only"], "source_pages": [33], "evidence": "Organ Donor: Donor hospitalisation expenses covered up to SI", "confidence": 0.95}}
}}

---
DOCUMENT TEXT:
"""


# 9. infertility_ambulance
GROUP_PROMPTS["infertility_ambulance"] = f"""
TASK: Extract infertility treatment, surrogacy, road ambulance, and air ambulance benefit details.

For EACH field, return a FeatureValue object:
{_FV_SCHEMA}

FIELDS:
- infertility_treatment: IVF, IUI, ICSI and other infertility/ART treatments
- surrogacy: Surrogacy benefit
- ambulance_charges: Road/emergency ambulance charges
- air_ambulance: Air ambulance / aero ambulance / helicopter evacuation

EXAMPLE (invented):
Input: "[PAGE 38] Infertility: IVF/IUI/ICSI covered up to Rs. 1,00,000 per policy year (maximum 2 attempts). Surrogacy: Not covered. Ambulance: Rs. 2,000 per hospitalisation. Air Ambulance: Rs. 5,00,000 per policy year."
Output:
{{
  "infertility_treatment": {{"status": "limited", "limit_amount": 100000, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Rs. 1,00,000 per policy year", "conditions": ["Maximum 2 attempts per policy year", "Covers IVF/IUI/ICSI"], "source_pages": [38], "evidence": "Infertility: IVF/IUI/ICSI covered up to Rs. 1,00,000 per policy year (maximum 2 attempts)", "confidence": 0.96}},
  "surrogacy": {{"status": "not_covered", "limit_amount": null, "limit_percent_of_si": null, "limit_days": null, "limit_text": null, "conditions": [], "source_pages": [38], "evidence": "Surrogacy: Not covered", "confidence": 0.98}},
  "ambulance_charges": {{"status": "limited", "limit_amount": 2000, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Rs. 2,000 per hospitalisation", "conditions": [], "source_pages": [38], "evidence": "Ambulance: Rs. 2,000 per hospitalisation", "confidence": 0.97}},
  "air_ambulance": {{"status": "limited", "limit_amount": 500000, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Rs. 5,00,000 per policy year", "conditions": [], "source_pages": [38], "evidence": "Air Ambulance: Rs. 5,00,000 per policy year", "confidence": 0.96}}
}}

---
DOCUMENT TEXT:
"""


# 10. buffer_waiver
GROUP_PROMPTS["buffer_waiver"] = f"""
TASK: Extract corporate buffer limit, disease-wise capping, and applicable waiver conditions.

FIELDS:
- corporate_buffer_amount: A FeatureValue for the total corporate buffer/top-up pool amount.
- corporate_buffer_eligibility: A string describing who can access the buffer and under what conditions.
- disease_wise_capping: A list of objects, each with {{disease: str, limit_amount: int or null, limit_text: str or null}}.
- waiver_conditions: A list of strings describing conditions under which waivers apply.
- source_pages: list of page numbers
- confidence: float

FeatureValue schema:
{_FV_SCHEMA}

EXAMPLE (invented):
Input: "[PAGE 45] Corporate Buffer: Rs. 10,00,000 available for all employees collectively once individual SI exhausted. Disease-wise capping: Cataract: Rs. 30,000 per eye; Hernia: Rs. 60,000; Knee Replacement: Rs. 1,50,000. Waiver: Co-pay waived for employees above 55 years. Waiting period waived for pre-existing conditions."
Output:
{{
  "corporate_buffer_amount": {{"status": "covered", "limit_amount": 1000000, "limit_percent_of_si": null, "limit_days": null, "limit_text": "Rs. 10,00,000 for all employees collectively", "conditions": ["Available after individual SI exhausted"], "source_pages": [45], "evidence": "Corporate Buffer: Rs. 10,00,000 available for all employees collectively once individual SI exhausted", "confidence": 0.95}},
  "corporate_buffer_eligibility": "All employees; accessible after individual sum insured is exhausted",
  "disease_wise_capping": [
    {{"disease": "Cataract", "limit_amount": 30000, "limit_text": "Rs. 30,000 per eye"}},
    {{"disease": "Hernia", "limit_amount": 60000, "limit_text": null}},
    {{"disease": "Knee Replacement", "limit_amount": 150000, "limit_text": null}}
  ],
  "waiver_conditions": ["Co-pay waived for employees above 55 years", "Waiting period waived for pre-existing conditions"],
  "source_pages": [45],
  "confidence": 0.94
}}

---
DOCUMENT TEXT:
"""


def build_group_prompt(group_key: str, pages_text: str) -> str:
    """
    Build the full user-facing prompt for a given group.

    Args:
        group_key: One of the 10 group keys (e.g., 'maternity').
        pages_text: The concatenated [PAGE n] text from retrieved pages.

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    template = GROUP_PROMPTS.get(group_key)
    if template is None:
        raise ValueError(f"Unknown group key: '{group_key}'")
    return template + pages_text
