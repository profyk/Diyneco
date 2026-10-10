"""platform admin: support grants and the narrow definer functions admin endpoints use

Platform requests carry no hotel, so RLS hides every tenant row (guests, stays, folios) from
them. What the admin panel needs across hotels comes only through the SECURITY DEFINER
functions below, which return aggregates and never a guest field (API spec: platform admin
endpoints return aggregates rather than guest records). Plans and feature flags are
read-only for the app roles (G7), so their writes also go through definer functions.
Writes to one hotel (status, subscription, support grants) run under that hotel's context.
(DECISIONS D48, resolving G19.)

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-10 09:00
"""

import alembic_helpers as h
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

CONNECTED_WITHIN = "interval '5 minutes'"

FUNCTIONS = (
    "app.admin_hotels()",
    "app.admin_metrics(date, date)",
    "app.admin_outbox_health()",
    "app.admin_flags()",
    "app.admin_set_flag(text, uuid, boolean, uuid)",
    "app.admin_create_plan(text, text, bigint, char, jsonb, jsonb)",
    "app.admin_hotel_exists(uuid)",
    "app.admin_platform_events(timestamptz)",
)


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE app.support_grants (
          id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id          uuid NOT NULL REFERENCES app.hotels(id),
          platform_user_id  uuid NOT NULL REFERENCES app.users(id),
          ticket_reference  text NOT NULL CHECK (length(ticket_reference) BETWEEN 3 AND 60),
          reason            text,
          starts_at         timestamptz NOT NULL DEFAULT now(),
          expires_at        timestamptz NOT NULL,
          revoked_at        timestamptz,
          revoked_by        uuid REFERENCES app.users(id),
          CHECK (expires_at > starts_at AND expires_at <= starts_at + interval '60 minutes')
        );
        CREATE INDEX support_grants_hotel ON app.support_grants(hotel_id, expires_at DESC);
        """
    )
    h.tenant_rls("support_grants")
    h.mutable("support_grants")

    op.execute(
        f"""
        CREATE FUNCTION app.admin_hotels()
        RETURNS TABLE (
          id uuid, name text, slug text, status text, status_reason text, created_at timestamptz,
          plan_code text, subscription_status text, renews_on date,
          rooms bigint, devices bigint, connected_devices bigint, staff bigint, active_stays bigint,
          last_activity timestamptz
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT h.id, h.name, h.slug, h.status, h.status_reason, h.created_at,
            p.code, s.status, s.renews_on,
            (SELECT count(*) FROM app.rooms r WHERE r.hotel_id = h.id AND r.deleted_at IS NULL),
            (SELECT count(*) FROM app.devices d WHERE d.hotel_id = h.id AND d.status <> 'revoked'),
            (SELECT count(*) FROM app.devices d WHERE d.hotel_id = h.id AND d.status <> 'revoked'
               AND d.last_seen_at > now() - {CONNECTED_WITHIN}),
            (SELECT count(*) FROM app.hotel_users u WHERE u.hotel_id = h.id AND u.status = 'active'),
            (SELECT count(*) FROM app.stays st WHERE st.hotel_id = h.id
               AND st.status IN ('checked_in','active','checkout_pending')),
            (SELECT max(e.created_at) FROM app.event_outbox e WHERE e.hotel_id = h.id)
          FROM app.hotels h
          LEFT JOIN app.subscriptions s ON s.hotel_id = h.id AND s.status IN ('trialing','active','past_due')
          LEFT JOIN app.plans p ON p.id = s.plan_id
          ORDER BY h.created_at DESC
        $$;

        CREATE FUNCTION app.admin_metrics(p_today date, p_month_start date)
        RETURNS TABLE (
          hotels bigint, active_hotels bigint, pending_hotels bigint, suspended_hotels bigint,
          rooms bigint, connected_devices bigint, active_stays bigint,
          orders_today bigint, orders_month bigint,
          mrr_minor bigint, active_subscriptions bigint, cancelled_this_month bigint
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT
            (SELECT count(*) FROM app.hotels),
            (SELECT count(*) FROM app.hotels WHERE status = 'active'),
            (SELECT count(*) FROM app.hotels WHERE status = 'pending_approval'),
            (SELECT count(*) FROM app.hotels WHERE status = 'suspended'),
            (SELECT count(*) FROM app.rooms WHERE deleted_at IS NULL),
            (SELECT count(*) FROM app.devices WHERE status <> 'revoked'
               AND last_seen_at > now() - {CONNECTED_WITHIN}),
            (SELECT count(*) FROM app.stays WHERE status IN ('checked_in','active','checkout_pending')),
            (SELECT count(*) FROM app.orders o JOIN app.hotel_settings hs ON hs.hotel_id = o.hotel_id
               WHERE (o.created_at AT TIME ZONE hs.timezone)::date = p_today),
            (SELECT count(*) FROM app.orders o JOIN app.hotel_settings hs ON hs.hotel_id = o.hotel_id
               WHERE (o.created_at AT TIME ZONE hs.timezone)::date >= p_month_start),
            (SELECT coalesce(sum(p.monthly_price_minor), 0)::bigint FROM app.subscriptions s
               JOIN app.plans p ON p.id = s.plan_id JOIN app.hotels h ON h.id = s.hotel_id
               WHERE s.status IN ('active','past_due') AND h.status = 'active'),
            (SELECT count(*) FROM app.subscriptions WHERE status IN ('active','past_due')),
            (SELECT count(*) FROM app.subscriptions WHERE status = 'cancelled'
               AND cancelled_at >= p_month_start)
        $$;

        CREATE FUNCTION app.admin_outbox_health()
        RETURNS TABLE (pending bigint, oldest_pending_seconds double precision)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT count(*), coalesce(extract(epoch FROM now() - min(created_at)), 0)
          FROM app.event_outbox WHERE published_at IS NULL
        $$;

        CREATE FUNCTION app.admin_flags()
        RETURNS TABLE (key text, hotel_id uuid, enabled boolean, updated_at timestamptz, updated_by uuid)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT f.key, f.hotel_id, f.enabled, f.updated_at, f.updated_by FROM app.feature_flags f
          ORDER BY f.key, f.hotel_id NULLS FIRST
        $$;

        CREATE FUNCTION app.admin_set_flag(p_key text, p_hotel uuid, p_enabled boolean, p_user uuid)
        RETURNS void
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          INSERT INTO app.feature_flags (key, hotel_id, enabled, updated_by)
          VALUES (p_key, p_hotel, p_enabled, p_user)
          ON CONFLICT (key, hotel_id) DO UPDATE
            SET enabled = EXCLUDED.enabled, updated_by = EXCLUDED.updated_by, updated_at = now()
        $$;

        CREATE FUNCTION app.admin_create_plan(
          p_code text, p_name text, p_price bigint, p_currency char, p_limits jsonb, p_features jsonb
        ) RETURNS uuid
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          INSERT INTO app.plans (code, name, monthly_price_minor, currency, limits, features)
          VALUES (p_code, p_name, p_price, p_currency, p_limits, p_features)
          RETURNING id
        $$;

        CREATE FUNCTION app.admin_platform_events(p_since timestamptz)
        RETURNS TABLE (
          id uuid, hotel_id uuid, seq bigint, type text, channels text[], payload jsonb,
          created_at timestamptz
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT e.id, e.hotel_id, e.seq, e.type, e.channels, e.payload, e.created_at
          FROM app.event_outbox e
          WHERE 'platform' = ANY (e.channels) AND e.created_at > p_since
            AND e.created_at > now() - interval '24 hours'
          ORDER BY e.created_at, e.id
          LIMIT 500
        $$;

        CREATE FUNCTION app.admin_hotel_exists(p_hotel uuid) RETURNS boolean
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT EXISTS (SELECT 1 FROM app.hotels WHERE id = p_hotel)
        $$;
        """
    )
    for fn in FUNCTIONS:
        op.execute(f"REVOKE ALL ON FUNCTION {fn} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {fn} TO diyneco_api, diyneco_platform")


def downgrade() -> None:
    for fn in FUNCTIONS:
        op.execute(f"DROP FUNCTION IF EXISTS {fn}")
    h.refuse_if_data("support_grants")
    h.drop_tables("support_grants")
