"""subscription invoices: Diyneco's invoices and credit notes to hotels

DECISIONS D78 (owner's billing brief, section 8).
- subscription_invoices (per hotel, RLS): an invoice or a credit note from Diyneco Tech (Pty)
  Ltd to a hotel. A draft has no number; issuing gives it the next number and freezes it. It
  keeps its own copy of the seller (company settings), the buyer (billing contact and hotel),
  tax name, rate and amounts, payment instructions and period, so later settings changes
  never alter it. After issue a trigger allows only forward status changes (issued, overdue,
  partially paid, paid, credited, void) and setting the PDF once. Nothing is ever deleted.
- subscription_invoice_lines (append-only): lines may be added only while the invoice is a draft.
- subscription_invoice_events (append-only): every status change with who, why and when.
- subscription_invoice_sequences (control plane): one counter per kind, prefix and year
  (year 0 for a running sequence), advanced by app.next_subscription_invoice_number inside the
  issuing transaction: concurrent issues serialise on the counter row, a rolled-back issue
  gives its number back, so numbers are unique and gapless and never reused.

Revision ID: 0029
Revises: 0028
Create Date: 2026-10-13 09:00
"""

from alembic import op

import alembic_helpers as h

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

NUMBERED = "'issued','partially_paid','paid','overdue','credited'"


