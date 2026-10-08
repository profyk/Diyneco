"""Owner sign-up: one owner account and one hotel in a single transaction.

Signup returns no tokens (DECISIONS G12): the owner verifies their email and signs in, which
also starts MFA enrolment because Hotel Owner is an MFA-required role. A signup with an email
that already has an account creates nothing and tells that account's owner by email; the
response is identical, so the endpoint cannot be used to discover who has an account.
"""

from __future__ import annotations

import re
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, text

from app.audit.writer import write_audit
from app.core import crypto
from app.core.passwords import check_password
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.domain import OrderNumberSequence
from app.models.events import EventSeq
from app.models.tenancy import Hotel, HotelSettings, HotelUser, Plan, Subscription, User, UserRole
from app.realtime.outbox import emit
from app.repositories.roles import RoleRepository
from app.services.auth import ClientInfo, send_verification_email

DEFAULT_PLAN = "starter"
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


async def signup(
    st: AppState,
    uow: UnitOfWork,
    *,
    owner_name: str,
    email: str,
    password: str,
    hotel: dict[str, Any],
    client: ClientInfo,
) -> dict[str, Any]:
    s = uow.session
    email = email.strip()
    check_password(password, email=email, field="owner.password")

    existing = (await s.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing is not None:
        await st.mailer.queue(
            uow,
            hotel_id=None,
            template="signup_existing_account",
            to=existing.email,
            subject="Someone tried to sign up with your email",
            body=(
                "An account already exists for this email. Sign in, or reset your password if you forgot it."
            ),
        )
        return SIGNUP_RESPONSE

    hotel_id: uuid.UUID = (await s.execute(text("SELECT app.uuid_v7()"))).scalar_one()
    user_id: uuid.UUID = (await s.execute(text("SELECT app.uuid_v7()"))).scalar_one()
    await set_tenant(s, hotel_id, user_id)

    await s.execute(
        insert(User).values(
            id=user_id, email=email, name=owner_name.strip(), password_hash=crypto.hash_secret(password)
        )
    )
    await s.execute(
        insert(Hotel).values(
            id=hotel_id,
            name=hotel["name"].strip(),
            legal_name=hotel.get("legal_name"),
            slug=slugify(hotel["name"]),
            address=hotel.get("address") or {},
            phone=hotel.get("phone"),
            email=hotel.get("email"),
        )
    )
    await s.execute(
        insert(HotelSettings).values(hotel_id=hotel_id, invoice_prefix=invoice_prefix(hotel["name"]))
    )
    plan_id = (await s.execute(select(Plan.id).where(Plan.code == DEFAULT_PLAN))).scalar_one()
    await s.execute(
        insert(Subscription).values(
            hotel_id=hotel_id, plan_id=plan_id, status="trialing", starts_on=datetime.now(UTC).date()
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
        actor_label=f"{owner_name.strip()} (Hotel Owner)",
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
        "hotel.signup",
        "hotel",
        hotel_id,
        new_value={"name": hotel["name"], "plan": DEFAULT_PLAN, "status": "pending_approval"},
    )
    await emit(s, ctx, "TENANT_CREATED", ["platform"], {"hotel_id": str(hotel_id)})
    user = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
    await send_verification_email(st, uow, user, hotel_id)
    return SIGNUP_RESPONSE
