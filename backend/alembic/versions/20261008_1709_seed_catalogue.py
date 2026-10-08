"""seed catalogue: permissions, system roles and their permissions, platform roles,
system charge categories, plans

Data here is copied into the migration on purpose: a migration must not change meaning when
application code changes later. The role matrix is checked against the security spec by
tests/seeds/test_role_matrix.py.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-08 17:09
"""

import json

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

# Role columns in the order of the security spec's matrix.
HOTEL_ROLES = [
    ("hotel_owner", "Hotel Owner"),
    ("hotel_admin", "Hotel Admin"),
    ("general_manager", "General Manager"),
    ("reception_manager", "Reception Manager"),
    ("receptionist", "Receptionist"),
    ("finance_manager", "Finance Manager"),
    ("kitchen_manager", "Kitchen Manager"),
    ("kitchen_staff", "Kitchen Staff"),
    ("room_service_manager", "Room-Service Manager"),
    ("room_service_staff", "Room-Service Staff"),
]

# code: (sensitive, description, matrix flags Own Adm GM RM Rec Fin KM KS SM SS)
HOTEL_PERMISSIONS: dict[str, tuple[bool, str, str]] = {
    "hotel.read": (False, "View the hotel profile, status and plan", "1111111010"),
    "hotel.update": (False, "Edit the hotel profile", "1110000000"),
    "settings.read": (False, "View operational settings", "1111010000"),
    "settings.update": (True, "Change operational settings", "1110000000"),
    "rooms.read": (False, "View rooms and room types", "1111110010"),
    "rooms.manage": (False, "Create, edit and remove rooms and room types", "1110000000"),
    "rooms.status": (False, "Change a room's housekeeping status", "1111100000"),
    "devices.read": (False, "View tablets and kitchen displays", "1111101000"),
    "devices.manage": (False, "Pair, lock, reset and reassign devices", "1111000000"),
    "staff.read": (False, "View staff, invitations, roles and permissions", "1111000000"),
    "staff.manage": (True, "Invite, edit and deactivate staff and change their roles", "1110000000"),
    "roles.manage": (True, "Create and edit custom roles", "1100000000"),
    "guests.read": (False, "Search and view guests", "1111110000"),
    "guests.manage": (False, "Create and edit guests", "1111100000"),
    "privacy.manage": (True, "Export or anonymise a guest's personal data", "1110000000"),
    "billing.manage": (False, "Create and edit company billing profiles", "1111100000"),
    "stays.read": (False, "View stays", "1111110000"),
    "stays.manage": (False, "Create, check in, extend, move and cancel stays", "1111100000"),
    "stays.rate_override": (False, "Set a negotiated nightly rate on a stay", "1111000000"),
    "menu.read": (False, "View the menu and kitchen stations", "1111101010"),
    "menu.manage": (False, "Edit the menu", "1110001000"),
    "menu.price.update": (True, "Change menu prices", "1110000000"),
    "menu.availability": (False, "Mark items sold out or back in stock", "1111001000"),
    "menu.certify": (False, "Set halaal and kosher tags", "1110001000"),
    "kitchen.manage": (False, "Manage kitchen stations", "1110001000"),
    "kitchen.view": (False, "View the kitchen board", "1110001100"),
    "kitchen.update": (False, "Accept and progress orders in the kitchen", "1110001100"),
    "orders.read": (False, "View orders", "1111111010"),
    "orders.create": (False, "Enter an order for a room", "1111100000"),
    "orders.approve": (True, "Approve or decline orders over the auto-approve limit", "1111000000"),
    "orders.cancel": (True, "Cancel an order before preparation", "1111000000"),
    "deliveries.view": (False, "View deliveries", "1111100011"),
    "deliveries.update": (False, "Claim, pick up and deliver orders", "1110000011"),
    "deliveries.manage": (False, "Assign deliveries to staff", "1110000010"),
    "folio.read": (False, "View folios", "1111110000"),
    "folio.charge": (False, "Post other service charges to a folio", "1111100000"),
    "folio.discount": (True, "Give a discount on a folio", "1111010000"),
    "folio.adjust.request": (False, "Request an adjustment to a folio entry", "1111110000"),
    "folio.adjust.approve": (True, "Approve or reject another person's adjustment", "1111010000"),
    "payments.record": (False, "Record a payment", "1111110011"),
    "payments.read": (False, "View payments", "1111110010"),
    "checkout.perform": (True, "Check a guest out", "1111100000"),
    "checkout.override": (True, "Check out with an outstanding balance", "1111000000"),
    "invoices.read": (False, "View invoices", "1111110000"),
    "invoices.send": (False, "Email invoices", "1111110000"),
    "invoices.credit": (True, "Issue a credit note", "1110010000"),
    "reports.read": (False, "View operational reports", "1111011010"),
    "reports.finance": (False, "View finance reports and the daily close", "1110010000"),
    "audit.read": (False, "View the audit log", "1111010000"),
    "subscription.read": (False, "View the subscription and usage", "1110010000"),
    "subscription.manage": (False, "Request a plan change", "1000000000"),
    "integrations.manage": (True, "Manage API keys and webhooks", "1100000000"),
}

