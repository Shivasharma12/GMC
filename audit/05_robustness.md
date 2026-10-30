# Phase 5: Robustness and Generalization Audit

**Date**: 2026-10-30  
**Auditor**: Independent Senior Reviewer & QA/Security Engineer  
**Status**: Completed  

---

## 1. Normalizer Unit Tests

Tested parsing of common Indian currency amounts, percentages, day durations, and date formats across Indian/MNC insurance documents:

| Test Input | Category | Expected Output | Actual Output | Status |
|---|---|---|---|:---:|
| `"5,00,000"` | Indian Currency (Lakh format) | `500000` | `500000` | **PASS** |
| `"500000"` | Raw Integer | `500000` | `500000` | **PASS** |
| `"Rs. 5 lakh"` | Spelled-out Lakh | `500000` | `500000` | **PASS** |
| `"INR 5 Lacs"` | Alternate spelling Lacs | `500000` | `500000` | **PASS** |
| `"₹ 7.5 L"` | Shorthand with Rupee symbol | `750000` | `750000` | **PASS** |
| `"1 crore"` | Crore format | `10000000` | `10000000` | **PASS** |
| `"1% of SI"` | Percentage of SI | `1.0` | `1.0` | **PASS** |
| `"30 days"` | Days period | `30` | `30` | **PASS** |
| `"2 months"` | Months to days | `60` | `60` | **PASS** |
| `"1 year"` | Years to days | `365` | `365` | **PASS** |
| `"26th April 2024"` | Alphanumeric Date (Day first) | `"2024-04-26"` | `"2024-04-26"` | **PASS** |
| `"26/04/2024"` | Slash numeric (DD/MM/YYYY) | `"2024-04-26"` | `"2024-04-26"` | **PASS** |
| `"26-Apr-24"` | 2-digit year with dash | `"2024-04-26"` | `"2024-04-26"` | **PASS** |
| `"April 26, 2024"` | Month first (Month DD, YYYY) | `"2024-04-26"` | `None` | **FAIL** |

### Finding:
- **[HIGH] F-09: Normalizer regex fails on `Month DD, YYYY` date format**
  - *Location*: [`gmc_extractor/postprocess/normalizer.py:41-44`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/gmc_extractor/postprocess/normalizer.py#L41-L44)
  - *Evidence*: `parse_date('April 26, 2024')` returns `None` because `_DATE_DMY_ALPHA` requires the day to precede the month.
  - *Recommendation*: Add regex `_DATE_MDY_ALPHA = re.compile(r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", re.I)`.

---

## 2. Retrieval Recall Test (`1.Policy Copy.pdf`)

Retriever was evaluated across all 10 schema groups:
- `identity`: retrieved pages `[1, 2, 3]` (target answer is on Page 1) -> **100% Recall**
- `policy_details`: retrieved pages `[1, 2, 3, 4]` (target answers on Page 1 & 2) -> **100% Recall**
- `demographics`: retrieved pages `[1, 2, 3, 4]` (target answers on Page 1) -> **100% Recall**
- `room_hospitalization`: retrieved pages `[1, 2, 3]` (target answers on Page 2) -> **100% Recall**
- `maternity`: retrieved pages `[1, 2, 3]` (target answers on Page 2) -> **100% Recall**
- `waiting_periods`: retrieved pages `[1, 2, 3, 4]` (target answers on Page 2) -> **100% Recall**
- `other_benefits_a`: retrieved pages `[1, 2, 3]` (target answers on Page 2) -> **100% Recall**
- `other_benefits_b`: retrieved pages `[1, 2, 3, 4]` (target answers on Page 2) -> **100% Recall**
- `infertility_ambulance`: retrieved pages `[1, 2, 3, 4]` (target answers on Page 2 & 3) -> **100% Recall**
- `buffer_waiver`: retrieved pages `[1, 2, 3, 4]` (target answers on Page 2) -> **100% Recall**

---

## 3. Failure Handling & Resilience

Tested with `FlakyLLMClient` simulating:
1. Call 1: Network Timeout (`TimeoutError`)
2. Call 2: Unparseable/Malformed JSON (`ValueError`)
3. Call 3: Rate limit exceeded (`429 RESOURCE_EXHAUSTED`)

### Command Output:
```text
Group 'identity' (1st): LLM call failed: Simulated LLM network timeout
Group 'identity': extraction failed; using empty defaults.
Group 'policy_details' (1st): LLM call failed: Simulated Invalid JSON format returned
Group 'policy_details': extraction failed; using empty defaults.
Group 'demographics' (1st): LLM call failed: 429 RESOURCE_EXHAUSTED: Rate limit exceeded
Group 'demographics': extraction failed; using empty defaults.
Pipeline survived flaky client! Warnings recorded: 6
```
- **Verdict**: PASS. The pipeline handles network timeouts, malformed JSON responses, and HTTP 429 errors gracefully without crashing, logging diagnostic warnings, and proceeding to remaining field groups.

---

## 4. OCR Fallback & Graceful Degradation

Tested `_check_tesseract()` when Tesseract executable is not on PATH:
- Correctly logs warning: `Tesseract not found. OCR fallback disabled. Install Tesseract-OCR and ensure it is on your PATH to enable OCR.`
- Returns `False` and skips OCR gracefully without exception.

---

## 5. Caching & Free-Tier Quota Safeguards

- **Response Caching**: Verified deterministic SHA-256 caching key generation. Cache `put()` and `get()` hit returned exact matching JSON.
- **Rate Limiter Safeguard**: Verified that setting `max_requests_per_run=5` halts on request #6 with:
  `RuntimeError: MAX_REQUESTS_PER_RUN (5) reached. Aborting to protect free-tier quota.`
- **Verdict**: PASS. Prevents unexpected API billing or quota exhaustion on Google Gemini / OpenAI free tiers.
