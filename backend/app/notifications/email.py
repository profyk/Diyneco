"""Email through a provider interface. Each message is logged in app.notifications inside
the request's transaction and sent only after commit, so a rolled-back request sends nothing.

The `console` provider is for development and tests: it keeps messages in memory and prints
them to stderr (bypassing the redacting logger, so links with tokens stay usable locally).
"""

from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

from sqlalchemy import insert, text

from app.db.session import UnitOfWork
from app.models.events import Notification


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str
    template: str
    sender: str


class EmailProvider(Protocol):
    async def send(self, message: EmailMessage) -> str: ...


@dataclass
class ConsoleEmailProvider:
    echo: bool = True
    sent: list[EmailMessage] = field(default_factory=list)

    async def send(self, message: EmailMessage) -> str:
        self.sent.append(message)
        if self.echo:
            print(
                f"\n--- email ({message.template}) ---\nFrom: {message.sender}\nTo: {message.to}\n"
                f"Subject: {message.subject}\n\n{message.body}\n--- end email ---\n",
                file=sys.stderr,
            )
        return f"console-{uuid.uuid4()}"


@dataclass(frozen=True)
class Mailer:
    provider: EmailProvider
    sender: str

    async def queue(
        self,
        uow: UnitOfWork,
        *,
        hotel_id: uuid.UUID | None,
        template: str,
        to: str,
        subject: str,
        body: str,
        subject_ref: dict[str, Any] | None = None,
    ) -> None:
        notification_id = (
            await uow.session.execute(
                insert(Notification)
                .values(
                    hotel_id=hotel_id,
                    channel="email",
                    template=template,
                    recipient=to,
                    subject_ref=subject_ref or {},
                )
                .returning(Notification.id)
            )
        ).scalar_one()
        message = EmailMessage(to=to, subject=subject, body=body, template=template, sender=self.sender)

        async def _send() -> None:
            status, provider_id, error = "sent", None, None
            try:
                provider_id = await self.provider.send(message)
            except Exception as exc:
                status, error = "failed", type(exc).__name__
            async with uow.sessionmaker() as s, s.begin():
                await s.execute(
                    text("SELECT app.notification_mark(:id, :st, :pid, :err)"),
                    {"id": notification_id, "st": status, "pid": provider_id, "err": error},
                )

        uow.after_commit(_send)
