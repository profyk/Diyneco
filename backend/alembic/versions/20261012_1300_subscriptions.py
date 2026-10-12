"""subscriptions: lifecycle statuses, plan-free trial, agreed price, billing anchor, contacts

DECISIONS D76 (owner's billing brief, sections 5 and 6; D73: a signup starts a free trial
with no plan).
- Statuses become trial, pending_payment, active, past_due, suspended,
  cancellation_scheduled, cancelled and expired ('trialing' is renamed 'trial'). A hotel has
  at most one current subscription (any status but cancelled or expired).
- plan_id may be empty only for a trial.
- The agreed price is kept on the subscription when it is sold (interval, plan price row,
  amount, currency, introductory price and periods left, tax treatment): later plan price
  changes never alter it, except as the price row's own policy allows at renewal.
- Billing anchor: anchor_day (1-31) plus current_period_start; a period ends on the same day
  of the month N months later, or on the month's last day when it is shorter (31 Jan ->
  28/29 Feb -> 31 Mar). trial_ends_on, cancel_reason and ended_on record the lifecycle.
- billing_settings gains the trial: trial_days and trial_limits (defaults 14 days and small
  limits; both edited in the admin panel).
- subscription_billing_contacts (per hotel, RLS): who Diyneco bills: legal name, VAT number, billing email,
  phone, contact name and address. Hotels edit it; invoices copy it when issued.

Revision ID: 0028
Revises: 0027
Create Date: 2026-10-12 13:00
"""

from alembic import op

import alembic_helpers as h

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

CURRENT = "'trial','pending_payment','active','past_due','suspended','cancellation_scheduled'"


