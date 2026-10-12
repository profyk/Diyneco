"""plans and pricing: plan lifecycle, details and a price history per billing interval

DECISIONS D74 (subscription billing brief of 2026-10-12, sections 3 and 4).
- plans gain descriptions, highlighted features for the pricing page, status (draft,
  published, archived) in place of is_active, display order, a recommended flag, setup fee,
  trial days, tax treatment (prices exclusive or inclusive of tax), support level, overage
  policy, upgrade and downgrade eligibility and a promotional discount. Only published plans can be subscribed to.
- plan_prices: the price of a plan for one billing interval (month, quarter, year), with an
  optional introductory price for a number of periods, from a moment on. The price in force
  is the latest row on or before now that was not withdrawn. Rows are append-only: a change is
  a new row with a reason and a policy for existing subscribers (new subscriptions only, or
  existing ones from their next renewal after notice). Only a row not yet in force can be
  withdrawn. Subscriptions and invoices will keep their own snapshot of the price (D75+).
- monthly_price_minor is dropped: a plan has no price outside plan_prices.
- billing_settings (one row): the notice before a price change reaches existing subscribers.
- The three seeded plans become drafts priced R499, R999 and R1,999 a month (owner's brief);
  no other interval is priced, and nothing is published until a Super Admin publishes it.
- Plans and prices stay read-only for the app roles (G7); writes go through definer functions.

Revision ID: 0026
Revises: 0025
Create Date: 2026-10-12 11:00
"""

import re

from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None

FUNCTIONS = (
    "app.admin_save_plan(uuid, jsonb)",
    "app.admin_add_plan_price(uuid, text, bigint, bigint, integer, timestamptz, text, integer, text, uuid)",
    "app.admin_withdraw_plan_price(uuid)",
    "app.admin_mrr()",
)
METRICS = "app.admin_metrics(date, date)"
# admin_metrics summed the dropped monthly price; its MRR now comes from admin_mrr (one currency
# per row there; this total is kept only for the function's shape and is not shown anywhere).
OLD_MRR = (
    r"\(SELECT coalesce\(sum\(p\.monthly_price_minor\), 0\)::bigint FROM app\.subscriptions s\s+"
    r"JOIN app\.plans p ON p\.id = s\.plan_id JOIN app\.hotels h ON h\.id = s\.hotel_id\s+"
    r"WHERE s\.status IN \('active','past_due'\) AND h\.status = 'active'\)"
)
NEW_MRR = "(SELECT coalesce(sum(m.mrr_minor), 0)::bigint FROM app.admin_mrr() m)"
RESTORED_MRR = (
    "(SELECT coalesce(sum(p.monthly_price_minor), 0)::bigint FROM app.subscriptions s "
    "JOIN app.plans p ON p.id = s.plan_id JOIN app.hotels h ON h.id = s.hotel_id "
    "WHERE s.status IN ('active','past_due') AND h.status = 'active')"
)
# Columns admin_save_plan may set from its jsonb argument, with their cast.
SAVE_COLUMNS = (
    ("name", "->>", ""),
    ("currency", "->>", ""),
    ("short_description", "->>", ""),
    ("description", "->>", ""),
    ("highlights", "->", ""),
    ("status", "->>", ""),
    ("display_order", "->>", "::int"),
    ("recommended", "->>", "::boolean"),
    ("setup_fee_minor", "->>", "::bigint"),
    ("trial_days", "->>", "::int"),
    ("tax_treatment", "->>", ""),
    ("support_level", "->>", ""),
    ("overage_policy", "->>", ""),
    ("can_upgrade", "->>", "::boolean"),
    ("can_downgrade", "->>", "::boolean"),
    ("promo_discount_bp", "->>", "::int"),
    ("promo_ends_on", "->>", "::date"),
    ("limits", "->", ""),
    ("features", "->", ""),
)
SAVE_SET = "\n            ".join(
    f"{c} = CASE WHEN p ? '{c}' THEN (p{op_}'{c}'){cast} ELSE {c} END," for c, op_, cast in SAVE_COLUMNS
)
OLD_FUNCTIONS = (
    "app.admin_update_plan(uuid, text, bigint, char, jsonb, jsonb, boolean)",
    "app.admin_create_plan(text, text, bigint, char, jsonb, jsonb)",
)


