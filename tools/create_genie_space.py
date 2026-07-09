#!/usr/bin/env python3
"""Create or update the SPECIALIZED Genie spaces for the model.

One space per business domain — P&C book, Reinsurance & Exchange, Life &
Valuations — each small and high-signal (Genie allows at most 30 tables per
space). Genie One then surfaces the certified spaces together as one chat
front door, and an agent supervisor can orchestrate them as tools.

All spaces share the generated instructions (build/genie/genie_instructions.md
— run tools/generate.py first); each carries its own example SQL and SQL
benchmark answers.

Usage:
    uv run --with databricks-sdk,pyyaml tools/create_genie_space.py \
        --space pnc|reinsurance|life [--profile DEFAULT] \
        [--warehouse-id ID] [--space-id ID to update]
"""

import argparse
import json
import uuid
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient

ROOT = Path(__file__).resolve().parents[1]
PARENT_PATH = "/Workspace/Shared/bricksurance-data-core"
MAX_SPACE_TABLES = 30
DISCLAIMER = "Bricksurance is fictional; all data is synthetic."


def spaces_config(t):
    """Per-space definition. t(domain, name) -> fully qualified name."""
    return {
        "pnc": {
            "title": "Bricksurance — P&C Book",
            "description": ("The direct P&C book of Bricksurance SE: quotes, policies, "
                            "endorsements, coverages, insured objects, premium, claims — "
                            f"with certified underwriting metrics. {DISCLAIMER}"),
            "objects": [("policy", "policy"), ("policy", "quote"), ("policy", "endorsement"),
                        ("policy", "coverage"), ("policy", "insured_object"),
                        ("policy", "vehicle"), ("policy", "premium_transaction"),
                        ("claim", "claim"), ("claim", "claim_transaction"),
                        ("party", "party"), ("party", "party_role"),
                        ("semantics", "underwriting_metrics"),
                        ("semantics", "financial_transaction"),
                        ("reference", "data_dictionary")],
            "examples": [
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
            ],
            "benchmarks": [
                ("What is our gross written premium by line of business for underwriting year 2026 in GBP?",
                 f"SELECT line_of_business, MEASURE(gross_written_premium) AS gwp "
                 f"FROM {t('semantics', 'underwriting_metrics')} "
                 f"WHERE currency_code = 'GBP' AND underwriting_year = 2026 GROUP BY line_of_business"),
                ("What is the outstanding reserve on claim CLM-2026-000001?",
                 f"SELECT SUM(ct.amount) AS outstanding_reserve FROM {t('claim', 'claim_transaction')} ct "
                 f"JOIN {t('claim', 'claim')} c ON c.claim_id = ct.claim_id "
                 f"WHERE c.claim_number = 'CLM-2026-000001' "
                 f"AND ct.claim_transaction_type_code = 'CASE_RESERVE_MOVEMENT'"),
                ("Who is the broker on policy POL-2025-000002?",
                 f"SELECT pt.name FROM {t('party', 'party_role')} pr "
                 f"JOIN {t('party', 'party')} pt ON pt.party_id = pr.party_id "
                 f"JOIN {t('policy', 'policy')} p ON p.policy_id = pr.policy_id "
                 f"WHERE p.policy_number = 'POL-2025-000002' AND pr.party_role_type_code = 'BROKER'"),
                ("What share of 2026 quotes converted into policies?",
                 f"SELECT COUNT(CASE WHEN quote_status_code = 'CONVERTED' THEN 1 END) / COUNT(*) "
                 f"AS conversion_rate FROM {t('policy', 'quote')} WHERE YEAR(quote_date) >= 2025"),
            ],
        },
        "reinsurance": {
            "title": "Bricksurance — Reinsurance & Exchange",
            "description": ("The reinsurance book and data exchange of the Bricksurance group: "
                            "submissions, treaties and layers, cessions, catastrophe events and "
                            f"the cession bordereau shared with Bricksurance Re. {DISCLAIMER}"),
            "objects": [("reinsurance", "submission"), ("reinsurance", "treaty"),
                        ("reinsurance", "treaty_layer"), ("reinsurance", "cession"),
                        ("reinsurance", "cat_event"), ("reinsurance", "event_loss"),
                        ("exchange", "cession_bordereau_line"),
                        ("exchange", "premium_bordereau_line"),
                        ("party", "party"), ("party", "party_role"),
                        ("semantics", "cession_metrics"), ("semantics", "submission_metrics"),
                        ("reference", "data_dictionary")],
            "examples": [
                ("Ceded premium by treaty (GBP)",
                 f"SELECT treaty_reference, MEASURE(ceded_premium) AS ceded_premium "
                 f"FROM {t('semantics', 'cession_metrics')} WHERE currency_code = 'GBP' "
                 f"GROUP BY treaty_reference",
                 "Cession KPIs use the metric view with MEASURE(); constrain currency_code."),
                ("Modelled vs reported losses for an event",
                 f"SELECT e.event_name, l.loss_basis_code, l.as_of_date, "
                 f"SUM(l.gross_loss_amount) AS gross_loss FROM {t('reinsurance', 'event_loss')} l "
                 f"JOIN {t('reinsurance', 'cat_event')} e ON e.cat_event_id = l.cat_event_id "
                 f"GROUP BY e.event_name, l.loss_basis_code, l.as_of_date",
                 "Event losses are as-of snapshots on an explicit MODELLED/REPORTED basis, never overwritten."),
            ],
            "benchmarks": [
                ("Which policies are ceded to treaty TR-QS-PROP-2026 and at what share?",
                 f"SELECT p.policy_number, ces.ceded_share FROM {t('reinsurance', 'cession')} ces "
                 f"JOIN {t('policy', 'policy')} p ON p.policy_id = ces.policy_id "
                 f"JOIN {t('reinsurance', 'treaty')} tr ON tr.treaty_id = ces.treaty_id "
                 f"WHERE tr.treaty_reference = 'TR-QS-PROP-2026' ORDER BY p.policy_number"),
                ("Which submissions have we bound, and into which treaties?",
                 f"SELECT s.submission_reference, tr.treaty_reference "
                 f"FROM {t('reinsurance', 'submission')} s "
                 f"JOIN {t('reinsurance', 'treaty')} tr ON tr.treaty_id = s.treaty_id "
                 f"WHERE s.submission_status_code = 'BOUND' ORDER BY s.submission_reference"),
                ("What is our reported gross loss for Windstorm Ostara on the treaty book?",
                 f"SELECT SUM(l.gross_loss_amount) AS gross_loss FROM {t('reinsurance', 'event_loss')} l "
                 f"JOIN {t('reinsurance', 'cat_event')} e ON e.cat_event_id = l.cat_event_id "
                 f"WHERE e.event_name = 'Windstorm Ostara' AND l.loss_basis_code = 'REPORTED' "
                 f"AND l.treaty_id IS NOT NULL"),
            ],
        },
        "life": {
            "title": "Bricksurance — Life & Valuations",
            "description": ("Bricksurance Life and group valuations: model points, governed "
                            "assumption sets, scenario sets, auditable valuation runs and "
                            f"published results across regimes. {DISCLAIMER}"),
            "objects": [("life", "model_point"), ("life", "assumption_set"),
                        ("life", "scenario_set"), ("life", "valuation_run"),
                        ("life", "valuation_run_assumption"),
                        ("finance", "valuation_result"),
                        ("semantics", "valuation_metrics"),
                        ("reference", "data_dictionary")],
            "examples": [
                ("BEL by line of business at a valuation date",
                 f"SELECT line_of_business, MEASURE(total_amount) AS bel "
                 f"FROM {t('semantics', 'valuation_metrics')} "
                 f"WHERE valuation_measure_code = 'BEL' AND valuation_date = DATE '2026-06-30' "
                 f"AND currency_code = 'GBP' GROUP BY line_of_business",
                 "Always constrain valuation_measure_code AND currency_code before summing."),
                ("The full recipe of a valuation run (reproducibility)",
                 f"SELECT r.valuation_run_id, r.valuation_date, r.run_verdict_code, r.model_version, "
                 f"s.name AS scenario_set, a.assumption_type_code, a.version "
                 f"FROM {t('life', 'valuation_run')} r "
                 f"LEFT JOIN {t('life', 'scenario_set')} s ON s.scenario_set_id = r.scenario_set_id "
                 f"LEFT JOIN {t('life', 'valuation_run_assumption')} ra ON ra.valuation_run_id = r.valuation_run_id "
                 f"LEFT JOIN {t('life', 'assumption_set')} a ON a.assumption_set_id = ra.assumption_set_id "
                 f"ORDER BY r.run_timestamp",
                 "Run + assumption sets + scenario set + model version = the reproducible recipe."),
            ],
            "benchmarks": [
                ("What is the BEL for Term Life at the 30 June 2026 valuation in GBP?",
                 f"SELECT MEASURE(total_amount) AS bel FROM {t('semantics', 'valuation_metrics')} "
                 f"WHERE valuation_measure_code = 'BEL' AND line_of_business = 'Term Life' "
                 f"AND valuation_date = DATE '2026-06-30' AND currency_code = 'GBP'"),
                ("Which assumption sets did the latest green valuation run use?",
                 f"SELECT a.assumption_type_code, a.version, a.assumption_status_code "
                 f"FROM {t('life', 'valuation_run')} r "
                 f"JOIN {t('life', 'valuation_run_assumption')} ra ON ra.valuation_run_id = r.valuation_run_id "
                 f"JOIN {t('life', 'assumption_set')} a ON a.assumption_set_id = ra.assumption_set_id "
                 f"WHERE r.run_verdict_code = 'GREEN' AND r.scenario_set_id IS NOT NULL "
                 f"AND r.run_timestamp = (SELECT MAX(run_timestamp) FROM {t('life', 'valuation_run')} "
                 f"WHERE run_verdict_code = 'GREEN' AND scenario_set_id IS NOT NULL)"),
                ("How many life policies are represented in the 30 June 2026 model point file?",
                 f"SELECT SUM(policy_count) AS policies_represented FROM {t('life', 'model_point')} "
                 f"WHERE valuation_date = DATE '2026-06-30'"),
            ],
        },
    }