def upgrade() -> None:
    op.execute(
        f"""
        ALTER TABLE app.subscriptions DROP CONSTRAINT subscriptions_status_check;
        DROP INDEX app.subscriptions_one_current;
        UPDATE app.subscriptions SET status = 'trial' WHERE status = 'trialing';
        ALTER TABLE app.subscriptions
          ADD CONSTRAINT subscriptions_status_check CHECK (status IN ({CURRENT}, 'cancelled', 'expired')),
          ALTER COLUMN plan_id DROP NOT NULL,
          ADD COLUMN interval             text CHECK (interval IN ('month', 'quarter', 'year')),
          ADD COLUMN plan_price_id        uuid REFERENCES app.plan_prices(id),
          ADD COLUMN amount_minor         bigint CHECK (amount_minor >= 0),
          ADD COLUMN currency             char(3),
          ADD COLUMN intro_amount_minor   bigint CHECK (intro_amount_minor >= 0),
          ADD COLUMN intro_periods_left   integer NOT NULL DEFAULT 0 CHECK (intro_periods_left >= 0),
          ADD COLUMN tax_treatment        text CHECK (tax_treatment IN ('exclusive', 'inclusive')),
          ADD COLUMN anchor_day           smallint CHECK (anchor_day BETWEEN 1 AND 31),
          ADD COLUMN current_period_start date,
          ADD COLUMN trial_ends_on        date,
          ADD COLUMN cancel_reason        text CHECK (length(cancel_reason) <= 500),
          ADD COLUMN ended_on             date,
          ADD COLUMN version              integer NOT NULL DEFAULT 1,
          ADD CONSTRAINT subscriptions_plan_unless_trial CHECK (status = 'trial' OR plan_id IS NOT NULL),
          ADD CONSTRAINT subscriptions_price_when_sold CHECK (
            status <> 'pending_payment'
            OR (interval IS NOT NULL AND amount_minor IS NOT NULL AND currency IS NOT NULL
                AND anchor_day IS NOT NULL AND tax_treatment IS NOT NULL)
          );
        CREATE UNIQUE INDEX subscriptions_one_current ON app.subscriptions(hotel_id)
          WHERE status IN ({CURRENT});

        ALTER TABLE app.billing_settings
          ADD COLUMN trial_days   integer NOT NULL DEFAULT 14 CHECK (trial_days BETWEEN 0 AND 365),
          ADD COLUMN trial_limits jsonb NOT NULL
            DEFAULT '{{"rooms": 20, "devices": 25, "staff": 15, "api_keys": 0}}'
            CHECK (jsonb_typeof(trial_limits) = 'object');

        CREATE TABLE app.subscription_billing_contacts (
          hotel_id      uuid PRIMARY KEY REFERENCES app.hotels(id),
          legal_name    text CHECK (length(legal_name) <= 200),
          vat_number    text CHECK (length(vat_number) <= 30),
          billing_email citext,
          phone         text CHECK (length(phone) <= 30),
          contact_name  text CHECK (length(contact_name) <= 120),
          address       jsonb NOT NULL DEFAULT '{{}}',
          version       integer NOT NULL DEFAULT 1,
          updated_at    timestamptz NOT NULL DEFAULT now(),
          updated_by    uuid REFERENCES app.users(id)
        );
        """
    )
    h.tenant_rls("subscription_billing_contacts")
    h.mutable("subscription_billing_contacts")
    h.updated_at("subscription_billing_contacts")
    # admin_hotels listed only the old current statuses.
    op.execute(
        """
        DO $$
        DECLARE body text;
        BEGIN
          body := pg_get_functiondef('app.admin_hotels()'::regprocedure);
          IF position('''trialing'',''active'',''past_due''' IN body) = 0 THEN
            RAISE EXCEPTION 'admin_hotels changed; update this migration';
          END IF;
          EXECUTE replace(body, '''trialing'',''active'',''past_due''',
            '''trial'',''pending_payment'',''active'',''past_due'',''suspended'',''cancellation_scheduled''');
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE body text;
        BEGIN
          body := pg_get_functiondef('app.admin_hotels()'::regprocedure);
          EXECUTE replace(body,
            '''trial'',''pending_payment'',''active'',''past_due'',''suspended'',''cancellation_scheduled''',
            '''trialing'',''active'',''past_due''');
        END $$;
        """
    )
    h.refuse_if_data("subscription_billing_contacts")
    op.execute(
        """
        DROP TABLE IF EXISTS app.subscription_billing_contacts;
        ALTER TABLE app.billing_settings DROP COLUMN trial_limits, DROP COLUMN trial_days;
        DROP INDEX app.subscriptions_one_current;
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM app.subscriptions WHERE plan_id IS NULL
                     OR status IN ('pending_payment', 'suspended', 'cancellation_scheduled', 'expired')) THEN
            RAISE EXCEPTION 'subscriptions use the new statuses or have no plan; cannot downgrade';
          END IF;
        END $$;
        ALTER TABLE app.subscriptions
          DROP CONSTRAINT subscriptions_price_when_sold,
          DROP CONSTRAINT subscriptions_plan_unless_trial,
          DROP CONSTRAINT subscriptions_status_check,
          DROP COLUMN interval, DROP COLUMN plan_price_id, DROP COLUMN amount_minor, DROP COLUMN currency,
          DROP COLUMN intro_amount_minor, DROP COLUMN intro_periods_left, DROP COLUMN tax_treatment,
          DROP COLUMN anchor_day, DROP COLUMN current_period_start, DROP COLUMN trial_ends_on,
          DROP COLUMN cancel_reason, DROP COLUMN ended_on, DROP COLUMN version,
          ALTER COLUMN plan_id SET NOT NULL;
        UPDATE app.subscriptions SET status = 'trialing' WHERE status = 'trial';
        ALTER TABLE app.subscriptions ADD CONSTRAINT subscriptions_status_check
          CHECK (status IN ('trialing','active','past_due','cancelled'));
        CREATE UNIQUE INDEX subscriptions_one_current ON app.subscriptions(hotel_id)
          WHERE status IN ('trialing','active','past_due');
        """
    )