def _rewrite_metrics(pattern: str, new: str) -> None:
    body = op.get_bind().exec_driver_sql(f"SELECT pg_get_functiondef('{METRICS}'::regprocedure)").scalar_one()
    changed, n = re.subn(pattern, lambda _m: new, body)
    if n != 1:
        raise RuntimeError("admin_metrics changed; update this migration")
    op.execute(changed)


def upgrade() -> None:
    op.execute(
        r"""
        ALTER TABLE app.plans
          ADD COLUMN short_description text CHECK (length(short_description) <= 200),
          ADD COLUMN description       text CHECK (length(description) <= 5000),
          ADD COLUMN highlights        jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(highlights) = 'array'),
          ADD COLUMN status            text NOT NULL DEFAULT 'draft'
                                       CHECK (status IN ('draft', 'published', 'archived')),
          ADD COLUMN display_order     integer NOT NULL DEFAULT 0,
          ADD COLUMN recommended       boolean NOT NULL DEFAULT false,
          ADD COLUMN setup_fee_minor   bigint NOT NULL DEFAULT 0 CHECK (setup_fee_minor >= 0),
          ADD COLUMN trial_days        integer NOT NULL DEFAULT 0 CHECK (trial_days BETWEEN 0 AND 365),
          ADD COLUMN tax_treatment     text NOT NULL DEFAULT 'exclusive'
                                       CHECK (tax_treatment IN ('exclusive', 'inclusive')),
          ADD COLUMN support_level     text CHECK (length(support_level) <= 200),
          ADD COLUMN overage_policy    text CHECK (length(overage_policy) <= 500),
          ADD COLUMN can_upgrade       boolean NOT NULL DEFAULT true,
          ADD COLUMN can_downgrade     boolean NOT NULL DEFAULT true,
          ADD COLUMN promo_discount_bp integer NOT NULL DEFAULT 0
                                       CHECK (promo_discount_bp BETWEEN 0 AND 10000),
          ADD COLUMN promo_ends_on     date,
          ADD COLUMN published_at      timestamptz,
          ADD COLUMN archived_at       timestamptz,
          ADD COLUMN version           integer NOT NULL DEFAULT 1,
          ADD CONSTRAINT plans_promo_dated CHECK (promo_discount_bp = 0 OR promo_ends_on IS NOT NULL);
        UPDATE app.plans SET status = CASE WHEN is_active THEN 'published' ELSE 'archived' END;

        CREATE TABLE app.plan_prices (
          id                  uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          plan_id             uuid NOT NULL REFERENCES app.plans(id),
          interval            text NOT NULL CHECK (interval IN ('month', 'quarter', 'year')),
          amount_minor        bigint NOT NULL CHECK (amount_minor >= 0),
          currency            char(3) NOT NULL,
          intro_amount_minor  bigint CHECK (intro_amount_minor >= 0),
          intro_periods       integer CHECK (intro_periods BETWEEN 1 AND 36),
          effective_from      timestamptz NOT NULL DEFAULT now(),
          existing_policy     text NOT NULL DEFAULT 'new_only'
                              CHECK (existing_policy IN ('new_only', 'next_renewal')),
          notice_days         integer CHECK (notice_days BETWEEN 0 AND 365),
          reason              text NOT NULL CHECK (length(reason) BETWEEN 3 AND 500),
          created_by          uuid REFERENCES app.users(id),
          created_at          timestamptz NOT NULL DEFAULT now(),
          withdrawn_at        timestamptz,
          UNIQUE (plan_id, interval, effective_from),
          CHECK ((intro_amount_minor IS NULL) = (intro_periods IS NULL)),
          CHECK (intro_amount_minor IS NULL OR intro_amount_minor < amount_minor),
          CHECK (existing_policy = 'new_only' OR notice_days IS NOT NULL)
        );
        CREATE INDEX plan_prices_current ON app.plan_prices (plan_id, interval, effective_from DESC)
          WHERE withdrawn_at IS NULL;

        -- History is never rewritten: the only change allowed is withdrawing a row not yet in force.
        CREATE FUNCTION app.plan_prices_guard() RETURNS trigger
        LANGUAGE plpgsql SET search_path = app, extensions, pg_temp AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'plan prices are append-only' USING ERRCODE = 'insufficient_privilege';
          END IF;
          IF OLD.withdrawn_at IS NOT NULL OR NEW.withdrawn_at IS NULL OR OLD.effective_from <= now()
             OR (to_jsonb(NEW) - 'withdrawn_at') <> (to_jsonb(OLD) - 'withdrawn_at') THEN
            RAISE EXCEPTION 'plan prices are append-only; only a price not yet in force can be withdrawn'
              USING ERRCODE = 'insufficient_privilege';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER plan_prices_guard BEFORE UPDATE OR DELETE ON app.plan_prices
          FOR EACH ROW EXECUTE FUNCTION app.plan_prices_guard();
        REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON app.plan_prices FROM diyneco_api, diyneco_worker;

        -- The seeded plans: drafts at the owner's proposed monthly prices.
        INSERT INTO app.plan_prices (plan_id, interval, amount_minor, currency, effective_from, reason)
          SELECT p.id, 'month', v.amount, 'ZAR', now(),
            'Proposed starting price (owner''s brief of 2026-10-12)'
          FROM app.plans p JOIN (VALUES ('starter', 49900), ('professional', 99900), ('enterprise', 199900))
            AS v(code, amount) ON v.code = p.code;
        UPDATE app.plans SET status = 'draft', published_at = NULL, features = features - 'placeholder',
          display_order = CASE code WHEN 'starter' THEN 1 WHEN 'professional' THEN 2 ELSE 3 END
          WHERE code IN ('starter', 'professional', 'enterprise');

        ALTER TABLE app.plans DROP COLUMN monthly_price_minor, DROP COLUMN is_active;

        CREATE TABLE app.billing_settings (
          id                        boolean PRIMARY KEY DEFAULT true CHECK (id),
          price_change_notice_days  integer NOT NULL DEFAULT 30
                                    CHECK (price_change_notice_days BETWEEN 0 AND 365),
          version                   integer NOT NULL DEFAULT 1,
          updated_at                timestamptz NOT NULL DEFAULT now(),
          updated_by                uuid REFERENCES app.users(id)
        );
        INSERT INTO app.billing_settings DEFAULT VALUES;
        REVOKE INSERT, DELETE, TRUNCATE ON app.billing_settings FROM diyneco_api, diyneco_worker;
        GRANT UPDATE ON app.billing_settings TO diyneco_api;
        """
    )
    for fn in OLD_FUNCTIONS:
        op.execute(f"DROP FUNCTION IF EXISTS {fn}")
    op.execute("DROP FUNCTION IF EXISTS app.admin_mrr()")
    op.execute(
        r"""
        -- Creates (p_id NULL) or updates a plan from the allowed keys of p; returns its id.
        CREATE FUNCTION app.admin_save_plan(p_id uuid, p jsonb) RETURNS uuid
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
        DECLARE
          out_id uuid;
        BEGIN
          IF p_id IS NULL THEN
            INSERT INTO app.plans (code, name, currency)
              VALUES (p->>'code', p->>'name', p->>'currency') RETURNING id INTO out_id;
          ELSE
            out_id := p_id;
          END IF;
          UPDATE app.plans SET
            {SAVE_SET}
            published_at      = CASE WHEN p->>'status' = 'published' AND status <> 'published'
                                     THEN now() ELSE published_at END,
            archived_at       = CASE WHEN p->>'status' = 'archived' THEN now()
                                     WHEN p ? 'status' THEN NULL ELSE archived_at END,
            version           = version + CASE WHEN p_id IS NULL THEN 0 ELSE 1 END,
            updated_at        = now()
          WHERE id = out_id;
          RETURN out_id;
        END $$;

        CREATE FUNCTION app.admin_add_plan_price(
          p_plan uuid, p_interval text, p_amount bigint, p_intro bigint, p_intro_periods integer,
          p_from timestamptz, p_policy text, p_notice integer, p_reason text, p_user uuid
        ) RETURNS uuid
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          INSERT INTO app.plan_prices (plan_id, interval, amount_minor, currency, intro_amount_minor,
            intro_periods, effective_from, existing_policy, notice_days, reason, created_by)
          SELECT id, p_interval, p_amount, currency, p_intro, p_intro_periods, coalesce(p_from, now()),
            p_policy, p_notice, p_reason, p_user
          FROM app.plans WHERE id = p_plan
          RETURNING id
        $$;

        CREATE FUNCTION app.admin_withdraw_plan_price(p_price uuid) RETURNS boolean
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          UPDATE app.plan_prices SET withdrawn_at = now()
          WHERE id = p_price AND withdrawn_at IS NULL AND effective_from > now()
          RETURNING true
        $$;

        -- Monthly recurring revenue per currency from each current subscription's plan price in
        -- force today, normalised to a month (later slices use the subscription's own snapshot).
        CREATE FUNCTION app.admin_mrr()
        RETURNS TABLE (currency char(3), mrr_minor bigint, subscriptions bigint)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT pr.currency, coalesce(sum(pr.amount_minor), 0)::bigint, count(*)
          FROM app.subscriptions s JOIN app.hotels h ON h.id = s.hotel_id
          JOIN LATERAL (
            SELECT x.currency, x.amount_minor FROM app.plan_prices x
            WHERE x.plan_id = s.plan_id AND x.interval = 'month' AND x.withdrawn_at IS NULL
              AND x.effective_from <= now()
            ORDER BY x.effective_from DESC LIMIT 1
          ) pr ON true
          WHERE s.status IN ('active', 'past_due') AND h.status = 'active'
          GROUP BY pr.currency ORDER BY pr.currency
        $$;
        """.replace("{SAVE_SET}", SAVE_SET)
    )
    for fn in FUNCTIONS:
        op.execute(f"REVOKE ALL ON FUNCTION {fn} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {fn} TO diyneco_api, diyneco_platform")
    _rewrite_metrics(OLD_MRR, NEW_MRR)


