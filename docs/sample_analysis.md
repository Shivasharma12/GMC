# Sample PDF Analysis & Generic Extraction Patterns

This document details layout structures, terminology variations, and extraction observations across Indian Group Medical Cover (GMC) insurance policies (e.g. Star Health, ICICI Lombard, HDFC ERGO, Care Health, New India Assurance, etc.).

---

## 1. Document Structure & Layout Patterns

Indian GMC policies generally span between 30 and 80+ pages and are structured into distinct tiers:

| Section | Typical Location | Content & Format | Challenges & Pipeline Handling |
|---|---|---|---|
| **Cover & Policy Schedule** | Pages 1–5 | Insurer details, TPA name, Policyholder/Employer name, Policy Period, Inception Premium (with/without GST), Family Definition (1+3, 1+5 floater), Sum Insured Tiers. | Often formatted in dense multi-column key-value tables. Handled by pdfplumber table-to-markdown converter. |
| **Member Census / Demographics** | Pages 2–6 or Appendix | Employee count, dependent spouses, children, parents/in-laws, total lives. | Stated totals may conflict with sum of individual categories. Demographics model captures both stated and computed totals, flagging discrepancies. |
| **Benefit Schedule (Base Policy)** | Pages 5–30 | Hospitalization, Room Rent capping (e.g. 1% of SI or Single Private AC Room), ICU limits (2% of SI), Pre/Post hospitalization days (30/60 or 60/90 days). | Diverse wording ("proportionate deduction", "fair and reasonable", "actuals"). Handled by synonym retrieval and `FeatureValue` schema. |
| **Maternity & Newborn Cover** | Pages 10–35 | 9-month waiting period waiver, normal delivery vs C-section limits, baby day 1 cover, vaccination. | Tiered limits (Metro vs Non-Metro, e.g. 50k / 40k). Represented via `metro` and `non_metro` variants. |
| **Waiting Periods & Exclusions** | Pages 15–45 | 30-day initial waiting period, 1st/2nd/4th year specific ailment waiting periods, Pre-existing Disease (PED). | In GMC, these are typically **waived off**. Pipeline distinguishes `waived_off` vs `applied` vs `not_covered`. |
| **Other Benefits & Special Covers** | Pages 20–55 | Day Care, OPD, Teleconsultation, Domiciliary, AYUSH, Modern Treatment, Bariatric, Psychiatric, Organ Donor, Ambulance. | Varied sub-limits, percentages, and conditions (e.g. BMI > 35 for bariatric). Preserved in `conditions` array. |
| **Annexures, Endorsements & Special Conditions** | End of document (Pages 40–80) | Corporate Floater Buffer, Disease-wise Capping (Cataract, Joint Replacement), Special Waivers. | **Critical Rule**: Endorsements override base terms. Retriever applies a 1.25x structural BM25 boost to Annexure/Endorsement pages. |

---

## 2. Text Selectability & OCR Fallback

- **Digital Native PDFs**: Most insurer schedules and terms are digital vector PDFs with selectable text. PyMuPDF extracts text at high fidelity and speed.
- **Scanned Endorsements & Stamps**: Certain policies include scanned signed endorsement sheets or policy schedules (character count < 30 per page).
- **Fallback Strategy**:
  - `gmc_extractor/pdf/ocr.py` detects scanned pages (`is_scanned = len(text) < 30`).
  - Renders the page image using PyMuPDF (`page.get_pixmap()`, avoiding poppler dependencies).
  - Invokes `pytesseract` if installed.
  - If Tesseract is not installed in the environment, logs a warning and gracefully continues without crashing.

---

## 3. Inspected Sample: `sample_gmc_policy.pdf`

Output from `python main.py inspect samples/sample_gmc_policy.pdf`:

```text
Inspecting: samples/sample_gmc_policy.pdf
INFO Reading PDF: sample_gmc_policy.pdf
INFO Read 8 pages (0 scanned)
  Total pages : 8
  Scanned     : 0 []
  Headings    : 6
+---------------------------------------------------------+
| Page | Heading                                          |
|------+--------------------------------------------------|
| 1    | POLICY SCHEDULE - GROUP MEDICAL COVER            |
| 2    | MEMBER CENSUS AND DEMOGRAPHICS SCHEDULE          |
| 3    | SECTION I - HOSPITALIZATION EXPENSES & ROOM RENT |
| 4    | SECTION II - MATERNITY AND NEWBORN BABY BENEFIT  |
| 5    | SECTION III - WAITING PERIODS AND WAIVERS        |
| 8    | ANNEXURE I - SPECIAL ENDORSEMENTS AND CONDITIONS |
+---------------------------------------------------------+
```

### Key Verification Points:
1. **Section Heading Detection**: Accurately identified uppercase and clause headings across all major sections.
2. **Page Markers**: `[PAGE n]` markers maintained throughout text parsing to support grounding and citation.
3. **Retrieval**: BM25 correctly matches relevant pages based on `config/keywords.yaml` without requiring hardcoded page indices.

---

## 4. Generic Retrieval & Pipeline Tuning

Based on cross-insurer terminology variations, `config/keywords.yaml` has been configured with comprehensive Indian insurance terminology:
- **Amounts & Currency**: `lakh`, `lac`, `lakhs`, `lacs`, `crore`, `cr`, `INR`, `Rs.`, `₹`
- **Family Structure**: `1+3`, `1+5`, `ESC`, `ESCP`, `floater`, `dependent`, `in-laws`
- **Room Rent & ICU**: `room rent`, `proportionate deduction`, `single private AC`, `ICU charges`, `ICU per day`
- **Maternity**: `9 month`, `nine month`, `baby day one`, `newborn`, `vaccination`, `normal delivery`, `caesarean`, `c-section`
- **Waiting Periods**: `PED`, `pre-existing`, `initial waiting period`, `30 days`, `specific illness`, `waived off`
- **Buffer & Capping**: `corporate buffer`, `floater buffer`, `disease-wise capping`, `cataract`, `joint replacement`
