"""account separation: Diyneco staff accounts and hotel accounts never mix

DECISIONS D75 (owner's instruction of 2026-10-12: no admin account signs in to a hotel app
and the other way round, with no bypass).
- An account's kind (users.is_platform) is fixed when it is created and can never change.
- A Diyneco staff account can never become a member of a hotel (hotel_users).
The API enforces the same at sign-in (separate endpoints per kind) and on every route
(platform permissions only for platform principals, hotel permissions never for them).

Revision ID: 0027
Revises: 0026
Create Date: 2026-10-12 12:00
"""

from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION app.users_kind_fixed() RETURNS trigger
        LANGUAGE plpgsql SET search_path = app, extensions, pg_temp AS $$
        BEGIN
          IF NEW.is_platform IS DISTINCT FROM OLD.is_platform THEN
            RAISE EXCEPTION 'an account cannot change between Diyneco staff and hotel staff'
              USING ERRCODE = 'insufficient_privilege';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER users_kind_fixed BEFORE UPDATE OF is_platform ON app.users
          FOR EACH ROW EXECUTE FUNCTION app.users_kind_fixed();

        CREATE FUNCTION app.hotel_users_not_platform() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
        BEGIN
          IF EXISTS (SELECT 1 FROM app.users WHERE id = NEW.user_id AND is_platform) THEN
            RAISE EXCEPTION 'a Diyneco staff account cannot be a member of a hotel'
              USING ERRCODE = 'insufficient_privilege';
          END IF;
          RETURN NEW;
        END $$;
        REVOKE ALL ON FUNCTION app.hotel_users_not_platform() FROM PUBLIC;
        CREATE TRIGGER hotel_users_not_platform BEFORE INSERT OR UPDATE OF user_id ON app.hotel_users
          FOR EACH ROW EXECUTE FUNCTION app.hotel_users_not_platform();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS hotel_users_not_platform ON app.hotel_users;
        DROP FUNCTION IF EXISTS app.hotel_users_not_platform();
        DROP TRIGGER IF EXISTS users_kind_fixed ON app.users;
        DROP FUNCTION IF EXISTS app.users_kind_fixed();
        """
    )
