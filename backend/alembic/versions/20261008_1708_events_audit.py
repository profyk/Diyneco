"""integrations, events, idempotency and audit: api keys, webhooks, notifications, event
sequence and outbox, idempotency keys, audit logs (partitioned), PII catalogue, partition
maintenance and worker functions

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-08 17:08
"""

import alembic_helpers as h
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

PII_COLUMNS = [
    # table, column, category, anonymise_to
    ("guests", "full_name", "identity", "redacted"),
    ("guests", "email", "contact", "null"),
    ("guests", "phone", "contact", "null"),
    ("guests", "id_number_enc", "government_id", "null"),
    ("stays", "traveller_name", "identity", "redacted"),
    ("orders", "special_instructions", "free_text", "redacted"),
    ("order_items", "note", "free_text", "redacted"),
    ("billing_profiles", "billing_email", "contact", "null"),
    ("notifications", "recipient", "contact", "hash"),
    ("users", "name", "identity", "redacted"),
    ("users", "email", "contact", "hash"),
    ("invitations", "email", "contact", "hash"),
    ("invitations", "name", "identity", "redacted"),
]


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE TABLE app.api_keys (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
          name          text NOT NULL,
          environment   text NOT NULL CHECK (environment IN ('sandbox','production')),
          prefix        text NOT NULL UNIQUE,
          secret_hash   bytea NOT NULL,
          scopes        text[] NOT NULL,
          created_by    uuid NOT NULL REFERENCES app.users(id),
          created_at    timestamptz NOT NULL DEFAULT now(),
          last_used_at  timestamptz,
          usage_count   bigint NOT NULL DEFAULT 0,
          revoked_at    timestamptz
        );

        CREATE TABLE app.webhooks (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
          url           text NOT NULL CHECK (url LIKE 'https://%'),
          events        text[] NOT NULL,
          secret_enc    bytea NOT NULL,
          status        text NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled')),
          failure_count integer NOT NULL DEFAULT 0,
          created_at    timestamptz NOT NULL DEFAULT now(),
          UNIQUE (hotel_id, id)                                                        -- G6
        );

        CREATE TABLE app.webhook_deliveries (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid NOT NULL,
          webhook_id    uuid NOT NULL,
          event_id      uuid NOT NULL,
          attempt       smallint NOT NULL,
          status_code   smallint,
          error         text,
          next_attempt_at timestamptz,
          created_at    timestamptz NOT NULL DEFAULT now(),
          FOREIGN KEY (hotel_id, webhook_id) REFERENCES app.webhooks(hotel_id, id)       -- G6
        );

        CREATE TABLE app.notifications (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid REFERENCES app.hotels(id),
          channel       text NOT NULL CHECK (channel IN ('in_app','email','push','sms','whatsapp')),
          template      text NOT NULL,
          recipient     text NOT NULL,
          subject_ref   jsonb NOT NULL DEFAULT '{}',
          status        text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','sent','failed','read')),
          provider_message_id text,
          error         text,
          created_at    timestamptz NOT NULL DEFAULT now(),
          sent_at       timestamptz
        );

        CREATE TABLE app.event_seq (
          hotel_id  uuid PRIMARY KEY REFERENCES app.hotels(id),
          last_seq  bigint NOT NULL DEFAULT 0
        );

        CREATE TABLE app.event_outbox (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id      uuid REFERENCES app.hotels(id),
          seq           bigint,
          type          text NOT NULL,
          channels      text[] NOT NULL,
          payload       jsonb NOT NULL,
          created_at    timestamptz NOT NULL DEFAULT now(),
          published_at  timestamptz,
          attempts      smallint NOT NULL DEFAULT 0
        );
        CREATE INDEX event_outbox_pending ON app.event_outbox(created_at) WHERE published_at IS NULL;
        CREATE INDEX event_outbox_replay ON app.event_outbox(hotel_id, seq);

        CREATE TABLE app.idempotency_keys (
          principal_key  text NOT NULL,
          key            uuid NOT NULL,
          method         text NOT NULL,
          path           text NOT NULL,
          request_hash   bytea NOT NULL,
          status         text NOT NULL CHECK (status IN ('in_progress','completed')),
          response_code  smallint,
          response_body  jsonb,
          created_at     timestamptz NOT NULL DEFAULT now(),
          expires_at     timestamptz NOT NULL DEFAULT now() + interval '24 hours',
          PRIMARY KEY (principal_key, key)
        );
        CREATE INDEX idempotency_keys_expiry ON app.idempotency_keys(expires_at);

        CREATE TABLE app.audit_logs (
          id            bigint GENERATED ALWAYS AS IDENTITY,
          hotel_id      uuid,
          actor_type    text NOT NULL CHECK (actor_type IN ('user','device','api_key','system','platform')),
          actor_id      uuid,
          actor_label   text NOT NULL,
          action        text NOT NULL,
          entity_type   text NOT NULL,
          entity_id     uuid,
          old_value     jsonb,
          new_value     jsonb,
          reason        text,
          ip            inet,
          device_id     uuid,
          request_id    text,
          created_at    timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at);
        CREATE INDEX audit_logs_hotel ON app.audit_logs(hotel_id, created_at DESC);
        CREATE INDEX audit_logs_entity ON app.audit_logs(entity_type, entity_id);

        CREATE TABLE app.pii_columns (
          table_name   text NOT NULL,
          column_name  text NOT NULL,
          category     text NOT NULL CHECK (category IN ('identity','contact','government_id','free_text')),
          anonymise_to text NOT NULL,
          PRIMARY KEY (table_name, column_name)
        );
        """
    )
    for t in ("api_keys", "webhooks", "webhook_deliveries", "event_seq", "event_outbox"):
        h.tenant_rls(t)
    # audit_logs and notifications: platform-level rows have hotel_id NULL. Hotels read only
    # their own rows; a NULL row can be written but never read back by the app roles.
    for t, policy in (("audit_logs", "audit_hotel"), ("notifications", "notifications_hotel")):
        op.execute(f"ALTER TABLE app.{t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE app.{t} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {policy} ON app.{t} "
            "USING (hotel_id = app.current_hotel_id()) "
            "WITH CHECK (hotel_id IS NULL OR hotel_id = app.current_hotel_id())"
        )
    h.append_only("audit_logs")

    h.read_only("pii_columns")
    for t in ("api_keys", "webhooks", "event_seq"):
        h.mutable(t)
    h.mutable("idempotency_keys", roles="diyneco_api")
    op.execute("GRANT DELETE ON app.idempotency_keys TO diyneco_api, diyneco_worker")  # G13, G14
    h.mutable("event_outbox", roles="diyneco_worker")
    h.mutable("notifications", roles="diyneco_worker")
    h.mutable("webhook_deliveries", roles="diyneco_worker")

    rows = ",\n".join(f"('{t}','{c}','{cat}','{to}')" for t, c, cat, to in PII_COLUMNS)
    op.execute(f"INSERT INTO app.pii_columns (table_name, column_name, category, anonymise_to) VALUES\n{rows}")

    op.execute(
        """
        -- Monthly partitions for audit_logs and order_status_history, from the current month
        -- to p_months_ahead months ahead. Partitions are reached only through their parent
        -- (which carries RLS), so the app roles get no rights on them directly. (G14)
        CREATE FUNCTION app.ensure_partitions(p_months_ahead integer DEFAULT 3) RETURNS integer
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
        DECLARE
          t       text;
          m       integer;
          start_d date;
          name    text;
          created integer := 0;
        BEGIN
          FOREACH t IN ARRAY ARRAY['audit_logs','order_status_history'] LOOP
            FOR m IN 0..p_months_ahead LOOP
              start_d := (date_trunc('month', now() AT TIME ZONE 'UTC') + make_interval(months => m))::date;
              name := format('%s_y%sm%s', t, to_char(start_d, 'YYYY'), to_char(start_d, 'MM'));
              IF to_regclass('app.' || name) IS NULL THEN
                EXECUTE format('CREATE TABLE app.%I PARTITION OF app.%I FOR VALUES FROM (%L) TO (%L)',
                               name, t, start_d::timestamptz,
                               (start_d + interval '1 month')::date::timestamptz);
                EXECUTE format('REVOKE ALL ON app.%I FROM diyneco_api, diyneco_worker', name);
                created := created + 1;
              END IF;
            END LOOP;
          END LOOP;
          RETURN created;
        END $$;
        REVOKE ALL ON FUNCTION app.ensure_partitions(integer) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.ensure_partitions(integer) TO diyneco_worker;

        -- Outbox drain across hotels for the worker, which has no BYPASSRLS (G5).
        CREATE FUNCTION app.outbox_claim(p_limit integer) RETURNS SETOF app.event_outbox
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          UPDATE app.event_outbox o SET attempts = o.attempts + 1
          WHERE o.id IN (
            SELECT id FROM app.event_outbox
            WHERE published_at IS NULL
            ORDER BY created_at
            LIMIT p_limit
            FOR UPDATE SKIP LOCKED)
          RETURNING o.*
        $$;

        CREATE FUNCTION app.outbox_mark_published(p_ids uuid[]) RETURNS integer
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          WITH u AS (
            UPDATE app.event_outbox SET published_at = now()
            WHERE id = ANY(p_ids) AND published_at IS NULL RETURNING 1)
          SELECT count(*)::integer FROM u
        $$;

        CREATE FUNCTION app.outbox_purge(p_older_than interval DEFAULT interval '7 days') RETURNS integer
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          WITH d AS (
            DELETE FROM app.event_outbox
            WHERE published_at IS NOT NULL AND published_at < now() - p_older_than RETURNING 1)
          SELECT count(*)::integer FROM d
        $$;

        -- Email delivery status for notifications written before a hotel exists or for
        -- platform mail (hotel_id NULL), which RLS would otherwise hide from the update.
        CREATE FUNCTION app.notification_mark(p_id uuid, p_status text, p_provider_message_id text,
                                              p_error text) RETURNS void
        LANGUAGE sql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          UPDATE app.notifications
          SET status = p_status, provider_message_id = p_provider_message_id, error = p_error,
              sent_at = CASE WHEN p_status = 'sent' THEN now() ELSE sent_at END
          WHERE id = p_id AND status = 'queued' AND p_status IN ('sent','failed')
        $$;

        REVOKE ALL ON FUNCTION app.outbox_claim(integer), app.outbox_mark_published(uuid[]),
                               app.outbox_purge(interval),
                               app.notification_mark(uuid, text, text, text) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.outbox_claim(integer), app.outbox_mark_published(uuid[]),
                                  app.outbox_purge(interval) TO diyneco_worker;
        GRANT EXECUTE ON FUNCTION app.notification_mark(uuid, text, text, text) TO diyneco_api, diyneco_worker;

        SELECT app.ensure_partitions(3);
        """
    )


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("audit_logs", "event_outbox")
    op.execute(
        """
        DROP FUNCTION IF EXISTS app.notification_mark(uuid, text, text, text);
        DROP FUNCTION IF EXISTS app.outbox_purge(interval);
        DROP FUNCTION IF EXISTS app.outbox_mark_published(uuid[]);
        DROP FUNCTION IF EXISTS app.outbox_claim(integer);
        DROP FUNCTION IF EXISTS app.ensure_partitions(integer);
        """
    )
    # order_status_history partitions were created here; dropping them is safe only when empty.
    h.refuse_if_data("order_status_history")
    op.execute(
        """
        DO $$ DECLARE p text;
        BEGIN
          FOR p IN SELECT c.relname FROM pg_inherits i
                   JOIN pg_class c ON c.oid = i.inhrelid
                   JOIN pg_class parent ON parent.oid = i.inhparent
                   JOIN pg_namespace n ON n.oid = parent.relnamespace
                   WHERE n.nspname = 'app' AND parent.relname = 'order_status_history'
          LOOP
            EXECUTE format('DROP TABLE app.%I', p);
          END LOOP;
        END $$;
        """
    )
    h.drop_tables("pii_columns", "audit_logs", "idempotency_keys", "event_outbox", "event_seq",
                  "notifications", "webhook_deliveries", "webhooks", "api_keys")
