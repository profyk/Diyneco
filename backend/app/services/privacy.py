"""POPIA data subject requests and retention (security spec, Data subject participation and
Retention; API spec, Guests).

- Export: everything the hotel holds about one guest, as JSON: profile, stays, orders with
  their lines and notes, folio entries, payments, invoices and the emails sent to them.
- Anonymise: replaces the guest's personal fields as catalogued in `app.pii_columns` (name,
  email, phone, ID number, traveller names, order notes, the email log). Amounts and the
  financial rows are kept for tax law. Issued invoices are not changed: a tax invoice must keep
  its recipient for the retention period (DECISIONS D59).
- Retention: the worker anonymises guests whose last stay ended more than the hotel's
  `guest_data_retention_days` ago.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import text

from app.audit.writer import write_audit
from app.core.errors import AppError
from app.core.state import Keyring
from app.db.session import TenantContext, UnitOfWork, set_tenant

REDACTED = "[redacted]"
ANONYMOUS_NAME = "Anonymised guest"
LIVE = ("reserved", "checked_in", "active", "checkout_pending")


async def _rows(s: Any, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(r) for r in (await s.execute(text(sql), params)).mappings().all()]


async def _guest(s: Any, ctx: TenantContext, guest_id: uuid.UUID) -> dict[str, Any]:
    rows = await _rows(
        s,
        "SELECT id, full_name, email, phone, nationality, anonymised_at, created_at, updated_at, "
        "id_number_enc IS NOT NULL AS has_id_number FROM app.guests WHERE hotel_id = :h AND id = :g",
        {"h": ctx.hotel_id, "g": guest_id},
    )
    if not rows:
        raise AppError("NOT_FOUND")
    return rows[0]


async def export_guest(
    uow: UnitOfWork, ctx: TenantContext, guest_id: uuid.UUID, keyring: Keyring | None = None
) -> dict[str, Any]:
    s = uow.session
    p = {"h": ctx.hotel_id, "g": guest_id}
    guest = await _guest(s, ctx, guest_id)
    if guest.pop("has_id_number") and keyring is not None:
        sealed = (
            await s.execute(text("SELECT id_number_enc FROM app.guests WHERE hotel_id = :h AND id = :g"), p)
        ).scalar_one()
        guest["id_number"] = (
            await keyring.decrypt(str(ctx.hotel_id), sealed, f"guest-id:{guest_id}")
        ).decode()
    stays = await _rows(
        s,
        "SELECT s.id, r.number AS room, s.status, s.arrival_date, s.departure_date, s.billing_type, "
        "bp.company_name AS billed_to_company, s.purchase_order, s.traveller_name, s.checked_in_at, "
        "s.checked_out_at, s.nightly_rate_minor, s.currency "
        "FROM app.stays s JOIN app.rooms r ON r.id = s.room_id "
        "LEFT JOIN app.billing_profiles bp ON bp.id = s.billing_profile_id "
        "WHERE s.hotel_id = :h AND s.guest_id = :g ORDER BY s.arrival_date",
        p,
    )
    orders = await _rows(
        s,
        "SELECT o.id, o.number, o.stay_id, o.status, o.created_at, o.special_instructions, "
        "o.total_minor, o.currency, coalesce(json_agg(json_build_object('name', i.name, "
        "'quantity', i.quantity, 'line_total_minor', i.line_total_minor, 'note', i.note)) "
        "FILTER (WHERE i.id IS NOT NULL), '[]') AS items "
        "FROM app.orders o LEFT JOIN app.order_items i ON i.order_id = o.id "
        "WHERE o.hotel_id = :h AND o.stay_id IN "
        "(SELECT id FROM app.stays WHERE hotel_id = :h AND guest_id = :g) "
        "GROUP BY o.id ORDER BY o.created_at",
        p,
    )
    entries = await _rows(
        s,
        "SELECT f.stay_id, e.business_date, e.entry_type, c.code AS category, e.description, "
        "e.quantity, e.amount_minor, e.vat_minor, e.currency FROM app.folio_entries e "
        "JOIN app.folios f ON f.id = e.folio_id JOIN app.charge_categories c ON c.id = e.category_id "
        "WHERE e.hotel_id = :h AND f.stay_id IN "
        "(SELECT id FROM app.stays WHERE hotel_id = :h AND guest_id = :g) ORDER BY e.created_at",
        p,
    )
    payments = await _rows(
        s,
        "SELECT p.id, f.stay_id, p.method, p.status, p.amount_due_minor, p.amount_received_minor, "
        "p.tip_amount_minor, p.currency, p.occurred_at FROM app.payments p "
        "JOIN app.folios f ON f.id = p.folio_id "
        "WHERE p.hotel_id = :h AND f.stay_id IN "
        "(SELECT id FROM app.stays WHERE hotel_id = :h AND guest_id = :g) ORDER BY p.occurred_at",
        p,
    )
    invoices = await _rows(
        s,
        "SELECT i.number, i.kind, i.issued_at, i.recipient, i.totals, i.currency FROM app.invoices i "
        "JOIN app.folios f ON f.id = i.folio_id WHERE i.hotel_id = :h AND f.stay_id IN "
        "(SELECT id FROM app.stays WHERE hotel_id = :h AND guest_id = :g) "
        "ORDER BY i.issued_at",
        p,
    )
    emails = (
        await _rows(
            s,
            "SELECT template, status, created_at, sent_at FROM app.notifications "
            "WHERE hotel_id = :h AND lower(recipient) = lower(:e) ORDER BY created_at",
            {"h": ctx.hotel_id, "e": guest["email"]},
        )
        if guest["email"]
        else []
    )
    await write_audit(s, ctx, "guest.export", "guest", guest_id, new_value={"stays": len(stays)})
    return {
        "generated_at": datetime.now(UTC),
        "guest": guest,
        "stays": stays,
        "orders": orders,
        "folio_entries": entries,
        "payments": payments,
        "invoices": invoices,
        "emails": emails,
        "notes": [
            "Amounts are in minor units (cents) of the stated currency.",
            "Issued invoices are tax records and are kept for the legal retention period.",
        ],
    }


async def anonymise_guest(
    uow: UnitOfWork, ctx: TenantContext, guest_id: uuid.UUID, *, reason: str, automatic: bool = False
) -> dict[str, Any]:
    s = uow.session
    p = {"h": ctx.hotel_id, "g": guest_id}
    guest = await _guest(s, ctx, guest_id)
    if guest["anonymised_at"] is not None:
        raise AppError("INVALID_TRANSITION", "This guest is already anonymised.")
    live = (
        await s.execute(
            text(
                "SELECT count(*) FROM app.stays WHERE hotel_id = :h AND guest_id = :g AND status = ANY(:live)"
            ),
            {**p, "live": list(LIVE)},
        )
    ).scalar_one()
    if live:
        raise AppError(
            "INVALID_TRANSITION", "The guest has a current or upcoming stay. Anonymise after it ends."
        )
    if guest["email"]:
        await s.execute(
            text("SELECT app.anonymise_recipient(:h, :e)"), {"h": ctx.hotel_id, "e": guest["email"]}
        )
    await s.execute(
        text(
            "UPDATE app.guests SET full_name = :n, email = NULL, phone = NULL, id_number_enc = NULL, "
            "nationality = NULL, anonymised_at = now(), updated_at = now() WHERE hotel_id = :h AND id = :g"
        ),
        {**p, "n": ANONYMOUS_NAME},
    )
    await s.execute(
        text("UPDATE app.stays SET traveller_name = NULL WHERE hotel_id = :h AND guest_id = :g"),
        p,
    )
    await s.execute(
        text(
            "UPDATE app.orders SET special_instructions = :r WHERE hotel_id = :h "
            "AND special_instructions IS NOT NULL AND stay_id IN "
            "(SELECT id FROM app.stays WHERE hotel_id = :h AND guest_id = :g)"
        ),
        {**p, "r": REDACTED},
    )
    await s.execute(
        text(
            "UPDATE app.order_items SET note = :r WHERE hotel_id = :h AND note IS NOT NULL "
            "AND order_id IN (SELECT id FROM app.orders WHERE hotel_id = :h AND stay_id IN "
            "(SELECT id FROM app.stays WHERE hotel_id = :h AND guest_id = :g))"
        ),
        {**p, "r": REDACTED},
    )
    # Guest personal data never enters audit values (D33); the entry records who and why.
    await write_audit(
        s,
        ctx,
        "guest.anonymise",
        "guest",
        guest_id,
        new_value={"automatic": automatic},
        reason=reason,
    )
    return {"id": guest_id, "anonymised": True}


async def guests_past_retention(uow: UnitOfWork, ctx: TenantContext, today: date) -> list[uuid.UUID]:
    """Guests with no current stay whose last departure is older than the retention period."""
    days = (
        await uow.session.execute(
            text("SELECT guest_data_retention_days FROM app.hotel_settings WHERE hotel_id = :h"),
            {"h": ctx.hotel_id},
        )
    ).scalar_one()
    cutoff = today - timedelta(days=int(days))
    rows = (
        await uow.session.execute(
            text(
                "SELECT g.id FROM app.guests g WHERE g.hotel_id = :h AND g.anonymised_at IS NULL "
                "AND NOT EXISTS (SELECT 1 FROM app.stays s "
                "WHERE s.guest_id = g.id AND s.status = ANY(:live)) "
                "AND coalesce((SELECT max(s.departure_date) FROM app.stays s WHERE s.guest_id = g.id), "
                "g.created_at::date) < :cutoff LIMIT 500"
            ),
            {"h": ctx.hotel_id, "live": list(LIVE), "cutoff": cutoff},
        )
    ).scalars()
    return list(rows)


async def run_retention(sessionmaker: Any, today: date | None = None) -> int:
    """Worker job: anonymise every guest past their hotel's retention period."""
    today = today or datetime.now(UTC).date()
    async with sessionmaker() as s, s.begin():
        result = await s.execute(text("SELECT hotel_id FROM app.hotels_for_jobs()"))
        hotels = [r[0] for r in result.all()]
    done = 0
    for hotel_id in hotels:
        async with sessionmaker() as s, s.begin():
            await set_tenant(s, hotel_id)
            uow = UnitOfWork(session=s, sessionmaker=sessionmaker)
            ctx = TenantContext(
                hotel_id=hotel_id, actor_type="system", actor_id=None, actor_label="Retention"
            )
            for guest_id in await guests_past_retention(uow, ctx, today):
                await anonymise_guest(uow, ctx, guest_id, reason="Retention period ended", automatic=True)
                done += 1
    return done
