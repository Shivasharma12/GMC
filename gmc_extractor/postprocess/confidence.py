"""
gmc_extractor/postprocess/confidence.py
Computes per-field and overall confidence scores.
Combines: LLM-reported confidence, grounding status, retrieval score.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def compute_overall_confidence(result_dict: dict[str, Any]) -> float:
    """
    Compute the overall extraction confidence as a weighted average
    of all per-field confidence values found in the result.

    Args:
        result_dict: The extraction result dict (model.model_dump()).

    Returns:
        Float in [0, 1].
    """
    scores: list[float] = []
    _collect_confidences(result_dict, scores)
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 3)


def _collect_confidences(obj: Any, scores: list[float]) -> None:
    """Recursively collect all confidence float values from the result dict."""
    if isinstance(obj, dict):
        # Top-level confidence (identity, policy_details, demographics)
        if "confidence" in obj and isinstance(obj["confidence"], (int, float)):
            scores.append(float(obj["confidence"]))
        for v in obj.values():
            _collect_confidences(v, scores)
    elif isinstance(obj, list):
        for item in obj:
            _collect_confidences(item, scores)
