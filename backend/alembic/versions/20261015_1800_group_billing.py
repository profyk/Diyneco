"""group billing: one payment for an owner's invoices, and a group discount (D89)

- group_payments (control plane: it spans hotels, so it has no hotel_id and no RLS; the API
  only shows a row to the owner who started it): one provider checkout for the balance of
  several of an owner's open invoices in one currency.
- subscription_payment_attempts.group_payment_id: each invoice's share is an ordinary attempt
  of its own hotel, linked to the group. When the group is paid, each attempt is settled under
  its hotel's context like any other payment, so every hotel keeps its own tax invoice,
  payment and audit trail.
- billing_settings.group_discount_bp and group_discount_min_properties: owners with at least
  that many paid properties get that discount on each property's plan (first and renewal
  invoices). 0 switches it off.
- owner_portfolio_size(hotel): the most paid properties any Hotel Owner of that hotel holds,
  counting the hotel itself (definer: hotels are tenant rows).

Revision ID: 0036
Revises: 0035
Create Date: 2026-10-15 18:00
"""

from alembic import op

import alembic_helpers as h

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        ALTER TABLE app.billing_settings
          ADD COLUMN group_discount_bp integer NOT NULL DEFAULT 0 CHECK (group_discount_bp BETWEEN 0 AND 5000),
          ADD COLUMN group_discount_min_properties integer NOT NULL DEFAULT 3
            CHECK (group_discount_min_properties BETWEEN 2 AND 100);

        CREATE FUNCTION app.owner_portfolio_size(target uuid) RETURNS integer
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          WITH owners AS (
            SELECT DISTINCT hu.user_id FROM app.hotel_users hu
            JOIN app.user_roles ur ON ur.hotel_user_id = hu.id
            JOIN app.roles r ON r.id = ur.role_id AND r.code = 'hotel_owner' AND r.hotel_id IS NULL
            WHERE hu.hotel_id = target AND hu.status = 'active'
          )
          SELECT coalesce(max(n), 0)::integer FROM (
            SELECT o.user_id, count(DISTINCT hu.hotel_id) AS n
            FROM owners o
            JOIN app.hotel_users hu ON hu.user_id = o.user_id AND hu.status = 'active'
            JOIN app.user_roles ur ON ur.hotel_user_id = hu.id
            JOIN app.roles r ON r.id = ur.role_id AND r.code = 'hotel_owner' AND r.hotel_id IS NULL
            JOIN app.hotels hh ON hh.id = hu.hotel_id AND hh.status <> 'closed'
            WHERE hu.hotel_id = target OR EXISTS (
              SELECT 1 FROM app.subscriptions s WHERE s.hotel_id = hu.hotel_id AND s.plan_id IS NOT NULL
                AND s.status IN ('pending_payment', 'active', 'past_due', 'suspended', 'cancellation_scheduled')
            )
            GROUP BY o.user_id
          ) per_owner
        $$;
        REVOKE ALL ON FUNCTION app.owner_portfolio_size(uuid) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.owner_portfolio_size(uuid) TO diyneco_api, diyneco_worker;

        CREATE TABLE app.group_payments (
          id               uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          owner_user_id    uuid NOT NULL REFERENCES app.users(id),
          provider         text NOT NULL CHECK (provider IN ('sandbox', 'stitch')),
          test_mode        boolean NOT NULL,
          currency         char(3) NOT NULL,
          amount_minor     bigint NOT NULL CHECK (amount_minor > 0),
          paid_minor       bigint CHECK (paid_minor >= 0),
          unallocated_minor bigint NOT NULL DEFAULT 0 CHECK (unallocated_minor >= 0),
          provider_ref     text CHECK (length(provider_ref) <= 200),
          checkout_url     text CHECK (length(checkout_url) <= 2000),
          status           text NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending', 'succeeded', 'failed', 'cancelled', 'expired')),
          failure_reason   text CHECK (length(failure_reason) <= 500),
          created_at       timestamptz NOT NULL DEFAULT now(),
          updated_at       timestamptz NOT NULL DEFAULT now(),
          completed_at     timestamptz,
          UNIQUE (provider, provider_ref),
          CHECK ((status = 'pending') = (completed_at IS NULL))
        );
        CREATE INDEX group_payments_owner ON app.group_payments (owner_user_id, created_at DESC);

        ALTER TABLE app.subscription_payment_attempts
          ADD COLUMN group_payment_id uuid REFERENCES app.group_payments(id);
        CREATE INDEX subscription_payment_attempts_group ON app.subscription_payment_attempts (group_payment_id)
          WHERE group_payment_id IS NOT NULL;

        -- The shares of a group payment, oldest first, so it can be settled hotel by hotel
        -- (attempts are tenant rows). Ids only; each share is then read under its hotel.
        CREATE FUNCTION app.group_payment_shares(gid uuid)
        RETURNS TABLE (hotel_id uuid, attempt_id uuid)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT a.hotel_id, a.id FROM app.subscription_payment_attempts a
          WHERE a.group_payment_id = gid ORDER BY a.created_at, a.id
        $$;
        REVOKE ALL ON FUNCTION app.group_payment_shares(uuid) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.group_payment_shares(uuid) TO diyneco_api, diyneco_worker;
        """
    )
    h.updated_at("group_payments")
    h.mutable("group_payments")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("group_payments")
    op.execute(
        """
        DROP FUNCTION IF EXISTS app.group_payment_shares(uuid);
        DROP INDEX app.subscription_payment_attempts_group;
        ALTER TABLE app.subscription_payment_attempts DROP COLUMN group_payment_id;
        DROP TABLE app.group_payments;
        DROP FUNCTION app.owner_portfolio_size(uuid);
        ALTER TABLE app.billing_settings DROP COLUMN group_discount_min_properties, DROP COLUMN group_discount_bp;
        """
    )
