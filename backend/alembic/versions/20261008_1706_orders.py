"""orders and deliveries: orders, items, modifiers, status history (partitioned), deliveries,
order state machine and amount lock

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-08 17:06
"""

import alembic_helpers as h
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE TABLE app.order_number_sequences (
          hotel_id     uuid PRIMARY KEY REFERENCES app.hotels(id),
          next_number  bigint NOT NULL DEFAULT 10001
        );

        CREATE TABLE app.orders (
          id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id          uuid NOT NULL REFERENCES app.hotels(id),
          number            bigint NOT NULL,
          stay_id           uuid NOT NULL,
          room_id           uuid NOT NULL,
          room_number       text NOT NULL,
          device_id         uuid,
          placed_by_user    uuid,
          late_reason       text,
          status            text NOT NULL CHECK (status IN ('PENDING_APPROVAL','NEW','ACCEPTED','PREPARING','READY',
                                               'ASSIGNED','PICKED_UP','DELIVERED','CLOSED','DECLINED','CANCELLED')),
          payment_method    text NOT NULL DEFAULT 'room_charge' CHECK (payment_method IN ('room_charge','card_terminal','cash')),
          special_instructions text CHECK (length(special_instructions) <= 500),
          subtotal_minor    bigint NOT NULL CHECK (subtotal_minor >= 0),
          fee_minor         bigint NOT NULL DEFAULT 0 CHECK (fee_minor >= 0),
          total_minor       bigint NOT NULL,
          vat_minor         bigint NOT NULL DEFAULT 0,
          currency          char(3) NOT NULL DEFAULT 'ZAR',
          needs_approval    boolean NOT NULL DEFAULT false,
          approved_by       uuid REFERENCES app.users(id),
          approved_at       timestamptz,
          decline_reason    text,
          posted_to_folio   boolean NOT NULL DEFAULT false,
          locked_at         timestamptz,
          accepted_at       timestamptz,
          ready_at          timestamptz,
          closed_at         timestamptz,
          idempotency_key   uuid NOT NULL,
          created_at        timestamptz NOT NULL DEFAULT now(),
          updated_at        timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, id),
          UNIQUE (hotel_id, number),
          UNIQUE (hotel_id, idempotency_key),
          FOREIGN KEY (hotel_id, stay_id) REFERENCES app.stays(hotel_id, id),
          FOREIGN KEY (hotel_id, room_id) REFERENCES app.rooms(hotel_id, id),
          CHECK (total_minor = subtotal_minor + fee_minor)
        );
        CREATE INDEX orders_active ON app.orders(hotel_id, status)
          WHERE status NOT IN ('CLOSED','DECLINED','CANCELLED');
        CREATE INDEX orders_stay ON app.orders(stay_id, created_at);

        -- G6: order references created earlier in 0005 become composite foreign keys
        ALTER TABLE app.folio_entries ADD FOREIGN KEY (hotel_id, order_id) REFERENCES app.orders(hotel_id, id);
        ALTER TABLE app.adjustments  ADD FOREIGN KEY (hotel_id, order_id) REFERENCES app.orders(hotel_id, id);

        CREATE TABLE app.order_items (
          id                 uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id           uuid NOT NULL,
          order_id           uuid NOT NULL,
          menu_item_id       uuid,
          station_id         uuid NOT NULL,
          name               text NOT NULL,
          description        text,
          charge_category_code text NOT NULL,
          unit_price_minor   bigint NOT NULL CHECK (unit_price_minor >= 0),
          quantity           integer NOT NULL CHECK (quantity BETWEEN 1 AND 99),
          line_total_minor   bigint NOT NULL,
          vat_rate_bp        integer NOT NULL,
          vat_minor          bigint NOT NULL,
          note               text CHECK (length(note) <= 200),
          prep_status        text NOT NULL DEFAULT 'PENDING' CHECK (prep_status IN ('PENDING','PREPARING','READY')),
          ready_at           timestamptz,
          ready_by           uuid,
          UNIQUE (hotel_id, id),                                       -- G6
          FOREIGN KEY (hotel_id, order_id)   REFERENCES app.orders(hotel_id, id),
          FOREIGN KEY (hotel_id, station_id) REFERENCES app.kitchen_stations(hotel_id, id),
          CHECK (line_total_minor = unit_price_minor * quantity)
        );
        CREATE INDEX order_items_station ON app.order_items(hotel_id, station_id, prep_status);

        CREATE TABLE app.order_item_modifiers (
          id                 uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id           uuid NOT NULL,
          order_item_id      uuid NOT NULL,
          modifier_id        uuid,
          group_name         text NOT NULL,
          name               text NOT NULL,
          price_delta_minor  bigint NOT NULL DEFAULT 0,
          FOREIGN KEY (hotel_id, order_item_id) REFERENCES app.order_items(hotel_id, id)  -- G6
        );

        CREATE TABLE app.order_status_history (
          id           bigint GENERATED ALWAYS AS IDENTITY,
          hotel_id     uuid NOT NULL,
          order_id     uuid NOT NULL,
          from_status  text,
          to_status    text NOT NULL,
          actor_user   uuid,
          actor_device uuid,
          note         text,
          created_at   timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (id, created_at),
          FOREIGN KEY (hotel_id, order_id) REFERENCES app.orders(hotel_id, id)       -- G6
        ) PARTITION BY RANGE (created_at);
        CREATE INDEX order_status_history_order ON app.order_status_history(order_id, created_at);

        CREATE TABLE app.deliveries (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid NOT NULL,
          order_id      uuid NOT NULL UNIQUE,
          assigned_to   uuid REFERENCES app.users(id),
          assigned_by   uuid REFERENCES app.users(id),
          assigned_at   timestamptz,
          picked_up_at  timestamptz,
          delivered_at  timestamptz,
          released_count smallint NOT NULL DEFAULT 0,
          FOREIGN KEY (hotel_id, order_id) REFERENCES app.orders(hotel_id, id),
          CHECK (picked_up_at IS NULL OR assigned_at IS NOT NULL),
          CHECK (delivered_at IS NULL OR picked_up_at IS NOT NULL)
        );

        -- Order state machine, amount lock and status history
        CREATE FUNCTION app.order_transition_allowed(f text, t text) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
          SELECT (f, t) IN (VALUES
            ('PENDING_APPROVAL','NEW'), ('PENDING_APPROVAL','DECLINED'),
            ('NEW','ACCEPTED'), ('NEW','CANCELLED'), ('ACCEPTED','PREPARING'), ('ACCEPTED','CANCELLED'),
            ('PREPARING','READY'), ('READY','ASSIGNED'), ('ASSIGNED','READY'),
            ('ASSIGNED','PICKED_UP'), ('PICKED_UP','DELIVERED'), ('DELIVERED','CLOSED'))
        $$;

        CREATE FUNCTION app.orders_guard_transition() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF OLD.locked_at IS NOT NULL AND
             (NEW.subtotal_minor, NEW.fee_minor, NEW.total_minor, NEW.vat_minor, NEW.stay_id, NEW.room_id)
             IS DISTINCT FROM
             (OLD.subtotal_minor, OLD.fee_minor, OLD.total_minor, OLD.vat_minor, OLD.stay_id, OLD.room_id) THEN
            RAISE EXCEPTION 'order % amounts are locked', OLD.number USING ERRCODE = 'P0003';
          END IF;
          IF NEW.status IS DISTINCT FROM OLD.status THEN
            IF NOT app.order_transition_allowed(OLD.status, NEW.status) THEN
              RAISE EXCEPTION 'order % cannot move % -> %', OLD.number, OLD.status, NEW.status USING ERRCODE = 'P0004';
            END IF;
            INSERT INTO app.order_status_history (hotel_id, order_id, from_status, to_status, actor_user, actor_device)
            VALUES (NEW.hotel_id, NEW.id, OLD.status, NEW.status,
                    nullif(current_setting('app.actor_user', true), '')::uuid,
                    nullif(current_setting('app.actor_device', true), '')::uuid);
          END IF;
          NEW.updated_at := now();
          RETURN NEW;
        END $$;
        CREATE TRIGGER orders_guard BEFORE UPDATE ON app.orders
          FOR EACH ROW EXECUTE FUNCTION app.orders_guard_transition();
        """
    )
    for t in ("order_number_sequences", "orders", "order_items", "order_item_modifiers",
              "order_status_history", "deliveries"):
        h.tenant_rls(t)
    h.append_only("order_status_history")
    for t in ("order_number_sequences", "orders", "order_items", "deliveries"):
        h.mutable(t)
    # Partitions are created by app.ensure_partitions() in migration 0009.


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("orders")
    op.execute("ALTER TABLE app.folio_entries DROP CONSTRAINT IF EXISTS folio_entries_hotel_id_order_id_fkey")
    op.execute("ALTER TABLE app.adjustments DROP CONSTRAINT IF EXISTS adjustments_hotel_id_order_id_fkey")
    h.drop_tables("deliveries", "order_status_history", "order_item_modifiers", "order_items",
                  "orders", "order_number_sequences")
    op.execute("DROP FUNCTION IF EXISTS app.orders_guard_transition()")
    op.execute("DROP FUNCTION IF EXISTS app.order_transition_allowed(text, text)")