def upgrade() -> None:
    op.execute(
        f"""
        CREATE TABLE app.subscription_invoices (
          id                  uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id            uuid NOT NULL REFERENCES app.hotels(id),
          subscription_id     uuid REFERENCES app.subscriptions(id),
          kind                text NOT NULL CHECK (kind IN ('invoice', 'credit_note')),
          credits_invoice_id  uuid REFERENCES app.subscription_invoices(id),
          number              text UNIQUE,
          status              text NOT NULL DEFAULT 'draft'
                              CHECK (status IN ('draft', {NUMBERED}, 'void')),
          is_tax_invoice      boolean NOT NULL DEFAULT false,
          currency            char(3) NOT NULL,
          subtotal_minor      bigint NOT NULL DEFAULT 0 CHECK (subtotal_minor >= 0),
          tax_minor           bigint NOT NULL DEFAULT 0 CHECK (tax_minor >= 0),
          total_minor         bigint NOT NULL DEFAULT 0 CHECK (total_minor >= 0),
          tax_name            text,
          tax_rate_bp         integer CHECK (tax_rate_bp BETWEEN 0 AND 10000),
          period_start        date,
          period_end          date,
          issued_at           timestamptz,
          due_on              date,
          seller              jsonb NOT NULL DEFAULT '{{}}',
          buyer               jsonb NOT NULL DEFAULT '{{}}',
          payment_instructions text,
          notes               text CHECK (length(notes) <= 2000),
          pdf_path            text,
          created_by          uuid REFERENCES app.users(id),
          created_at          timestamptz NOT NULL DEFAULT now(),
          updated_at          timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, id),
          CHECK (status NOT IN ({NUMBERED}) OR (number IS NOT NULL AND issued_at IS NOT NULL)),
          CHECK (status <> 'draft' OR number IS NULL),
          CHECK ((kind = 'credit_note') = (credits_invoice_id IS NOT NULL)),
          CHECK (subtotal_minor + tax_minor = total_minor),
          CHECK (period_end IS NULL OR period_end > period_start)
        );
        CREATE INDEX subscription_invoices_hotel ON app.subscription_invoices (hotel_id, created_at DESC);
        CREATE INDEX subscription_invoices_open ON app.subscription_invoices (due_on)
          WHERE status IN ('issued', 'partially_paid', 'overdue');

        CREATE TABLE app.subscription_invoice_lines (
          id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id          uuid NOT NULL,
          invoice_id        uuid NOT NULL,
          position          integer NOT NULL CHECK (position > 0),
          code              text NOT NULL CHECK (length(code) BETWEEN 1 AND 40),
          description       text NOT NULL CHECK (length(description) BETWEEN 1 AND 300),
          quantity          integer NOT NULL DEFAULT 1 CHECK (quantity > 0),
          unit_amount_minor bigint NOT NULL CHECK (unit_amount_minor >= 0),
          discount_minor    bigint NOT NULL DEFAULT 0 CHECK (discount_minor >= 0),
          tax_minor         bigint NOT NULL DEFAULT 0 CHECK (tax_minor >= 0),
          total_minor       bigint NOT NULL CHECK (total_minor >= 0),
          UNIQUE (invoice_id, position),
          FOREIGN KEY (hotel_id, invoice_id) REFERENCES app.subscription_invoices (hotel_id, id)
        );

        CREATE TABLE app.subscription_invoice_events (
          id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id    uuid NOT NULL,
          invoice_id  uuid NOT NULL,
          status_from text,
          status_to   text NOT NULL,
          reason      text CHECK (length(reason) <= 500),
          actor_type  text NOT NULL,
          actor_id    uuid,
          created_at  timestamptz NOT NULL DEFAULT now(),
          FOREIGN KEY (hotel_id, invoice_id) REFERENCES app.subscription_invoices (hotel_id, id)
        );
        CREATE INDEX subscription_invoice_events_invoice ON app.subscription_invoice_events (invoice_id, created_at);

        CREATE TABLE app.subscription_invoice_sequences (
          kind        text NOT NULL CHECK (kind IN ('invoice', 'credit_note')),
          prefix      text NOT NULL,
          year        integer NOT NULL,
          next_number bigint NOT NULL,
          PRIMARY KEY (kind, prefix, year)
        );
        REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON app.subscription_invoice_sequences
          FROM diyneco_api, diyneco_worker;

        CREATE FUNCTION app.next_subscription_invoice_number(p_kind text, p_prefix text, p_year integer)
        RETURNS bigint
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          INSERT INTO app.subscription_invoice_sequences AS q (kind, prefix, year, next_number)
          VALUES (p_kind, p_prefix, p_year, 2)
          ON CONFLICT (kind, prefix, year) DO UPDATE SET next_number = q.next_number + 1
          RETURNING next_number - 1
        $$;
        REVOKE ALL ON FUNCTION app.next_subscription_invoice_number(text, text, integer) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.next_subscription_invoice_number(text, text, integer)
          TO diyneco_api, diyneco_worker;

        -- An issued invoice is a permanent record: only its status moves forward and its PDF is
        -- attached once. A draft may change freely until it is issued or discarded (void).
        CREATE FUNCTION app.subscription_invoices_freeze() RETURNS trigger
        LANGUAGE plpgsql SET search_path = app, extensions, pg_temp AS $$
        DECLARE
          allowed text[];
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'subscription invoices are never deleted' USING ERRCODE = 'insufficient_privilege';
          END IF;
          IF OLD.status = 'draft' THEN
            RETURN NEW;
          END IF;
          IF (to_jsonb(NEW) - ARRAY['status', 'pdf_path', 'updated_at'])
             <> (to_jsonb(OLD) - ARRAY['status', 'pdf_path', 'updated_at'])
             OR (OLD.pdf_path IS NOT NULL AND NEW.pdf_path IS DISTINCT FROM OLD.pdf_path) THEN
            RAISE EXCEPTION 'an issued invoice is frozen' USING ERRCODE = 'insufficient_privilege';
          END IF;
          IF NEW.status <> OLD.status THEN
            allowed := CASE OLD.status
              WHEN 'issued' THEN ARRAY['partially_paid', 'paid', 'overdue', 'void', 'credited']
              WHEN 'overdue' THEN ARRAY['partially_paid', 'paid', 'void', 'credited']
              WHEN 'partially_paid' THEN ARRAY['paid', 'overdue', 'credited']
              WHEN 'paid' THEN ARRAY['credited']
              ELSE ARRAY[]::text[]
            END;
            IF NOT NEW.status = ANY (allowed) THEN
              RAISE EXCEPTION 'invoice status cannot go from % to %', OLD.status, NEW.status
                USING ERRCODE = 'insufficient_privilege';
            END IF;
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER subscription_invoices_freeze BEFORE UPDATE OR DELETE ON app.subscription_invoices
          FOR EACH ROW EXECUTE FUNCTION app.subscription_invoices_freeze();

        CREATE FUNCTION app.subscription_invoice_lines_draft_only() RETURNS trigger
        LANGUAGE plpgsql SET search_path = app, extensions, pg_temp AS $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM app.subscription_invoices i
                         WHERE i.id = NEW.invoice_id AND i.status = 'draft') THEN
            RAISE EXCEPTION 'lines can only be added to a draft invoice' USING ERRCODE = 'insufficient_privilege';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER subscription_invoice_lines_draft_only BEFORE INSERT ON app.subscription_invoice_lines
          FOR EACH ROW EXECUTE FUNCTION app.subscription_invoice_lines_draft_only();
        """
    )
    for t in ("subscription_invoices", "subscription_invoice_lines", "subscription_invoice_events"):
        h.tenant_rls(t)
    h.mutable("subscription_invoices")
    h.updated_at("subscription_invoices")
    h.append_only("subscription_invoice_lines")
    h.append_only("subscription_invoice_events")


def downgrade() -> None:
    h.refuse_if_data("subscription_invoices")
    op.execute(
        """
        DROP TABLE IF EXISTS app.subscription_invoice_events;
        DROP TABLE IF EXISTS app.subscription_invoice_lines;
        DROP TABLE IF EXISTS app.subscription_invoices;
        DROP TABLE IF EXISTS app.subscription_invoice_sequences;
        DROP FUNCTION IF EXISTS app.next_subscription_invoice_number(text, text, integer);
        DROP FUNCTION IF EXISTS app.subscription_invoices_freeze();
        DROP FUNCTION IF EXISTS app.subscription_invoice_lines_draft_only();
        """
    )
