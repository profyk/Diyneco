"""onboarding: operational countries, emailed sign-up codes and hotel profile details

DECISIONS D84 (user request).
- operational_countries: the countries where new hotels can sign up, chosen by Diyneco staff
  with platform.countries.manage (control plane: no hotel, so no RLS). Seeded with South
  Africa and every country that already has a hotel, so nothing that works today stops.
- one_time_tokens: purpose 'email_code' (a 6-digit code emailed at sign-up, entered in the
  form), with an attempts counter (5 wrong tries end a code) and created_at (resend throttle).
- hotels.property_type, hotels.room_count and hotels.website; users.phone (the owner's
  mobile, for account and billing contact).
New permission platform.countries.manage for the Super Admin.

Revision ID: 0033
Revises: 0032
Create Date: 2026-10-15 10:00
"""

from alembic import op

import alembic_helpers as h

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None

PROPERTY_TYPES = (
    "'hotel','boutique_hotel','resort','lodge','guest_house','bed_and_breakfast',"
    "'serviced_apartments','hostel','other'"
)


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        f"""
        CREATE TABLE app.operational_countries (
          country     char(2) PRIMARY KEY CHECK (country ~ '^[A-Z]{{2}}$'),
          enabled_at  timestamptz NOT NULL DEFAULT now(),
          enabled_by  uuid REFERENCES app.users(id)
        );
        INSERT INTO app.operational_countries (country)
          SELECT 'ZA' UNION SELECT DISTINCT country FROM app.hotels;

        ALTER TABLE app.one_time_tokens DROP CONSTRAINT one_time_tokens_purpose_check;
        ALTER TABLE app.one_time_tokens
          ADD CONSTRAINT one_time_tokens_purpose_check
            CHECK (purpose IN ('password_reset','email_verify','platform_invite','email_code')),
          ADD COLUMN attempts   smallint NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 10),
          ADD COLUMN created_at timestamptz NOT NULL DEFAULT now();
        CREATE INDEX one_time_tokens_user_purpose ON app.one_time_tokens (user_id, purpose, created_at DESC);

        ALTER TABLE app.hotels
          ADD COLUMN property_type text CHECK (property_type IN ({PROPERTY_TYPES})),
          ADD COLUMN room_count    integer CHECK (room_count BETWEEN 1 AND 5000),
          ADD COLUMN website       text CHECK (website ~ '^https?://[^\\s]+$' AND length(website) <= 200);
        ALTER TABLE app.users
          ADD COLUMN phone text CHECK (phone ~ '^\\+[0-9]{{6,15}}$');

        -- Hotels per country for the admin panel (hotels are tenant rows: a narrow definer).
        CREATE FUNCTION app.admin_country_counts()
        RETURNS TABLE (country char(2), hotels bigint, active bigint)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT h.country, count(*), count(*) FILTER (WHERE h.status = 'active')
          FROM app.hotels h GROUP BY h.country
        $$;
        REVOKE ALL ON FUNCTION app.admin_country_counts() FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.admin_country_counts() TO diyneco_api;

        INSERT INTO app.permissions (code, scope, description, sensitive) VALUES
          ('platform.countries.manage', 'platform', 'Choose the countries where new hotels can sign up', true);
        INSERT INTO app.role_permissions (role_id, permission_code)
          SELECT r.id, 'platform.countries.manage' FROM app.roles r
          WHERE r.hotel_id IS NULL AND r.code = 'platform_super_admin';
        """
    )
    op.execute("GRANT DELETE ON app.operational_countries TO diyneco_api")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        DELETE FROM app.role_permissions WHERE permission_code = 'platform.countries.manage';
        DELETE FROM app.permissions WHERE code = 'platform.countries.manage';
        DROP FUNCTION app.admin_country_counts();
        ALTER TABLE app.users DROP COLUMN phone;
        ALTER TABLE app.hotels DROP COLUMN website, DROP COLUMN room_count, DROP COLUMN property_type;
        DROP INDEX app.one_time_tokens_user_purpose;
        DELETE FROM app.one_time_tokens WHERE purpose = 'email_code';
        ALTER TABLE app.one_time_tokens DROP CONSTRAINT one_time_tokens_purpose_check;
        ALTER TABLE app.one_time_tokens
          DROP COLUMN created_at,
          DROP COLUMN attempts,
          ADD CONSTRAINT one_time_tokens_purpose_check
            CHECK (purpose IN ('password_reset','email_verify','platform_invite'));
        """
    )
    h.drop_tables("operational_countries")
