"""privacy: anonymise a guest's address in the notification log

POPIA anonymisation (security spec, Data subject participation and Retention) replaces a
guest's personal fields. The notification log is writable only by the worker, so the API
hashes a guest's email there through this one narrow definer function, scoped to one hotel.
(DECISIONS D59.)

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-10 20:00
"""

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION app.anonymise_recipient(p_hotel uuid, p_recipient text) RETURNS integer
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
        DECLARE n integer;
        BEGIN
          UPDATE app.notifications
             SET recipient = 'sha256:' || encode(extensions.digest(lower(recipient), 'sha256'), 'hex')
           WHERE hotel_id = p_hotel AND lower(recipient) = lower(p_recipient);
          GET DIAGNOSTICS n = ROW_COUNT;
          RETURN n;
        END $$;
        REVOKE ALL ON FUNCTION app.anonymise_recipient(uuid, text) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.anonymise_recipient(uuid, text) TO diyneco_api, diyneco_worker;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS app.anonymise_recipient(uuid, text)")
