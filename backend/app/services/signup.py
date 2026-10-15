"""Owner sign-up: one owner account and one hotel in a single transaction.

Signup returns no tokens (DECISIONS G12): the owner verifies their email and signs in, which
also starts MFA enrolment because Hotel Owner is an MFA-required role. A signup with an email
that already has an account creates nothing and tells that account's owner by email; the
response is identical, so the endpoint cannot be used to discover who has an account.

`prepare_hotel` and `create_hotel` are shared with owners adding another property (D86).
"""

from __future__ import annotations

import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import insert, select, text

from app.audit.writer import write_audit
from app.core import crypto
from app.core.countries import Country
from app.core.countries import country as country_of
from app.core.currencies import is_supported
from app.core.errors import AppError
from app.core.passwords import check_password
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.domain import OrderNumberSequence
from app.models.events import EventSeq
from app.models.tenancy import BillingSettings, Hotel, HotelSettings, HotelUser, Subscription, User, UserRole
from app.realtime.outbox import emit
from app.repositories.roles import RoleRepository
from app.services import countries, legal
from app.services.auth import ClientInfo, send_verification_email

SIGNUP_RESPONSE = {
    "status": "verification_sent",
    "message": "Check your email to confirm your address, then sign in.",
}


def slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "hotel"
    return f"{base}-{secrets.token_hex(3)}"


def invoice_prefix(name: str) -> str:
    """Initials of the hotel name, 2 to 4 letters (DECISIONS G17); editable in settings."""
    words = [w for w in re.split(r"[^A-Za-z0-9]+", name) if w]
    initials = "".join(w[0] for w in words).upper()[:4]
    if len(initials) < 2:
        initials = re.sub(r"[^A-Za-z0-9]", "", name).upper()[:3]
    return initials or "INV"


def _field(field: str, message: str, problem: str) -> AppError:
    return AppError(
        "VALIDATION_FAILED",
        message,
        details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]},
    )


@dataclass(frozen=True)
class PreparedHotel:
    """A new hotel's details, checked: an operational country, one of its time zones, a
    supported currency, an address with its region, and the legal documents accepted."""

    hotel: dict[str, Any]
    place: Country
    timezone: str
    currency: str
    address: dict[str, Any]
    documents: list[Any]


async def prepare_hotel(
    uow: UnitOfWork, hotel: dict[str, Any], accepted_documents: list[uuid.UUID] | None
) -> PreparedHotel:
    place = country_of(hotel["country"])
    # Only countries the platform has switched on take new hotels (D84).
    if place is None or not await countries.is_operational(uow, place.code):
        raise _field("hotel.country", "Diyneco is not available in that country yet.", "Not supported.")
    tz = hotel.get("timezone") or place.timezone
    if tz not in place.timezones:
        raise _field("hotel.timezone", "Choose one of the country's time zones.", "Unknown.")
    currency = hotel.get("currency") or place.currency
    if not is_supported(currency):
        raise _field("hotel.currency", "That currency is not supported.", "Not supported.")
    address = (
        countries.checked_address(place.code, hotel["address"], "hotel.address")
        if hotel.get("address")
        else {}
    )
    documents = await legal.signup_documents(uow, place.code, accepted_documents)
    return PreparedHotel(hotel, place, tz, currency, address, documents)


