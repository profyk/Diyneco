"""property and devices: room types, rooms, kitchen stations, devices, pairings

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-08 17:03
"""

import alembic_helpers as h
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

TABLES = ("room_types", "rooms", "kitchen_stations", "devices", "device_stations", "device_pairings")


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE TABLE app.room_types (
          id               uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id         uuid NOT NULL REFERENCES app.hotels(id),
          name             text NOT NULL,
          base_rate_minor  bigint NOT NULL CHECK (base_rate_minor >= 0),
          currency         char(3) NOT NULL DEFAULT 'ZAR',
          capacity         smallint NOT NULL DEFAULT 2 CHECK (capacity BETWEEN 1 AND 20),
          amenities        text[] NOT NULL DEFAULT '{}',
          created_at       timestamptz NOT NULL DEFAULT now(),
          updated_at       timestamptz NOT NULL DEFAULT now(),
          deleted_at       timestamptz,
          version          integer NOT NULL DEFAULT 1,
          UNIQUE (hotel_id, id)
        );
        CREATE UNIQUE INDEX room_types_name ON app.room_types(hotel_id, lower(name)) WHERE deleted_at IS NULL;

        CREATE TABLE app.rooms (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
          room_type_id  uuid NOT NULL,
          number        text NOT NULL,
          floor         text,
          rate_minor    bigint CHECK (rate_minor >= 0),
          capacity      smallint,
          amenities     text[] NOT NULL DEFAULT '{}',
          status        text NOT NULL DEFAULT 'available'
                        CHECK (status IN ('available','occupied','reserved','cleaning','maintenance','out_of_service')),
          status_changed_at timestamptz NOT NULL DEFAULT now(),
          created_at    timestamptz NOT NULL DEFAULT now(),
          updated_at    timestamptz NOT NULL DEFAULT now(),
          deleted_at    timestamptz,
          version       integer NOT NULL DEFAULT 1,
          UNIQUE (hotel_id, id),
          FOREIGN KEY (hotel_id, room_type_id) REFERENCES app.room_types(hotel_id, id)
        );
        CREATE UNIQUE INDEX rooms_number ON app.rooms(hotel_id, number) WHERE deleted_at IS NULL;
        CREATE INDEX rooms_status ON app.rooms(hotel_id, status) WHERE deleted_at IS NULL;

        CREATE TABLE app.kitchen_stations (
          id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id    uuid NOT NULL REFERENCES app.hotels(id),
          name        text NOT NULL,
          sort_order  smallint NOT NULL DEFAULT 0,
          is_active   boolean NOT NULL DEFAULT true,
          created_at  timestamptz NOT NULL DEFAULT now(),
          updated_at  timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, id),
          UNIQUE (hotel_id, name)
        );

        CREATE TABLE app.devices (
          id               uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id         uuid NOT NULL REFERENCES app.hotels(id),
          label            text NOT NULL,
          kind             text NOT NULL CHECK (kind IN ('guest','kitchen')),
          room_id          uuid,
          credential_hash  bytea,
          status           text NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active','locked','disabled','reset_required','revoked')),
          os               text,
          app_version      text,
          last_seen_at     timestamptz,
          last_ip          inet,
          paired_at        timestamptz,
          revoked_at       timestamptz,
          created_at       timestamptz NOT NULL DEFAULT now(),
          updated_at       timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, id),
          UNIQUE (hotel_id, label),
          FOREIGN KEY (hotel_id, room_id) REFERENCES app.rooms(hotel_id, id),
          CHECK (kind <> 'guest' OR room_id IS NOT NULL OR status = 'revoked'),
          CHECK (kind <> 'kitchen' OR room_id IS NULL)
        );
        CREATE UNIQUE INDEX devices_one_guest_per_room ON app.devices(room_id)
          WHERE kind = 'guest' AND status <> 'revoked';
        CREATE INDEX devices_last_seen ON app.devices(hotel_id, last_seen_at);

        CREATE TABLE app.device_stations (
          hotel_id    uuid NOT NULL,
          device_id   uuid NOT NULL,
          station_id  uuid NOT NULL,
          PRIMARY KEY (device_id, station_id),
          FOREIGN KEY (hotel_id, device_id)  REFERENCES app.devices(hotel_id, id),
          FOREIGN KEY (hotel_id, station_id) REFERENCES app.kitchen_stations(hotel_id, id)
        );

        CREATE TABLE app.device_pairings (
          id           uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id     uuid NOT NULL REFERENCES app.hotels(id),
          kind         text NOT NULL CHECK (kind IN ('guest','kitchen')),
          room_id      uuid,
          station_ids  uuid[],
          code_hash    bytea NOT NULL,
          created_by   uuid NOT NULL REFERENCES app.users(id),
          expires_at   timestamptz NOT NULL,
          used_at      timestamptz,
          used_by_device uuid,
          attempts     smallint NOT NULL DEFAULT 0,
          created_at   timestamptz NOT NULL DEFAULT now(),
          FOREIGN KEY (hotel_id, room_id) REFERENCES app.rooms(hotel_id, id)
        );
        CREATE UNIQUE INDEX device_pairings_live_code ON app.device_pairings(code_hash) WHERE used_at IS NULL;
        """
    )
    for t in ("room_types", "rooms", "kitchen_stations", "devices"):
        h.updated_at(t)
    for t in TABLES:
        h.tenant_rls(t)
    for t in ("room_types", "rooms", "kitchen_stations", "devices", "device_pairings"):
        h.mutable(t)
    op.execute("GRANT DELETE ON app.device_stations TO diyneco_api")

    # Pairing runs before any hotel context exists, so it goes through one narrow definer function.
    op.execute(
        """
        CREATE FUNCTION app.redeem_pairing(p_code_hash bytea) RETURNS TABLE (pairing_id uuid, hotel_id uuid)
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          UPDATE app.device_pairings SET used_at = now()
          WHERE code_hash = p_code_hash AND used_at IS NULL AND expires_at > now()
          RETURNING id, hotel_id
        $$;
        REVOKE ALL ON FUNCTION app.redeem_pairing(bytea) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.redeem_pairing(bytea) TO diyneco_api;
        """
    )


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("rooms", "devices")
    op.execute("DROP FUNCTION IF EXISTS app.redeem_pairing(bytea)")
    h.drop_tables(*reversed(TABLES))
