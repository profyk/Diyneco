"""ingredients: what a menu item is made of, shown to guests

Guests ask what is in a dish beyond the 14 declared allergens (DECISIONS D66). At most 40
ingredients of up to 60 characters each.

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-11 11:00
"""

from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app.menu_items
          ADD COLUMN ingredients text[] NOT NULL DEFAULT '{}'
          CONSTRAINT menu_items_ingredients_check CHECK (cardinality(ingredients) <= 40);
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE app.menu_items DROP COLUMN IF EXISTS ingredients")
