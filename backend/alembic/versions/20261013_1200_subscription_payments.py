"""subscription payments, refunds, webhooks, billing engine and billing dashboard reads

DECISIONS D79 (owner's billing brief, sections 6, 9, 10, 12; billing slices 5-7).
- subscription_payment_attempts (per hotel, RLS): one checkout with a payment provider for
  an invoice (sandbox or Stitch). Pending until the provider's status is verified on the
  server; then succeeded, failed, cancelled or expired, and never changed again.
- subscription_payments (per hotel, RLS): money received for an invoice: from a verified
  attempt or recorded by a billing administrator (EFT and other offline payments, with the
  bank reference). Amount, method and invoice never change; only the reconciliation status
  (unreconciled, matched, disputed) moves. A provider's payment id is unique, so the same
  provider payment can never be counted twice. Sandbox payments are marked test_mode and are
  never counted as collected revenue.
- subscription_refunds (append-only): money given back, always against a credit note.
- billing_webhook_events (control plane): every provider webhook, unique per provider and
  event id (a repeated delivery is recognised and not processed again); written only through
  app.billing_webhook_record and app.billing_webhook_done.
- subscription_billing_events (append-only): renewals, reminders, suspensions and other
  lifecycle events; a dedupe key makes each reminder and renewal step happen once.
- A plan-free trial may end (expired or cancelled) without a plan; anything sold has one.
- subscriptions gain a scheduled plan change (pending plan, price row and interval) applied
  at renewal, past_due_since and suspended_at.
- subscription_invoices gain purpose (manual, initial, renewal, proration) and plan_id; one
  initial or renewal invoice per subscription and period start (duplicate renewals refused
  by the database).
- billing_settings gain reminders (days relative to the due date), grace days, renewal lead
  days, suspension rules, proration and the card payment provider.
- admin_mrr now sums the agreed prices on subscriptions, not the plans' list prices.
- app.billing_hotels (worker) lists hotels with billing work; app.admin_billing_* return
  cross-hotel billing aggregates and lists for the platform's billing dashboard.

Revision ID: 0030
Revises: 0029
Create Date: 2026-10-13 12:00
"""

from alembic import op

import alembic_helpers as h

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None

ADMIN_FUNCTIONS = (
    "app.admin_billing_summary(date, date)",
    "app.admin_billing_by_plan(date, date)",
    "app.admin_billing_invoices(text, text, date, date, text, text, integer, integer)",
    "app.admin_billing_payments(text, text, date, date, integer, integer)",
    "app.admin_billing_webhooks(integer)",
)

# MRR per currency from the price each subscription agreed (D79): an interval's price spread
# over its months, rounded half up.
MRR_SQL = """
  SELECT s.currency::char(3) AS currency,
         sum((s.amount_minor * 2 + m.months) / (2 * m.months))::bigint AS mrr_minor,
         count(*) AS subscriptions
  FROM app.subscriptions s
  JOIN (VALUES ('month', 1), ('quarter', 3), ('year', 12)) AS m(interval, months)
    ON m.interval = s.interval
  WHERE s.status IN ('active', 'past_due', 'cancellation_scheduled') AND s.amount_minor IS NOT NULL
  GROUP BY s.currency ORDER BY s.currency
"""


