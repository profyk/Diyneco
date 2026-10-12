"""international: country required, data region, locale and tax label per hotel

docs/ARCHITECTURE-GLOBAL.md, DECISIONS D69.
- hotels.country loses its 'ZA' default: signup must state the country.
- hotels.data_region names the regional data cell holding the hotel's data; it comes from the
  country at signup and does not change (moving a hotel is an operator procedure).
- hotel_settings.locale (BCP 47) drives formatting and, later, the interface language.
- hotel_settings.tax_label is what invoices and screens call the tax (VAT, GST, IVA...).
Existing hotels (all South African so far) get af-south, en-ZA and VAT.

Revision ID: 0022
Revises: 0021
Create Date: 2026-10-11 14:00
"""

from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app.hotels ALTER COLUMN country DROP DEFAULT;
        ALTER TABLE app.hotels ADD COLUMN data_region text;
        UPDATE app.hotels SET data_region = 'af-south';
        ALTER TABLE app.hotels
          ALTER COLUMN data_region SET NOT NULL,
          ADD CONSTRAINT hotels_data_region_check
            CHECK (data_region IN ('af-south', 'eu-west', 'me-central', 'ap-southeast', 'us-east')),
          ADD CONSTRAINT hotels_country_check CHECK (country ~ '^[A-Z]{2}$');

        ALTER TABLE app.hotel_settings
          ADD COLUMN locale text NOT NULL DEFAULT 'en-ZA'
            CONSTRAINT hotel_settings_locale_check CHECK (locale ~ '^[a-z]{2,3}(-[A-Z]{2})?$'),
          ADD COLUMN tax_label text NOT NULL DEFAULT 'VAT'
            CONSTRAINT hotel_settings_tax_label_check CHECK (length(tax_label) BETWEEN 1 AND 30);
        ALTER TABLE app.hotel_settings ALTER COLUMN locale DROP DEFAULT, ALTER COLUMN tax_label DROP DEFAULT;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE app.hotel_settings DROP COLUMN IF EXISTS tax_label, DROP COLUMN IF EXISTS locale;
        ALTER TABLE app.hotels DROP CONSTRAINT IF EXISTS hotels_country_check,
          DROP CONSTRAINT IF EXISTS hotels_data_region_check, DROP COLUMN IF EXISTS data_region;
        ALTER TABLE app.hotels ALTER COLUMN country SET DEFAULT 'ZA';
        """
    )
