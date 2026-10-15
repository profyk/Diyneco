"""admin analytics: aggregate facts for the platform's adoption, revenue and owner views (D87)

Narrow SECURITY DEFINER functions over tenant tables, like app.admin_hotels(): they return
per-hotel and per-owner aggregates only, never guest data, and only diyneco_api may call
them (the admin routes check platform permissions).
- admin_hotel_facts(): location, category, plan and price, usage (rooms, staff, devices,
  orders) and money processed in the last 30 days in the hotel's currency.
- admin_owner_facts(): each Hotel Owner with their hotels.
- admin_subscription_history(): every subscription's status and dates, for MRR, churn,
  conversion and cohorts.
- admin_user_activity(): staff accounts and how many signed in within 7 and 30 days.

Revision ID: 0035
Revises: 0034
Create Date: 2026-10-15 16:00
"""

from alembic import op

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None

FUNCTIONS = (
    "admin_hotel_facts()",
    "admin_owner_facts()",
    "admin_subscription_history()",
    "admin_user_activity()",
)


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE FUNCTION app.admin_hotel_facts()
        RETURNS TABLE (
          id uuid, name text, code text, status text, created_at timestamptz,
          country char(2), province_code text, province text, city text,
          property_type text, declared_rooms integer, currency char(3),
          rooms bigint, staff bigint, devices bigint,
          sub_status text, plan_code text, plan_name text, sub_interval text,
          sub_amount_minor bigint, sub_currency char(3), trial_ends_on date,
          owner_verified boolean, first_order_at timestamptz, last_order_at timestamptz,
          orders_30d bigint, gmv_30d_minor bigint
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT h.id, h.name, h.code, h.status, h.created_at,
            h.country, h.address->>'province_code', h.address->>'province', h.address->>'city',
            h.property_type, h.room_count, hs.currency,
            (SELECT count(*) FROM app.rooms r WHERE r.hotel_id = h.id AND r.deleted_at IS NULL),
            (SELECT count(*) FROM app.hotel_users u WHERE u.hotel_id = h.id AND u.status = 'active'),
            (SELECT count(*) FROM app.devices d WHERE d.hotel_id = h.id AND d.status <> 'revoked'),
            s.status, p.code, p.name, s.interval, s.amount_minor, s.currency, s.trial_ends_on,
            EXISTS (
              SELECT 1 FROM app.hotel_users hu
              JOIN app.user_roles ur ON ur.hotel_user_id = hu.id
              JOIN app.roles r ON r.id = ur.role_id AND r.code = 'hotel_owner'
              JOIN app.users us ON us.id = hu.user_id
              WHERE hu.hotel_id = h.id AND us.email_verified_at IS NOT NULL
            ),
            (SELECT min(o.created_at) FROM app.orders o WHERE o.hotel_id = h.id),
            (SELECT max(o.created_at) FROM app.orders o WHERE o.hotel_id = h.id),
            (SELECT count(*) FROM app.orders o WHERE o.hotel_id = h.id AND o.created_at > now() - interval '30 days'),
            (SELECT coalesce(sum(fe.amount_minor), 0) FROM app.folio_entries fe
               JOIN app.charge_categories c ON c.id = fe.category_id
               JOIN app.folios f ON f.id = fe.folio_id
               WHERE fe.hotel_id = h.id
                 AND fe.entry_type IN ('charge', 'reversal', 'adjustment', 'discount')
                 AND c.revenue_group IN ('accommodation', 'fnb', 'other')
                 AND fe.business_date > current_date - 30
                 AND NOT EXISTS (SELECT 1 FROM app.stays st WHERE st.id = f.stay_id AND st.is_training))
          FROM app.hotels h
          JOIN app.hotel_settings hs ON hs.hotel_id = h.id
          LEFT JOIN app.subscriptions s ON s.hotel_id = h.id
            AND s.status IN ('trial', 'pending_payment', 'active', 'past_due', 'suspended', 'cancellation_scheduled')
          LEFT JOIN app.plans p ON p.id = s.plan_id
        $$;

        CREATE FUNCTION app.admin_owner_facts()
        RETURNS TABLE (
          user_id uuid, name text, email text, phone text, created_at timestamptz,
          last_login_at timestamptz, email_verified boolean, hotel_ids uuid[]
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT u.id, u.name, u.email::text, u.phone, u.created_at, u.last_login_at,
                 u.email_verified_at IS NOT NULL, array_agg(hu.hotel_id ORDER BY hu.created_at)
          FROM app.users u
          JOIN app.hotel_users hu ON hu.user_id = u.id AND hu.status = 'active'
          JOIN app.user_roles ur ON ur.hotel_user_id = hu.id
          JOIN app.roles r ON r.id = ur.role_id AND r.code = 'hotel_owner'
          GROUP BY u.id
        $$;

        CREATE FUNCTION app.admin_subscription_history()
        RETURNS TABLE (
          hotel_id uuid, status text, paid boolean, starts_on date, ended_on date,
          trial_ends_on date, sub_interval text, amount_minor bigint, currency char(3)
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT s.hotel_id, s.status, s.plan_id IS NOT NULL, s.starts_on, s.ended_on,
                 s.trial_ends_on, s.interval, s.amount_minor, s.currency
          FROM app.subscriptions s
        $$;

        CREATE FUNCTION app.admin_user_activity()
        RETURNS TABLE (role_code text, members bigint, active_7d bigint, active_30d bigint)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          WITH last_seen AS (
            SELECT user_id, max(last_used_at) AS at FROM app.sessions GROUP BY user_id
          )
          SELECT r.code, count(DISTINCT hu.user_id),
                 count(DISTINCT hu.user_id) FILTER (WHERE ls.at > now() - interval '7 days'),
                 count(DISTINCT hu.user_id) FILTER (WHERE ls.at > now() - interval '30 days')
          FROM app.hotel_users hu
          JOIN app.user_roles ur ON ur.hotel_user_id = hu.id
          JOIN app.roles r ON r.id = ur.role_id
          LEFT JOIN last_seen ls ON ls.user_id = hu.user_id
          WHERE hu.status = 'active'
          GROUP BY r.code
        $$;
        """
    )
    for fn in FUNCTIONS:
        op.execute(f"REVOKE ALL ON FUNCTION app.{fn} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION app.{fn} TO diyneco_api")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    for fn in FUNCTIONS:
        op.execute(f"DROP FUNCTION IF EXISTS app.{fn}")
