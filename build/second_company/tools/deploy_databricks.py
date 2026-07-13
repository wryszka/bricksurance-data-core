#!/usr/bin/env python3
"""Deploy the generated Databricks artifacts to a workspace.

Executes every build/databricks/*.sql file in order (schemas, reference data,
entities, relationships, then demo data if generated) through the SQL
Statement Execution API. Idempotent: tables use IF NOT EXISTS, seeds use
INSERT OVERWRITE, and existing-constraint errors are skipped.

Usage:
    uv run --with databricks-sdk tools/deploy_databricks.py \
        [--profile DEFAULT] [--warehouse-id ID]
"""

import argparse
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient

BUILD = Path(__file__).resolve().parents[1] / "build" / "databricks"
SKIPPABLE = ("already exists", "ALREADY_EXISTS")


def statements(path):
    """Split a generated SQL file into statements (separated by ';' + blank line)."""
    text = "\n".join(l for l in path.read_text().splitlines() if not l.startswith("--"))
    parts = [p.strip().rstrip(";").strip() for p in text.split(";\n\n")]
    return [p + ";" for p in parts if p]


def pick_warehouse(w):
    warehouses = list(w.warehouses.list())
    if not warehouses:
        sys.exit("No SQL warehouse available in the workspace.")
    running = [wh for wh in warehouses if wh.state and wh.state.value == "RUNNING"]
    return (running or warehouses)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--warehouse-id")
    args = ap.parse_args()

    w = WorkspaceClient(profile=args.profile)
    wid = args.warehouse_id or pick_warehouse(w).id
    print(f"Workspace: {w.config.host}\nWarehouse: {wid}\n")

    ok = skipped = 0
    for path in sorted(BUILD.glob("*.sql")):
        stmts = statements(path)
        print(f"{path.name}: {len(stmts)} statements")
        for stmt in stmts:
            resp = w.statement_execution.execute_statement(
                statement=stmt, warehouse_id=wid, wait_timeout="50s")
            while resp.status.state.value in ("PENDING", "RUNNING"):
                resp = w.statement_execution.get_statement(resp.statement_id)
            if resp.status.state.value == "SUCCEEDED":
                ok += 1
            else:
                message = resp.status.error.message or ""
                if any(s in message for s in SKIPPABLE):
                    skipped += 1
                else:
                    first = stmt.splitlines()[0]
                    sys.exit(f"FAILED on: {first}\n{message}")
    print(f"\nDone: {ok} statements succeeded, {skipped} skipped (already existed).")


if __name__ == "__main__":
    main()
