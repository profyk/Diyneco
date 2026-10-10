"""image variants: resized copies of menu item photos

The API spec says the server makes three sizes of each menu photo (D32 left this open). The
worker writes them and records their storage keys here: `{"source": <image_path>, "160": key,
"480": key, "1200": key}`, or `{"source": ..., "error": "invalid" | "missing"}` (DECISIONS D64).

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-11 09:00
"""

from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE app.menu_items ADD COLUMN image_variants jsonb")


def downgrade() -> None:
    op.execute("ALTER TABLE app.menu_items DROP COLUMN IF EXISTS image_variants")
