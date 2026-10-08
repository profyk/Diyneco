"""The migration check script and model/schema drift."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from app.models import Base
from tests.conftest import TEST_MIGRATIONS_DATABASE_URL

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import check_migrations  # noqa: E402

DSN = TEST_MIGRATIONS_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")


def test_migration_check_passes_on_migrated_schema():
    with psycopg.connect(DSN) as conn:
        assert check_migrations.check(conn) == []


def test_migration_check_catches_missing_rls_and_append_only():
    with psycopg.connect(DSN) as conn:
        conn.execute("CREATE TABLE app.zz_unsafe (id uuid PRIMARY KEY, hotel_id uuid NOT NULL)")
        conn.execute("DROP TRIGGER payments_append_only ON app.payments")
        conn.execute("GRANT UPDATE ON app.tips TO diyneco_api")
        conn.execute("CREATE VIEW app.zz_view AS SELECT 1 AS x")
        problems = check_migrations.check(conn)
        conn.rollback()
    joined = "\n".join(problems)
    assert "app.zz_unsafe: row level security is not enabled" in joined
    assert "app.zz_unsafe: has hotel_id but no RLS policy" in joined
    assert "app.payments: financial table lacks the append-only trigger" in joined
    assert "app.tips: diyneco_api holds UPDATE" in joined
    assert "app.zz_view: view is not security_invoker" in joined


def _family(sql_type: str) -> str:
    t = sql_type.lower()
    for prefix, family in (("timestamp", "timestamptz"), ("character varying", "text"), ("character", "char"),
                           ("bpchar", "char"), ("char", "char"), ("varchar", "text"), ("text", "text"), ("citext", "citext"),
                           ("uuid[]", "uuid[]"), ("text[]", "text[]"), ("uuid", "uuid"), ("bigint", "bigint"),
                           ("smallint", "smallint"), ("integer", "integer"), ("boolean", "boolean"),
                           ("bytea", "bytea"), ("jsonb", "jsonb"), ("inet", "inet"), ("date", "date"),
                           ("time", "time")):
        if t.startswith(prefix):
            return family
    return t


async def test_models_match_migrated_tables(owner_engine):
    async with owner_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT c.table_name, c.column_name, c.is_nullable = 'YES' AS nullable, "
                    "format_type(a.atttypid, a.atttypmod) AS type "
                    "FROM information_schema.columns c "
                    "JOIN pg_class k ON k.relname = c.table_name "
                    "JOIN pg_namespace n ON n.oid = k.relnamespace AND n.nspname = c.table_schema "
                    "JOIN pg_attribute a ON a.attrelid = k.oid AND a.attname = c.column_name "
                    "WHERE c.table_schema = 'app' AND k.relkind IN ('r','p') AND NOT k.relispartition"
                )
            )
        ).all()
    db: dict[str, dict[str, tuple[bool, str]]] = {}
    for r in rows:
        db.setdefault(r.table_name, {})[r.column_name] = (r.nullable, _family(r.type))

    dialect = postgresql.dialect()
    models = {t.name: t for t in Base.metadata.tables.values()}
    assert set(models) == set(db), f"tables differ: {set(models) ^ set(db)}"
    problems = []
    for name, table in models.items():
        cols = {c.name: c for c in table.columns}
        if set(cols) != set(db[name]):
            problems.append(f"{name}: columns differ {set(cols) ^ set(db[name])}")
            continue
        for col_name, col in cols.items():
            nullable, family = db[name][col_name]
            model_family = _family(col.type.compile(dialect=dialect))
            if model_family != family:
                problems.append(f"{name}.{col_name}: model {model_family} vs db {family}")
            if bool(col.nullable) != nullable and not col.primary_key:
                problems.append(f"{name}.{col_name}: model nullable={col.nullable} vs db {nullable}")
    assert problems == []
