"""In-process event bus. The worker publishes drained outbox events here; the WebSocket
gateway subscribes when it arrives in Phase 3. Until then, subscribers are logging and tests."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

log = logging.getLogger("diyneco.realtime")


@dataclass(frozen=True)
class Event:
    event_id: str
    hotel_id: str | None
    seq: int | None
    type: str
    channels: list[str]
    occurred_at: datetime
    data: dict[str, Any]


Subscriber = Callable[[Event], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []

    def subscribe(self, fn: Subscriber) -> None:
        self._subscribers.append(fn)

    async def publish(self, event: Event) -> None:
        log.info(
            "event published",
            extra={
                "event_type": event.type,
                "seq": event.seq,
                "channels": event.channels,
                "hotel_id": event.hotel_id,
            },
        )
        for fn in self._subscribers:
            await fn(event)
