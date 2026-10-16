"""guest feedback: stars and a comment for an order, a request or the stay (D98)

- guest_feedback (tenant table, RLS): one rating per delivered order, per finished service
  request and per stay, from the room's tablet during the stay. 1 to 5 stars and an optional
  comment of up to 500 characters, which is redacted when the guest is anonymised.

Revision ID: 0038
Revises: 0037
Create Date: 2026-10-16 12:00
"""

from alembic import op

import alembic_helpers as h

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE TABLE app.guest_feedback (
          id           uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id     uuid NOT NULL REFERENCES app.hotels(id),
          stay_id      uuid NOT NULL,
          room_id      uuid NOT NULL,
          room_number  text NOT NULL CHECK (length(room_number) BETWEEN 1 AND 20),
          subject      text NOT NULL CHECK (subject IN ('order', 'request', 'stay')),
          order_id     uuid,
          request_id   uuid REFERENCES app.service_requests(id),
          rating       smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
          comment      text CHECK (length(comment) <= 500),
          created_at   timestamptz NOT NULL DEFAULT now(),
          FOREIGN KEY (hotel_id, stay_id) REFERENCES app.stays(hotel_id, id),
          FOREIGN KEY (hotel_id, room_id) REFERENCES app.rooms(hotel_id, id),
          FOREIGN KEY (hotel_id, order_id) REFERENCES app.orders(hotel_id, id),
          CHECK ((subject = 'order') = (order_id IS NOT NULL)),
          CHECK ((subject = 'request') = (request_id IS NOT NULL))
        );
        CREATE UNIQUE INDEX guest_feedback_one_per_order ON app.guest_feedback (order_id) WHERE order_id IS NOT NULL;
        CREATE UNIQUE INDEX guest_feedback_one_per_request ON app.guest_feedback (request_id)
          WHERE request_id IS NOT NULL;
        CREATE UNIQUE INDEX guest_feedback_one_per_stay ON app.guest_feedback (stay_id) WHERE subject = 'stay';
        CREATE INDEX guest_feedback_recent ON app.guest_feedback (hotel_id, created_at DESC);
        """
    )
    h.tenant_rls("guest_feedback")
    h.mutable("guest_feedback")  # only to redact a comment when the guest is anonymised


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("guest_feedback")
    op.execute("DROP TABLE app.guest_feedback")