def downgrade() -> None:
    for fn in FUNCTIONS:
        op.execute(f"DROP FUNCTION IF EXISTS {fn}")
    op.execute(
        """
        DROP TABLE IF EXISTS app.billing_settings;
        ALTER TABLE app.plans ADD COLUMN monthly_price_minor bigint NOT NULL DEFAULT 0
            CHECK (monthly_price_minor >= 0),
          ADD COLUMN is_active boolean NOT NULL DEFAULT true;
        ALTER TABLE app.plans ALTER COLUMN monthly_price_minor DROP DEFAULT;
        UPDATE app.plans p SET is_active = (p.status = 'published'),
          monthly_price_minor = coalesce((
            SELECT x.amount_minor FROM app.plan_prices x
            WHERE x.plan_id = p.id AND x.interval = 'month' AND x.withdrawn_at IS NULL
            ORDER BY x.effective_from DESC LIMIT 1), 0);
        UPDATE app.plans SET features = features || '{"placeholder": true}'
          WHERE code IN ('starter', 'professional', 'enterprise');
        DROP TABLE IF EXISTS app.plan_prices;
        DROP FUNCTION IF EXISTS app.plan_prices_guard();
        ALTER TABLE app.plans DROP CONSTRAINT plans_promo_dated,
          DROP COLUMN short_description, DROP COLUMN description, DROP COLUMN highlights, DROP COLUMN status,
          DROP COLUMN display_order, DROP COLUMN recommended, DROP COLUMN setup_fee_minor,
          DROP COLUMN trial_days, DROP COLUMN tax_treatment, DROP COLUMN support_level,
          DROP COLUMN overage_policy, DROP COLUMN can_upgrade, DROP COLUMN can_downgrade,
          DROP COLUMN promo_discount_bp, DROP COLUMN promo_ends_on, DROP COLUMN published_at,
          DROP COLUMN archived_at, DROP COLUMN version;

        CREATE FUNCTION app.admin_mrr()
        RETURNS TABLE (currency char(3), mrr_minor bigint, subscriptions bigint)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT p.currency, coalesce(sum(p.monthly_price_minor), 0)::bigint, count(*)
          FROM app.subscriptions s JOIN app.plans p ON p.id = s.plan_id JOIN app.hotels h ON h.id = s.hotel_id
          WHERE s.status IN ('active','past_due') AND h.status = 'active'
          GROUP BY p.currency ORDER BY p.currency
        $$;
        CREATE FUNCTION app.admin_create_plan(
          p_code text, p_name text, p_price bigint, p_currency char, p_limits jsonb, p_features jsonb
        ) RETURNS uuid
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          INSERT INTO app.plans (code, name, monthly_price_minor, currency, limits, features)
          VALUES (p_code, p_name, p_price, p_currency, p_limits, p_features)
          RETURNING id
        $$;
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
        """
    )
    _rewrite_metrics(re.escape(NEW_MRR), RESTORED_MRR)
    for fn in ("app.admin_mrr()", *OLD_FUNCTIONS):
        op.execute(f"REVOKE ALL ON FUNCTION {fn} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {fn} TO diyneco_api, diyneco_platform")
