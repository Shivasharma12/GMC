"""
create_ghi_policy.py
Creates a synthetic GMC policy PDF: samples/GHI_Policy.pdf
Uses only PyMuPDF (fitz) — already installed in venv.
All values are synthetic; no real insurer/policyholder data.
"""
import fitz  # PyMuPDF
from pathlib import Path

OUT = Path(__file__).parent / "samples" / "GHI_Policy.pdf"
OUT.parent.mkdir(exist_ok=True)

POLICY_TEXT = [
    # Page 1 — Policy Schedule / Certificate
    """\
GROUP HEALTH INSURANCE POLICY - POLICY SCHEDULE
=================================================
Issued by: Global Health Insurance Company Limited
Registered Office: 7th Floor, Health Tower, Sector 18, Gurugram, Haryana - 122001
IRDAI Registration No.: 145  |  CIN: U66010HR2005PLC038705
On behalf of: Global Health Insurance Company Limited
Authorized Signatory: [Digital Signature]

Policy Number     : GHI/GMC/2024/00542
Policy Start Date : 01-Apr-2024  (00:01 hrs)
Policy End Date   : 31-Mar-2025  (23:59 hrs)
Tenure            : 12 months

Policyholder Name         : Techsphere Solutions Pvt. Ltd.
Address                   : Plot No. 9, Electronic City Phase II, Bengaluru - 560100
Group Name                : Techsphere Employee Group

Details of Insured Members:
  Primary Insured Members (Employees) : 50
  Dependents                           : 66
  Total Lives                          : 116

Sum Insured Details:
  Sum Insured per member               : Rs. 2,00,000 (Two Lakhs Only)
  Total Sum Insured                    : Rs. 1,32,00,000 (One Crore Thirty-Two Lakhs Only)

Premium Details:
  Net Premium (excl. GST)              : Rs. 3,96,000
  GST @ 18%                            : Rs. 71,280
  Total Premium (incl. GST)            : Rs. 4,67,280

Third Party Administrator (TPA)       : Paramount Health Services & Insurance TPA Pvt. Ltd.
TPA IRDAI Registration No.            : TPA-001

For Claims & Assistance, please contact Paramount Health Services:
  Toll Free: 1800-103-7458  |  Email: claims@paramounttpa.com
  Cashless Helpdesk: Available 24x7
""",
    # Page 2 — Coverage Details
    """\
SECTION 1: COVERAGE DETAILS
============================
1.1 Family Structure / Definition of Family:
    Self + Spouse + 2 Dependent Children
    Note: Parents are NOT covered under this policy.

1.2 Sum Insured:
    All insured members are covered under a Graded Sum Insured structure.
    Each insured member is entitled to a Sum Insured of Rs. 2,00,000 per policy year
    on an Individual (Non-Floater) basis.

1.3 Room Rent:
    Room rent is limited to 1% of Sum Insured per day (i.e., Rs. 2,000 per day).
    Single private air-conditioned room applicable.

1.4 ICU Charges:
    ICU / ICCU charges are limited to 2% of Sum Insured per day (i.e., Rs. 4,000 per day).

1.5 Pre-Hospitalization:
    Pre-hospitalization expenses are covered for 30 days prior to date of admission.

1.6 Post-Hospitalization:
    Post-hospitalization expenses are covered for 60 days from date of discharge.

1.7 Ambulance Charges:
    Road ambulance charges are covered up to Rs. 2,000 per event of hospitalization.

SECTION 2: MATERNITY BENEFITS
==============================
2.1 Normal Delivery          : Covered up to Rs. 25,000 (No metro/non-metro distinction)
2.2 Caesarean Section (LSCS) : Covered up to Rs. 40,000 (No metro/non-metro distinction)
    Note: No metro/non-metro distinction stated in policy; single limit applies.
    Restricted to first 2 living children per insured female member.

2.3 Maternity Waiting Period:
    The 9-month waiting period applicable to maternity benefits is hereby waived off
    from the date of inception of this policy.

2.4 Baby Day One Cover:
    Newborn baby is covered from the first day of birth under the mother's Sum Insured.
""",
    # Page 3 — Waiting Periods and Co-Pay
    """\
SECTION 3: WAITING PERIODS
============================
3.1 Initial 30-Day Waiting Period:
    The standard 30-day initial waiting period is waived off for all insured members
    enrolled at the inception of this policy.

3.2 First Year Specific Disease Exclusion:
    The first year exclusion for specific diseases (e.g., hernia, cataract, sinusitis)
    is waived off from the date of inception.

3.3 Second Year Specific Disease Exclusion:
    The second year exclusion for specific diseases is also waived off from the date of inception.

3.4 Pre-Existing Disease (PED) Waiting Period:
    The waiting period applicable to pre-existing diseases is waived off for all
    existing insured members from the date of inception of this policy.

SECTION 4: CO-PAYMENT AND SUB-LIMITS
======================================
4.1 Co-Payment Clause:
    A co-payment of 10% shall apply for all cases except maternity, normal delivery,
    C-section, and diseases covered under disease-wise sub-limit.
    The insured member shall bear 10% of the admissible claim amount.

4.2 Sub-Limit for Specific Procedures / Devices:
    50% co-pay for Cochlear Implant and other hearing devices implanted during surgery.
    Knee / Hip joint prosthesis: sub-limited to Rs. 50,000 per joint replacement surgery.
    Cataract surgery: capped at Rs. 15,000 per eye.

4.3 Disease-Wise Capping (Refer Schedule B):
    Hernia surgery             : Rs. 30,000 per episode
    Tonsillectomy              : Rs. 20,000 per episode
    Hysterectomy               : Rs. 50,000 per episode
""",
    # Page 4 — Corporate Buffer / Floater
    """\
SECTION 5: CORPORATE BUFFER / FLOATER
=======================================
5.1 Buffer Amount:
    A Corporate Buffer / Floater of Rs. 5,00,000 (Five Lakhs) is available over and
    above the individual Sum Insured for employees who are diagnosed with any of the
    following critical illnesses during the policy period.

5.2 Eligibility:
    This corporate floater is available only to Primary Insured Members (Employees)
    after complete exhaustion of the individual Sum Insured, subject to HR approval.
    Dependents are NOT eligible for this corporate buffer.

5.3 Critical Illnesses Covered under Corporate Buffer:
    The following 9 critical illnesses are eligible for the Corporate Buffer:
    1. Cancer of Specified Severity
    2. Myocardial Infarction (First Heart Attack of Specified Severity)
    3. Stroke Resulting in Permanent Symptoms
    4. Major Organ / Bone Marrow Transplant
    5. Coronary Artery Bypass Graft (CABG)
    6. Kidney Failure Requiring Regular Dialysis
    7. Multiple Sclerosis with Persisting Symptoms
    8. Aorta Graft Surgery
    9. End Stage Liver Disease

5.4 How to Access the Buffer:
    Submit corporate buffer claim form + treating physician certification confirming
    critical illness diagnosis to HR department. HR department shall verify and approve.
""",
    # Page 5 — Exclusions and General Terms
    """\
SECTION 6: EXCLUSIONS (SELECTED)
==================================
6.1 Cosmetic or plastic surgery (unless necessitated by accident or burn).
6.2 Self-inflicted injuries or suicide attempts.
6.3 Infertility treatment and assisted reproduction (IVF/ICSI).
6.4 Surrogacy-related expenses.
6.5 Treatment outside India.
6.6 Experimental treatments not approved by appropriate medical authorities.

SECTION 7: GENERAL CONDITIONS
===============================
7.1 This policy is governed by the applicable provisions of the Insurance Act, 1938,
    and the IRDAI Regulations in force.
7.2 All disputes shall be subject to jurisdiction of courts at Gurugram, Haryana.
7.3 Renewal of this policy: Renewal of this policy is at the discretion of both parties.
    This document is treated as the previous year expiring policy for renewal purposes.
    Previous policy inception date: 01-Apr-2024 (same as current start date for base year).

Claims Servicing Team - Global Health Insurance Company Limited
  For grievances: grievance@globalhealthins.com
  IRDAI Grievance Cell: igms.irdai.gov.in | 155255
""",
]


