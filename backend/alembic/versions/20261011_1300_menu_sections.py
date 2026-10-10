"""menu sections: Food and Drinks above categories; each category routes to a kitchen station

- menu_categories.section ('food' or 'drinks') gives the menu its top level, so tablets show
  Food and Drinks and then their categories (Starters, Mains... Coffees, Wines, MCC...).
- menu_categories.default_station_id is where the category's dishes are prepared (Bar, Pastry,
  Main kitchen...); new and imported items follow it. DECISIONS D68.

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-11 13:00
"""

from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app.menu_categories
          ADD COLUMN section text NOT NULL DEFAULT 'food'
            CONSTRAINT menu_categories_section_check CHECK (section IN ('food', 'drinks')),
          ADD COLUMN default_station_id uuid REFERENCES app.kitchen_stations(id);
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE app.menu_categories DROP COLUMN IF EXISTS default_station_id, "
        "DROP COLUMN IF EXISTS section"
    )
