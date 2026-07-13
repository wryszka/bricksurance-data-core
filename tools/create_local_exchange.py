#!/usr/bin/env python3
"""Simulate the Bricksurance Re exchange locally — same objects, no share.

Creates a `partner_re` schema holding exactly what the Delta Share
(tools/create_share.py) would deliver to Bricksurance Re — the live cession
bordereau plus the data dictionary and the code sets it depends on — as
views. When the D2D grant lands, the swap is: recipient mounts the share
instead of these views. The receiving analyst's queries are identical.

Usage:
    uv run --with databricks-sdk,pyyaml tools/create_local_exchange.py [--profile DEFAULT]
"""

import argparse
import sys
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy_databricks import pick_warehouse  # noqa: E402
from smoke_test import run_sql  # noqa: E402
from create_share import OBJECTS, SHARE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--warehouse-id")
    args = ap.parse_args()

    binding = yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())
    cat = binding["catalog"]
    partner = f"{cat}.{binding['schema_pattern'].format(domain='partner_re')}"

    def fqn(domain, name):
        return f"{cat}.{binding['schema_pattern'].format(domain=domain)}.{name}"

    w = WorkspaceClient(profile=args.profile)
    wid = args.warehouse_id or pick_warehouse(w).id

    run_sql(w, wid,
            f"CREATE SCHEMA IF NOT EXISTS {partner} COMMENT "
            f"'Simulates what the Delta Share {SHARE} delivers to Bricksurance Re: "
            f"the same objects, locally, until the D2D share replaces this schema. "
            f"The dictionary travels with the data.'")
    for domain, name, _ in OBJECTS:
        run_sql(w, wid, f"CREATE OR REPLACE VIEW {partner}.{name} AS "
                        f"SELECT * FROM {fqn(domain, name)}")
        print(f"  {partner}.{name}")

    # the receiving analyst's first query: rows WITH their meaning
    rows = run_sql(w, wid,
                   f"SELECT COUNT(*), CAST(SUM(ceded_premium) AS DECIMAL(18,2)) "
                   f"FROM {partner}.cession_bordereau_line")
    meaning = run_sql(w, wid,
                      f"SELECT definition FROM {partner}.data_dictionary "
                      f"WHERE attribute_name = 'ceded_premium' LIMIT 1")
    print(f"\nRe's view: {rows[0][0]} bordereau lines, ceded premium {rows[0][1]}")
    print(f"Re reads the meaning locally: {str(meaning[0][0])[:90]}...")


if __name__ == "__main__":
    main()
