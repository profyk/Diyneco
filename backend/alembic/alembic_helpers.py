"""Shared DDL helpers for migrations.

Every migration that creates a table with hotel_id calls tenant_rls() for it, and every
financial table gets append_only() in the migration that creates it. Keep these helpers
stable: changing one changes the meaning of every migration that already used it.
"""

from alembic import op

API_ROLES = "diyneco_api, diyneco_worker"


def tenant_rls(table: str, column: str = "hotel_id") -> None:
    """Enable and force RLS with the standard one-hotel policy."""
    op.execute(f"ALTER TABLE app.{table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE app.{table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON app.{table} "
        f"USING ({column} = app.current_hotel_id()) "
        f"WITH CHECK ({column} = app.current_hotel_id())"
    )


def shared_catalogue_rls(table: str, policy: str) -> None:
    """System rows (hotel_id NULL) readable by every hotel; hotel rows only by that hotel."""
    op.execute(f"ALTER TABLE app.{table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE app.{table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {policy} ON app.{table} "
        "USING (hotel_id IS NULL OR hotel_id = app.current_hotel_id()) "
        "WITH CHECK (hotel_id = app.current_hotel_id())"
    )


def append_only(table: str) -> None:
    """Trigger plus revoked grants: no UPDATE, DELETE or TRUNCATE for the app roles."""
    op.execute(
        f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON app.{table} "
        "FOR EACH ROW EXECUTE FUNCTION app.forbid_change()"
    )
    op.execute(f"REVOKE UPDATE, DELETE, TRUNCATE ON app.{table} FROM {API_ROLES}")


def updated_at(table: str) -> None:
    op.execute(
        f"CREATE TRIGGER {table}_updated_at BEFORE UPDATE ON app.{table} "
        "FOR EACH ROW EXECUTE FUNCTION app.set_updated_at()"
    )


def mutable(table: str, roles: str = API_ROLES) -> None:
    """Grant UPDATE on a configuration or state table (SELECT and INSERT come by default)."""
    op.execute(f"GRANT UPDATE ON app.{table} TO {roles}")


def read_only(table: str, roles: str = API_ROLES) -> None:
    """Catalogue tables the app may read but never write."""
    op.execute(f"REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON app.{table} FROM {roles}")


def shared_ref(table: str, column: str, ref_table: str) -> None:
    """Reference to a table holding system rows (hotel_id NULL) and hotel rows:
    the target must be a system row or belong to the same hotel."""
    op.execute(
        f"CREATE TRIGGER {table}_{column}_shared_ref BEFORE INSERT OR UPDATE OF {column} "
        f"ON app.{table} FOR EACH ROW EXECUTE FUNCTION app.check_shared_ref('{ref_table}', '{column}')"
    )


def drop_tables(*tables: str) -> None:
    for t in tables:
        op.execute(f"DROP TABLE IF EXISTS app.{t} CASCADE")


def refuse_if_data(*tables: str) -> None:
    """Downgrades that would destroy data raise instead of running."""
    for t in tables:
        op.execute(
            f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM app.{t}) THEN "
            f"RAISE EXCEPTION 'refusing to downgrade: app.{t} has rows'; END IF; END $$"
        )
