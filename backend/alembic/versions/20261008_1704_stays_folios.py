"""guests, stays and folios: guests, billing profiles, stays, folios, charge categories,
folio entries (append-only), adjustments, discounts, folio_balances view

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-08 17:04
"""

import alembic_helpers as h
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE TABLE app.guests (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
          full_name     text NOT NULL,
          email         citext,
          phone         text,
          id_number_enc bytea,
          nationality   char(2),
          anonymised_at timestamptz,
          created_at    timestamptz NOT NULL DEFAULT now(),
          updated_at    timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, id)
        );
        CREATE INDEX guests_search ON app.guests USING gin (hotel_id, full_name gin_trgm_ops);

        CREATE TABLE app.billing_profiles (
          id                  uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id            uuid NOT NULL REFERENCES app.hotels(id),
          company_name        text NOT NULL,
          registration_number text,
          vat_number          text,
          billing_address     jsonb NOT NULL DEFAULT '{}',
          billing_email       citext,
          created_at          timestamptz NOT NULL DEFAULT now(),
          updated_at          timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, id)
        );

        CREATE TABLE app.stays (
          id                 uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id           uuid NOT NULL REFERENCES app.hotels(id),
          room_id            uuid NOT NULL,
          guest_id           uuid NOT NULL,
          billing_type       text NOT NULL DEFAULT 'personal' CHECK (billing_type IN ('personal','company')),
          billing_profile_id uuid,
          purchase_order     text,
          traveller_name     text,
          status             text NOT NULL DEFAULT 'reserved'
                             CHECK (status IN ('reserved','checked_in','active','checkout_pending','checked_out','cancelled')),
          arrival_date       date NOT NULL,
          departure_date     date NOT NULL,
          nightly_rate_minor bigint NOT NULL CHECK (nightly_rate_minor >= 0),
          rate_override_reason text,
          currency           char(3) NOT NULL DEFAULT 'ZAR',
          charges_blocked    boolean NOT NULL DEFAULT false,
          is_training        boolean NOT NULL DEFAULT false,
          checked_in_at      timestamptz,
          checked_in_by      uuid,
          checked_out_at     timestamptz,
          checked_out_by     uuid,
          checkout_override_reason text,
          created_at         timestamptz NOT NULL DEFAULT now(),
          updated_at         timestamptz NOT NULL DEFAULT now(),
          version            integer NOT NULL DEFAULT 1,
          UNIQUE (hotel_id, id),
          FOREIGN KEY (hotel_id, room_id)  REFERENCES app.rooms(hotel_id, id),
          FOREIGN KEY (hotel_id, guest_id) REFERENCES app.guests(hotel_id, id),
          FOREIGN KEY (hotel_id, billing_profile_id) REFERENCES app.billing_profiles(hotel_id, id),
          CHECK (departure_date > arrival_date),
          CHECK (billing_type = 'personal' OR billing_profile_id IS NOT NULL)
        );
        CREATE UNIQUE INDEX stays_one_live_per_room ON app.stays(room_id)
          WHERE status IN ('checked_in','active','checkout_pending');
        CREATE INDEX stays_dates ON app.stays(hotel_id, arrival_date, departure_date);

        CREATE TABLE app.folios (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
          stay_id       uuid NOT NULL,
          status        text NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
          currency      char(3) NOT NULL DEFAULT 'ZAR',
          closed_at     timestamptz,
          created_at    timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, id),
          UNIQUE (stay_id),
          FOREIGN KEY (hotel_id, stay_id) REFERENCES app.stays(hotel_id, id)
        );

        CREATE TABLE app.charge_categories (
          id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id    uuid REFERENCES app.hotels(id),
          code        text NOT NULL,
          name        text NOT NULL,
          revenue_group text NOT NULL CHECK (revenue_group IN ('accommodation','fnb','other','tip','payment')),
          vat_rate_bp integer,
          is_revenue  boolean NOT NULL,
          UNIQUE NULLS NOT DISTINCT (hotel_id, code)
        );

        CREATE TABLE app.folio_entries (
          id              uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id        uuid NOT NULL,
          folio_id        uuid NOT NULL,
          entry_type      text NOT NULL CHECK (entry_type IN ('charge','payment','tip','reversal','adjustment','discount')),
          category_id     uuid NOT NULL REFERENCES app.charge_categories(id),
          description     text NOT NULL,
          quantity        integer NOT NULL DEFAULT 1 CHECK (quantity > 0),
          unit_amount_minor bigint NOT NULL,
          amount_minor    bigint NOT NULL,
          vat_rate_bp     integer NOT NULL DEFAULT 0,
          vat_minor       bigint NOT NULL DEFAULT 0,
          currency        char(3) NOT NULL DEFAULT 'ZAR',
          business_date   date NOT NULL,
          order_id        uuid,
          payment_id      uuid,
          reverses_entry_id uuid,
          adjustment_id   uuid,
          created_by      uuid,
          created_by_device uuid,
          created_at      timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, id),                                    -- target of composite FKs (G6)
          FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
          FOREIGN KEY (hotel_id, reverses_entry_id) REFERENCES app.folio_entries(hotel_id, id),  -- G6
          CHECK (amount_minor = unit_amount_minor * quantity),
          CHECK (entry_type <> 'reversal' OR reverses_entry_id IS NOT NULL)
        );
        CREATE INDEX folio_entries_folio ON app.folio_entries(folio_id, created_at);
        CREATE INDEX folio_entries_reporting ON app.folio_entries(hotel_id, business_date, category_id);

        CREATE TABLE app.adjustments (
          id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id          uuid NOT NULL REFERENCES app.hotels(id),
          folio_id          uuid NOT NULL,
          target_entry_id   uuid,
          order_id          uuid,
          original_minor    bigint NOT NULL,
          new_minor         bigint NOT NULL CHECK (new_minor >= 0),
          reason            text NOT NULL CHECK (length(reason) >= 3),
          status            text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
          requested_by      uuid NOT NULL REFERENCES app.users(id),
          requested_at      timestamptz NOT NULL DEFAULT now(),
          decided_by        uuid REFERENCES app.users(id),
          decided_at        timestamptz,
          decision_note     text,
          UNIQUE (hotel_id, id),
          FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
          FOREIGN KEY (hotel_id, target_entry_id) REFERENCES app.folio_entries(hotel_id, id),   -- G6
          CHECK (decided_by IS NULL OR decided_by <> requested_by)
        );

        ALTER TABLE app.folio_entries
          ADD FOREIGN KEY (hotel_id, adjustment_id) REFERENCES app.adjustments(hotel_id, id);  -- G6

        CREATE TABLE app.discounts (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
          folio_id      uuid NOT NULL,
          kind          text NOT NULL CHECK (kind IN ('percent','fixed')),
          percent_bp    integer CHECK (percent_bp BETWEEN 1 AND 10000),
          amount_minor  bigint CHECK (amount_minor > 0),
          applies_to    text NOT NULL CHECK (applies_to IN ('accommodation','fnb','other','all')),
          reason        text NOT NULL,
          created_by    uuid NOT NULL REFERENCES app.users(id),
          created_at    timestamptz NOT NULL DEFAULT now(),
          FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
          CHECK ((kind = 'percent') = (percent_bp IS NOT NULL) AND (kind = 'fixed') = (amount_minor IS NOT NULL))
        );

        -- Read model used by the API, reports and checkout. security_invoker so the caller's
        -- RLS applies; a plain view would run as its owner and show every hotel (DECISIONS G1).
        CREATE VIEW app.folio_balances WITH (security_invoker = true) AS
        SELECT f.id AS folio_id, f.hotel_id, f.stay_id,
          sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'accommodation') AS accommodation_minor,
          sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'fnb')           AS fnb_minor,
          sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'other')         AS other_minor,
          sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'tip')           AS tips_minor,
          -sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'payment')      AS paid_minor,
          coalesce(sum(e.amount_minor) FILTER (WHERE c.revenue_group <> 'tip'), 0) AS balance_minor
        FROM app.folios f
        LEFT JOIN app.folio_entries e ON e.folio_id = f.id
        LEFT JOIN app.charge_categories c ON c.id = e.category_id
        GROUP BY f.id;
        GRANT SELECT ON app.folio_balances TO diyneco_api, diyneco_worker;

        -- No entries on a closed folio. A folio this hotel cannot see counts as not open.
        CREATE FUNCTION app.folio_must_be_open() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF coalesce((SELECT status FROM app.folios WHERE id = NEW.folio_id), 'missing') <> 'open' THEN
            RAISE EXCEPTION 'folio % is closed', NEW.folio_id USING ERRCODE = 'P0002';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER folio_entries_open BEFORE INSERT ON app.folio_entries
          FOR EACH ROW EXECUTE FUNCTION app.folio_must_be_open();
        """
    )
    for t in ("guests", "billing_profiles", "stays"):
        h.updated_at(t)
    for t in ("guests", "billing_profiles", "stays", "folios", "folio_entries", "adjustments", "discounts"):
        h.tenant_rls(t)
    h.shared_catalogue_rls("charge_categories", "categories_visible")
    h.shared_ref("folio_entries", "category_id", "charge_categories")  # G6

    h.append_only("folio_entries")
    for t in ("guests", "billing_profiles", "stays", "folios", "charge_categories", "adjustments"):
        h.mutable(t)


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("guests", "stays", "folio_entries")
    op.execute("DROP VIEW IF EXISTS app.folio_balances")
    op.execute("DROP FUNCTION IF EXISTS app.folio_must_be_open() CASCADE")
    h.drop_tables(
        "discounts", "folio_entries", "adjustments", "charge_categories",
        "folios", "stays", "billing_profiles", "guests",
    )
