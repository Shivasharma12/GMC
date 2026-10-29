"""
gmc_extractor/export/json_writer.py
Writes the full ExtractionResult to a JSON file.
Also writes a human-review Markdown report.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from gmc_extractor.schema.output import ExtractionResult

logger = logging.getLogger(__name__)

_LOW_CONFIDENCE_THRESHOLD = 0.6
_NOT_FOUND_STATUSES = {"not_mentioned"}


def write_json(result: ExtractionResult, output_path: Path) -> None:
    """
    Write the ExtractionResult as pretty-printed JSON.

    Args:
        result: The completed ExtractionResult.
        output_path: Destination file path (e.g. output/policy.json).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = result.model_dump(mode="json")
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Written JSON: %s", output_path)


def write_report(result: ExtractionResult, output_path: Path) -> None:
    """
    Write a human-review Markdown report highlighting:
    - Low-confidence fields (< 0.6)
    - Not-found / not_mentioned fields
    - Warnings from the pipeline

    Args:
        result: The completed ExtractionResult.
        output_path: Destination file path (e.g. output/policy.report.md).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = result.model_dump(mode="json")

    lines: list[str] = [
        f"# Extraction Review Report",
        f"",
        f"**File**: {result.document_info.file_name}  ",
        f"**Pages**: {result.document_info.total_pages} (scanned: {result.document_info.scanned_pages})  ",
        f"**Provider**: {result.document_info.provider} / {result.document_info.model}  ",
        f"**Run**: {result.document_info.run_timestamp}  ",
        f"**Overall Confidence**: {result.overall_confidence:.0%}",
        f"",
    ]

    # ── Warnings ──────────────────────────────────────────────────────────
    if result.warnings:
        lines.append("## ⚠️ Warnings")
        for w in result.warnings:
            lines.append(f"- {w}")
        lines.append("")

    # ── Low-confidence and not-found fields ───────────────────────────────
    low_conf: list[tuple[str, float]] = []
    not_found: list[str] = []
    _collect_issues(data, low_conf, not_found, path="")

    if not_found:
        lines.append("## ❌ Not Found / Not Mentioned")
        for f in not_found:
            lines.append(f"- `{f}`")
        lines.append("")

    if low_conf:
        lines.append("## 🔍 Low Confidence Fields (< 60%)")
        lines.append("| Field | Confidence |")
        lines.append("|---|---|")
        for field, conf in sorted(low_conf, key=lambda x: x[1]):
            lines.append(f"| `{field}` | {conf:.0%} |")
        lines.append("")

    if not low_conf and not not_found and not result.warnings:
        lines.append("✅ All fields extracted with acceptable confidence. No issues found.")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Written report: %s", output_path)


def _collect_issues(
    obj: Any,
    low_conf: list[tuple[str, float]],
    not_found: list[str],
    path: str,
) -> None:
    """Recursively collect low-confidence and not-found fields."""
    if isinstance(obj, dict):
        # FeatureValue-like dicts
        status = obj.get("status")
        conf = obj.get("confidence")

        if status in _NOT_FOUND_STATUSES and path:
            not_found.append(path)
        elif conf is not None and isinstance(conf, (int, float)) and conf < _LOW_CONFIDENCE_THRESHOLD and path:
            if status not in _NOT_FOUND_STATUSES:
                low_conf.append((path, float(conf)))

        for k, v in obj.items():
            if k in ("source_pages", "conditions", "warnings", "evidence"):
                continue
            child_path = f"{path}.{k}" if path else k
            _collect_issues(v, low_conf, not_found, child_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _collect_issues(item, low_conf, not_found, f"{path}[{i}]")
