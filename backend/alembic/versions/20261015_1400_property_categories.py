"""property categories: the full list of property types a hotel can choose (D85)

Adds motel, inn, aparthotel, holiday home, country house and camp or glamping to the types
of D84, and an index for the admin panel's adoption reports by country and type.

Revision ID: 0034
Revises: 0033
Create Date: 2026-10-15 14:00
"""

from alembic import op

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None

OLD = (
    "'hotel','boutique_hotel','resort','lodge','guest_house','bed_and_breakfast',"
    "'serviced_apartments','hostel','other'"
)
NEW = (
    "'hotel','boutique_hotel','resort','motel','inn','lodge','guest_house','bed_and_breakfast',"
    "'aparthotel','serviced_apartments','holiday_home','country_house','hostel','camp','other'"
)


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        f"""
        ALTER TABLE app.hotels DROP CONSTRAINT hotels_property_type_check;
        ALTER TABLE app.hotels ADD CONSTRAINT hotels_property_type_check CHECK (property_type IN ({NEW}));
        CREATE INDEX hotels_country_type ON app.hotels (country, property_type);
        """
    )


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        f"""
        DROP INDEX app.hotels_country_type;
        UPDATE app.hotels SET property_type = 'other' WHERE property_type NOT IN ({OLD});
        ALTER TABLE app.hotels DROP CONSTRAINT hotels_property_type_check;
        ALTER TABLE app.hotels ADD CONSTRAINT hotels_property_type_check CHECK (property_type IN ({OLD}));
        """
    )
