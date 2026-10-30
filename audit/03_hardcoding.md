# Phase 3: Hardcoding and Cheating Detection Audit

**Date**: 2026-10-30  
**Auditor**: Independent Senior Reviewer & QA/Security Engineer  
**Status**: Completed  

---

## 1. Global Repository Grep for Real Sample Values

A case-insensitive scan was executed across all `.py`, `.yaml`, `.json`, `.md` source files outside `tests/`, `samples/`, `uploads/`, `output/`, and `venv/`.

### Targeted Values Checked:
- Policy numbers: `41201895`, `STAR/GMC/2024/09841`
- Insurers: `Care Health`, `Star Health`, `Aayuv`
- Premiums: `349,469`, `412,373`, `12,50,000`, `14,75,000`
- People: `Manish Dodeja`

### Raw Grep Matches:
```text
.\create_sample_pdf.py:14 [Star Health] -> "INSURER: Star Health and Allied Insurance Company Limited\n"
.\create_sample_pdf.py:16 [STAR/GMC] -> "Policy Number: STAR/GMC/2024/09841\n"
.\create_sample_pdf.py:22 [12,?50,?000] -> "Inception Net Premium (without GST): Rs. 12,50,000\n"
.\create_sample_pdf.py:23 [14,?75,?000] -> "Total Inception Premium (with 18% GST): Rs. 14,75,000\n\n"
.\docs\sample_analysis.md:3 [Star Health] -> This document details layout structures...
.\docs\sample_analysis.md:3 [Care Health] -> This document details layout structures...
.\gmc_extractor\llm\mock_client.py:37 [Star Health] -> "insurer_name": "Star Health and Allied Insurance Company Limited",
.\gmc_extractor\llm\mock_client.py:45 [STAR/GMC] -> "policy_number": "STAR/GMC/2024/09841",
.\gmc_extractor\llm\mock_client.py:50 [12,?50,?000] -> "premium_excluding_gst": 1250000,
.\gmc_extractor\llm\mock_client.py:51 [14,?75,?000] -> "premium_including_gst": 1475000,
```

### Analysis & Findings:
- In production pipeline logic (`pdf/`, `retrieval/`, `extraction/`, `postprocess/`, `export/`), **ZERO** hardcoded policy numbers, insurers, dates, or premiums were found.
- **[HIGH] F-06: `gmc_extractor/llm/mock_client.py` contains hardcoded Star Health responses**
  - *Location*: [`gmc_extractor/llm/mock_client.py:36-120`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/gmc_extractor/llm/mock_client.py#L36-L120)
  - *Evidence*: `mock_client.py` hardcodes Star Health answers (`STAR/GMC/2024/09841`, ₹12,50,000, etc.) so tests pass offline without an API key. However, running `python main.py run <any_pdf> --provider mock` emits Star Health data regardless of the input PDF content.
  - *Impact*: Evaluators testing offline with `--provider mock` on an arbitrary document will observe static data.
  - *Recommendation*: Refactor `mock_client.py` so it only acts as an offline test fixture for `sample_gmc_policy.pdf`, or implement a dynamic keyword-based extractor for mock mode, or clearly label its scope.

---

## 2. Few-Shot Example Inspection in Prompts

Inspected: [`gmc_extractor/prompts/groups.py`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/gmc_extractor/prompts/groups.py)
- **Identity prompt** (Line 52): Uses invented entity `Horizon General Insurance Limited` and `MediAssist Healthcare Services Ltd.`.
- **Policy details prompt** (Line 98): Uses invented dates `01-April-2024 to 31-March-2025` and invented figures `Rs. 18,45,000` / `Rs. 21,77,100`.
- **Demographics prompt** (Line 145): Uses invented census counts `Employees: 250, Spouses: 180, Children: 220, Parents: 60`.
- **Verdict**: PASS. All few-shot examples in system prompts are fictitious and do not leak data from evaluation PDFs.

---

## 3. Generalization Test on Novel Document

A completely novel PDF was generated at `tests/fixtures/synthetic_different_policy.pdf`:
- Insurer: `Bajaj Allianz General Insurance Co. Ltd.`
- TPA: `Paramount Health Services & Insurance TPA Pvt. Ltd.`
- Policy Number: `BAGIC/CORP/GMC/2025/7712`
- Terminology: "Period of Cover", "Inception Consideration", "Per diem", "Lakhs", "Band A/B"
- SI Tiers: Band A (₹10 Lakhs), Band B (₹5 Lakhs)
- Demographics: 200 Employees, 150 Spouses, 250 Children, 50 Parents (Total 650)
- Room Rent: Rs. 6,000 daily or 1% of SI

### Command Run:
```bash
python main.py run tests/fixtures/synthetic_different_policy.pdf --provider gemini --no-cache
```

### Extracted JSON Verification:
- `insurer_name`: `"Bajaj Allianz General Insurance Co. Ltd."` (100% exact match)
- `tpa_name`: `"Paramount Health Services & Insurance TPA Pvt. Ltd."` (100% exact match)
- `policy_number`: `"BAGIC/CORP/GMC/2025/7712"` (100% exact match)
- `premium_excluding_gst`: `850000` (100% exact match from "Rs. 8,50,000")
- `premium_including_gst`: `1003000` (100% exact match from "Rs. 10,03,000")
- `sum_insured_tiers`: `[{"amount": 500000, "grade_or_category": "Band B (General Staff)"}, {"amount": 1000000, "grade_or_category": "Band A (Senior Staff)"}]` (100% exact conversion from Lakhs to INR)
- `demographics`: `{"num_employees": 200, "num_spouses": 150, "num_children": 250, "num_parents": 50, "total_lives_stated": 650, "total_lives_computed": 650, "count_mismatch": false}`
- `room_rent`: `limit_amount: 6000`, `limit_percent_of_si: 1.0`
- `overall_confidence`: **89%**
- **Verdict**: PASS. Generalizes seamlessly across unseen insurers, layouts, and terminology with zero code modifications.

---

## 4. Zero-Leakage Test with Null LLM Client

Ran pipeline with an LLM client returning empty dict `{}` for all calls:
- All identity fields: `None`
- All policy details: `None`
- All feature statuses: `not_mentioned`
- Confidence: `0.0`
- **Verdict**: PASS. Zero default data or hallucinations are hardcoded into the pipeline parser.
