"""Menu schedule windows, evaluated in the hotel's time zone (API spec, Menu).

A window is {"days": [1..7], "from": "HH:MM", "to": "HH:MM"} with ISO weekdays (1 = Monday).
`from` == `to` means the whole day. `to` earlier than `from` runs past midnight into the next
day, and still belongs to the day it started on (Friday 22:00-02:00 covers Saturday 01:00).
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any


def _t(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def _spans(window: dict[str, Any], day: datetime) -> list[tuple[datetime, datetime]]:
    """The window's open intervals that start on `day`'s date (local, naive-free)."""
    if day.isoweekday() not in window["days"]:
        return []
    start_t, end_t = _t(window["from"]), _t(window["to"])
    start = day.replace(hour=start_t.hour, minute=start_t.minute, second=0, microsecond=0)
    end = day.replace(hour=end_t.hour, minute=end_t.minute, second=0, microsecond=0)
    if end <= start:
        end += timedelta(days=1)
    return [(start, end)]


def is_open(windows: list[dict[str, Any]] | None, local_now: datetime) -> bool:
    if not windows:
        return True  # no schedule: always orderable
    for offset in (0, -1):  # a window that started yesterday may still be open
        day = local_now + timedelta(days=offset)
        for w in windows:
            for start, end in _spans(w, day):
                if start <= local_now < end:
                    return True
    return False


def next_open(windows: list[dict[str, Any]] | None, local_now: datetime) -> datetime | None:
    """Start of the next window after `local_now` within a week, or None."""
    if not windows:
        return None
    best: datetime | None = None
    for offset in range(8):
        day = local_now + timedelta(days=offset)
        for w in windows:
            for start, _ in _spans(w, day):
                if start > local_now and (best is None or start < best):
                    best = start
        if best is not None:
            return best
    return best
