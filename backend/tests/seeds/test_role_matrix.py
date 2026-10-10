"""The seeded role matrix must match the security spec exactly.

role_matrix_spec.md is the spec's table copied verbatim; this test parses it independently of
the migration that seeds it, so a transcription mistake in either place fails here."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

COLUMNS = {
    "Own": "hotel_owner",
    "Adm": "hotel_admin",
    "GM": "general_manager",
    "RM": "reception_manager",
    "Rec": "receptionist",
    "Fin": "finance_manager",
    "KM": "kitchen_manager",
    "KS": "kitchen_staff",
    "SM": "room_service_manager",
    "SS": "room_service_staff",
}


def parse_spec() -> tuple[dict[str, set[str]], set[str]]:
    lines = [
        line
        for line in (Path(__file__).parent / "role_matrix_spec.md").read_text(encoding="utf-8").splitlines()
        if line.startswith("|")
    ]
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    roles = [COLUMNS[h] for h in header[1:]]
    grants: dict[str, set[str]] = {r: set() for r in roles}
    sensitive: set[str] = set()
    for line in lines[2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        code = cells[0].split("`")[1]
        if "†" in cells[0]:
            sensitive.add(code)
        for role, cell in zip(roles, cells[1:], strict=True):
            if cell == "●":
                grants[role].add(code)
            else:
                assert cell == "", f"unexpected cell {cell!r} for {code}/{role}"
    return grants, sensitive


async def test_seeded_hotel_roles_match_the_security_spec(owner_engine):
    spec, spec_sensitive = parse_spec()
    async with owner_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT r.code, rp.permission_code FROM app.roles r "
                    "JOIN app.role_permissions rp ON rp.role_id = r.id WHERE r.hotel_id IS NULL"
                )
            )
        ).all()
        perms = (await conn.execute(text("SELECT code, scope, sensitive FROM app.permissions"))).all()
    seeded: dict[str, set[str]] = {}
    for role, perm in rows:
        seeded.setdefault(role, set()).add(perm)
    for role, expected in spec.items():
        assert seeded.get(role, set()) == expected, (
            f"{role}: missing {sorted(expected - seeded.get(role, set()))}, "
            f"extra {sorted(seeded.get(role, set()) - expected)}"
        )
    hotel_perms = {p.code for p in perms if p.scope == "hotel"}
    assert hotel_perms == set().union(*spec.values())
    assert len(hotel_perms) == 52
    assert {p.code for p in perms if p.sensitive} == spec_sensitive


async def test_platform_roles(owner_engine):
    async with owner_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT r.code, rp.permission_code FROM app.roles r JOIN app.role_permissions rp ON rp.role_id = r.id "
                    "WHERE r.code LIKE 'platform_%'"
                )
            )
        ).all()
    roles: dict[str, set[str]] = {}
    for role, perm in rows:
        roles.setdefault(role, set()).add(perm)
    assert roles["platform_support"] == {"platform.metrics", "platform.tenants.read", "platform.support"}
    assert roles["platform_super_admin"] == {
        "platform.metrics",
        "platform.tenants.read",
        "platform.tenants.manage",
        "platform.billing.manage",
        "platform.flags.manage",
        "platform.support",
    }
    # Neither platform role holds any hotel permission.
    assert all(p.startswith("platform.") for perms in roles.values() for p in perms)


async def test_catalogue_seeds(owner_engine):
    async with owner_engine.connect() as conn:
        plans = (
            await conn.execute(
                # Other tests may add plans through the admin API; check the seeded ones.
                text(
                    "SELECT code, monthly_price_minor, features FROM app.plans "
                    "WHERE code IN ('starter', 'professional', 'enterprise') ORDER BY code"
                )
            )
        ).all()
        cats = (
            await conn.execute(
                text(
                    "SELECT code, revenue_group, is_revenue FROM app.charge_categories WHERE hotel_id IS NULL"
                )
            )
        ).all()
    assert [p.code for p in plans] == ["enterprise", "professional", "starter"]
    assert all(p.features.get("placeholder") is True for p in plans)  # prices still to be decided
    by_code = {c.code: c for c in cats}
    assert by_code["tip"].revenue_group == "tip" and by_code["tip"].is_revenue is False
    assert by_code["payment"].is_revenue is False
    assert {"accommodation", "food", "beverage", "room_service_fee", "laundry", "minibar"} <= set(by_code)
