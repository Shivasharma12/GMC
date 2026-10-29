"""
gmc_extractor/export/qms_mapper.py
Maps the nested ExtractionResult to flat QMS rows (JSON + CSV)
using config/qms_mapping.yaml.
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

from gmc_extractor.config import Settings
from gmc_extractor.schema.output import ExtractionResult

logger = logging.getLogger(__name__)

_CSV_COLUMNS = [
    "qms_field",
    "label",
    "status",
    "limit_amount",
    "limit_text",
    "limit_percent_of_si",
    "limit_days",
    "conditions",
    "source_pages",
    "evidence",
    "confidence",
]


def write_qms(result: ExtractionResult, output_stem: Path, settings: Settings) -> None:
    """
    Write flat QMS JSON and CSV files from the ExtractionResult.

    Args:
        result: The completed ExtractionResult.
        output_stem: Path stem (without extension), e.g. output/policy.
        settings: Global settings (for QMS mapping config).
    """
    mapping: dict[str, Any] = settings.qms_mapping
    result_dict = result.model_dump(mode="json")

    rows: list[dict[str, Any]] = []
    for internal_path, meta in mapping.items():
        value = _get_nested(result_dict, internal_path)
        row = _make_row(internal_path, meta, value)
        rows.append(row)

    # Write JSON
    json_path = output_stem.parent / (output_stem.name + ".qms.json")
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Written QMS JSON: %s", json_path)

    # Write CSV
    csv_path = output_stem.parent / (output_stem.name + ".qms.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            # Flatten list fields for CSV
            csv_row = {k: _csv_value(row.get(k)) for k in _CSV_COLUMNS}
            writer.writerow(csv_row)
    logger.info("Written QMS CSV: %s", csv_path)


def _get_nested(data: dict, dotpath: str) -> Any:
    """Traverse a nested dict using dot-notation path. Returns None if not found."""
    parts = dotpath.split(".")
    obj = data
    for part in parts:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
        if obj is None:
            return None
    return obj


def _make_row(internal_path: str, meta: dict, value: Any) -> dict[str, Any]:
    """Build a single QMS output row from a mapping entry and its value."""
    qms_field = meta.get("qms_field", internal_path)
    label = meta.get("label", internal_path)
    field_type = meta.get("type", "text")

    row: dict[str, Any] = {
        "qms_field": qms_field,
        "label": label,
        "status": None,
        "limit_amount": None,
        "limit_text": None,
        "limit_percent_of_si": None,
        "limit_days": None,
        "conditions": [],
        "source_pages": [],
        "evidence": None,
        "confidence": None,
    }

    if value is None:
        row["status"] = "not_mentioned"
        return row

    # FeatureValue-like dict
    if isinstance(value, dict) and "status" in value:
        row["status"] = value.get("status")
        row["limit_amount"] = value.get("limit_amount")
        row["limit_text"] = value.get("limit_text")
        row["limit_percent_of_si"] = value.get("limit_percent_of_si")
        row["limit_days"] = value.get("limit_days")
        row["conditions"] = value.get("conditions", [])
        row["source_pages"] = value.get("source_pages", [])
        row["evidence"] = value.get("evidence")
        row["confidence"] = value.get("confidence")
    # Scalar value (bool, int, str, date)
    elif isinstance(value, bool):
        row["status"] = "covered" if value else "not_covered"
        row["limit_text"] = str(value)
        row["confidence"] = 1.0
    elif isinstance(value, int):
        row["limit_amount"] = value
        row["status"] = "covered"
        row["confidence"] = 1.0
    elif isinstance(value, str):
        row["limit_text"] = value
        row["status"] = "covered" if value else "not_mentioned"
        row["confidence"] = 1.0
    elif isinstance(value, list):
        row["limit_text"] = json.dumps(value, ensure_ascii=False)
        row["status"] = "covered" if value else "not_mentioned"
        row["confidence"] = 1.0

    return row


def _csv_value(v: Any) -> str:
    """Convert a value to a CSV-safe string."""
    if v is None:
        return ""
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return str(v)
