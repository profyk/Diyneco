"""foundation: schemas, extensions, grants and shared functions

Revision ID: 0001
Revises:
Create Date: 2026-10-08 17:00
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute("CREATE SCHEMA IF NOT EXISTS extensions")
    op.execute("GRANT USAGE ON SCHEMA extensions TO diyneco_api, diyneco_worker")
    for ext in ("pgcrypto", "citext", "pg_trgm", "btree_gin"):
        op.execute(f"CREATE EXTENSION IF NOT EXISTS {ext} WITH SCHEMA extensions")

    op.execute("CREATE SCHEMA app")
    op.execute("REVOKE ALL ON SCHEMA app FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA app TO diyneco_api, diyneco_worker")
    # Supabase default roles must never reach schema app.
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
            EXECUTE 'REVOKE ALL ON SCHEMA app FROM anon, authenticated';
            EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE ALL ON TABLES FROM anon, authenticated';
          END IF;
        END $$
        """
    )
    # Every new table: SELECT + INSERT for the app roles. UPDATE is granted per table
    # (alembic_helpers.mutable); DELETE only where a table needs it.
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE diyneco_owner IN SCHEMA app "
        "GRANT SELECT, INSERT ON TABLES TO diyneco_api, diyneco_worker"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE diyneco_owner IN SCHEMA app "
        "GRANT USAGE, SELECT ON SEQUENCES TO diyneco_api, diyneco_worker"
    )

    op.execute(
        """
        -- Time-ordered UUID (RFC 9562 version 7)
        CREATE FUNCTION app.uuid_v7() RETURNS uuid LANGUAGE plpgsql VOLATILE AS $$
        DECLARE
          ts bigint := floor(extract(epoch FROM clock_timestamp()) * 1000);
          b  bytea  := extensions.gen_random_bytes(16);
        BEGIN
          b := set_byte(b, 0, ((ts >> 40) & 255)::int);
          b := set_byte(b, 1, ((ts >> 32) & 255)::int);
          b := set_byte(b, 2, ((ts >> 24) & 255)::int);
          b := set_byte(b, 3, ((ts >> 16) & 255)::int);
          b := set_byte(b, 4, ((ts >> 8)  & 255)::int);
          b := set_byte(b, 5, (ts & 255)::int);
          b := set_byte(b, 6, (get_byte(b, 6) & 15) | 112);   -- version 7
          b := set_byte(b, 8, (get_byte(b, 8) & 63) | 128);   -- RFC variant
          RETURN encode(b, 'hex')::uuid;
        END $$;

        CREATE FUNCTION app.current_hotel_id() RETURNS uuid LANGUAGE sql STABLE AS $$
          SELECT nullif(current_setting('app.hotel_id', true), '')::uuid
        $$;

        CREATE FUNCTION app.forbid_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'table % is append-only', TG_TABLE_NAME USING ERRCODE = 'P0001';
        END $$;

        CREATE FUNCTION app.set_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          NEW.updated_at := now();
          RETURN NEW;
        END $$;

        -- References to tables that mix system rows (hotel_id NULL) and hotel rows
        -- (roles, charge_categories): the target must be a system row or the same hotel.
        -- TG_ARGV[0] = referenced table, TG_ARGV[1] = referencing column.
        CREATE FUNCTION app.check_shared_ref() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE
          ref_id    uuid := (to_jsonb(NEW) ->> TG_ARGV[1])::uuid;
          ref_found boolean;
          ref_hotel uuid;
        BEGIN
          IF ref_id IS NULL THEN
            RETURN NEW;
          END IF;
          EXECUTE format('SELECT true, hotel_id FROM app.%I WHERE id = $1', TG_ARGV[0])
            INTO ref_found, ref_hotel USING ref_id;
          IF ref_found IS NULL OR (ref_hotel IS NOT NULL AND ref_hotel IS DISTINCT FROM NEW.hotel_id) THEN
            RAISE EXCEPTION '%.% must reference a system row or a row of the same hotel',
              TG_TABLE_NAME, TG_ARGV[1] USING ERRCODE = '23503';
          END IF;
          RETURN NEW;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute("DROP SCHEMA app CASCADE")
    for ext in ("btree_gin", "pg_trgm", "citext", "pgcrypto"):
        op.execute(f"DROP EXTENSION IF EXISTS {ext}")
