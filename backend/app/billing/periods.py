"""Subscription billing periods (DECISIONS D76).

A subscription keeps its anchor day: the day of the month it started. Each period ends on the
anchor day 1, 3 or 12 months later; in a month without that day it ends on the month's last
day, and the next period returns to the anchor day when the month has it again:

    anchor 31: 31 Jan -> 28 Feb (29 in a leap year) -> 31 Mar -> 30 Apr -> 31 May
    anchor 29, yearly: 29 Feb 2028 -> 28 Feb 2029 -> 28 Feb 2030 -> 28 Feb 2031 -> 29 Feb 2032

Periods are calendar days in Diyneco's time zone; a period's end is also the next period's
start and the renewal date.
"""

from __future__ import annotations

import calendar
from datetime import date

MONTHS = {"month": 1, "quarter": 3, "year": 12}


def anchored(year: int, month: int, anchor_day: int) -> date:
    """The anchor day in a month, or the month's last day when it is shorter."""
    return date(year, month, min(anchor_day, calendar.monthrange(year, month)[1]))


def add_months(start: date, months: int, anchor_day: int) -> date:
    index = start.year * 12 + (start.month - 1) + months
    return anchored(index // 12, index % 12 + 1, anchor_day)


def period_end(start: date, interval: str, anchor_day: int) -> date:
    """The end (exclusive) of the period that begins on `start`."""
    if not 1 <= anchor_day <= 31:
        raise ValueError("anchor_day must be 1-31")
    return add_months(start, MONTHS[interval], anchor_day)


def periods(start: date, interval: str, count: int) -> list[tuple[date, date]]:
    """The first `count` periods of a subscription that starts on `start`."""
    out = []
    begin = start
    for _ in range(count):
        end = period_end(begin, interval, start.day)
        out.append((begin, end))
        begin = end
    return out
