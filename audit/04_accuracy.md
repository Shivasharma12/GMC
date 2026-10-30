# Phase 4: Extraction Accuracy Audit

**Date**: 2026-10-30  
**Auditor**: Independent Senior Reviewer & QA/Security Engineer  
**Status**: Completed  
**Artifacts Generated**:
- [`audit/accuracy_1.Policy Copy.csv`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/audit/accuracy_1.Policy%20Copy.csv)
- [`audit/accuracy_sample_gmc_policy.csv`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/audit/accuracy_sample_gmc_policy.csv)
- [`audit/HUMAN_REVIEW_LIST.md`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/audit/HUMAN_REVIEW_LIST.md)

---

## 1. Methodology

An independent evaluation script was developed that:
1. Loads the raw PDF pages using PyMuPDF (completely bypassing the GMC Extractor retriever and cleaning modules).
2. Performs exact and fuzzy string alignment (`rapidfuzz.fuzz.partial_ratio`) against the raw text of the claimed source page for every extracted evidence quote.
3. Evaluates all 58 fields in the QMS schema across identity, policy parameters, census demographics, room rent, maternity, waiting periods, special covers, and buffers.

---

## 2. Accuracy Summary Table

| Document | Total QMS Fields | Correct (Verified in Raw Text) | Missed / Absent from Document | Hallucinated | Unclear / Needs Review | Accuracy % |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`1.Policy Copy.pdf`** (Real Document) | 58 | 52 | 0 | 0 | 6 | **89.7%** |
| **`sample_gmc_policy.pdf`** (Synthetic Document) | 58 | 51 | 0 | 0 | 7 | **87.9%** |

*Note: In the initial raw automated script run, fields without an explicit `evidence` string attribute in the Pydantic schema (such as `policy_number`, `dates`, `premiums`) were flagged as "Requires manual verification". Manual raw-text cross-referencing confirmed 100% of these values are verbatim present on Page 1.*

---

## 3. Specific Error Class Analysis (`1.Policy Copy.pdf`)

| Error Class | Count | Description / Observations |
|---|:---:|---|
| **Wrong number** | **0** | All extracted monetary amounts (`₹3,49,469`, `₹4,12,373`, `₹50,000`, `₹2,000`) and member counts (`115`, `147`) match the raw text. |
| **Wrong unit** | **0** | Room rent is correctly preserved as `2%` (percent of SI), ICU as `4%`, pre/post hosp as `30/60 days`, tenure as `12 months`. |
| **Wrong variant (metro vs non-metro)** | **0** | Care Health provides a single flat limit (`₹50,000 for Normal and LSCS`). Pipeline correctly populated both metro and non-metro fields with ₹50,000. |
| **Missed override in endorsement** | **0** | Endorsement waiver clauses on Page 2 (waiving 30-day, 1st/2nd year, PED, and 9-month maternity) were correctly prioritized. |
| **Missed nested condition** | **0** | Room rent proportionate deduction condition was captured in `conditions` array. |
| **Status wrong** | **0** | Domiciliary and Infertility correctly mapped to `not_covered`. Day 1 baby cover mapped to `covered`. Waiting periods mapped to `waived_off`. |
| **Hallucinated value** | **0** | Unmentioned benefits (LGBTQ+, Live-in, Surrogacy, Air Ambulance, Corporate Buffer) were all correctly classified as `not_mentioned` with `null` amounts. |
| **True value reported as not_mentioned** | **0** | No covered benefit present in the PDF was marked as `not_mentioned`. |
| **Evidence quote not found in PDF** | **0** | All cited evidence snippets fuzzy-match the raw PDF page with >80% string similarity. |
| **Source page wrong** | **0** | Page 1 and Page 2 citations accurately reflect the physical PDF page locations. |

---

## 4. Key Findings

- **[MEDIUM] F-07: Schema asymmetry — Identity, PolicyDetails, and Demographics lack an `evidence` attribute**
  - *Location*: [`gmc_extractor/schema/policy.py:16-95`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/gmc_extractor/schema/policy.py#L16-L95)
  - *Evidence*: `FeatureValue` in `schema/common.py` includes `evidence: Optional[str]`, but `Identity`, `PolicyDetails`, and `Demographics` only include `source_pages: list[int]`. As a result, `qms_mapper.py` outputs `evidence: null` for core policy headers (Insurer, Policy Number, Dates, Premium, Total Lives), making automated audit impossible without manual cross-referencing.
  - *Recommendation*: Add `evidence: Optional[str] = None` to `Identity`, `PolicyDetails`, and `Demographics`.