def upgrade() -> None:
    op.execute(
        r"""
        ALTER TABLE app.subscriptions
          ADD COLUMN pending_plan_id       uuid REFERENCES app.plans(id),
          ADD COLUMN pending_plan_price_id uuid REFERENCES app.plan_prices(id),
          ADD COLUMN pending_interval      text CHECK (pending_interval IN ('month', 'quarter', 'year')),
          ADD COLUMN past_due_since        date,
          ADD COLUMN suspended_at          timestamptz,
          -- A plan-free trial may also end (expired or cancelled) without ever having a plan.
          DROP CONSTRAINT subscriptions_plan_unless_trial,
          ADD CONSTRAINT subscriptions_plan_unless_trial CHECK (
            plan_id IS NOT NULL OR (status IN ('trial', 'expired', 'cancelled') AND amount_minor IS NULL)),
          ADD CONSTRAINT subscriptions_pending_change CHECK (
            (pending_plan_id IS NULL) = (pending_interval IS NULL)
            AND (pending_plan_id IS NULL) = (pending_plan_price_id IS NULL));

        ALTER TABLE app.subscription_invoices
          ADD COLUMN purpose text NOT NULL DEFAULT 'manual'
            CHECK (purpose IN ('manual', 'initial', 'renewal', 'proration', 'credit')),
          ADD COLUMN plan_id uuid REFERENCES app.plans(id);
        CREATE UNIQUE INDEX subscription_invoices_one_per_period
          ON app.subscription_invoices (subscription_id, period_start)
          WHERE purpose IN ('initial', 'renewal') AND status <> 'void';

        ALTER TABLE app.billing_settings
          ADD COLUMN reminder_offsets   integer[] NOT NULL DEFAULT '{-3,0,3}'
            CHECK (cardinality(reminder_offsets) <= 10
                   AND -60 <= ALL (reminder_offsets) AND 60 >= ALL (reminder_offsets)),
          ADD COLUMN grace_days          integer NOT NULL DEFAULT 7 CHECK (grace_days BETWEEN 0 AND 90),
          ADD COLUMN renewal_lead_days   integer NOT NULL DEFAULT 7 CHECK (renewal_lead_days BETWEEN 0 AND 60),
          ADD COLUMN suspend_after_grace boolean NOT NULL DEFAULT true,
          ADD COLUMN read_only_when_suspended boolean NOT NULL DEFAULT true,
          ADD COLUMN proration_enabled   boolean NOT NULL DEFAULT false,
          ADD COLUMN card_provider       text NOT NULL DEFAULT 'sandbox'
            CHECK (card_provider IN ('none', 'sandbox', 'stitch')),
          ADD COLUMN eft_enabled         boolean NOT NULL DEFAULT true;

        CREATE TABLE app.subscription_payment_attempts (
          id              uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id        uuid NOT NULL,
          invoice_id      uuid NOT NULL,
          provider        text NOT NULL CHECK (provider IN ('sandbox', 'stitch')),
          test_mode       boolean NOT NULL,
          amount_minor    bigint NOT NULL CHECK (amount_minor > 0),
          currency        char(3) NOT NULL,
          provider_ref    text CHECK (length(provider_ref) <= 200),
          checkout_url    text CHECK (length(checkout_url) <= 2000),
          status          text NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'succeeded', 'failed', 'cancelled', 'expired')),
          failure_reason  text CHECK (length(failure_reason) <= 500),
          created_by      uuid REFERENCES app.users(id),
          created_at      timestamptz NOT NULL DEFAULT now(),
          updated_at      timestamptz NOT NULL DEFAULT now(),
          completed_at    timestamptz,
          UNIQUE (provider, provider_ref),
          UNIQUE (hotel_id, id),
          FOREIGN KEY (hotel_id, invoice_id) REFERENCES app.subscription_invoices (hotel_id, id),
          CHECK ((status = 'pending') = (completed_at IS NULL))
        );
        CREATE INDEX subscription_payment_attempts_invoice
          ON app.subscription_payment_attempts (invoice_id, created_at DESC);

        -- Pending until verified; then final. The provider's reference and checkout address are
        -- set once.
        CREATE FUNCTION app.subscription_payment_attempts_guard() RETURNS trigger
        LANGUAGE plpgsql SET search_path = app, extensions, pg_temp AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'payment attempts are never deleted' USING ERRCODE = 'insufficient_privilege';
          END IF;
          IF OLD.status <> 'pending'
             OR (OLD.provider_ref IS NOT NULL AND NEW.provider_ref IS DISTINCT FROM OLD.provider_ref)
             OR (OLD.checkout_url IS NOT NULL AND NEW.checkout_url IS DISTINCT FROM OLD.checkout_url)
             OR (to_jsonb(NEW) - ARRAY['status', 'failure_reason', 'completed_at', 'provider_ref',
                                       'checkout_url', 'updated_at'])
                <> (to_jsonb(OLD) - ARRAY['status', 'failure_reason', 'completed_at', 'provider_ref',
                                          'checkout_url', 'updated_at']) THEN
            RAISE EXCEPTION 'a completed payment attempt is final' USING ERRCODE = 'insufficient_privilege';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER subscription_payment_attempts_guard
          BEFORE UPDATE OR DELETE ON app.subscription_payment_attempts
          FOR EACH ROW EXECUTE FUNCTION app.subscription_payment_attempts_guard();

        CREATE TABLE app.subscription_payments (
          id                    uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id              uuid NOT NULL,
          invoice_id            uuid NOT NULL,
          attempt_id            uuid UNIQUE,
          method                text NOT NULL CHECK (method IN ('eft', 'pay_by_bank', 'card', 'sandbox', 'other')),
          provider              text NOT NULL CHECK (provider IN ('manual', 'sandbox', 'stitch')),
          test_mode             boolean NOT NULL DEFAULT false,
          amount_minor          bigint NOT NULL CHECK (amount_minor > 0),
          currency              char(3) NOT NULL,
          reference             text CHECK (length(reference) BETWEEN 1 AND 100),
          provider_payment_id   text CHECK (length(provider_payment_id) <= 200),
          received_on           date NOT NULL,
          notes                 text CHECK (length(notes) <= 500),
          reconciliation_status text NOT NULL DEFAULT 'unreconciled'
                                CHECK (reconciliation_status IN ('unreconciled', 'matched', 'disputed')),
          reconciled_at         timestamptz,
          reconciled_by         uuid REFERENCES app.users(id),
          reconciliation_note   text CHECK (length(reconciliation_note) <= 500),
          recorded_by           uuid REFERENCES app.users(id),
          created_at            timestamptz NOT NULL DEFAULT now(),
          updated_at            timestamptz NOT NULL DEFAULT now(),
          UNIQUE (provider, provider_payment_id),
          UNIQUE (hotel_id, id),
          FOREIGN KEY (hotel_id, invoice_id) REFERENCES app.subscription_invoices (hotel_id, id),
          FOREIGN KEY (hotel_id, attempt_id) REFERENCES app.subscription_payment_attempts (hotel_id, id),
          CHECK (provider <> 'manual' OR reference IS NOT NULL),
          CHECK (provider = 'manual' OR attempt_id IS NOT NULL),
          CHECK (test_mode = (provider = 'sandbox'))
        );
        CREATE INDEX subscription_payments_invoice ON app.subscription_payments (invoice_id);
        CREATE INDEX subscription_payments_received ON app.subscription_payments (received_on DESC);

        CREATE FUNCTION app.subscription_payments_guard() RETURNS trigger
        LANGUAGE plpgsql SET search_path = app, extensions, pg_temp AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'payments are never deleted' USING ERRCODE = 'insufficient_privilege';
          END IF;
          IF (to_jsonb(NEW) - ARRAY['reconciliation_status', 'reconciled_at', 'reconciled_by',
                                    'reconciliation_note', 'updated_at'])
             <> (to_jsonb(OLD) - ARRAY['reconciliation_status', 'reconciled_at', 'reconciled_by',
                                       'reconciliation_note', 'updated_at']) THEN
            RAISE EXCEPTION 'a payment is a permanent record; only its reconciliation changes'
              USING ERRCODE = 'insufficient_privilege';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER subscription_payments_guard BEFORE UPDATE OR DELETE ON app.subscription_payments
          FOR EACH ROW EXECUTE FUNCTION app.subscription_payments_guard();

        CREATE TABLE app.subscription_refunds (
          id                 uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id           uuid NOT NULL,
          payment_id         uuid NOT NULL,
          credit_note_id     uuid NOT NULL,
          amount_minor       bigint NOT NULL CHECK (amount_minor > 0),
          currency           char(3) NOT NULL,
          method             text NOT NULL CHECK (method IN ('provider', 'manual')),
          provider_refund_id text CHECK (length(provider_refund_id) <= 200),
          reference          text CHECK (length(reference) <= 100),
          test_mode          boolean NOT NULL DEFAULT false,
          reason             text NOT NULL CHECK (length(reason) BETWEEN 3 AND 500),
          created_by         uuid REFERENCES app.users(id),
          created_at         timestamptz NOT NULL DEFAULT now(),
          FOREIGN KEY (hotel_id, payment_id) REFERENCES app.subscription_payments (hotel_id, id),
          FOREIGN KEY (hotel_id, credit_note_id) REFERENCES app.subscription_invoices (hotel_id, id)
        );
        CREATE INDEX subscription_refunds_payment ON app.subscription_refunds (payment_id);

        CREATE TABLE app.subscription_billing_events (
          id              uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id        uuid NOT NULL REFERENCES app.hotels(id),
          subscription_id uuid REFERENCES app.subscriptions(id),
          invoice_id      uuid REFERENCES app.subscription_invoices(id),
          kind            text NOT NULL CHECK (length(kind) BETWEEN 1 AND 60),
          dedupe_key      text CHECK (length(dedupe_key) <= 200),
          detail          jsonb NOT NULL DEFAULT '{}',
          created_at      timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, dedupe_key)
        );
        CREATE INDEX subscription_billing_events_hotel ON app.subscription_billing_events (hotel_id, created_at DESC);

        CREATE TABLE app.billing_webhook_events (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          provider      text NOT NULL CHECK (provider IN ('stitch')),
          event_id      text NOT NULL CHECK (length(event_id) BETWEEN 1 AND 200),
          event_type    text CHECK (length(event_type) <= 200),
          payload       jsonb NOT NULL,
          received_at   timestamptz NOT NULL DEFAULT now(),
          processed_at  timestamptz,
          outcome       text CHECK (length(outcome) <= 200),
          error         text CHECK (length(error) <= 500),
          UNIQUE (provider, event_id)
        );
        REVOKE ALL ON app.billing_webhook_events FROM diyneco_api, diyneco_worker;

        -- A webhook is stored once; `duplicate` says it was seen before (and how it ended).
        CREATE FUNCTION app.billing_webhook_record(p_provider text, p_event_id text, p_type text, p_payload jsonb)
        RETURNS TABLE (id uuid, duplicate boolean, processed boolean)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
        DECLARE
          new_id uuid;
        BEGIN
          INSERT INTO app.billing_webhook_events (provider, event_id, event_type, payload)
          VALUES (p_provider, p_event_id, p_type, p_payload)
          ON CONFLICT (provider, event_id) DO NOTHING
          RETURNING billing_webhook_events.id INTO new_id;
          IF new_id IS NOT NULL THEN
            RETURN QUERY SELECT new_id, false, false;
          ELSE
            RETURN QUERY SELECT e.id, true, e.processed_at IS NOT NULL FROM app.billing_webhook_events e
              WHERE e.provider = p_provider AND e.event_id = p_event_id;
          END IF;
        END $$;

        CREATE FUNCTION app.billing_webhook_done(p_id uuid, p_outcome text, p_error text) RETURNS void
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          UPDATE app.billing_webhook_events
            SET processed_at = CASE WHEN p_error IS NULL THEN now() ELSE processed_at END,
                outcome = left(p_outcome, 200), error = left(p_error, 500)
          WHERE id = p_id
        $$;

        -- The hotel a provider's checkout belongs to, so a webhook (which carries no hotel) is
        -- processed under that hotel's context.
        CREATE FUNCTION app.billing_attempt_hotel(p_provider text, p_ref text) RETURNS uuid
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT hotel_id FROM app.subscription_payment_attempts WHERE provider = p_provider AND provider_ref = p_ref
        $$;

        CREATE FUNCTION app.billing_hotels() RETURNS TABLE (hotel_id uuid)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT DISTINCT s.hotel_id FROM app.subscriptions s
            WHERE s.status IN ('trial','pending_payment','active','past_due','suspended','cancellation_scheduled')
          UNION
          SELECT DISTINCT i.hotel_id FROM app.subscription_invoices i
            WHERE i.status IN ('issued', 'partially_paid', 'overdue')
        $$;
        """
    )
    for fn in (
        "app.billing_webhook_record(text, text, text, jsonb)",
        "app.billing_webhook_done(uuid, text, text)",
        "app.billing_attempt_hotel(text, text)",
        "app.billing_hotels()",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION {fn} FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION app.billing_webhook_record(text, text, text, jsonb), "
        "app.billing_webhook_done(uuid, text, text), app.billing_attempt_hotel(text, text) TO diyneco_api"
    )
    op.execute("GRANT EXECUTE ON FUNCTION app.billing_hotels() TO diyneco_worker, diyneco_api")

    for t in (
        "subscription_payment_attempts",
        "subscription_payments",
        "subscription_refunds",
        "subscription_billing_events",
    ):
        h.tenant_rls(t)
    h.mutable("subscription_payment_attempts")
    h.updated_at("subscription_payment_attempts")
    h.mutable("subscription_payments")
    h.updated_at("subscription_payments")
    h.append_only("subscription_refunds")
    h.append_only("subscription_billing_events")

    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION app.admin_mrr()
        RETURNS TABLE (currency char(3), mrr_minor bigint, subscriptions bigint)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          {MRR_SQL}
        $$;

        -- Billing dashboard figures per currency for [p_from, p_to] (Diyneco's time zone).
        -- Collected is money actually received (test payments excluded) less refunds; invoiced
        -- is issued invoices less credit notes; outstanding and MRR are as of now.
        CREATE FUNCTION app.admin_billing_summary(p_from date, p_to date)
        RETURNS TABLE (
          currency char(3), mrr_minor bigint, invoiced_minor bigint, credited_minor bigint,
          collected_minor bigint, refunded_minor bigint, test_collected_minor bigint,
          outstanding_minor bigint, overdue_minor bigint, overdue_invoices bigint
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          WITH tz AS (SELECT timezone FROM app.company_settings),
          open_inv AS (
            SELECT i.currency, i.status,
              greatest(0, i.total_minor
                - coalesce((SELECT sum(c.total_minor) FROM app.subscription_invoices c
                            WHERE c.credits_invoice_id = i.id AND c.status <> 'void'), 0)
                - coalesce((SELECT sum(p.amount_minor) FROM app.subscription_payments p WHERE p.invoice_id = i.id), 0)
                + coalesce((SELECT sum(r.amount_minor) FROM app.subscription_refunds r
                            JOIN app.subscription_payments p ON p.id = r.payment_id WHERE p.invoice_id = i.id), 0)
              ) AS balance
            FROM app.subscription_invoices i
            WHERE i.kind = 'invoice' AND i.status IN ('issued', 'partially_paid', 'overdue')
          ),
          currencies AS (
            SELECT currency FROM app.subscription_invoices
            UNION SELECT currency FROM app.subscriptions WHERE currency IS NOT NULL
          )
          SELECT c.currency::char(3),
            coalesce((SELECT m.mrr_minor FROM app.admin_mrr() m WHERE m.currency = c.currency), 0),
            coalesce((SELECT sum(i.total_minor) FROM app.subscription_invoices i, tz
              WHERE i.currency = c.currency AND i.kind = 'invoice' AND i.status <> 'void' AND i.number IS NOT NULL
                AND (i.issued_at AT TIME ZONE tz.timezone)::date BETWEEN p_from AND p_to), 0)::bigint,
            coalesce((SELECT sum(i.total_minor) FROM app.subscription_invoices i, tz
              WHERE i.currency = c.currency AND i.kind = 'credit_note' AND i.status <> 'void'
                AND (i.issued_at AT TIME ZONE tz.timezone)::date BETWEEN p_from AND p_to), 0)::bigint,
            coalesce((SELECT sum(p.amount_minor) FROM app.subscription_payments p
              WHERE p.currency = c.currency AND NOT p.test_mode
                AND p.received_on BETWEEN p_from AND p_to), 0)::bigint,
            coalesce((SELECT sum(r.amount_minor) FROM app.subscription_refunds r, tz
              WHERE r.currency = c.currency AND NOT r.test_mode
                AND (r.created_at AT TIME ZONE tz.timezone)::date BETWEEN p_from AND p_to), 0)::bigint,
            coalesce((SELECT sum(p.amount_minor) FROM app.subscription_payments p
              WHERE p.currency = c.currency AND p.test_mode
                AND p.received_on BETWEEN p_from AND p_to), 0)::bigint,
            coalesce((SELECT sum(o.balance) FROM open_inv o WHERE o.currency = c.currency), 0)::bigint,
            coalesce((SELECT sum(o.balance) FROM open_inv o WHERE o.currency = c.currency
              AND o.status = 'overdue'), 0)::bigint,
            (SELECT count(*) FROM open_inv o WHERE o.currency = c.currency AND o.status = 'overdue')
          FROM currencies c
          ORDER BY 1
        $$;

        CREATE FUNCTION app.admin_billing_counts(p_from date, p_to date)
        RETURNS TABLE (
          active_subscriptions bigint, trials bigint, past_due bigint, suspended bigint,
          new_subscriptions bigint, cancelled_subscriptions bigint, failed_payments bigint
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          WITH tz AS (SELECT timezone FROM app.company_settings)
          SELECT
            (SELECT count(*) FROM app.subscriptions WHERE status IN ('active', 'past_due', 'cancellation_scheduled')),
            (SELECT count(*) FROM app.subscriptions WHERE status = 'trial'),
            (SELECT count(*) FROM app.subscriptions WHERE status = 'past_due'),
            (SELECT count(*) FROM app.subscriptions WHERE status = 'suspended'),
            (SELECT count(*) FROM app.subscriptions WHERE amount_minor IS NOT NULL
               AND starts_on BETWEEN p_from AND p_to),
            (SELECT count(*) FROM app.subscriptions WHERE status IN ('cancelled', 'expired')
               AND amount_minor IS NOT NULL AND ended_on BETWEEN p_from AND p_to),
            (SELECT count(*) FROM app.subscription_payment_attempts a, tz WHERE a.status = 'failed'
               AND (a.created_at AT TIME ZONE tz.timezone)::date BETWEEN p_from AND p_to)
        $$;

        CREATE FUNCTION app.admin_billing_by_plan(p_from date, p_to date)
        RETURNS TABLE (plan_code text, plan_name text, currency char(3), subscriptions bigint,
                       mrr_minor bigint, collected_minor bigint)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT p.code, p.name, p.currency::char(3),
            (SELECT count(*) FROM app.subscriptions s WHERE s.plan_id = p.id
               AND s.status IN ('active', 'past_due', 'cancellation_scheduled')),
            coalesce((SELECT sum((s.amount_minor * 2 + m.months) / (2 * m.months)) FROM app.subscriptions s
               JOIN (VALUES ('month', 1), ('quarter', 3), ('year', 12)) AS m(interval, months) ON m.interval = s.interval
               WHERE s.plan_id = p.id AND s.status IN ('active', 'past_due', 'cancellation_scheduled')
                 AND s.amount_minor IS NOT NULL), 0)::bigint,
            coalesce((SELECT sum(pay.amount_minor) FROM app.subscription_payments pay
               JOIN app.subscription_invoices i ON i.id = pay.invoice_id
               WHERE i.plan_id = p.id AND NOT pay.test_mode AND pay.received_on BETWEEN p_from AND p_to), 0)::bigint
          FROM app.plans p
          ORDER BY p.display_order, p.name
        $$;

        -- Invoices and credit notes across hotels. p_q matches the hotel name or id or the
        -- document number; p_payment is paid, unpaid, partial or overdue.
        CREATE FUNCTION app.admin_billing_invoices(
          p_q text, p_status text, p_from date, p_to date, p_plan text, p_payment text,
          p_limit integer, p_offset integer)
        RETURNS TABLE (
          id uuid, hotel_id uuid, hotel_name text, kind text, purpose text, number text, status text,
          currency char(3), total_minor bigint, tax_minor bigint, paid_minor bigint, credited_minor bigint,
          balance_minor bigint, issued_at timestamptz, due_on date, period_start date, period_end date,
          plan_code text, is_tax_invoice boolean, total_count bigint
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          WITH tz AS (SELECT timezone FROM app.company_settings),
          rows AS (
            SELECT i.*, h.name AS hotel_name, pl.code AS plan_code,
              coalesce((SELECT sum(p.amount_minor) FROM app.subscription_payments p WHERE p.invoice_id = i.id), 0)
              - coalesce((SELECT sum(r.amount_minor) FROM app.subscription_refunds r
                          JOIN app.subscription_payments p ON p.id = r.payment_id WHERE p.invoice_id = i.id), 0)
                AS paid,
              coalesce((SELECT sum(c.total_minor) FROM app.subscription_invoices c
                        WHERE c.credits_invoice_id = i.id AND c.status <> 'void'), 0) AS credited
            FROM app.subscription_invoices i
            JOIN app.hotels h ON h.id = i.hotel_id
            LEFT JOIN app.plans pl ON pl.id = i.plan_id
            WHERE i.number IS NOT NULL
          ),
          filtered AS (
            SELECT r.*, CASE WHEN r.kind = 'invoice' THEN greatest(0, r.total_minor - r.paid - r.credited) ELSE 0 END
              AS balance
            FROM rows r, tz
            WHERE (p_q IS NULL OR r.hotel_name ILIKE '%' || p_q || '%' OR r.hotel_id::text = lower(p_q)
                   OR r.number ILIKE '%' || p_q || '%')
              AND (p_status IS NULL OR r.status = p_status)
              AND (p_from IS NULL OR (r.issued_at AT TIME ZONE tz.timezone)::date >= p_from)
              AND (p_to IS NULL OR (r.issued_at AT TIME ZONE tz.timezone)::date <= p_to)
              AND (p_plan IS NULL OR r.plan_code = p_plan)
          ),
          paid_filtered AS (
            SELECT f.* FROM filtered f
            WHERE p_payment IS NULL
              OR (p_payment = 'paid' AND f.kind = 'invoice' AND f.status = 'paid')
              OR (p_payment = 'partial' AND f.status = 'partially_paid')
              OR (p_payment = 'overdue' AND f.status = 'overdue')
              OR (p_payment = 'unpaid' AND f.kind = 'invoice' AND f.status IN ('issued', 'overdue') AND f.paid = 0)
          )
          SELECT f.id, f.hotel_id, f.hotel_name, f.kind, f.purpose, f.number, f.status, f.currency::char(3),
            f.total_minor, f.tax_minor, f.paid::bigint, f.credited::bigint, f.balance::bigint, f.issued_at,
            f.due_on, f.period_start, f.period_end, f.plan_code, f.is_tax_invoice,
            count(*) OVER ()
          FROM paid_filtered f
          ORDER BY f.issued_at DESC, f.number DESC
          LIMIT least(greatest(p_limit, 1), 5000) OFFSET greatest(p_offset, 0)
        $$;

        -- Payments across hotels for reconciliation. p_reconciliation filters its status.
        CREATE FUNCTION app.admin_billing_payments(
          p_q text, p_reconciliation text, p_from date, p_to date, p_limit integer, p_offset integer)
        RETURNS TABLE (
          id uuid, hotel_id uuid, hotel_name text, invoice_id uuid, invoice_number text, method text,
          provider text, test_mode boolean, amount_minor bigint, refunded_minor bigint, currency char(3),
          reference text, provider_payment_id text, received_on date, reconciliation_status text,
          reconciliation_note text, reconciled_at timestamptz, created_at timestamptz, total_count bigint
        )
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT p.id, p.hotel_id, h.name, p.invoice_id, i.number, p.method, p.provider, p.test_mode,
            p.amount_minor,
            coalesce((SELECT sum(r.amount_minor) FROM app.subscription_refunds r WHERE r.payment_id = p.id), 0)::bigint,
            p.currency::char(3), p.reference, p.provider_payment_id, p.received_on, p.reconciliation_status,
            p.reconciliation_note, p.reconciled_at, p.created_at, count(*) OVER ()
          FROM app.subscription_payments p
          JOIN app.hotels h ON h.id = p.hotel_id
          JOIN app.subscription_invoices i ON i.id = p.invoice_id
          WHERE (p_q IS NULL OR h.name ILIKE '%' || p_q || '%' OR p.hotel_id::text = lower(p_q)
                 OR i.number ILIKE '%' || p_q || '%' OR p.reference ILIKE '%' || p_q || '%')
            AND (p_reconciliation IS NULL OR p.reconciliation_status = p_reconciliation)
            AND (p_from IS NULL OR p.received_on >= p_from)
            AND (p_to IS NULL OR p.received_on <= p_to)
          ORDER BY p.received_on DESC, p.created_at DESC
          LIMIT least(greatest(p_limit, 1), 5000) OFFSET greatest(p_offset, 0)
        $$;

        CREATE FUNCTION app.admin_billing_webhooks(p_limit integer)
        RETURNS TABLE (id uuid, provider text, event_id text, event_type text, received_at timestamptz,
                       processed_at timestamptz, outcome text, error text)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT id, provider, event_id, event_type, received_at, processed_at, outcome, error
          FROM app.billing_webhook_events ORDER BY received_at DESC LIMIT least(greatest(p_limit, 1), 500)
        $$;
        """
    )
    for fn in (*ADMIN_FUNCTIONS, "app.admin_billing_counts(date, date)"):
        op.execute(f"REVOKE ALL ON FUNCTION {fn} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {fn} TO diyneco_api, diyneco_platform")


def downgrade() -> None:
    h.refuse_if_data(
        "subscription_payment_attempts",
        "subscription_payments",
        "subscription_refunds",
        "subscription_billing_events",
        "billing_webhook_events",
    )
    for fn in (*ADMIN_FUNCTIONS, "app.admin_billing_counts(date, date)"):
        op.execute(f"DROP FUNCTION IF EXISTS {fn}")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app.admin_mrr()
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
        DROP FUNCTION IF EXISTS app.billing_hotels();
        DROP FUNCTION IF EXISTS app.billing_attempt_hotel(text, text);
        DROP FUNCTION IF EXISTS app.billing_webhook_done(uuid, text, text);
        DROP FUNCTION IF EXISTS app.billing_webhook_record(text, text, text, jsonb);
        DROP TABLE IF EXISTS app.billing_webhook_events;
        DROP TABLE IF EXISTS app.subscription_billing_events;
        DROP TABLE IF EXISTS app.subscription_refunds;
        DROP TABLE IF EXISTS app.subscription_payments;
        DROP TABLE IF EXISTS app.subscription_payment_attempts;
        DROP FUNCTION IF EXISTS app.subscription_payments_guard();
        DROP FUNCTION IF EXISTS app.subscription_payment_attempts_guard();
        ALTER TABLE app.billing_settings
          DROP COLUMN reminder_offsets, DROP COLUMN grace_days, DROP COLUMN renewal_lead_days,
          DROP COLUMN suspend_after_grace, DROP COLUMN read_only_when_suspended,
          DROP COLUMN proration_enabled, DROP COLUMN card_provider, DROP COLUMN eft_enabled;
        DROP INDEX IF EXISTS app.subscription_invoices_one_per_period;
        ALTER TABLE app.subscription_invoices DROP COLUMN plan_id, DROP COLUMN purpose;
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM app.subscriptions WHERE plan_id IS NULL AND status <> 'trial') THEN
            RAISE EXCEPTION 'ended plan-free trials exist; cannot downgrade';
          END IF;
        END $$;
        ALTER TABLE app.subscriptions
          DROP CONSTRAINT subscriptions_plan_unless_trial,
          ADD CONSTRAINT subscriptions_plan_unless_trial CHECK (status = 'trial' OR plan_id IS NOT NULL),
          DROP CONSTRAINT subscriptions_pending_change,
          DROP COLUMN pending_plan_id, DROP COLUMN pending_plan_price_id, DROP COLUMN pending_interval,
          DROP COLUMN past_due_since, DROP COLUMN suspended_at;
        """
    )
