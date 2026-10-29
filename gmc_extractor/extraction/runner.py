"""
gmc_extractor/extraction/runner.py
Generic extraction runner:
  1. Retrieve relevant pages via BM25
  2. Build prompt
  3. Call LLM
  4. Parse into Pydantic model
  5. Retry once on parse failure
  6. Second-pass widening if >50% of fields are null/not_mentioned
"""
from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, ValidationError

from gmc_extractor.extraction.groups import GroupSpec
from gmc_extractor.llm.base import LLMClient
from gmc_extractor.prompts.groups import build_group_prompt
from gmc_extractor.prompts.system import SYSTEM_PROMPT
from gmc_extractor.retrieval.indexer import PageIndex
from gmc_extractor.retrieval.retriever import retrieve, DEFAULT_TOP_K, DEFAULT_CHAR_BUDGET

logger = logging.getLogger(__name__)

# Fraction of null/not_mentioned fields that triggers a second-pass
_SECOND_PASS_THRESHOLD = 0.5
# Second pass uses wider retrieval
_SECOND_PASS_TOP_K = DEFAULT_TOP_K * 2
_SECOND_PASS_NEIGHBOR = 2
_SECOND_PASS_CHAR_BUDGET = DEFAULT_CHAR_BUDGET * 2


def extract_group(
    spec: GroupSpec,
    index: PageIndex,
    keywords: dict[str, Any],
    client: LLMClient,
    warnings: list[str],
) -> BaseModel:
    """
    Run the full retrieval → prompt → LLM → parse loop for one group.

    Args:
        spec: The GroupSpec defining this group.
        index: BM25 PageIndex over the PDF.
        keywords: Full keywords config dict.
        client: LLM client instance.
        warnings: Mutable list to append non-fatal warnings.

    Returns:
        A parsed Pydantic model instance for this group.
    """
    # ── First pass ──────────────────────────────────────────────────────────
    result = _run_pass(
        spec=spec,
        index=index,
        keywords=keywords,
        client=client,
        warnings=warnings,
        top_k=DEFAULT_TOP_K,
        neighbor_window=1,
        char_budget=DEFAULT_CHAR_BUDGET,
        pass_label="1st",
    )

    # ── Check if second pass is needed ──────────────────────────────────────
    if result is not None and _needs_second_pass(result):
        logger.info("Group '%s': >50%% null — running second-pass with wider retrieval", spec.name)
        result2 = _run_pass(
            spec=spec,
            index=index,
            keywords=keywords,
            client=client,
            warnings=warnings,
            top_k=_SECOND_PASS_TOP_K,
            neighbor_window=_SECOND_PASS_NEIGHBOR,
            char_budget=_SECOND_PASS_CHAR_BUDGET,
            pass_label="2nd",
        )
        if result2 is not None:
            result = _merge(result, result2, spec)

    if result is None:
        warnings.append(f"Group '{spec.name}': extraction failed; using empty defaults.")
        result = spec.model()  # type: ignore[call-arg]

    return result


def _run_pass(
    spec: GroupSpec,
    index: PageIndex,
    keywords: dict[str, Any],
    client: LLMClient,
    warnings: list[str],
    top_k: int,
    neighbor_window: int,
    char_budget: int,
    pass_label: str,
) -> BaseModel | None:
    """Run a single retrieve-prompt-LLM-parse pass."""
    pages = retrieve(
        index=index,
        keywords=keywords,
        group_key=spec.keyword_key,
        top_k=top_k,
        neighbor_window=neighbor_window,
        char_budget=char_budget,
    )
    pages_text = "\n\n".join(p.full_text for p in pages)

    if not pages_text.strip():
        warnings.append(f"Group '{spec.name}' ({pass_label}): no text retrieved.")
        return None

    prompt = build_group_prompt(spec.name, pages_text)

    raw_dict = _call_llm(client, prompt, spec.name, warnings, pass_label)
    if raw_dict is None:
        return None

    return _parse_model(spec, raw_dict, prompt, client, warnings, pass_label)


def _call_llm(
    client: LLMClient,
    prompt: str,
    group_name: str,
    warnings: list[str],
    pass_label: str,
) -> dict | None:
    """Call the LLM and return a dict, or None on unrecoverable failure."""
    try:
        return client.ask_json(SYSTEM_PROMPT, prompt)
    except Exception as exc:
        msg = f"Group '{group_name}' ({pass_label}): LLM call failed: {exc}"
        logger.error(msg)
        warnings.append(msg)
        return None


