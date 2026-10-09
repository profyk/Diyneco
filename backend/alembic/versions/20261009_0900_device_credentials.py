"""device credentials: lookup function and index

A tablet exchanges its device credential for a 1-hour device token before any hotel is
known (security spec, Credentials), so the lookup goes through one narrow definer function,
like app.redeem_pairing. It returns only ids; the API then works under that hotel's context.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-09 09:00
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CONCURRENTLY cannot run inside a transaction (DECISIONS G15).
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS devices_credential "
            "ON app.devices(credential_hash) WHERE credential_hash IS NOT NULL"
        )
    op.execute(
        """
        CREATE FUNCTION app.device_lookup(p_credential_hash bytea)
        RETURNS TABLE (device_id uuid, hotel_id uuid)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT d.id, d.hotel_id FROM app.devices d
          WHERE d.credential_hash = p_credential_hash AND d.status <> 'revoked'
        $$;
        REVOKE ALL ON FUNCTION app.device_lookup(bytea) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.device_lookup(bytea) TO diyneco_api;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS app.device_lookup(bytea)")
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS app.devices_credential")
