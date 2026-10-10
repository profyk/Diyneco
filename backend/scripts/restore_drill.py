"""Restore drill (operations runbook, Runbook: backup and restore; Phase 9 exit criterion).

Dumps the source database's `app` schema, restores it into an isolated target database and
runs the runbook's integrity checks on the restored copy:

  1. row counts per table equal the source;
  2. every folio balance equals the sum of its entries (tips excluded);
  3. no order is marked as posted without folio entries;
  4. invoice numbers have no gaps per hotel and year;
  5. tenant isolation and append-only protections survived the restore (the migration check).

The drill is timed against the 4-hour recovery target and appends a line to the drill log.

    uv run python scripts/restore_drill.py --source-url URL --target-url URL [--wipe-target]
        [--pg-bin DIR | --docker CONTAINER] [--log FILE]

URLs are libpq or SQLAlchemy URLs for a role that owns the schema (diyneco_owner). The target
database must exist; --wipe-target drops its `app` schema first (never point it at a database
you need). With --docker the PostgreSQL tools run inside that container (CI, where the
runner's client is older than the server).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.check_migrations import check as migration_check

RECOVERY_TARGET_S = 4 * 3600


def libpq(url: str) -> str:
    return re.sub(r"^postgresql\+\w+://", "postgresql://", url)


def tool(name: str, pg_bin: str | None, docker: str | None, *, stdin: bool = False) -> list[str]:
    if docker:
        return ["docker", "exec", *(["-i"] if stdin else []), docker, name]
    if pg_bin:
        return [str(Path(pg_bin) / name)]
    found = shutil.which(name)
    if not found:
        raise SystemExit(f"{name} not found; pass --pg-bin or --docker")
    return [found]


def dump(source: str, pg_bin: str | None, docker: str | None) -> bytes:
    cmd = [
        *tool("pg_dump", pg_bin, docker),
        "--format=custom",
        "--schema=app",
        "--no-owner",
        f"--dbname={source}",
    ]
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def restore(target: str, data: bytes, pg_bin: str | None, docker: str | None) -> None:
    cmd = [
        *tool("pg_restore", pg_bin, docker, stdin=True),
        "--no-owner",
        "--exit-on-error",
        "--single-transaction",
        f"--dbname={target}",
    ]
    subprocess.run(cmd, input=data, check=True, capture_output=True)


def table_counts(conn: psycopg.Connection) -> dict[str, int]:
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'app' AND c.relkind IN ('r', 'p') AND NOT c.relispartition ORDER BY 1"
        ).fetchall()
    ]
    counts = {}
    for t in tables:
        row = conn.execute(sql.SQL("SELECT count(*) FROM app.{}").format(sql.Identifier(t))).fetchone()
        counts[t] = int(row[0]) if row else 0
    return counts


def integrity(conn: psycopg.Connection) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = {}
    bad_folios = conn.execute(
        """
        SELECT f.id FROM app.folios f
        LEFT JOIN app.folio_balances b ON b.folio_id = f.id
        WHERE coalesce(b.balance_minor, 0) <> (
          SELECT coalesce(sum(e.amount_minor), 0) FROM app.folio_entries e
          JOIN app.charge_categories c ON c.id = e.category_id
          WHERE e.folio_id = f.id AND c.revenue_group <> 'tip')
        """
    ).fetchall()
    problems["folio_balances"] = [str(r[0]) for r in bad_folios]
    unposted = conn.execute(
        "SELECT o.id FROM app.orders o WHERE o.posted_to_folio "
        "AND NOT EXISTS (SELECT 1 FROM app.folio_entries e WHERE e.order_id = o.id)"
    ).fetchall()
    problems["orders_without_entries"] = [str(r[0]) for r in unposted]
    gaps = []
    for hotel_id, year, next_number in conn.execute(
        "SELECT hotel_id, year, next_number FROM app.invoice_sequences"
    ).fetchall():
        numbers = sorted(
            int(r[0].rsplit("-", 1)[1])
            for r in conn.execute(
                "SELECT number FROM app.invoices WHERE hotel_id = %s AND split_part(number, '-', 2) = %s",
                (hotel_id, str(year)),
            ).fetchall()
        )
        if numbers != list(range(1, int(next_number))):
            gaps.append(f"{hotel_id}/{year}")
    problems["invoice_gaps"] = gaps
    problems["protections"] = migration_check(conn)
    return problems


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--source-url", required=True)
    p.add_argument("--target-url", required=True)
    p.add_argument("--wipe-target", action="store_true")
    p.add_argument("--pg-bin")
    p.add_argument("--docker")
    p.add_argument("--log")
    args = p.parse_args()
    source, target = libpq(args.source_url), libpq(args.target_url)
    if source == target:
        raise SystemExit("source and target must differ")

    started = time.monotonic()
    with psycopg.connect(source) as src:
        source_counts = table_counts(src)
    data = dump(source, args.pg_bin, args.docker)
    with psycopg.connect(target, autocommit=True) as tgt:
        exists = tgt.execute("SELECT 1 FROM pg_namespace WHERE nspname = 'app'").fetchone()
        if exists and not args.wipe_target:
            raise SystemExit("target already has schema app; use an empty database or --wipe-target")
        if exists:
            tgt.execute("DROP SCHEMA app CASCADE")
    restore(target, data, args.pg_bin, args.docker)
    with psycopg.connect(target) as tgt:
        restored_counts = table_counts(tgt)
        problems = integrity(tgt)
    elapsed = time.monotonic() - started

    count_mismatch = sorted(t for t in source_counts if source_counts[t] != restored_counts.get(t))
    problems["row_counts"] = count_mismatch
    ok = not any(problems.values()) and elapsed < RECOVERY_TARGET_S
    result = {
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
        "ok": ok,
        "seconds": round(elapsed, 1),
        "dump_bytes": len(data),
        "tables": len(source_counts),
        "rows": sum(source_counts.values()),
        "folios": restored_counts.get("folios", 0),
        "invoices": restored_counts.get("invoices", 0),
        "problems": {k: v for k, v in problems.items() if v},
    }
    print(json.dumps(result, indent=2))
    if args.log:
        with open(args.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
