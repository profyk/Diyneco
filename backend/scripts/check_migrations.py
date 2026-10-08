"""Fail if the migrated schema breaks a tenancy or financial safeguard.

Run after `alembic upgrade head`, against the same database, with MIGRATIONS_DATABASE_URL
(or a URL as the first argument; falls back to backend/.env). Exits 1 and lists every problem found.

Checks:
  1. Every app table with hotel_id (and app.hotels) has RLS enabled and forced, and a policy.
  2. Every financial table has the append-only trigger, and the app roles hold no
     UPDATE, DELETE or TRUNCATE on it.
  3. Partitions grant nothing to the app roles (RLS lives on the parent only).
  4. Every view in app is security_invoker, so the caller's RLS applies.
  5. Every SECURITY DEFINER function pins search_path and is not executable by PUBLIC.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

FINANCIAL_TABLES = (
    "folio_entries",
    "payments",
    "payment_allocations",
    "tips",
    "invoices",
    "invoice_items",
    "audit_logs",
    "order_status_history",
)
APP_ROLES = ("diyneco_api", "diyneco_worker")


def _dsn(argv: list[str]) -> str:
    url = argv[1] if len(argv) > 1 else os.environ.get("MIGRATIONS_DATABASE_URL", "")
    if not url:
        # Same fallback as alembic/env.py: read backend/.env.
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("MIGRATIONS_DATABASE_URL="):
                    url = line.split("=", 1)[1].split("#", 1)[0].strip().strip('"')
    if not url:
        sys.exit("usage: check_migrations.py <postgres url>  (or set MIGRATIONS_DATABASE_URL)")
    return url.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+asyncpg://", "postgresql://"
    )


def check(conn: psycopg.Connection) -> list[str]:
    problems: list[str] = []

    tenant_tables = conn.execute(
        """
        SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity,
               (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid)
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'app' AND c.relkind IN ('r', 'p') AND NOT c.relispartition
          AND (c.relname = 'hotels' OR EXISTS (
                SELECT 1 FROM pg_attribute a
                WHERE a.attrelid = c.oid AND a.attname = 'hotel_id' AND NOT a.attisdropped))
        ORDER BY 1
        """
    ).fetchall()
    if not tenant_tables:
        problems.append("no tenant tables found: is the schema migrated?")
    for name, enabled, forced, policies in tenant_tables:
        if not enabled:
            problems.append(f"app.{name}: row level security is not enabled")
        if not forced:
            problems.append(f"app.{name}: row level security is not forced")
        if policies == 0:
            problems.append(f"app.{name}: has hotel_id but no RLS policy")

    for table in FINANCIAL_TABLES:
        has_trigger = conn.execute(
            """
            SELECT EXISTS (
              SELECT 1 FROM pg_trigger t
              JOIN pg_class c ON c.oid = t.tgrelid
              JOIN pg_namespace n ON n.oid = c.relnamespace
              JOIN pg_proc p ON p.oid = t.tgfoid
              WHERE n.nspname = 'app' AND c.relname = %s AND p.proname = 'forbid_change'
                AND NOT t.tgisinternal
                AND (t.tgtype & 8) <> 0 AND (t.tgtype & 16) <> 0)   -- fires on DELETE and UPDATE
            """,
            (table,),
        ).fetchone()
        if not (has_trigger and has_trigger[0]):
            problems.append(f"app.{table}: financial table lacks the append-only trigger")
        for role in APP_ROLES:
            for priv in ("UPDATE", "DELETE", "TRUNCATE"):
                row = conn.execute(
                    "SELECT has_table_privilege(%s, %s, %s)", (role, f"app.{table}", priv)
                ).fetchone()
                if row and row[0]:
                    problems.append(f"app.{table}: {role} holds {priv}")

    for (name,) in conn.execute(
        "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'app' AND c.relispartition AND c.relkind = 'r'"
    ).fetchall():
        for role in APP_ROLES:
            row = conn.execute(
                "SELECT has_table_privilege(%s, %s, 'SELECT') OR has_table_privilege(%s, %s, 'INSERT')",
                (role, f"app.{name}", role, f"app.{name}"),
            ).fetchone()
            if row and row[0]:
                problems.append(f"app.{name}: partition is directly accessible to {role}")

    for name, options in conn.execute(
        "SELECT c.relname, c.reloptions FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'app' AND c.relkind = 'v'"
    ).fetchall():
        if not options or "security_invoker=true" not in options:
            problems.append(f"app.{name}: view is not security_invoker")

    for name, config, public_exec in conn.execute(
        """
        SELECT p.proname, p.proconfig, has_function_privilege('public', p.oid, 'EXECUTE')
        FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'app' AND p.prosecdef
        """
    ).fetchall():
        if not config or not any(c.startswith("search_path=") for c in config):
            problems.append(f"app.{name}(): SECURITY DEFINER without a pinned search_path")
        if public_exec:
            problems.append(f"app.{name}(): SECURITY DEFINER executable by PUBLIC")

    return problems


def main(argv: list[str]) -> int:
    with psycopg.connect(_dsn(argv)) as conn:
        problems = check(conn)
    if problems:
        print(f"Migration check FAILED ({len(problems)} problems):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("Migration check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