def create_pdf():
    doc = fitz.open()
    font_size_title = 14
    font_size_body = 10

    for page_text in POLICY_TEXT:
        page = doc.new_page(width=595, height=842)  # A4
        lines = page_text.strip().split("\n")
        y = 50
        for line in lines:
            line_stripped = line.strip()
            # Simple heuristic: lines ending with === or starting with SECTION are headers
            if line_stripped.endswith("=") or (line_stripped.startswith("SECTION") and ":" in line_stripped):
                fs = font_size_title
            else:
                fs = font_size_body
            # Wrap long lines
            max_width = 480
            if len(line_stripped) > 90:
                words = line_stripped.split()
                current = ""
                for word in words:
                    if len(current + " " + word) > 90:
                        page.insert_text((50, y), current.strip(), fontsize=fs)
                        y += fs + 3
                        current = word
                    else:
                        current = (current + " " + word).strip()
                if current:
                    page.insert_text((50, y), current.strip(), fontsize=fs)
                    y += fs + 3
            else:
                page.insert_text((50, y), line_stripped, fontsize=fs)
                y += fs + 3
            if y > 800:
                break  # Safety: don't overflow page

    doc.save(str(OUT))
    print(f"Created: {OUT}  ({doc.page_count} pages)")
    doc.close()


if __name__ == "__main__":
    create_pdf()

