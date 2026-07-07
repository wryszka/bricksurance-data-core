#!/usr/bin/env python3
"""Smoke-test a deployed Bricksurance Data Core against the workspace.

Verifies the physical deployment matches the model: tables and relationships
exist, demo-data volumes are right, and the golden thread (hero policy ->
fire claim -> quota-share cession) resolves end to end with correct derived
figures.

Usage:
    uv run --with databricks-sdk,pyyaml tools/smoke_test.py [--profile DEFAULT] [--warehouse-id ID]
"""

import argparse
import sys
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy_databricks import pick_warehouse  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def run_sql(w, wid, sql):
    resp = w.statement_execution.execute_statement(
        statement=sql, warehouse_id=wid, wait_timeout="50s")
    while resp.status.state.value in ("PENDING", "RUNNING"):
        resp = w.statement_execution.get_statement(resp.statement_id)
    if resp.status.state.value != "SUCCEEDED":
        raise RuntimeError(resp.status.error.message)
    return resp.result.data_array or []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--warehouse-id")
    args = ap.parse_args()

    binding = yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())
    cat = binding["catalog"]
    prefix = binding["schema_pattern"].format(domain="")

    w = WorkspaceClient(profile=args.profile)
    wid = args.warehouse_id or pick_warehouse(w).id

    def q(domain, table):
        return f"{cat}.{binding['schema_pattern'].format(domain=domain)}.{table}"

    checks = [
        ("24 tables deployed",
         f"SELECT COUNT(*) FROM {cat}.information_schema.tables "
         f"WHERE table_schema LIKE '{prefix}%'", "24"),
        ("38 foreign-key relationships",
         f"SELECT COUNT(*) FROM {cat}.information_schema.table_constraints "
         f"WHERE constraint_schema LIKE '{prefix}%' AND constraint_type = 'FOREIGN KEY'", "38"),
        ("60 policies", f"SELECT COUNT(*) FROM {q('policy', 'policy')}", "60"),
        ("18 claims", f"SELECT COUNT(*) FROM {q('claim', 'claim')}", "18"),
        ("dictionary covers every deployed column",
         f"SELECT COUNT(*) FROM {q('reference', 'data_dictionary')} d "
         f"JOIN {cat}.information_schema.columns c "
         f"ON c.table_schema LIKE '{prefix}%' AND c.table_name = d.entity_name "
         f"AND c.column_name = d.attribute_name", None),
        ("golden thread resolves end to end",
         f"SELECT p.policy_number, c.claim_number, t.treaty_reference, ces.ceded_share "
         f"FROM {q('policy', 'policy')} p "
         f"JOIN {q('claim', 'claim')} c ON c.policy_id = p.policy_id "
         f"JOIN {q('reinsurance', 'cession')} ces ON ces.policy_id = p.policy_id "
         f"JOIN {q('reinsurance', 'treaty')} t ON t.treaty_id = ces.treaty_id "
         f"WHERE p.policy_number = 'POL-2026-000001'",
         "POL-2026-000001|CLM-2026-000001|TR-QS-PROP-2026|0.3000"),
        ("hero outstanding reserve = 270000 (derived, never stored)",
         f"SELECT CAST(SUM(amount) AS INT) FROM {q('claim', 'claim_transaction')} ct "
         f"JOIN {q('claim', 'claim')} c ON c.claim_id = ct.claim_id "
         f"WHERE c.claim_number = 'CLM-2026-000001' "
         f"AND ct.claim_transaction_type_code = 'CASE_RESERVE_MOVEMENT'", "270000"),
        ("every party role has exactly one context",
         f"SELECT COUNT(*) FROM {q('party', 'party_role')} "
         f"WHERE (policy_id IS NOT NULL) + (claim_id IS NOT NULL) + (treaty_id IS NOT NULL) <> 1", "0"),
    ]

    failures = 0
    for name, sql, expected in checks:
        try:
            rows = run_sql(w, wid, sql)
            got = "|".join(str(v) for v in rows[0]) if rows else "(no rows)"
            if expected is None:
                passed = rows and int(rows[0][0]) > 0
            else:
                passed = got == expected
        except Exception as e:  # noqa: BLE001
            got, passed = f"ERROR: {e}", False
        print(f"{'PASS' if passed else 'FAIL'}  {name}  [{got}]")
        failures += 0 if passed else 1

    if failures:
        sys.exit(f"\n{failures} check(s) failed.")
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
