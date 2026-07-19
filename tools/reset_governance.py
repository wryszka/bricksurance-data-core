#!/usr/bin/env python3
"""Reset the Atlas governance-action capture table so the next presenter starts
clean. The certification attestations and the model itself are NOT touched —
those are regenerated from the specs. This only clears the in-app proposal/issue
capture (reference.governance_action).

Usage:
    uv run --with databricks-sdk tools/reset_governance.py --profile DEFAULT
"""
import argparse
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient

CATALOG = "lr_serverless_aws_us_catalog"
SCHEMA = "bricksurance_reference"
TABLE = f"{CATALOG}.{SCHEMA}.governance_action"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="DEFAULT")
    args = ap.parse_args()
    w = WorkspaceClient(profile=args.profile)
    running = [wh for wh in w.warehouses.list() if wh.state and wh.state.value == "RUNNING"]
    wid = (running or list(w.warehouses.list()))[0].id
    r = w.statement_execution.execute_statement(
        statement=f"DELETE FROM {TABLE}", warehouse_id=wid, wait_timeout="50s")
    while r.status.state.value in ("PENDING", "RUNNING"):
        r = w.statement_execution.get_statement(r.statement_id)
    if r.status.state.value == "SUCCEEDED":
        print(f"Reset: cleared all rows from {TABLE}.")
    elif "TABLE_OR_VIEW_NOT_FOUND" in (r.status.error.message or ""):
        print(f"Nothing to reset — {TABLE} does not exist yet.")
    else:
        sys.exit(f"Reset failed: {r.status.error.message}")


if __name__ == "__main__":
    main()
