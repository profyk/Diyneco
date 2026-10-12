"""Billing periods keep their anchor day across short months and leap years (D76)."""

from __future__ import annotations

from datetime import date
from itertools import pairwise

import pytest

from app.billing.periods import period_end, periods


def test_month_end_anchor_returns_after_short_months():
    ends = [end for _, end in periods(date(2027, 1, 31), "month", 5)]
    assert ends == [
        date(2027, 2, 28),
        date(2027, 3, 31),
        date(2027, 4, 30),
        date(2027, 5, 31),
        date(2027, 6, 30),
    ]
    leap = [end for _, end in periods(date(2028, 1, 31), "month", 2)]
    assert leap == [date(2028, 2, 29), date(2028, 3, 31)]


def test_ordinary_days_quarters_and_years():
    assert period_end(date(2026, 10, 12), "month", 12) == date(2026, 11, 12)
    assert period_end(date(2026, 11, 30), "quarter", 30) == date(2027, 2, 28)
    assert period_end(date(2026, 12, 15), "month", 15) == date(2027, 1, 15)  # across the year end
    assert [e for _, e in periods(date(2026, 8, 31), "quarter", 3)] == [
        date(2026, 11, 30),
        date(2027, 2, 28),
        date(2027, 5, 31),
    ]


def test_a_leap_day_yearly_subscription():
    ends = [end for _, end in periods(date(2028, 2, 29), "year", 4)]
    assert ends == [date(2029, 2, 28), date(2030, 2, 28), date(2031, 2, 28), date(2032, 2, 29)]


def test_periods_are_contiguous_and_reject_bad_anchors():
    ps = periods(date(2027, 1, 30), "month", 12)
    assert all(a[1] == b[0] for a, b in pairwise(ps))
    with pytest.raises(ValueError):
        period_end(date(2027, 1, 1), "month", 32)
