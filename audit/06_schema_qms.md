# Phase 6: Schema and QMS Mapping Audit

**Date**: 2026-10-30  
**Auditor**: Independent Senior Reviewer & QA/Security Engineer  
**Status**: Completed  

---

## 1. Pydantic Model Validation

Programmatic validation of all JSON outputs against `gmc_extractor.schema.output.ExtractionResult`:

```text
Validating 3 output JSON file(s) against Pydantic schema:
  1.Policy Copy.json: VALID Pydantic ExtractionResult (overall_confidence=0.93)
  sample_gmc_policy.json: VALID Pydantic ExtractionResult (overall_confidence=0.02)
  synthetic_different_policy.json: VALID Pydantic ExtractionResult (overall_confidence=0.89)
```
- **Verdict**: PASS. All generated JSON files strictly validate against the Pydantic v2 model without schema violations or validation exceptions.

---

## 2. QMS JSON and CSV Uniformity Audit

Audited `*.qms.json` and `*.qms.csv` for structural consistency and type uniformity:

```text
1.Policy Copy.qms.json: 58 rows | Missing keys: 0 | Duplicate keys: 0
1.Policy Copy.qms.csv: 58 rows | Columns: 11 (Header + Data)
sample_gmc_policy.qms.json: 58 rows | Missing keys: 0 | Duplicate keys: 0
sample_gmc_policy.qms.csv: 58 rows | Columns: 11 (Header + Data)
synthetic_different_policy.qms.json: 58 rows | Missing keys: 0 | Duplicate keys: 0
synthetic_different_policy.qms.csv: 58 rows | Columns: 11 (Header + Data)
```

### Checks Performed:
- **Duplicate Keys**: 0 duplicates across all files.
- **Completeness**: Exactly 58 rows in every file, matching 100% of the definitions in `config/qms_mapping.yaml`.
- **Column Consistency**: All CSV files have identical 11 columns:
  `[qms_field, label, status, limit_amount, limit_text, limit_percent_of_si, limit_days, conditions, source_pages, evidence, confidence]`
- **Status Value Enums**: All statuses conform to allowed values: `{covered, not_covered, waived_off, applied, limited, not_mentioned, null}`.
- **Waiting Period Statuses**: Standardized strictly to `{applied, waived_off, not_covered, not_mentioned}`.

---

## 3. Assignment Requirement vs Schema Completeness Matrix

