"""service requests: guests ask for towels, cleaning, a repair or a wake-up call (D93)

- service_requests (tenant table, RLS): one request for a room, from the room's tablet during
  the active stay or logged by staff (a phone call, a request at the desk). Kinds are fixed;
  the guest's note is free text and is redacted when the guest is anonymised.
  open -> acknowledged -> in_progress -> done, and open/acknowledged/in_progress -> cancelled.
  The transition is enforced by a trigger like orders, so no code path can skip it.
- Permissions requests.view and requests.update for Owner, Admin, GM, Reception Manager,
  Receptionist, Room-Service Manager and Room-Service Staff (the people who already walk the
  floors); the realtime channel hotel:{id}:requests is open to requests.view.

Revision ID: 0037
Revises: 0036
Create Date: 2026-10-16 09:00
"""

from alembic import op

import alembic_helpers as h

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None

ROLES = (
    "hotel_owner",
    "hotel_admin",
    "general_manager",
    "reception_manager",
    "receptionist",
    "room_service_manager",
    "room_service_staff",
)


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    roles = ", ".join(f"'{r}'" for r in ROLES)
    op.execute(
        f"""
        CREATE TABLE app.service_requests (
          id               uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id         uuid NOT NULL REFERENCES app.hotels(id),
          room_id          uuid NOT NULL,
          room_number      text NOT NULL CHECK (length(room_number) BETWEEN 1 AND 20),
          stay_id          uuid,
          kind             text NOT NULL CHECK (kind IN (
                             'towels', 'toiletries', 'pillows', 'cleaning', 'turndown', 'maintenance',
                             'wake_up', 'late_checkout', 'luggage', 'other')),
          note             text CHECK (length(note) <= 300),
          due_at           timestamptz,
          source           text NOT NULL CHECK (source IN ('guest', 'staff')),
          created_by       uuid REFERENCES app.users(id),
          device_id        uuid,
          status           text NOT NULL DEFAULT 'open'
                           CHECK (status IN ('open', 'acknowledged', 'in_progress', 'done', 'cancelled')),
          assigned_to      uuid REFERENCES app.users(id),
          acknowledged_at  timestamptz,
          started_at       timestamptz,
          completed_at     timestamptz,
          cancelled_at     timestamptz,
          cancelled_by     text CHECK (cancelled_by IN ('guest', 'staff')),
          cancel_reason    text CHECK (length(cancel_reason) <= 200),
          created_at       timestamptz NOT NULL DEFAULT now(),
          updated_at       timestamptz NOT NULL DEFAULT now(),
          FOREIGN KEY (hotel_id, room_id) REFERENCES app.rooms(hotel_id, id),
          FOREIGN KEY (hotel_id, stay_id) REFERENCES app.stays(hotel_id, id),
          FOREIGN KEY (hotel_id, device_id) REFERENCES app.devices(hotel_id, id),
          CHECK ((source = 'guest') = (device_id IS NOT NULL)),
          CHECK (source = 'guest' OR created_by IS NOT NULL),
          CHECK (source = 'staff' OR stay_id IS NOT NULL),
          CHECK ((status = 'done') = (completed_at IS NOT NULL)),
          CHECK ((status = 'cancelled') = (cancelled_at IS NOT NULL))
        );
        CREATE INDEX service_requests_open ON app.service_requests (hotel_id, created_at)
          WHERE status IN ('open', 'acknowledged', 'in_progress');
        CREATE INDEX service_requests_recent ON app.service_requests (hotel_id, created_at DESC);
        CREATE INDEX service_requests_stay ON app.service_requests (hotel_id, stay_id) WHERE stay_id IS NOT NULL;

        CREATE FUNCTION app.service_requests_guard() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF (NEW.hotel_id, NEW.room_id, NEW.stay_id, NEW.kind, NEW.source, NEW.created_by, NEW.device_id,
              NEW.created_at)
             IS DISTINCT FROM
             (OLD.hotel_id, OLD.room_id, OLD.stay_id, OLD.kind, OLD.source, OLD.created_by, OLD.device_id,
              OLD.created_at) THEN
            RAISE EXCEPTION 'service request % cannot change who, where or what', OLD.id USING ERRCODE = 'P0004';
          END IF;
          IF NEW.status IS DISTINCT FROM OLD.status AND NOT ((OLD.status, NEW.status) IN (VALUES
               ('open', 'acknowledged'), ('open', 'in_progress'), ('open', 'done'),
               ('acknowledged', 'in_progress'), ('acknowledged', 'done'), ('in_progress', 'done'),
               ('open', 'cancelled'), ('acknowledged', 'cancelled'), ('in_progress', 'cancelled'))) THEN
            RAISE EXCEPTION 'service request cannot move % -> %', OLD.status, NEW.status USING ERRCODE = 'P0004';
          END IF;
          NEW.updated_at := now();
          RETURN NEW;
        END $$;
        CREATE TRIGGER service_requests_guard BEFORE UPDATE ON app.service_requests
          FOR EACH ROW EXECUTE FUNCTION app.service_requests_guard();

        INSERT INTO app.permissions (code, scope, description, sensitive) VALUES
          ('requests.view', 'hotel', 'View guest service requests', false),
          ('requests.update', 'hotel', 'Log, take and complete guest service requests', false);
        INSERT INTO app.role_permissions (role_id, permission_code)
          SELECT r.id, p.code FROM app.roles r
          CROSS JOIN (VALUES ('requests.view'), ('requests.update')) AS p(code)
          WHERE r.hotel_id IS NULL AND r.code IN ({roles});
        """
    )
    h.tenant_rls("service_requests")
    h.mutable("service_requests")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("service_requests")
    op.execute(
        """
        DELETE FROM app.role_permissions WHERE permission_code IN ('requests.view', 'requests.update');
        DELETE FROM app.permissions WHERE code IN ('requests.view', 'requests.update');
        DROP TABLE app.service_requests;
        DROP FUNCTION app.service_requests_guard();
        """
    )
