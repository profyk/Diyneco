"""payments, tips and invoices (all append-only), invoice sequences, daily closes

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-08 17:07
"""

import alembic_helpers as h
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

APPEND_ONLY = ("payments", "payment_allocations", "tips", "invoices", "invoice_items")


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE TABLE app.payments (
          id                      uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id                uuid NOT NULL REFERENCES app.hotels(id),
          folio_id                uuid NOT NULL,
          order_id                uuid,
          method                  text NOT NULL CHECK (method IN ('room_charge','card_terminal','cash','eft','gateway')),
          status                  text NOT NULL CHECK (status IN ('pending','paid','partial','failed','refunded')),
          amount_due_minor        bigint NOT NULL CHECK (amount_due_minor >= 0),
          amount_received_minor   bigint NOT NULL CHECK (amount_received_minor >= 0),
          tip_amount_minor        bigint NOT NULL DEFAULT 0 CHECK (tip_amount_minor >= 0),
          currency                char(3) NOT NULL DEFAULT 'ZAR',
          provider                text,
          provider_reference      text,
          external_transaction_id text,
          recorded_by             uuid REFERENCES app.users(id),
          recorded_by_device      uuid,
          occurred_at             timestamptz NOT NULL DEFAULT now(),
          late_reason             text,
          idempotency_key         uuid NOT NULL,
          created_at              timestamptz NOT NULL DEFAULT now(),
          CHECK (occurred_at >= created_at - interval '72 hours'),
          CHECK (late_reason IS NOT NULL OR occurred_at >= created_at - interval '10 minutes'),
          UNIQUE (hotel_id, id),                                          -- G6
          UNIQUE (hotel_id, idempotency_key),
          FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
          FOREIGN KEY (hotel_id, order_id) REFERENCES app.orders(hotel_id, id),   -- G6
          CHECK (tip_amount_minor = greatest(0, amount_received_minor - amount_due_minor)),
          CHECK (method <> 'card_terminal' OR provider_reference ~ '^[A-Za-z0-9-]{4,20}$')
        );
        CREATE UNIQUE INDEX payments_one_per_order ON app.payments(order_id)
          WHERE order_id IS NOT NULL AND status IN ('paid','partial');

        ALTER TABLE app.folio_entries ADD FOREIGN KEY (hotel_id, payment_id) REFERENCES app.payments(hotel_id, id);  -- G6

        CREATE TABLE app.payment_allocations (
          id             uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id       uuid NOT NULL,
          payment_id     uuid NOT NULL,
          folio_entry_id uuid NOT NULL,
          amount_minor   bigint NOT NULL CHECK (amount_minor > 0),
          created_at     timestamptz NOT NULL DEFAULT now(),
          FOREIGN KEY (hotel_id, payment_id)     REFERENCES app.payments(hotel_id, id),       -- G6
          FOREIGN KEY (hotel_id, folio_entry_id) REFERENCES app.folio_entries(hotel_id, id)   -- G6
        );

        CREATE TABLE app.tips (
          id             uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id       uuid NOT NULL,
          payment_id     uuid NOT NULL UNIQUE,
          folio_entry_id uuid NOT NULL,
          amount_minor   bigint NOT NULL CHECK (amount_minor > 0),
          staff_user_id  uuid REFERENCES app.users(id),
          confirmed_by   uuid NOT NULL REFERENCES app.users(id),
          confirmed_at   timestamptz NOT NULL DEFAULT now(),
          FOREIGN KEY (hotel_id, payment_id)     REFERENCES app.payments(hotel_id, id),       -- G6
          FOREIGN KEY (hotel_id, folio_entry_id) REFERENCES app.folio_entries(hotel_id, id)   -- G6
        );

        CREATE TABLE app.invoice_sequences (
          hotel_id     uuid NOT NULL REFERENCES app.hotels(id),
          year         smallint NOT NULL,
          next_number  integer NOT NULL DEFAULT 1,
          PRIMARY KEY (hotel_id, year)
        );

        CREATE TABLE app.invoices (
          id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id          uuid NOT NULL REFERENCES app.hotels(id),
          folio_id          uuid NOT NULL,
          number            text NOT NULL,
          kind              text NOT NULL CHECK (kind IN ('tax_invoice','abridged_tax_invoice','guest_statement','credit_note')),
          credits_invoice_id uuid,
          issued_at         timestamptz NOT NULL DEFAULT now(),
          supplier          jsonb NOT NULL,
          recipient         jsonb NOT NULL,
          totals            jsonb NOT NULL,
          currency          char(3) NOT NULL DEFAULT 'ZAR',
          pdf_path          text,
          pdf_sha256        bytea,
          created_by        uuid REFERENCES app.users(id),
          UNIQUE (hotel_id, id),                                                         -- G6
          UNIQUE (hotel_id, number),
          FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
          FOREIGN KEY (hotel_id, credits_invoice_id) REFERENCES app.invoices(hotel_id, id),  -- G6
          CHECK ((kind = 'credit_note') = (credits_invoice_id IS NOT NULL))
        );

        CREATE TABLE app.invoice_items (
          id             uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id       uuid NOT NULL,
          invoice_id     uuid NOT NULL,
          folio_entry_id uuid,
          line_no        smallint NOT NULL,
          category       text NOT NULL,
          description    text NOT NULL,
          quantity       integer NOT NULL,
          amount_minor   bigint NOT NULL,
          vat_rate_bp    integer NOT NULL,
          vat_minor      bigint NOT NULL,
          UNIQUE (invoice_id, line_no),
          FOREIGN KEY (hotel_id, invoice_id)     REFERENCES app.invoices(hotel_id, id),       -- G6
          FOREIGN KEY (hotel_id, folio_entry_id) REFERENCES app.folio_entries(hotel_id, id)   -- G6
        );

        CREATE TABLE app.daily_closes (
          hotel_id                     uuid NOT NULL REFERENCES app.hotels(id),
          business_date                date NOT NULL,
          terminal_batch_total_minor   bigint CHECK (terminal_batch_total_minor >= 0),
          cash_counted_minor           bigint CHECK (cash_counted_minor >= 0),
          card_recorded_minor          bigint,
          cash_recorded_minor          bigint,
          flags                        jsonb NOT NULL DEFAULT '[]',
          notes                        text,
          reviewed_by                  uuid REFERENCES app.users(id),
          reviewed_at                  timestamptz,
          PRIMARY KEY (hotel_id, business_date)
        );
        """
    )
    for t in (*APPEND_ONLY, "invoice_sequences", "daily_closes"):
        h.tenant_rls(t)
    for t in APPEND_ONLY:
        h.append_only(t)
    h.mutable("invoice_sequences")
    h.mutable("daily_closes")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("payments", "invoices")
    op.execute("ALTER TABLE app.folio_entries DROP CONSTRAINT IF EXISTS folio_entries_hotel_id_payment_id_fkey")
    h.drop_tables("daily_closes", "invoice_items", "invoices", "invoice_sequences",
                  "tips", "payment_allocations", "payments")
