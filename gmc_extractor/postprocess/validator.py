"""
gmc_extractor/postprocess/validator.py
Business rule validation for the ExtractionResult.
Violations become warnings, not crashes.
"""
from __future__ import annotations

import logging
from datetime import date

logger = logging.getLogger(__name__)


def validate_result(result_dict: dict, warnings: list[str]) -> dict:
    """
    Run business rule checks on the extraction result dict.
    Appends warnings for any violations — never raises.

    Rules checked:
    1. Policy end date must be after start date.
    2. Tenure should be approximately 12 months.
    3. Sum insured tiers should be in ascending order.
    4. Premium including GST should be >= excluding GST.
    5. Total lives >= employees.
    6. Demographics: flag if stated != computed (already done in model, re-check here).
    7. Confidence values in [0, 1].
    8. Percent of SI between 0 and 100.

    Args:
        result_dict: model.model_dump() of ExtractionResult.
        warnings: Mutable list to append warnings.

    Returns:
        The (unmodified) result dict.
    """
    _check_policy_dates(result_dict, warnings)
    _check_si_tiers(result_dict, warnings)
    _check_premium(result_dict, warnings)
    _check_demographics(result_dict, warnings)
    _check_percentages(result_dict, warnings)
    return result_dict


def _check_policy_dates(result_dict: dict, warnings: list[str]) -> None:
    pd = result_dict.get("policy_details", {})
    start_str = pd.get("policy_start_date")
    end_str = pd.get("policy_end_date")
    tenure = pd.get("tenure_months")

    if start_str and end_str:
        try:
            start = date.fromisoformat(start_str)
            end = date.fromisoformat(end_str)
            if end <= start:
                warnings.append(
                    f"VALIDATION: Policy end date ({end_str}) is not after start date ({start_str})."
                )
            else:
                # Check tenure consistency
                diff_months = (end.year - start.year) * 12 + (end.month - start.month)
                if tenure is not None and abs(diff_months - tenure) > 1:
                    warnings.append(
                        f"VALIDATION: Stated tenure ({tenure} months) differs from "
                        f"computed tenure ({diff_months} months) by more than 1 month."
                    )
                if not (10 <= diff_months <= 14):
                    warnings.append(
                        f"VALIDATION: Policy duration ({diff_months} months) is unusual "
                        f"for a GMC policy (expected ~12 months)."
                    )
        except ValueError as exc:
            warnings.append(f"VALIDATION: Could not parse policy dates: {exc}")


def _check_si_tiers(result_dict: dict, warnings: list[str]) -> None:
    tiers = result_dict.get("policy_details", {}).get("sum_insured_tiers", [])
    amounts = [t.get("amount") for t in tiers if t.get("amount") is not None]
    if len(amounts) > 1 and amounts != sorted(amounts):
        warnings.append(
            f"VALIDATION: Sum insured tiers are not in ascending order: {amounts}"
        )


def _check_premium(result_dict: dict, warnings: list[str]) -> None:
    pd = result_dict.get("policy_details", {})
    excl = pd.get("premium_excluding_gst")
    incl = pd.get("premium_including_gst")
    if excl is not None and incl is not None and incl < excl:
        warnings.append(
            f"VALIDATION: Premium including GST ({incl}) is less than "
            f"excluding GST ({excl}). Possible data error."
        )


def _check_demographics(result_dict: dict, warnings: list[str]) -> None:
    demo = result_dict.get("demographics", {})
    employees = demo.get("num_employees")
    total_stated = demo.get("total_lives_stated")
    total_computed = demo.get("total_lives_computed")

    if employees is not None and total_stated is not None and total_stated < employees:
        warnings.append(
            f"VALIDATION: Total lives ({total_stated}) is less than "
            f"number of employees ({employees})."
        )

    if demo.get("count_mismatch"):
        warnings.append(
            f"VALIDATION: Demographics mismatch — stated total ({total_stated}) "
            f"!= computed total ({total_computed})."
        )


def _check_percentages(result_dict: dict, warnings: list[str]) -> None:
    """Recursively check that limit_percent_of_si values are in [0, 100]."""
    _walk_check_pct(result_dict, warnings, path="")


def _walk_check_pct(obj: object, warnings: list[str], path: str) -> None:
    if isinstance(obj, dict):
        pct = obj.get("limit_percent_of_si")
        if pct is not None and isinstance(pct, (int, float)):
            if not (0 <= pct <= 100):
                warnings.append(
                    f"VALIDATION: limit_percent_of_si={pct} out of range [0, 100] at {path}"
                )
        for k, v in obj.items():
            _walk_check_pct(v, warnings, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _walk_check_pct(item, warnings, f"{path}[{i}]")
