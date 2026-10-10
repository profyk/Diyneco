"""reports and integrations: API key lookup, due webhook deliveries, admin analytics

An API key arrives before any hotel is known, so it is resolved through one narrow definer
function (like app.device_lookup). The worker finds due webhook deliveries across hotels the
same way, then works each one under its hotel's context. Admin analytics is an aggregate.
(DECISIONS D50, D51.)

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-10 12:00
"""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION app.api_key_lookup(p_secret_hash bytea)
        RETURNS TABLE (key_id uuid, hotel_id uuid)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT k.id, k.hotel_id FROM app.api_keys k
          WHERE k.secret_hash = p_secret_hash AND k.revoked_at IS NULL
        $$;
        REVOKE ALL ON FUNCTION app.api_key_lookup(bytea) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.api_key_lookup(bytea) TO diyneco_api;

        CREATE INDEX webhook_deliveries_due ON app.webhook_deliveries(next_attempt_at)
          WHERE next_attempt_at IS NOT NULL;

        CREATE FUNCTION app.webhook_due(p_limit integer)
        RETURNS TABLE (delivery_id uuid, hotel_id uuid)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT d.id, d.hotel_id FROM app.webhook_deliveries d
          WHERE d.next_attempt_at IS NOT NULL AND d.next_attempt_at <= now()
          ORDER BY d.next_attempt_at
          LIMIT p_limit
        $$;
        REVOKE ALL ON FUNCTION app.webhook_due(integer) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.webhook_due(integer) TO diyneco_worker;

        CREATE FUNCTION app.hotels_for_jobs()
        RETURNS TABLE (hotel_id uuid, timezone text)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT h.id, hs.timezone FROM app.hotels h JOIN app.hotel_settings hs ON hs.hotel_id = h.id
          WHERE h.status = 'active'
        $$;
        REVOKE ALL ON FUNCTION app.hotels_for_jobs() FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.hotels_for_jobs() TO diyneco_worker;

        CREATE FUNCTION app.admin_analytics(p_days integer)
        RETURNS TABLE (day date, orders bigint, new_hotels bigint, checkins bigint)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          WITH days AS (
            SELECT generate_series(
              (now() AT TIME ZONE 'Africa/Johannesburg')::date - (p_days - 1),
              (now() AT TIME ZONE 'Africa/Johannesburg')::date, interval '1 day')::date AS day
          )
          SELECT d.day,
            (SELECT count(*) FROM app.orders o
               WHERE (o.created_at AT TIME ZONE 'Africa/Johannesburg')::date = d.day),
            (SELECT count(*) FROM app.hotels h
               WHERE (h.created_at AT TIME ZONE 'Africa/Johannesburg')::date = d.day),
            (SELECT count(*) FROM app.stays s
               WHERE (s.checked_in_at AT TIME ZONE 'Africa/Johannesburg')::date = d.day
                 AND NOT s.is_training)
          FROM days d ORDER BY d.day
        $$;
        REVOKE ALL ON FUNCTION app.admin_analytics(integer) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.admin_analytics(integer) TO diyneco_api, diyneco_platform;

        -- Production API keys need plan support (security spec, Credentials). Placeholder
        -- plans: Professional and Enterprise include them.
        UPDATE app.plans SET features = features || '{"api_production_keys": true}'
        WHERE code IN ('professional', 'enterprise');
        """
    )


def downgrade() -> None:
    op.execute("UPDATE app.plans SET features = features - 'api_production_keys'")
    op.execute("DROP FUNCTION IF EXISTS app.admin_analytics(integer)")
    op.execute("DROP FUNCTION IF EXISTS app.hotels_for_jobs()")
    op.execute("DROP FUNCTION IF EXISTS app.webhook_due(integer)")
    op.execute("DROP INDEX IF EXISTS app.webhook_deliveries_due")
    op.execute("DROP FUNCTION IF EXISTS app.api_key_lookup(bytea)")
