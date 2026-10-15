"""Operational countries (DECISIONS D84): Diyneco knows every country (app/core/countries.py)
but new hotels can sign up only where the platform has switched the country on. Hotels that
already exist keep working when their country is switched off; only new signups stop."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, insert, select, text

from app.audit.writer import write_platform_audit
from app.core.countries import COUNTRIES, Country
from app.core.errors import AppError
from app.db.session import UnitOfWork
from app.models.tenancy import OperationalCountry


def payload(c: Country) -> dict[str, Any]:
    return {
        "code": c.code,
        "name": c.name,
        "currency": c.currency,
        "timezone": c.timezone,
        "timezones": list(c.timezones),
        "locale": c.locale,
        "dial": c.dial,
        "region": c.region,
        "tax_label": c.tax_label,
        "tax_id_label": c.tax_id_label,
        "tax_id_pattern": c.tax_id_pattern,
        "tax_rate_bp": c.tax_rate_bp,
    }


async def operational_codes(uow: UnitOfWork) -> set[str]:
    return set((await uow.session.execute(select(OperationalCountry.country))).scalars())


async def is_operational(uow: UnitOfWork, code: str) -> bool:
    row = await uow.session.execute(
        select(OperationalCountry.country).where(OperationalCountry.country == code)
    )
    return row.first() is not None


async def public_list(uow: UnitOfWork) -> list[dict[str, Any]]:
    """Countries a new hotel can choose at signup, by name."""
    codes = await operational_codes(uow)
    return [payload(c) for c in sorted(COUNTRIES.values(), key=lambda c: c.name) if c.code in codes]


async def admin_list(uow: UnitOfWork) -> list[dict[str, Any]]:
    """Every country with whether it takes signups and how many hotels it has."""
    enabled = {r.country: r for r in (await uow.session.execute(select(OperationalCountry))).scalars()}
    counts = {
        r["country"]: r
        for r in (await uow.session.execute(text("SELECT * FROM app.admin_country_counts()"))).mappings()
    }
    out = []
    for c in sorted(COUNTRIES.values(), key=lambda c: c.name):
        row = enabled.get(c.code)
        n = counts.get(c.code)
        out.append(
            {
                **payload(c),
                "operational": row is not None,
                "enabled_at": row.enabled_at if row else None,
                "hotels": int(n["hotels"]) if n else 0,
                "active_hotels": int(n["active"]) if n else 0,
            }
        )
    return out


async def set_operational(
    uow: UnitOfWork, actor: dict[str, Any], code: str, operational: bool, reason: str
) -> dict[str, Any]:
    c = COUNTRIES.get(code)
    if c is None:
        raise AppError("NOT_FOUND")
    s = uow.session
    was = await is_operational(uow, code)
    if operational and not was:
        await s.execute(insert(OperationalCountry).values(country=code, enabled_by=actor["actor_id"]))
    elif not operational and was:
        await s.execute(delete(OperationalCountry).where(OperationalCountry.country == code))
    if operational != was:
        await write_platform_audit(
            s,
            **actor,
            action="platform.country_enabled" if operational else "platform.country_disabled",
            entity_type="country",
            entity_id=None,
            new_value={"country": code, "reason": reason},
        )
    await s.flush()
    return next(x for x in await admin_list(uow) if x["code"] == code)
