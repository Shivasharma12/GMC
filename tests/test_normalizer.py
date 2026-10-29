"""
tests/test_normalizer.py
Unit tests for the normalizer module.
Tests all common Indian insurance document amount/date/days formats.
"""
import pytest
from gmc_extractor.postprocess.normalizer import (
    parse_amount,
    parse_date,
    parse_days,
    parse_percent,
)


# ── Amount tests ───────────────────────────────────────────────────────────────

class TestParseAmount:
    def test_plain_integer(self):
        assert parse_amount("500000") == 500000

    def test_indian_comma_format(self):
        assert parse_amount("5,00,000") == 500000

    def test_rs_prefix(self):
        assert parse_amount("Rs. 5,00,000") == 500000

    def test_inr_prefix(self):
        assert parse_amount("INR 500000") == 500000

    def test_rupee_symbol(self):
        assert parse_amount("₹ 7,50,000") == 750000

    def test_lakh_word(self):
        assert parse_amount("5 lakh") == 500000

    def test_lakh_decimal(self):
        assert parse_amount("7.5 lakh") == 750000

    def test_lac_variant(self):
        assert parse_amount("INR 5 Lacs") == 500000

    def test_L_shorthand(self):
        assert parse_amount("₹ 7.5 L") == 750000

    def test_crore(self):
        assert parse_amount("1 crore") == 10_000_000

    def test_crore_with_rs(self):
        assert parse_amount("Rs. 1 crore") == 10_000_000

    def test_half_crore(self):
        assert parse_amount("0.5 crore") == 5_000_000

    def test_large_indian(self):
        assert parse_amount("1,00,00,000") == 10_000_000

    def test_none_on_garbage(self):
        assert parse_amount("not an amount") is None

    def test_plain_zero(self):
        assert parse_amount("0") == 0


# ── Percent tests ──────────────────────────────────────────────────────────────

class TestParsePercent:
    def test_simple_pct(self):
        assert parse_percent("1% of SI") == 1.0

    def test_float_pct(self):
        assert parse_percent("2.5%") == 2.5

    def test_of_sum_insured(self):
        assert parse_percent("1% of Sum Insured") == 1.0

    def test_no_pct(self):
        assert parse_percent("500000") is None


# ── Days tests ─────────────────────────────────────────────────────────────────

class TestParseDays:
    def test_days(self):
        assert parse_days("30 days") == 30

    def test_months(self):
        assert parse_days("2 months") == 60

    def test_year(self):
        assert parse_days("1 year") == 365

    def test_no_duration(self):
        assert parse_days("covered") is None

    def test_90_days(self):
        assert parse_days("Post-hospitalisation: 90 days") == 90


# ── Date tests ─────────────────────────────────────────────────────────────────

class TestParseDate:
    def test_iso_passthrough(self):
        assert parse_date("2024-04-26") == "2024-04-26"

    def test_dmy_slash(self):
        assert parse_date("26/04/2024") == "2024-04-26"

    def test_dmy_dash(self):
        assert parse_date("26-04-2024") == "2024-04-26"

    def test_alpha_month(self):
        assert parse_date("26th April 2024") == "2024-04-26"

    def test_short_month(self):
        assert parse_date("26-Apr-24") == "2024-04-26"

    def test_full_month_no_suffix(self):
        assert parse_date("1 January 2025") == "2025-01-01"

    def test_none_on_garbage(self):
        assert parse_date("no date here") is None