def _parse_model(
    spec: GroupSpec,
    raw_dict: dict,
    original_prompt: str,
    client: LLMClient,
    warnings: list[str],
    pass_label: str,
) -> BaseModel | None:
    """Parse raw dict into the Pydantic model; retry once on ValidationError."""
    try:
        return spec.model.model_validate(raw_dict)
    except (ValidationError, Exception) as exc:
        logger.warning(
            "Group '%s' (%s): parse error, retrying with error hint: %s",
            spec.name, pass_label, exc
        )
        # Retry with error message appended to prompt
        retry_prompt = (
            original_prompt
            + f"\n\n[SYSTEM NOTE: Your previous response caused a parsing error: {exc}. "
            "Please fix the JSON and return only valid JSON matching the schema exactly.]"
        )
        try:
            raw_dict2 = client.ask_json(SYSTEM_PROMPT, retry_prompt)
            return spec.model.model_validate(raw_dict2)
        except Exception as exc2:
            msg = f"Group '{spec.name}' ({pass_label}): parse retry failed: {exc2}"
            logger.error(msg)
            warnings.append(msg)
            return None


def _needs_second_pass(model: BaseModel) -> bool:
    """
    Return True if more than 50% of fields are null or not_mentioned.
    Works for both FeatureValue-containing models and simpler models.
    """
    data = model.model_dump()
    null_count = 0
    total_count = 0
    _count_nulls(data, null_count_ref=[0], total_count_ref=[0])
    # Re-count using helper
    n, t = _flatten_null_check(data)
    if t == 0:
        return False
    ratio = n / t
    logger.debug("Second-pass check: %.0f%% null (%d/%d)", ratio * 100, n, t)
    return ratio > _SECOND_PASS_THRESHOLD


def _flatten_null_check(obj: Any) -> tuple[int, int]:
    """Recursively count null/not_mentioned values vs total leaf values."""
    null_count = 0
    total_count = 0

    if isinstance(obj, dict):
        for k, v in obj.items():
            # Skip metadata fields
            if k in ("source_pages", "confidence", "conditions", "warnings"):
                continue
            n, t = _flatten_null_check(v)
            null_count += n
            total_count += t
    elif isinstance(obj, list):
        # A non-empty list counts as found
        total_count += 1
        if not obj:
            null_count += 1
    elif obj is None:
        null_count += 1
        total_count += 1
    elif obj == "not_mentioned":
        null_count += 1
        total_count += 1
    elif isinstance(obj, (str, int, float, bool)):
        total_count += 1

    return null_count, total_count


def _count_nulls(data: Any, null_count_ref: list, total_count_ref: list) -> None:
    """Unused helper kept for compatibility."""
    pass


def _merge(first: BaseModel, second: BaseModel, spec: GroupSpec) -> BaseModel:
    """
    Merge two extraction results, preferring non-null/non-not_mentioned values
    from whichever pass found more.
    """
    first_data = first.model_dump()
    second_data = second.model_dump()
    merged = _merge_dicts(first_data, second_data)
    try:
        return spec.model.model_validate(merged)
    except Exception:
        return first  # Fall back to first pass if merge fails


def _merge_dicts(first: Any, second: Any) -> Any:
    """Recursively merge two dicts, preferring non-null values from second."""
    if isinstance(first, dict) and isinstance(second, dict):
        result = dict(first)
        for k, v2 in second.items():
            v1 = first.get(k)
            if _is_empty(v1) and not _is_empty(v2):
                result[k] = v2
            elif isinstance(v1, dict) and isinstance(v2, dict):
                result[k] = _merge_dicts(v1, v2)
        return result
    return first if not _is_empty(first) else second


def _is_empty(v: Any) -> bool:
    """Return True if the value is null/empty/not_mentioned."""
    if v is None:
        return True
    if v == "not_mentioned":
        return True
    if isinstance(v, list) and not v:
        return True
    if isinstance(v, dict):
        status = v.get("status")
        if status in (None, "not_mentioned"):
            limit_amount = v.get("limit_amount")
            limit_text = v.get("limit_text")
            if limit_amount is None and limit_text is None:
                return True
    return False
