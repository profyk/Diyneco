"""platform health: signals the worker watches and platform-level events

`HEALTH_DEGRADED` goes to the `platform` channel (API spec) but has no hotel, and the outbox's
tenant policy only admits rows for the current hotel. Two narrow definer functions, for the
worker only: one reads cross-hotel health counters (no tenant data), one queues a platform
event with no hotel and no sequence number (DECISIONS D65).

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-11 10:00
"""

from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

FUNCTIONS = ("app.platform_health_signals()", "app.emit_platform_event(text, jsonb)")


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION app.platform_health_signals()
        RETURNS TABLE (pending_events bigint, oldest_pending_seconds double precision,
                       failed_emails_hour bigint, stuck_emails bigint)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT
            (SELECT count(*) FROM app.event_outbox WHERE published_at IS NULL),
            (SELECT coalesce(extract(epoch FROM now() - min(created_at)), 0)
               FROM app.event_outbox WHERE published_at IS NULL),
            (SELECT count(*) FROM app.notifications
               WHERE status = 'failed' AND created_at > now() - interval '1 hour'),
            (SELECT count(*) FROM app.notifications
               WHERE status = 'queued' AND created_at < now() - interval '15 minutes'
                 AND created_at > now() - interval '1 day')
        $$;

        CREATE FUNCTION app.emit_platform_event(p_type text, p_payload jsonb) RETURNS uuid
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
        DECLARE v_id uuid;
        BEGIN
          IF p_type NOT IN ('HEALTH_DEGRADED', 'HEALTH_RECOVERED') THEN
            RAISE EXCEPTION 'not a platform event: %', p_type;
          END IF;
          INSERT INTO app.event_outbox (hotel_id, seq, type, channels, payload)
          VALUES (NULL, NULL, p_type, ARRAY['platform'], p_payload)
          RETURNING id INTO v_id;
          RETURN v_id;
        END $$;
        """
    )
    for fn in FUNCTIONS:
        op.execute(f"REVOKE ALL ON FUNCTION {fn} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {fn} TO diyneco_worker")


def downgrade() -> None:
    for fn in FUNCTIONS:
        op.execute(f"DROP FUNCTION IF EXISTS {fn}")
