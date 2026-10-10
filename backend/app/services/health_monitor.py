"""Platform health watch (DECISIONS D65).

Every minute the worker reads cross-hotel health counters. When the platform becomes degraded,
or the set of problems changes, it emits `HEALTH_DEGRADED` on the `platform` channel (the Admin
panel shows it live) and logs an error, which Sentry turns into an alert. When everything is
back to normal it emits `HEALTH_RECOVERED` once.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text

log = logging.getLogger("diyneco.health")

QUEUE_LAG_S = 120  # events waiting longer than this: realtime and webhooks are behind
FAILED_EMAILS_PER_HOUR = 5
STUCK_EMAILS = 1


def problems(signals: dict[str, Any]) -> dict[str, str]:
    """Problem code -> human description, from one reading of the signals."""
    found: dict[str, str] = {}
    lag = float(signals["oldest_pending_seconds"])
    if lag > QUEUE_LAG_S:
        found["event_queue_behind"] = (
            f"{int(signals['pending_events'])} events waiting, the oldest for {int(lag)} s"
        )
    if int(signals["failed_emails_hour"]) >= FAILED_EMAILS_PER_HOUR:
        found["emails_failing"] = f"{int(signals['failed_emails_hour'])} emails failed in the last hour"
    if int(signals["stuck_emails"]) >= STUCK_EMAILS:
        found["emails_stuck"] = f"{int(signals['stuck_emails'])} emails queued for over 15 minutes"
    return found


@dataclass
class HealthMonitor:
    current: frozenset[str] = field(default_factory=frozenset)

    async def check(self, sessionmaker: Any) -> str | None:
        """Returns the event emitted, if any."""
        async with sessionmaker() as s, s.begin():
            row = (await s.execute(text("SELECT * FROM app.platform_health_signals()"))).mappings().one()
            found = problems(dict(row))
            codes = frozenset(found)
            if codes == self.current:
                return None
            if codes:
                event = "HEALTH_DEGRADED"
                payload: dict[str, Any] = {
                    "problems": [{"code": c, "detail": found[c]} for c in sorted(codes)]
                }
                log.error("platform health degraded", extra={"problems": sorted(codes)})
            else:
                event = "HEALTH_RECOVERED"
                payload = {"resolved": sorted(self.current)}
                log.warning("platform health recovered", extra={"resolved": sorted(self.current)})
            await s.execute(
                text("SELECT app.emit_platform_event(:t, CAST(:p AS jsonb))"),
                {"t": event, "p": json.dumps(payload)},
            )
        self.current = codes
        return event