| Requirement from Specification | QMS Field Code | Label in QMS Schema | Data Type | Status |
|---|---|---|---|:---:|
| Insurer Name | `IDENT_INSURER` | Insurer Name | Text | **Covered** |
| Existing TPA | `IDENT_TPA` | TPA Name | Text | **Covered** |
| Previous Inception Date | `POL_PREV_INCEPTION` | Previous Year Inception Date | Date (ISO) | **Covered** |
| Policy Tenure | `POL_TENURE_MONTHS` | Policy Tenure (months) | Integer | **Covered** |
| Net Premium (excl GST) | `POL_PREMIUM_EXCL_GST` | Premium (excluding GST) | INR Amount | **Covered** |
| Gross Premium (incl GST) | `POL_PREMIUM_INCL_GST` | Premium (including GST) | INR Amount | **Covered** |
| Family - Employee | `FAM_EMPLOYEE` | Family - Employee Covered | Boolean | **Covered** |
| Family - Spouse | `FAM_SPOUSE` | Family - Spouse Covered | Boolean | **Covered** |
| Family - Children | `FAM_CHILDREN` | Family - Children Covered | Boolean | **Covered** |
| Family - Parents | `FAM_PARENTS` | Family - Parents Covered | Boolean | **Covered** |
| Family - Parents-in-Law | `FAM_PARENTS_IN_LAW` | Family - Parents-in-Law Covered | Boolean | **Covered** |
| SI Tiers (Multiple) | Nested list | `sum_insured_tiers` (Amount + Grade) | Structured | **Covered** |
| Employees Count | `DEM_EMPLOYEES` | Number of Employees | Integer | **Covered** |
| Spouses Count | `DEM_SPOUSES` | Number of Spouses | Integer | **Covered** |
| Children Count | `DEM_CHILDREN` | Number of Children | Integer | **Covered** |
| Parents Count | `DEM_PARENTS` | Number of Parents / Parents-in-Law | Integer | **Covered** |
| Total Lives Stated | `DEM_TOTAL_STATED` | Total Lives (as stated in policy) | Integer | **Covered** |
| Total Lives Computed | `DEM_TOTAL_COMPUTED` | Total Lives (computed) | Integer | **Covered** |
| Room Rent Limit | `ROOM_RENT` | Room Rent Limit | Amount / % / Conditions | **Covered** |
| Room Rent % of SI | `ROOM_RENT_PCT` | Room Rent (% of SI) | Percentage | **Covered** |
| ICU Charges Limit | `ROOM_ICU` | ICU Charges Limit | Amount / % / Conditions | **Covered** |
| ICU Charges % of SI | `ROOM_ICU_PCT` | ICU Charges (% of SI) | Percentage | **Covered** |
| Pre-Hospitalization Days | `ROOM_PRE_HOSP_DAYS` | Pre-Hospitalisation Days | Integer (Days) | **Covered** |
| Post-Hospitalization Days | `ROOM_POST_HOSP_DAYS` | Post-Hospitalisation Days | Integer (Days) | **Covered** |
| 9-Month Maternity Waiting | `MAT_9M_WAIT` | Maternity 9-Month Waiting Period | Waived/Applied | **Covered** |
| Baby Day One Cover | `MAT_BABY_DAY1` | Baby Day One Cover | Status + text | **Covered** |
| Baby Vaccination Cover | `MAT_VACCINATION` | Baby Vaccination Cover | Status + text | **Covered** |
| Normal Delivery (Metro) | `MAT_NORMAL_METRO` | Maternity - Normal Delivery (Metro) | INR Amount | **Covered** |
| Normal Delivery (Non-Metro)| `MAT_NORMAL_NON_METRO`| Maternity - Normal Delivery (Non-Metro) | INR Amount | **Covered** |
| C-Section (Metro) | `MAT_CSEC_METRO` | Maternity - C-Section (Metro) | INR Amount | **Covered** |
| C-Section (Non-Metro) | `MAT_CSEC_NON_METRO` | Maternity - C-Section (Non-Metro) | INR Amount | **Covered** |
| 30-Day Waiting Period | `WAIT_30DAY` | 30-Day Initial Waiting Period | Waived/Applied | **Covered** |
| 1st Year Waiting Period | `WAIT_1YEAR` | 1st Year Specific Disease Waiting | Waived/Applied | **Covered** |
| 2nd Year Waiting Period | `WAIT_2YEAR` | 2nd Year Specific Disease Waiting | Waived/Applied | **Covered** |
| PED Waiting Period | `WAIT_PED` | Pre-Existing Disease (PED) Waiting | Waived/Applied | **Covered** |
| Day Care Procedures | `BEN_DAYCARE` | Day Care Procedures | Status + text | **Covered** |
| OPD Benefit | `BEN_OPD` | OPD Benefit | Status + Amount | **Covered** |
| Teleconsultation | `BEN_TELECONSULT` | Teleconsultation | Status + text | **Covered** |
| Pharmacy Discount | `BEN_PHARMACY` | Pharmacy Discount | Status + text | **Covered** |
| Domiciliary Hospitalization| `BEN_DOMICILIARY` | Domiciliary Hospitalisation | Status + text | **Covered** |
| Annual Health Check-Up | `BEN_HEALTH_CHECK` | Annual Health Check-Up | Status + text | **Covered** |
| Modern / Advanced Treatment| `BEN_MODERN_TREAT` | Modern / Advanced Treatment | Status + text | **Covered** |
| Bariatric Surgery | `BEN_BARIATRIC` | Bariatric Surgery | Status + text | **Covered** |
| Psychiatric Treatment | `BEN_PSYCHIATRIC` | Psychiatric / Mental Health Treatment | Status + text | **Covered** |
| AYUSH Treatment | `BEN_AYUSH` | AYUSH Treatment | Status + text | **Covered** |
| LGBTQ+ Cover | `BEN_LGBTQ` | LGBTQ+ Cover | Status + text | **Covered** |
| Live-In Partner Cover | `BEN_LIVEIN` | Live-In Partner Cover | Status + text | **Covered** |
| Organ Donor Expenses | `BEN_ORGAN_DONOR` | Organ Donor Expenses | Status + text | **Covered** |
| Infertility Treatment | `INF_TREATMENT` | Infertility Treatment | Status + Amount | **Covered** |
| Surrogacy | `INF_SURROGACY` | Surrogacy | Status + text | **Covered** |
| Road Ambulance Charges | `AMB_ROAD` | Ambulance Charges (Road) | INR Amount | **Covered** |
| Air Ambulance Charges | `AMB_AIR` | Air Ambulance | INR Amount | **Covered** |
| Corporate Buffer Limit | `BUF_AMOUNT` | Corporate Buffer Limit | INR Amount | **Covered** |
| Corporate Buffer Eligibility| `BUF_ELIGIBILITY` | Corporate Buffer - Who Can Use | Text | **Covered** |
| Disease-Wise Capping | `BUF_DISEASE_CAPPING` | Disease-Wise Capping | Structured list | **Covered** |
| Waiver Conditions | `BUF_WAIVER_CONDITIONS` | Applicable Waiver Conditions | Structured list | **Covered** |

- **Verdict**: PASS. 100% of required fields in the Technical Assessment specification are cleanly modeled and exported.