PLATFORM_PERMISSIONS = {
    "platform.metrics": "View platform metrics and health",
    "platform.tenants.read": "View hotels on the platform",
    "platform.tenants.manage": "Approve, suspend and reactivate hotels",
    "platform.billing.manage": "Manage plans and hotel subscriptions",
    "platform.flags.manage": "Manage feature flags",
    "platform.support": "Open time-boxed support access to a hotel",
}
PLATFORM_ROLES = {
    "platform_super_admin": ("Platform Super Admin", list(PLATFORM_PERMISSIONS)),
    "platform_support": ("Platform Support", ["platform.metrics", "platform.tenants.read", "platform.support"]),
}

# code, name, revenue_group, is_revenue
CHARGE_CATEGORIES = [
    ("accommodation", "Accommodation", "accommodation", True),
    ("accommodation_tax", "Accommodation tax", "accommodation", True),
    ("food", "Food", "fnb", True),
    ("beverage", "Beverage", "fnb", True),
    ("room_service_fee", "Room-service fee", "fnb", True),
    ("laundry", "Laundry", "other", True),
    ("spa", "Spa", "other", True),
    ("minibar", "Minibar", "other", True),
    ("transport", "Transport", "other", True),
    ("activities", "Activities", "other", True),
    ("extra_bed", "Extra bed", "other", True),
    ("other_services", "Other services", "other", True),
    ("tip", "Tip", "tip", False),
    ("payment", "Payment", "payment", False),
]

# PLACEHOLDERS: prices and limits are not in the specs (DECISIONS.md). Change them through a
# later migration or the admin plan catalogue once they are decided.
PLANS = [
    ("starter", "Starter", {"rooms": 50, "devices": 60, "staff": 40, "api_keys": 2}),
    ("professional", "Professional", {"rooms": 250, "devices": 300, "staff": 150, "api_keys": 5}),
    ("enterprise", "Enterprise", {"rooms": 2000, "devices": 2400, "staff": 1000, "api_keys": 20}),
]


def _q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    values = [f"({_q(c)}, 'hotel', {_q(d)}, {str(s).lower()})" for c, (s, d, _) in HOTEL_PERMISSIONS.items()]
    values += [f"({_q(c)}, 'platform', {_q(d)}, false)" for c, d in PLATFORM_PERMISSIONS.items()]
    op.execute("INSERT INTO app.permissions (code, scope, description, sensitive) VALUES " + ", ".join(values))

    roles = [f"({_q(c)}, {_q(n)}, true)" for c, n in HOTEL_ROLES]
    roles += [f"({_q(c)}, {_q(n)}, true)" for c, (n, _) in PLATFORM_ROLES.items()]
    op.execute("INSERT INTO app.roles (code, name, is_system) VALUES " + ", ".join(roles))

    pairs = [
        (role_code, perm)
        for perm, (_, _, flags) in HOTEL_PERMISSIONS.items()
        for (role_code, _), flag in zip(HOTEL_ROLES, flags, strict=True)
        if flag == "1"
    ]
    pairs += [(rc, p) for rc, (_, perms) in PLATFORM_ROLES.items() for p in perms]
    op.execute(
        "INSERT INTO app.role_permissions (role_id, permission_code) "
        "SELECT r.id, v.perm FROM (VALUES " + ", ".join(f"({_q(r)}, {_q(p)})" for r, p in pairs) + ") "
        "AS v(role_code, perm) JOIN app.roles r ON r.code = v.role_code AND r.hotel_id IS NULL"
    )

    cats = [f"({_q(c)}, {_q(n)}, {_q(g)}, {str(r).lower()})" for c, n, g, r in CHARGE_CATEGORIES]
    op.execute("INSERT INTO app.charge_categories (code, name, revenue_group, is_revenue) VALUES " + ", ".join(cats))

    plans = [
        f"({_q(c)}, {_q(n)}, 0, {_q(json.dumps(limits))}::jsonb, {_q(json.dumps({'placeholder': True}))}::jsonb)"
        for c, n, limits in PLANS
    ]
    op.execute("INSERT INTO app.plans (code, name, monthly_price_minor, limits, features) VALUES " + ", ".join(plans))


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM app.hotels) THEN
            RAISE EXCEPTION 'refusing to downgrade: hotels exist that depend on the catalogue';
          END IF;
        END $$;
        DELETE FROM app.plans;
        DELETE FROM app.charge_categories WHERE hotel_id IS NULL;
        DELETE FROM app.role_permissions;
        DELETE FROM app.roles WHERE hotel_id IS NULL;
        DELETE FROM app.permissions;
        """
    )
