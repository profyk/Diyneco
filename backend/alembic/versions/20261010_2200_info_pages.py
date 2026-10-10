"""info pages: hotel information shown on guest tablets

The API spec's `GET /guest/info` returns "hotel information pages" but the database spec has no
place for them (D37 returned an empty list). They are short title-and-text pages kept on the
hotel's settings row, at most 20 and 64 KB in all (DECISIONS D61).

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-10 22:00
"""

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app.hotel_settings
          ADD COLUMN info_pages jsonb NOT NULL DEFAULT '[]'::jsonb
          CONSTRAINT hotel_settings_info_pages_check CHECK (
            jsonb_typeof(info_pages) = 'array'
            AND jsonb_array_length(info_pages) <= 20
            AND octet_length(info_pages::text) <= 65536
          );
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE app.hotel_settings DROP COLUMN IF EXISTS info_pages")
