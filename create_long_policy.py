"""
create_long_policy.py
Creates a 52-page synthetic GMC policy PDF: tests/fixtures/long_policy_50p.pdf
Uses PyMuPDF (fitz). All data is synthetic.
Includes:
- Schedule with Graded SI (1 Lakh, 2 Lakhs, 3 Lakhs, 5 Lakhs)
- Terminology: "Hospitalisation", "Lacs", "MediAssist TPA Services Ltd."
- Endorsement page (page 50) overriding base room rent
"""
import fitz
from pathlib import Path

OUT = Path(__file__).parent / "tests" / "fixtures" / "long_policy_50p.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

def build_long_pdf():
    doc = fitz.open()

    # Page 1: Policy Schedule
    p1_text = """\
COMPREHENSIVE GROUP HEALTH INSURANCE POLICY
POLICY SCHEDULE & CERTIFICATE
===============================================
Issued by: National Assurance Company Limited
Registered Office: 12, Parliament Street, New Delhi - 110001
IRDAI Reg. No.: 102 | CIN: U10200DL2000PLC098765
On behalf of: National Assurance Company Limited
Authorized Signatory: John Doe, Vice President (Underwriting)

Policy Number: NAC/GMC/2024/789012
Period of Insurance: From 00:00 hrs 01-Jul-2024 to Midnight 30-Jun-2025
Tenure: 12 months

Name of Policyholder: Alpha Global Enterprises India Pvt. Ltd.
Address: Tower B, Cyber City, Phase 3, Gurugram, Haryana - 122002

Sum Insured Structure (Graded Sum Insured):
  Grade 1 (Executive): Rs. 5,00,000 (5 Lacs)
  Grade 2 (Senior Manager): Rs. 3,00,000 (3 Lacs)
  Grade 3 (Manager): Rs. 2,00,000 (2 Lacs)
  Grade 4 (Staff): Rs. 1,00,000 (1 Lac)
  Total Sum Insured: Rs. 25,00,00,000 (Twenty Five Crores Only)

Member Demographics:
  Total Employees: 500
  Total Dependents: 750
  Total Insured Lives: 1250

Third Party Administrator (TPA):
  MediAssist TPA Services Ltd.
  IRDAI License No.: 003

Premium Details:
  Base Premium: Rs. 45,00,000
  Goods and Services Tax (GST 18%): Rs. 8,10,000
  Total Premium: Rs. 53,10,000
"""
    p = doc.new_page(width=595, height=842)
    p.insert_text((50, 60), p1_text, fontsize=9)

    # Page 2: Family Structure & Base Limits
    p2_text = """\
SECTION 1: BENEFIT SPECIFICATIONS
===================================
1.1 Definition of Family:
    Self + Spouse + up to 2 Dependent Children (1+3 floater).
    Dependent parents are not covered under this base policy.

1.2 Room Rent & Intensive Care Unit (ICU):
    Normal Hospitalisation Room Rent: 1% of Sum Insured per day.
    ICU / ICCU Hospitalisation Charges: 2% of Sum Insured per day.
    Pre-Hospitalisation Medical Expenses: 30 days prior to hospitalisation.
    Post-Hospitalisation Medical Expenses: 60 days following discharge.

1.3 Ambulance Cover:
    Road ambulance expenses covered up to Rs. 2,500 per hospitalisation episode.
    Air ambulance covered up to Rs. 1,00,000 per policy year.
"""
    p = doc.new_page(width=595, height=842)
    p.insert_text((50, 60), p2_text, fontsize=9)

    # Page 3: Maternity & Day Care
    p3_text = """\
SECTION 2: MATERNITY & SPECIAL COVERS
======================================
2.1 Maternity Hospitalisation:
    Normal Delivery: Rs. 50,000
    Caesarean Section (LSCS): Rs. 75,000
    Note: No metro/non-metro distinction stated in policy; single limit applies.
    Nine month waiting period in respect of maternity hospitalisation is waived off.
    Newborn baby cover from Day One of birth included.

2.2 Day Care Procedures:
    All day care treatments requiring less than 24 hours hospitalisation are covered.
    Modern Treatments / Advanced Medical Procedures covered up to 50% of Sum Insured.
"""
    p = doc.new_page(width=595, height=842)
    p.insert_text((50, 60), p3_text, fontsize=9)

    # Pages 4 to 49: Terms, General Exclusions, Policy Clauses (simulate long policy wording)
    for page_idx in range(4, 50):
        filler_text = f"""\
STANDARD POLICY TERMS AND CONDITIONS - CLAUSE {page_idx}
============================================================
Hospitalisation Defined:
Hospitalisation shall mean admission in a hospital for a minimum period of 24 consecutive
in-patient care hours except for day care procedures specified in Schedule C.

Clause {page_idx}.1:
Medical practitioner qualifications, reasonable and customary charges, network hospital
agreements, and cashless claim processing procedures. All claims must be submitted to
MediAssist TPA Services Ltd. within 30 days of discharge from hospital.

Clause {page_idx}.2:
Exclusions applicable to hospitalisation expenses incurred outside the territorial limits
of the Republic of India. Investigations and diagnostic tests without active active treatment
remain non-payable.

Clause {page_idx}.3:
Subrogation and contribution conditions applicable in accordance with IRDAI guidelines.
"""
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 60), filler_text, fontsize=9)

    # Page 50: Corporate Buffer & Waivers
    p50_text = """\
SECTION 18: CORPORATE FLOATER BUFFER & WAIVER CONDITIONS
=========================================================
18.1 Corporate Floater Buffer:
A Corporate Floater Buffer of Rs. 25,00,000 is available for critical illness hospitalisation
cases on recommendation of the corporate Human Resources department.
Eligible illnesses: Cancer, Stroke, Open Heart CABG, Organ Transplant, Kidney Failure.

18.2 Waiver of Exclusions:
Initial 30-day waiting period is waived off from policy inception date.
First and second year exclusions for specific diseases are waived off.
Pre-existing disease (PED) waiting period is waived off from inception.

18.3 Co-Payment & Sub-Limits:
A co-payment of 10% shall apply for all cases except maternity, normal delivery, C-section,
and diseases covered under disease-wise sub-limit.
Cataract sub-limit: capped at Rs. 35,000 per eye.
"""
    p = doc.new_page(width=595, height=842)
    p.insert_text((50, 60), p50_text, fontsize=9)

    # Page 51: Endorsement No. 1 (Override Room Rent)
    p51_text = """\
POLICY ENDORSEMENT NO. 01 / 2024
ATTACHED TO AND FORMING PART OF POLICY NO.: NAC/GMC/2024/789012
==================================================================
Effective Date: 01-Jul-2024
Subject: Enhancement of Room Rent Limit

It is hereby noted and agreed that notwithstanding anything to the contrary contained
in the Policy Schedule or Terms & Conditions, the Room Rent limit is enhanced as under:

Original Room Rent Limit: 1% of Sum Insured per day.
Amended Room Rent Limit: Single Private AC Room or 1.5% of Sum Insured per day, whichever is higher.

All other terms, conditions, warranties and exclusions of the policy remain unaltered.

Issued by: National Assurance Company Limited
Authorized Signatory: Regional Underwriting Authority
"""
    p = doc.new_page(width=595, height=842)
    p.insert_text((50, 60), p51_text, fontsize=9)

    # Page 52: Grievance Redressal and Claims Servicing
    p52_text = """\
GRIEVANCE REDRESSAL MECHANISM
==============================
Claims Servicing Team: MediAssist TPA Services Ltd.
In-house Oversight: National Assurance Company Limited Claims Review Board
Registered Office: 12, Parliament Street, New Delhi - 110001
IRDAI Bima Bharosa Portal: bimaonline.irdai.gov.in
"""
    p = doc.new_page(width=595, height=842)
    p.insert_text((50, 60), p52_text, fontsize=9)

    doc.save(str(OUT))
    print(f"Created: {OUT} ({doc.page_count} pages)")
    doc.close()

if __name__ == "__main__":
    build_long_pdf()

