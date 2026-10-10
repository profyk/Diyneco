"""Email through a provider interface. Each message is logged in app.notifications inside
the request's transaction and sent only after commit, so a rolled-back request sends nothing.

The `console` provider is for development and tests: it keeps messages in memory and prints
them to stderr (bypassing the redacting logger, so links with tokens stay usable locally).
"""

from __future__ import annotations

import asyncio
import smtplib
import ssl
import sys
import uuid
from dataclasses import dataclass, field
from email.message import EmailMessage as MimeMessage
from email.utils import make_msgid, parseaddr
from typing import Any, Protocol
from urllib.parse import unquote, urlsplit

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
    attachments: tuple[tuple[str, bytes, str], ...] = ()  # (filename, content, media type)


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
                f"Subject: {message.subject}\n\n{message.body}\n"
                + "".join(f"[attachment {a[0]}, {len(a[1])} bytes]\n" for a in message.attachments)
                + "--- end email ---\n",
                file=sys.stderr,
            )
        return f"console-{uuid.uuid4()}"


@dataclass
class SmtpEmailProvider:
    """Any SMTP service (Amazon SES, Postmark, Mailgun, Microsoft 365, ...). STARTTLS on
    smtp://, implicit TLS on smtps://; certificates are always verified."""

    url: str
    password: str | None
    timeout_s: float = 15.0

    async def send(self, message: EmailMessage) -> str:
        return await asyncio.to_thread(self._send, message)

    def _send(self, message: EmailMessage) -> str:
        parts = urlsplit(self.url)
        if parts.scheme not in ("smtp", "smtps") or not parts.hostname:
            raise ValueError("EMAIL_SMTP_URL must be smtp:// or smtps://")
        msg = MimeMessage()
        msg["From"] = message.sender
        msg["To"] = message.to
        msg["Subject"] = message.subject
        message_id = make_msgid(domain=parseaddr(message.sender)[1].split("@")[-1] or None)
        msg["Message-ID"] = message_id
        msg.set_content(message.body)
        for filename, content, media_type in message.attachments:
            main, _, sub = media_type.partition("/")
            msg.add_attachment(content, maintype=main, subtype=sub or "octet-stream", filename=filename)
        context = ssl.create_default_context()
        user = unquote(parts.username) if parts.username else None
        if parts.scheme == "smtps":
            with smtplib.SMTP_SSL(
                parts.hostname, parts.port or 465, timeout=self.timeout_s, context=context
            ) as c:
                if user:
                    c.login(user, self.password or "")
                c.send_message(msg)
        else:
            with smtplib.SMTP(parts.hostname, parts.port or 587, timeout=self.timeout_s) as c:
                c.starttls(context=context)
                if user:
                    c.login(user, self.password or "")
                c.send_message(msg)
        return message_id


def build_email_provider(
    provider: str, *, smtp_url: str | None, key: str | None, echo: bool
) -> EmailProvider:
    if provider == "console":
        return ConsoleEmailProvider(echo=echo)
    if provider == "smtp" and smtp_url:
        return SmtpEmailProvider(url=smtp_url, password=key)
    raise RuntimeError(f"email provider {provider!r} is not supported")


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
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> None:
        notification_id = (await uow.session.execute(text("SELECT app.uuid_v7()"))).scalar_one()
        await uow.session.execute(
            insert(Notification).values(
                id=notification_id,
                hotel_id=hotel_id,
                channel="email",
                template=template,
                recipient=to,
                subject_ref=subject_ref or {},
            )
        )
        message = EmailMessage(
            to=to,
            subject=subject,
            body=body,
            template=template,
            sender=self.sender,
            attachments=tuple(attachments or ()),
        )

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
