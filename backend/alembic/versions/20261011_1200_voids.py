"""voids: cancel single order lines; kitchen staff mark items sold out

- order_items gain voided_at, voided_by and void_reason (a voided line leaves the kitchen ticket
  and the order total; its bill charge is reversed).
- folio_entries gain order_item_id so a voided line's own charge can be reversed exactly. The
  table stays append-only: this adds a nullable column, existing rows are not changed.
- (User decision) the built-in Kitchen Staff role may mark menu items sold out
  (`menu.availability`), and read the menu to do so (`menu.read`). DECISIONS D67.

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-11 12:00
"""

from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

KITCHEN_STAFF_GRANTS = ("menu.availability", "menu.read")
TRANSITIONS = """
CREATE OR REPLACE FUNCTION app.order_transition_allowed(f text, t text) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT (f, t) IN (VALUES
    ('PENDING_APPROVAL','NEW'), ('PENDING_APPROVAL','DECLINED'),
    ('NEW','ACCEPTED'), ('NEW','CANCELLED'), ('ACCEPTED','PREPARING'), ('ACCEPTED','CANCELLED'),
    ('PREPARING','READY'), ('READY','ASSIGNED'), ('ASSIGNED','READY'),
    ('ASSIGNED','PICKED_UP'), ('PICKED_UP','DELIVERED'), ('DELIVERED','CLOSED'){extra})
$$;
"""


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app.order_items
          ADD COLUMN voided_at timestamptz,
          ADD COLUMN voided_by uuid REFERENCES app.users(id),
          ADD COLUMN void_reason text,
          ADD CONSTRAINT order_items_void_check CHECK ((voided_at IS NULL) = (void_reason IS NULL));
        ALTER TABLE app.folio_entries ADD COLUMN order_item_id uuid REFERENCES app.order_items(id);
        """
    )
    # (User decision) management may cancel an order until it is delivered, not only before
    # preparation. Paid orders are refused by the API and corrected with an adjustment.
    op.execute(TRANSITIONS.format(extra=", ('PREPARING','CANCELLED'), ('READY','CANCELLED'), "
                                       "('ASSIGNED','CANCELLED'), ('PICKED_UP','CANCELLED')"))
    for code in KITCHEN_STAFF_GRANTS:
        op.execute(
            "INSERT INTO app.role_permissions (role_id, permission_code) "
            "SELECT r.id, '" + code + "' FROM app.roles r "  # noqa: S608 - constant codes
            "WHERE r.hotel_id IS NULL AND r.code = 'kitchen_staff' ON CONFLICT DO NOTHING"
        )


def downgrade() -> None:
    op.execute(TRANSITIONS.format(extra=""))
    for code in KITCHEN_STAFF_GRANTS:
        op.execute(
            "DELETE FROM app.role_permissions WHERE permission_code = '" + code + "' "  # noqa: S608
            "AND role_id IN (SELECT id FROM app.roles WHERE hotel_id IS NULL AND code = 'kitchen_staff')"
        )
    op.execute("ALTER TABLE app.folio_entries DROP COLUMN IF EXISTS order_item_id")
    op.execute(
        "ALTER TABLE app.order_items DROP CONSTRAINT IF EXISTS order_items_void_check, "
        "DROP COLUMN IF EXISTS void_reason, DROP COLUMN IF EXISTS voided_by, DROP COLUMN IF EXISTS voided_at"
    )
