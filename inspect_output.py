import json
from pathlib import Path

def inspect_policy(file_name):
    p = Path("output") / f"{file_name}.qms.json"
    if not p.exists():
        print(f"File {p} does not exist.")
        return
    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n=======================================================")
    print(f"POLICY: {file_name}")
    print(f"=======================================================")
    
    fields = [
        "IDENT_INSURER",
        "IDENT_TPA",
        "POL_SI_TIERS",
        "POL_TOTAL_SUM_INSURED",
        "POL_PREV_INCEPTION",
        "POL_TENURE",
        "DEM_DEPENDENTS",
        "DEM_TOTAL_COMPUTED",
        "MAT_NORMAL_METRO",
        "COPAY_SUBLIMITS",
        "BUF_WAIVER_CONDITIONS",
        "BUF_DISEASE_CAPPING",
    ]
    for field in fields:
        row = next((r for r in data if r["qms_field"] == field), None)
        if row:
            print(f"\n[{field}]")
            print(f"  status      : {row.get('status')}")
            print(f"  limit_amount: {row.get('limit_amount')}")
            print(f"  limit_text  : {str(row.get('limit_text'))[:90]}")
            print(f"  conditions  : {row.get('conditions')}")
            print(f"  source_pages: {row.get('source_pages')}")
            print(f"  evidence    : {str(row.get('evidence'))[:100]}")
            print(f"  confidence  : {row.get('confidence')}")

if __name__ == "__main__":
    inspect_policy("1.Policy Copy")
    inspect_policy("GHI_Policy")