def uid():
    return uuid.uuid4().hex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", required=True, choices=["pnc", "reinsurance", "life"])
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--warehouse-id")
    ap.add_argument("--space-id", help="Patch this space instead of creating a new one")
    args = ap.parse_args()

    binding = yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())

    def t(domain, name):
        return f"{binding['catalog']}.{binding['schema_pattern'].format(domain=domain)}.{name}"

    cfg = spaces_config(t)[args.space]
    tables = sorted({t(d, n) for d, n in cfg["objects"]})
    if len(tables) > MAX_SPACE_TABLES:
        raise SystemExit(f"{len(tables)} objects exceed the Genie limit of {MAX_SPACE_TABLES}.")

    instructions = (ROOT / "build" / "genie" / "genie_instructions.md").read_text()
    serialized = {
        "version": 2,
        "data_sources": {"tables": [{"identifier": i} for i in tables]},
        "instructions": {
            "text_instructions": [{"id": uid(), "content": [instructions]}],
            "example_question_sqls": sorted(
                ({"id": uid(), "question": [q], "sql": [sql], "usage_guidance": [g]}
                 for q, sql, g in cfg["examples"]), key=lambda x: x["id"]),
        },
        "benchmarks": {
            "questions": sorted(
                ({"id": uid(), "question": [q],
                  "answer": [{"format": "SQL", "content": [sql]}]}
                 for q, sql in cfg["benchmarks"]), key=lambda x: x["id"]),
        },
    }

    w = WorkspaceClient(profile=args.profile)
    wid = args.warehouse_id
    if not wid:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from deploy_databricks import pick_warehouse
        wid = pick_warehouse(w).id
    payload = {"title": cfg["title"], "description": cfg["description"],
               "warehouse_id": wid, "serialized_space": json.dumps(serialized, indent=2)}
    if args.space_id:
        resp = w.api_client.do("PATCH", f"/api/2.0/genie/spaces/{args.space_id}", body=payload)
    else:
        payload["parent_path"] = PARENT_PATH
        w.workspace.mkdirs(PARENT_PATH)
        resp = w.api_client.do("POST", "/api/2.0/genie/spaces", body=payload)
    print(f"{cfg['title']}: {w.config.host}/genie/rooms/{resp['space_id']}")


if __name__ == "__main__":
    main()
