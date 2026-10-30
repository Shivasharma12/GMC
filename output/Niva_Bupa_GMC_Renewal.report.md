# Extraction Review Report

**File**: Niva_Bupa_GMC_Renewal.pdf  
**Pages**: 6 (scanned: 0)  
**Provider**: gemini / gemini-3.5-flash-lite  
**Run**: 2026-10-31T01:03:20  
**Overall Confidence**: 82%

## ⚠️ Warnings
- GROUNDING GATE REJECT [features.room_hospitalization.icu_charges]: Evidence quote not found in document text with >= 90% match: 'Hospital Accommodation – Room rent/day & ICU/day | ICU | 2%...'
- GROUNDING GATE REJECT [features.maternity.normal_delivery_metro]: Evidence quote not found in document text with >= 90% match: 'Normal: 25,000...'
- GROUNDING GATE REJECT [features.maternity.normal_delivery_non_metro]: Evidence quote not found in document text with >= 90% match: 'Normal: 25,000...'
- GROUNDING GATE REJECT [features.maternity.c_section_metro]: Evidence quote not found in document text with >= 90% match: 'C-Section: 35,000...'
- GROUNDING GATE REJECT [features.maternity.c_section_non_metro]: Evidence quote not found in document text with >= 90% match: 'C-Section: 35,000...'
- GROUNDING GATE REJECT [features.waiting_periods.thirty_day_waiting]: limit_days=30 not found in evidence and cited page text
- GROUNDING GATE REJECT [features.waiting_periods.first_year_waiting]: limit_days=365 not found in evidence and cited page text
- GROUNDING GATE REJECT [features.waiting_periods.second_year_waiting]: limit_days=730 not found in evidence and cited page text
- VALIDATION: Demographics mismatch — stated total (20) != computed total (9).
- Conflict detected: Schedule (p. 4) states Gross Premium Rs. 98,476, while Receipt/Section (p. 6) states Rs. 104,635.

## ❌ Not Found / Not Mentioned
- `features.other_benefits_a.teleconsultation`
- `features.other_benefits_a.pharmacy_discount`
- `features.other_benefits_a.domiciliary_hospitalization`
- `features.other_benefits_a.annual_health_checkup`
- `features.other_benefits_b.bariatric`
- `features.other_benefits_b.ayush`
- `features.other_benefits_b.lgbtq`
- `features.other_benefits_b.live_in_partner`
- `features.other_benefits_b.organ_donor_expenses`
- `features.infertility_ambulance.infertility_treatment`
- `features.infertility_ambulance.surrogacy`
- `features.infertility_ambulance.air_ambulance`

## 🔍 Low Confidence Fields (< 60%)
| Field | Confidence |
|---|---|
| `features.room_hospitalization.icu_charges` | 20% |
| `features.maternity.normal_delivery_metro` | 20% |
| `features.maternity.normal_delivery_non_metro` | 20% |
| `features.maternity.c_section_metro` | 20% |
| `features.maternity.c_section_non_metro` | 20% |
| `features.waiting_periods.thirty_day_waiting` | 20% |
| `features.waiting_periods.first_year_waiting` | 20% |
| `features.waiting_periods.second_year_waiting` | 20% |
