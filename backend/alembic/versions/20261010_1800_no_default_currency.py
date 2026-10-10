"""no default currency; per-currency MRR; plans editable by the platform

Every hotel chooses its operating currency and every plan its billing currency, so no
column may fall back to a currency silently: the `DEFAULT 'ZAR'` on every `currency` column
is dropped and an insert without a currency now fails (DECISIONS D57). MRR is summed per
currency, and the platform can edit a plan (price and currency, limits, features, active)
through a definer function because plans are read-only for the app roles.

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-10 18:00
"""

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

CURRENCY_COLUMNS = """
  SELECT c.table_name FROM information_schema.columns c
  JOIN information_schema.tables t ON t.table_schema = c.table_schema AND t.table_name = c.table_name
  WHERE c.table_schema = 'app' AND c.column_name = 'currency' AND t.table_type = 'BASE TABLE'
"""


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        DECLARE r record;
        BEGIN
          FOR r IN {CURRENCY_COLUMNS} LOOP
            EXECUTE format('ALTER TABLE app.%I ALTER COLUMN currency DROP DEFAULT', r.table_name);
          END LOOP;
        END $$;

        CREATE FUNCTION app.admin_mrr()
        RETURNS TABLE (currency char(3), mrr_minor bigint, subscriptions bigint)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT p.currency, coalesce(sum(p.monthly_price_minor), 0)::bigint, count(*)
          FROM app.subscriptions s JOIN app.plans p ON p.id = s.plan_id JOIN app.hotels h ON h.id = s.hotel_id
          WHERE s.status IN ('active','past_due') AND h.status = 'active'
          GROUP BY p.currency ORDER BY p.currency
        $$;
        REVOKE ALL ON FUNCTION app.admin_mrr() FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.admin_mrr() TO diyneco_api, diyneco_platform;

        CREATE FUNCTION app.admin_update_plan(
          p_id uuid, p_name text, p_price bigint, p_currency char, p_limits jsonb, p_features jsonb,
          p_active boolean
        ) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          UPDATE app.plans SET
            name = coalesce(p_name, name),
            monthly_price_minor = coalesce(p_price, monthly_price_minor),
            currency = coalesce(p_currency, currency),
            limits = coalesce(p_limits, limits),
            features = coalesce(p_features, features),
            is_active = coalesce(p_active, is_active),
            updated_at = now()
          WHERE id = p_id
          RETURNING true
        $$;
        REVOKE ALL ON FUNCTION app.admin_update_plan(uuid, text, bigint, char, jsonb, jsonb, boolean) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.admin_update_plan(uuid, text, bigint, char, jsonb, jsonb, boolean)
          TO diyneco_api, diyneco_platform;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS app.admin_update_plan(uuid, text, bigint, char, jsonb, jsonb, boolean)")
    op.execute("DROP FUNCTION IF EXISTS app.admin_mrr()")
    op.execute(
        f"""
        DO $$
        DECLARE r record;
        BEGIN
          FOR r IN {CURRENCY_COLUMNS} LOOP
            EXECUTE format('ALTER TABLE app.%I ALTER COLUMN currency SET DEFAULT %L', r.table_name, 'ZAR');
          END LOOP;
        END $$;
        """
    )