async def create_hotel(
    st: AppState,
    uow: UnitOfWork,
    p: PreparedHotel,
    *,
    user_id: uuid.UUID,
    owner_label: str,
    client: ClientInfo,
    trial: bool,
    action: str,
) -> Hotel:
    """Creates the hotel with its settings, sequences and the user as its Hotel Owner, in the
    new hotel's context. With `trial`, a free trial without a plan starts (D73, D76);
    otherwise the hotel has no subscription until it chooses a plan or the platform grants a
    trial (D86)."""
    s = uow.session
    hotel = p.hotel
    hotel_id: uuid.UUID = (await s.execute(text("SELECT app.uuid_v7()"))).scalar_one()
    await set_tenant(s, hotel_id, user_id)
    await s.execute(
        insert(Hotel).values(
            id=hotel_id,
            name=hotel["name"].strip(),
            legal_name=hotel.get("legal_name"),
            slug=slugify(hotel["name"]),
            address=p.address,
            phone=hotel.get("phone"),
            email=hotel.get("email"),
            country=p.place.code,
            data_region=p.place.region,
            property_type=hotel.get("property_type"),
            room_count=hotel.get("room_count"),
            website=hotel.get("website"),
        )
    )
    await s.execute(
        insert(HotelSettings).values(
            hotel_id=hotel_id,
            invoice_prefix=invoice_prefix(hotel["name"]),
            currency=p.currency,
            timezone=p.timezone,
            locale=hotel.get("locale") or p.place.locale,
            tax_label=p.place.tax_label,
            # Suggestions only: the hotel confirms tax registration and rate in settings.
            vat_registered=False,
            vat_rate_bp=p.place.tax_rate_bp or 0,
            abridged_invoice_max_minor=p.place.abridged_invoice_max_minor,
        )
    )
    if trial:
        trial_days = (await s.execute(select(BillingSettings.trial_days))).scalar_one()
        today = datetime.now(UTC).date()
        await s.execute(
            insert(Subscription).values(
                hotel_id=hotel_id,
                plan_id=None,
                status="trial",
                starts_on=today,
                trial_ends_on=today + timedelta(days=trial_days),
            )
        )
    await s.execute(insert(EventSeq).values(hotel_id=hotel_id))
    await s.execute(insert(OrderNumberSequence).values(hotel_id=hotel_id))

    hotel_user_id = (
        await s.execute(insert(HotelUser).values(hotel_id=hotel_id, user_id=user_id).returning(HotelUser.id))
    ).scalar_one()
    ctx = TenantContext(
        hotel_id=hotel_id,
        actor_type="user",
        actor_id=user_id,
        actor_label=owner_label,
        ip=client.ip,
        request_id=client.request_id,
    )
    owner_role = await RoleRepository(s, ctx).system_role_id("hotel_owner")
    await s.execute(
        insert(UserRole).values(
            hotel_id=hotel_id, hotel_user_id=hotel_user_id, role_id=owner_role, granted_by=user_id
        )
    )
    await write_audit(
        s,
        ctx,
        action,
        "hotel",
        hotel_id,
        new_value={
            "name": hotel["name"],
            "subscription": "trial" if trial else "none",
            "status": "pending_approval",
        },
    )
    if p.documents:
        await legal.accept(uow, ctx, p.documents, user_agent=client.user_agent, country=p.place.code)
    await emit(s, ctx, "TENANT_CREATED", ["platform"], {"hotel_id": str(hotel_id)})
    return (await s.execute(select(Hotel).where(Hotel.id == hotel_id))).scalar_one()


async def signup(
    st: AppState,
    uow: UnitOfWork,
    *,
    owner_name: str,
    email: str,
    password: str,
    hotel: dict[str, Any],
    client: ClientInfo,
    accepted_documents: list[uuid.UUID] | None = None,
    owner_phone: str | None = None,
) -> dict[str, Any]:
    s = uow.session
    email = email.strip()
    check_password(password, email=email, field="owner.password")
    # Checked before the email lookup so a known address gets the same answers (no enumeration).
    prepared = await prepare_hotel(uow, hotel, accepted_documents)

    existing = (await s.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing is not None:
        await st.mailer.queue(
            uow,
            hotel_id=None,
            template="signup_existing_account",
            to=existing.email,
            subject="Someone tried to sign up with your email",
            body=(
                "An account already exists for this email. Sign in, or reset your password if you forgot it. "
                "To add another property, sign in and choose Add a property."
            ),
        )
        return SIGNUP_RESPONSE

    user_id: uuid.UUID = (await s.execute(text("SELECT app.uuid_v7()"))).scalar_one()
    await s.execute(
        insert(User).values(
            id=user_id,
            email=email,
            name=owner_name.strip(),
            password_hash=crypto.hash_secret(password),
            phone=owner_phone,
        )
    )
    created = await create_hotel(
        st,
        uow,
        prepared,
        user_id=user_id,
        owner_label=f"{owner_name.strip()} (Hotel Owner)",
        client=client,
        trial=True,
        action="hotel.signup",
    )
    user = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
    await send_verification_email(st, uow, user, created.id)
    return SIGNUP_RESPONSE
