"""
Script to generate a realistic sample GMC policy PDF for testing.
"""
from pathlib import Path
import fitz  # PyMuPDF

def generate_sample_pdf(output_path: Path):
    doc = fitz.open()

    pages_data = [
        # Page 1: Schedule of Insurance / Identity / Policy Details
        (
            "POLICY SCHEDULE - GROUP MEDICAL COVER\n\n"
            "INSURER: Star Health and Allied Insurance Company Limited\n"
            "TPA: Medi Assist Insurance TPA Private Limited\n"
            "Policy Number: STAR/GMC/2024/09841\n"
            "Previous Policy Renewal Inception Date: 01/04/2023\n"
            "Policy Inception Date: 01/04/2024\n"
            "Policy Expiry Date: 31/03/2025\n"
            "Policy Tenure: 12 months\n\n"
            "PREMIUM DETAILS:\n"
            "Inception Net Premium (without GST): Rs. 12,50,000\n"
            "Total Inception Premium (with 18% GST): Rs. 14,75,000\n\n"
            "FAMILY DEFINITION & COMPOSITION:\n"
            "Covered Members: Employee, Spouse, up to 2 dependent Children, and dependent Parents / Parents-in-law (1+5 Family Floater).\n"
            "Employee covered: Yes. Spouse covered: Yes. Children covered: Yes. Parents: Yes.\n\n"
            "SUM INSURED TIERS:\n"
            "- Grade A (Executive): INR 5,00,000 floater per family\n"
            "- Grade B (Management): INR 3,00,000 floater per family\n"
        ),
        # Page 2: Demographics
        (
            "MEMBER CENSUS AND DEMOGRAPHICS SCHEDULE\n\n"
            "Category breakdown of covered lives as of inception:\n\n"
            "Insured Employees: 150\n"
            "Insured Spouses: 120\n"
            "Insured Children: 180\n"
            "Insured Parents / In-Laws: 50\n\n"
            "Total Lives Insured: 500\n\n"
            "Note: Census list as per Annexure B attached with employee employee code and DOB."
        ),
        # Page 3: Room Rent & Hospitalization
        (
            "SECTION I - HOSPITALIZATION EXPENSES & ROOM RENT\n\n"
            "1. ROOM RENT AND BOARDING:\n"
            "Room Rent is covered up to 1% of Sum Insured per day, subject to a maximum of Rs. 5,000 per day for Single Private AC Room.\n"
            "Proportionate deduction will apply if room category exceeds the eligible limit.\n\n"
            "2. INTENSIVE CARE UNIT (ICU) CHARGES:\n"
            "ICU charges are covered up to 2% of Sum Insured per day, subject to maximum Rs. 10,000 per day.\n\n"
            "3. PRE AND POST HOSPITALIZATION:\n"
            "Pre-hospitalization medical expenses: Covered for 30 days prior to the date of admission.\n"
            "Post-hospitalization medical expenses: Covered for 60 days from the date of discharge.\n"
        ),
        # Page 4: Maternity & Newborn
        (
            "SECTION II - MATERNITY AND NEWBORN BABY BENEFIT\n\n"
            "1. MATERNITY BENEFIT:\n"
            "Maternity waiting period of 9 months is waived off from Day 1 for all employees and spouses.\n"
            "Normal Delivery limit: Rs. 50,000 in Metro cities; Rs. 40,000 in Non-Metro cities.\n"
            "Caesarean (C-Section) delivery limit: Rs. 75,000 in Metro cities; Rs. 60,000 in Non-Metro cities.\n"
            "Condition: Benefit is restricted to the first 2 living children per family.\n\n"
            "2. BABY DAY ONE AND VACCINATION:\n"
            "Baby Day One cover is included from birth up to normal delivery limit.\n"
            "Newborn vaccination cover is covered up to Rs. 5,000 within the first year.\n"
        ),
        # Page 5: Waiting Periods
        (
            "SECTION III - WAITING PERIODS AND WAIVERS\n\n"
            "1. 30 DAYS INITIAL WAITING PERIOD:\n"
            "The standard 30-day initial waiting period is waived off under this Group policy.\n\n"
            "2. FIRST & SECOND YEAR SPECIFIC DISEASE WAITING PERIOD:\n"
            "Waiting period of 1st and 2nd year for specified illnesses / treatments is waived off.\n\n"
            "3. PRE-EXISTING DISEASES (PED):\n"
            "Pre-existing diseases waiting period is waived off from inception of cover.\n"
            "Status: All waiting periods are waived off from day one of policy period.\n"
        ),
        # Page 6: Day Care & Outpatient Benefits
        (
            "SECTION IV - OTHER BENEFITS & EXPENSES (PART A)\n\n"
            "1. DAY CARE PROCEDURES: All day care procedures requiring less than 24 hours hospitalization due to advanced technology are covered.\n"
            "2. OUT-PATIENT (OPD) COVER: OPD consultations and diagnostics are covered up to Rs. 10,000 per family per policy year.\n"
            "3. TELECONSULTATION: Unlimited free audio/video consultations available via dedicated insurer mobile application.\n"
            "4. PHARMACY DISCOUNT: Up to 10% discount on prescribed medicines across network partner pharmacies.\n"
            "5. DOMICILIARY HOSPITALIZATION: Covered up to 20% of Sum Insured when treatment exceeds 3 days.\n"
            "6. ANNUAL HEALTH CHECK-UP: Free annual preventive health check-up package for employee and spouse.\n"
            "7. MODERN TREATMENT METHODS: Advances such as robotic surgery, stem cell therapy covered up to Sum Insured.\n"
        ),
        # Page 7: Special Benefits & Infertility & Ambulance
        (
            "SECTION V - EXTENDED BENEFITS & AMBULANCE (PART B)\n\n"
            "1. BARIATRIC SURGERY: Covered up to Rs. 1,50,000 for morbid obesity when BMI is greater than 35.\n"
            "2. PSYCHIATRIC AND MENTAL HEALTH: In-patient psychiatric treatment covered up to Sum Insured.\n"
            "3. AYUSH TREATMENT: In-patient Ayurvedic, Yoga, Unani, Siddha and Homeopathy treatments covered up to 100% of Sum Insured in registered hospitals.\n"
            "4. LGBTQ+ & LIVE-IN PARTNERS: Same-sex partners and live-in partners recognized as dependents under spouse definition.\n"
            "5. ORGAN DONOR EXPENSES: In-patient hospitalization expenses of donor covered up to Rs. 5,00,000.\n"
            "6. INFERTILITY TREATMENT: Infertility investigation and procedures covered up to Rs. 1,00,000 per family.\n"
            "7. SURROGACY: Surrogacy expenses are not covered.\n"
            "8. AMBULANCE CHARGES: Road ambulance expenses covered up to Rs. 2,500 per hospitalization episode.\n"
            "9. AIR AMBULANCE: Emergency air ambulance covered up to Rs. 1,00,000 per policy year.\n"
        ),
        # Page 8: Annexure / Corporate Buffer / Disease-wise Capping
        (
            "ANNEXURE I - SPECIAL ENDORSEMENTS AND CONDITIONS\n\n"
            "1. CORPORATE FLOATER BUFFER:\n"
            "A Corporate Floater Buffer of Rs. 25,00,000 is available for critical illness cases.\n"
            "Eligibility: Usable by employees and dependents after exhaustion of base sum insured, with approval of designated HR authority.\n\n"
            "2. DISEASE-WISE CAPPING (SUB-LIMITS):\n"
            "- Cataract surgery: Capped at Rs. 40,000 per eye.\n"
            "- Joint replacement surgery: Capped at Rs. 1,50,000 per joint.\n"
            "- Hernia surgery: Capped at Rs. 50,000.\n\n"
            "3. APPLICABLE WAIVERS AND OVERRIDES:\n"
            "- Waiver of 30-day initial waiting period.\n"
            "- Waiver of first four years waiting period for pre-existing diseases.\n"
            "- Waiver of maternity waiting period.\n"
            "Note: These special conditions and annexures supersede all standard terms and conditions of the base policy."
        ),
    ]

    for title_text in pages_data:
        page = doc.new_page()
        # insert textbox
        rect = fitz.Rect(50, 50, 550, 750)
        page.insert_textbox(rect, title_text, fontsize=11, fontname="helv")

    doc.save(str(output_path))
    doc.close()
    print(f"Generated sample PDF at: {output_path}")

if __name__ == "__main__":
    out = Path("samples/sample_gmc_policy.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    generate_sample_pdf(out)
