#!/usr/bin/env python3
"""Create or update the Genie space for the model, from the model.

Builds the space definition from the bindings, the model specs (which
objects to expose) and the generated Genie instructions
(build/genie/genie_instructions.md), plus curated example SQL and benchmark
questions. Run tools/generate.py first.

Usage:
    uv run --with databricks-sdk,pyyaml tools/create_genie_space.py \
        [--profile DEFAULT] [--warehouse-id ID] [--space-id ID to update]
"""

import argparse
import json
import uuid
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient

ROOT = Path(__file__).resolve().parents[1]
PARENT_PATH = "/Workspace/Shared/bricksurance-data-core"

TITLE = "Bricksurance Data Core"
DESCRIPTION = (
    "The canonical, ACORD-aligned insurance semantic model of Bricksurance SE: "
    "policies, claims, parties, reinsurance and certified underwriting metrics. "
    "Demo data is synthetic."
)

# Genie spaces allow AT MOST 30 tables. The space exposes every entity and
# semantic view plus the data dictionary and the line_of_business lookup;
# other code sets stay out — their values are in the instructions vocabulary,
# which is how Genie maps business labels to codes.
MAX_SPACE_TABLES = 30


def uid():
    return uuid.uuid4().hex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--warehouse-id")
    ap.add_argument("--space-id", help="Patch this space instead of creating a new one")
    args = ap.parse_args()

    binding = yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())

    def t(domain, name):
        return f"{binding['catalog']}.{binding['schema_pattern'].format(domain=domain)}.{name}"

    specs = [yaml.safe_load(p.read_text()) for p in sorted((ROOT / "model").rglob("*.yaml"))
             if p.name != "model.yaml"]
    tables = [t(s["domain"], s["name"]) for s in specs
              if s["kind"] in ("entity", "view", "metric_view")]
    tables += [t("reference", "data_dictionary")]
    if len(set(tables)) > MAX_SPACE_TABLES:
        raise SystemExit(
            f"{len(set(tables))} objects exceed the Genie limit of "
            f"{MAX_SPACE_TABLES} tables per space — curate the list.")

    instructions = (ROOT / "build" / "genie" / "genie_instructions.md").read_text()

    examples = [
        ("Trace a policy end to end: policy, claim, cession, treaty",
         f"SELECT p.policy_number, c.claim_number, tr.treaty_reference, ces.ceded_share "
         f"FROM {t('policy', 'policy')} p "
         f"JOIN {t('claim', 'claim')} c ON c.policy_id = p.policy_id "
         f"JOIN {t('reinsurance', 'cession')} ces ON ces.policy_id = p.policy_id "
         f"JOIN {t('reinsurance', 'treaty')} tr ON tr.treaty_id = ces.treaty_id "
         f"WHERE p.policy_number = 'POL-2026-000001'",
         "The golden-thread pattern: direct policy to claim to reinsurance cession."),
        ("Gross written premium and loss ratio by line of business (GBP, UWY 2026)",
         f"SELECT line_of_business, MEASURE(gross_written_premium) AS gwp, "
         f"MEASURE(loss_ratio) AS loss_ratio FROM {t('semantics', 'underwriting_metrics')} "
         f"WHERE currency_code = 'GBP' AND underwriting_year = 2026 GROUP BY line_of_business",
         "KPI questions use the metric view with MEASURE(); constrain currency_code before summing money."),
        ("Outstanding reserve per claim (derived from movements)",
         f"SELECT c.claim_number, SUM(ct.amount) AS outstanding_reserve "
         f"FROM {t('claim', 'claim_transaction')} ct "
         f"JOIN {t('claim', 'claim')} c ON c.claim_id = ct.claim_id "
         f"WHERE ct.claim_transaction_type_code = 'CASE_RESERVE_MOVEMENT' GROUP BY c.claim_number",
         "Outstanding is never stored; it is the sum of signed case reserve movements."),
    ]
    benchmarks = [
        ("What is our gross written premium by line of business for underwriting year 2026 in GBP?",
         f"SELECT line_of_business, MEASURE(gross_written_premium) AS gwp "
         f"FROM {t('semantics', 'underwriting_metrics')} "
         f"WHERE currency_code = 'GBP' AND underwriting_year = 2026 GROUP BY line_of_business"),
        ("What is the outstanding reserve on claim CLM-2026-000001?",
         f"SELECT SUM(ct.amount) AS outstanding_reserve FROM {t('claim', 'claim_transaction')} ct "
         f"JOIN {t('claim', 'claim')} c ON c.claim_id = ct.claim_id "
         f"WHERE c.claim_number = 'CLM-2026-000001' "
         f"AND ct.claim_transaction_type_code = 'CASE_RESERVE_MOVEMENT'"),
        ("Which policies are ceded to treaty TR-QS-PROP-2026 and at what share?",
         f"SELECT p.policy_number, ces.ceded_share FROM {t('reinsurance', 'cession')} ces "
         f"JOIN {t('policy', 'policy')} p ON p.policy_id = ces.policy_id "
         f"JOIN {t('reinsurance', 'treaty')} tr ON tr.treaty_id = ces.treaty_id "
         f"WHERE tr.treaty_reference = 'TR-QS-PROP-2026' ORDER BY p.policy_number"),
        ("Who is the broker on policy POL-2025-000002?",
         f"SELECT pt.name FROM {t('party', 'party_role')} pr "
         f"JOIN {t('party', 'party')} pt ON pt.party_id = pr.party_id "
         f"JOIN {t('policy', 'policy')} p ON p.policy_id = pr.policy_id "
         f"WHERE p.policy_number = 'POL-2025-000002' AND pr.party_role_type_code = 'BROKER'"),
        ("What is our loss ratio for Commercial Property in GBP?",
         f"SELECT MEASURE(loss_ratio) AS loss_ratio FROM {t('semantics', 'underwriting_metrics')} "
         f"WHERE currency_code = 'GBP' AND line_of_business = 'Commercial Property'"),
    ]

    serialized = {
        "version": 2,
        "data_sources": {
            "tables": sorted(({"identifier": i} for i in set(tables)),
                             key=lambda x: x["identifier"]),
        },
        "instructions": {
            "text_instructions": [{"id": uid(), "content": [instructions]}],
            "example_question_sqls": sorted(
                ({"id": uid(), "question": [q], "sql": [sql], "usage_guidance": [g]}
                 for q, sql, g in examples), key=lambda x: x["id"]),
        },
        "benchmarks": {
            "questions": sorted(
                ({"id": uid(), "question": [q],
                  "answer": [{"format": "SQL", "content": [sql]}]}
                 for q, sql in benchmarks), key=lambda x: x["id"]),
        },
    }

    w = WorkspaceClient(profile=args.profile)
    wid = args.warehouse_id
    if not wid:
        from deploy_databricks import pick_warehouse
        wid = pick_warehouse(w).id
    payload = {
        "title": TITLE, "description": DESCRIPTION, "warehouse_id": wid,
        "serialized_space": json.dumps(serialized, indent=2),
    }
    if args.space_id:
        resp = w.api_client.do("PATCH", f"/api/2.0/genie/spaces/{args.space_id}", body=payload)
    else:
        payload["parent_path"] = PARENT_PATH
        w.workspace.mkdirs(PARENT_PATH)
        resp = w.api_client.do("POST", "/api/2.0/genie/spaces", body=payload)
    print(f"Space {'updated' if args.space_id else 'created'}: "
          f"{w.config.host}/genie/rooms/{resp['space_id']}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
