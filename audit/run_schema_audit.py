import sys
import os
import json
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gmc_extractor.schema.output import ExtractionResult
from gmc_extractor.config import get_settings

settings = get_settings()
qms_mapping = settings.qms_mapping
expected_qms_keys = set(meta.get("qms_field") for meta in qms_mapping.values())
print(f"Total fields defined in config/qms_mapping.yaml: {len(expected_qms_keys)}")

output_dir = Path("output")
json_files = [f for f in output_dir.glob("*.json") if not f.name.endswith(".qms.json")]

print(f"\n1. Validating {len(json_files)} output JSON file(s) against Pydantic schema:")
for jf in json_files:
    try:
        data = json.loads(jf.read_text(encoding="utf-8"))
        res = ExtractionResult.model_validate(data)
        print(f"  {jf.name}: VALID Pydantic ExtractionResult (overall_confidence={res.overall_confidence:.2f})")
    except Exception as e:
        print(f"  {jf.name}: INVALID ({e})")

print("\n2. Auditing QMS JSON and CSV outputs:")
qms_files = list(output_dir.glob("*.qms.json"))
for qf in qms_files:
    stem = qf.name.replace(".qms.json", "")
    csv_file = output_dir / f"{stem}.qms.csv"
    
    rows = json.loads(qf.read_text(encoding="utf-8"))
    row_keys = [r["qms_field"] for r in rows]
    
    # Check duplicate keys
    duplicates = [k for k in row_keys if row_keys.count(k) > 1]
    
    # Check missing fields
    missing = expected_qms_keys - set(row_keys)
    
    print(f"  {qf.name}: {len(rows)} rows | Missing keys: {len(missing)} | Duplicate keys: {len(duplicates)}")
    
    # Check statuses
    allowed_statuses = {"covered", "not_covered", "waived_off", "applied", "limited", "not_mentioned", None}
    waiting_period_fields = {"WAIT_30DAY", "WAIT_1YEAR", "WAIT_2YEAR", "WAIT_PED", "MAT_9M_WAIT"}
    allowed_wp_statuses = {"applied", "waived_off", "not_covered", "not_mentioned", None}
    
    for r in rows:
        st = r.get("status")
        if st not in allowed_statuses:
            print(f"    INVALID STATUS in {r['qms_field']}: '{st}'")
        if r["qms_field"] in waiting_period_fields and st not in allowed_wp_statuses:
            print(f"    NON-STANDARD WAITING PERIOD STATUS in {r['qms_field']}: '{st}'")
            
    # Check CSV
    if csv_file.exists():
        with open(csv_file, encoding="utf-8") as cf:
            reader = csv.DictReader(cf)
            csv_rows = list(reader)
            print(f"  {csv_file.name}: {len(csv_rows)} rows | Columns: {len(reader.fieldnames)}")
    else:
        print(f"  MISSING CSV: {csv_file.name}")
