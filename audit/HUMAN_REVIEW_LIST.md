# Human Review List: Top 20 High-Impact / Ambiguous Extraction Fields

**Purpose**: This checklist provides the exact PDF page, clause context, extracted value, and specific reason human review is recommended for verification.

---

| # | Field Name | Document | Claimed Page | Extracted Value | Status | Reason for Human Review |
|---|---|---|:---:|---|---|---|
| **1** | `Sum Insured Tiers` | `1.Policy Copy.pdf` | Page 1 & 2 | ₹3,00,000 & ₹5,00,000 | `covered` | Page 1 states **"Total Sum Insured: 51,900,000"** (aggregate policy liability). Page 2 lists **"Graded Sum insured: Rs. 300,000 and Rs. 500,000"**. System correctly chose per-family tiers, but reviewer should confirm if QMS expects group aggregate or individual tier floater. |
| **2** | `DEM_TOTAL_STATED` | `1.Policy Copy.pdf` | Page 1 | `147` | `covered` | Page 1 states: Primary Members = 115, Dependents = 32, Total = 147. Spouses, children, and parents are not broken down in the table (grouped as "Dependents"). |
| **3** | `IDENT_TPA` | `1.Policy Copy.pdf` | Page 1 | `null` | `not_mentioned` | Policy is issued directly by Care Health Insurance Ltd. ("Intermediary: Direct"). No third-party TPA is listed. Reviewer should confirm if "In-house / Direct" is preferred over null. |
| **4** | `ROOM_RENT` | `1.Policy Copy.pdf` | Page 2 | `2% of Sum Insured per day` | `limited` | Page 2 clause: "Maximum eligibility for Normal Hospitalization: 2 % of Sum Insured per day". No absolute rupee cap (e.g. ₹5,000) exists in this policy. |
| **5** | `ROOM_ICU` | `1.Policy Copy.pdf` | Page 2 | `4% of Sum Insured per day` | `limited` | Page 2 clause: "Maximum eligibility for ICU Hospitalization: 4 % of Sum Insured per day". Proportionate deduction rules apply. |
| **6** | `MAT_NORMAL_METRO` vs `NON_METRO` | `1.Policy Copy.pdf` | Page 2 | `₹50,000` | `limited` | Page 2 clause 1: "Maximum Limit for Maternity claims is Rs. 50,000 for Normal and Rs. 50,000 for LSCS". Care Health applies a flat ₹50,000 limit with no metro vs non-metro split. Both fields mapped to 50,000. |
| **7** | `MAT_CSEC_METRO` vs `NON_METRO` | `1.Policy Copy.pdf` | Page 2 | `₹50,000` | `limited` | LSCS (Caesarean) limit is identical to normal delivery (₹50,000). System extracted 50,000 for both. |
| **8** | `MAT_9M_WAIT` | `1.Policy Copy.pdf` | Page 2 | `null` | `waived_off` | Page 2 clause 4: "9 month waiting period in respect of maternity claims waived for all Insured Members". Reviewer should verify waiver tag. |
| **9** | `MAT_BABY_DAY1` | `1.Policy Copy.pdf` | Page 2 | `covered within family floater SI` | `covered` | Page 2 clause 6: "New Born Baby covered from day one within family floater Sum Insured". |
| **10** | `MAT_VACCINATION` | `1.Policy Copy.pdf` | Page 2 | `null` | `not_mentioned` | Baby day one cover is endorsed, but no routine infant vaccination clause is present in the wording. |
| **11** | `WAIT_30DAY` | `1.Policy Copy.pdf` | Page 2 | `30 days` | `waived_off` | Page 2 clause 2: "30 Days Wait Period condition is waived for existing members and new joinees". |
| **12** | `WAIT_1YEAR` & `WAIT_2YEAR` | `1.Policy Copy.pdf` | Page 2 | `365 & 730 days` | `waived_off` | Page 2 clause 3: "First & Second year exclusion condition for specific diseases is waived for all Insured Members". |
| **13** | `WAIT_PED` | `1.Policy Copy.pdf` | Page 2 | `null` | `waived_off` | Page 2 clause 1: "Pre-existing diseases are covered for existing members and new joinees". System mapped to `waived_off`. |
| **14** | `BEN_MODERN_TREAT` | `1.Policy Copy.pdf` | Page 2 | `upto 50% of Sum Insured` | `limited` | Page 2 clause: "Modern treatments, psychiatric treatments and Bariatric Surgery covered... upto 50% of the Sum Insured". |
| **15** | `BEN_BARIATRIC` | `1.Policy Copy.pdf` | Page 2 | `upto 50% of Sum Insured` | `limited` | Bundled in the same clause as modern treatment with 50% sub-limit. |
| **16** | `BEN_PSYCHIATRIC` | `1.Policy Copy.pdf` | Page 2 | `upto 50% of Sum Insured` | `limited` | Bundled in the same clause as modern treatment with 50% sub-limit. |
| **17** | `BEN_DOMICILIARY` | `1.Policy Copy.pdf` | Page 3 | `specifically excluded` | `not_covered` | Page 3: "Domiciliary Hospitalization is specifically excluded unless mentioned specifically". System correctly tagged as `not_covered`. |
| **18** | `INF_TREATMENT` | `1.Policy Copy.pdf` | Page 3 | `specifically excluded` | `not_covered` | Page 3 Exclusions: "Infertility & related ailments including male sterility...". System correctly tagged as `not_covered`. |
| **19** | `AMB_ROAD` | `1.Policy Copy.pdf` | Page 2 | `₹2,000 per claim` | `limited` | Page 2 clause 1: "Ambulance charges payable up to a maximum amount of Rs. 2,000/- per claim". |
| **20** | `BUF_AMOUNT` | `1.Policy Copy.pdf` | N/A | `null` | `not_mentioned` | No corporate buffer endorsement exists in this 4-page policy certificate. Verify whether separate endorsement schedule was issued. |
