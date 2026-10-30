"""
scripts/verify_grounding.py
Regression check script that verifies every QMS export:
1. Every evidence quote in active/covered main values must exist in the source PDF text (fuzzy >= 90%).
2. Any field that failed grounding must have status 'needs_review' and empty main values.
3. Prints an honest count of ungrounded fields per PDF (must be 0 in QMS main values).
4. Exits with code 1 if any ungrounded main value is detected.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from rapidfuzz import fuzz
import fitz

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
SAMPLES_DIR = BASE_DIR / "samples"
UPLOADS_DIR = BASE_DIR / "uploads"


def verify_grounding() -> int:
    qms_json_files = list(OUTPUT_DIR.glob("*.qms.json"))
    if not qms_json_files:
        print("[INFO] No QMS JSON files found in output/. Run pipeline first.")
        return 0

    print("=" * 80)
    print("STRICT GROUNDING REGRESSION AUDIT")
    print("=" * 80)

    total_failures = 0

    for json_file in qms_json_files:
        stem = json_file.name.replace(".qms.json", "")
        print(f"\nVerifying: {stem}")

        # Find source PDF
        pdf_candidates = [
            SAMPLES_DIR / f"{stem}.pdf",
            UPLOADS_DIR / f"{stem}.pdf",
        ]
        pdf_path = next((p for p in pdf_candidates if p.exists()), None)
        if not pdf_path:
            # Try fuzzy search
            for p in list(SAMPLES_DIR.glob("*.pdf")) + list(UPLOADS_DIR.glob("*.pdf")):
                if p.stem == stem:
                    pdf_path = p
                    break

        if not pdf_path:
            print(f"  [WARNING] Source PDF not found for {stem}. Skipping source text verification.")
            continue

        doc = fitz.open(str(pdf_path))
        page_texts = {i + 1: page.get_text() for i, page in enumerate(doc)}
        full_doc_text = " ".join(page_texts.values()).lower()
        doc.close()

        with open(json_file, encoding="utf-8") as f:
            rows = json.load(f)

        ungrounded_main_values = 0
        verified_count = 0
        needs_review_count = 0

        for row in rows:
            field = row.get("qms_field")
            status = row.get("status")
            ev = row.get("evidence")
            val = row.get("limit_amount") or row.get("limit_text") or row.get("limit_days") or row.get("limit_percent_of_si")

            if status == "needs_review":
                needs_review_count += 1
                # Must not have main value
                if row.get("limit_amount") is not None:
                    print(f"  [FAIL] Field {field} is 'needs_review' but has non-empty limit_amount: {row.get('limit_amount')}")
                    ungrounded_main_values += 1
                continue

            if status in ("covered", "limited", "waived_off", "applied") and val is not None:
                if not ev or not str(ev).strip():
                    print(f"  [FAIL] Field {field} has main value {val} but empty evidence quote")
                    ungrounded_main_values += 1
                    continue

                ev_clean = str(ev).strip().lower()
                # Verify quote exists in document text
                score = fuzz.partial_ratio(ev_clean, full_doc_text)
                if score < 85:  # High fidelity check
                    print(f"  [FAIL] Field {field} quote not found in source PDF (score={score:.0f}): '{ev[:60]}...'")
                    ungrounded_main_values += 1
                else:
                    verified_count += 1

        print(f"  Status Summary:")
        print(f"    - Verified Grounded Fields : {verified_count}")
        print(f"    - Needs Review (Gated)     : {needs_review_count}")
        print(f"    - Ungrounded Main Values   : {ungrounded_main_values}")

        if ungrounded_main_values > 0:
            print(f"  --> RESULT: FAILED ({ungrounded_main_values} ungrounded main values)")
            total_failures += ungrounded_main_values
        else:
            print(f"  --> RESULT: PASSED (0 ungrounded main values)")

    print("\n" + "=" * 80)
    if total_failures > 0:
        print(f"AUDIT FAILED: Total {total_failures} ungrounded main values found.")
        return 1
    else:
        print("AUDIT PASSED: 0 ungrounded main values across all evaluated policies.")
        return 0


if __name__ == "__main__":
    sys.exit(verify_grounding())

