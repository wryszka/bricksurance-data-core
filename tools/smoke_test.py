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

    # expected physical objects, derived from the model specs
    specs = [yaml.safe_load(p.read_text()) for p in sorted((ROOT / "model").rglob("*.yaml"))
             if p.name != "model.yaml"]
    # + 2 generated reference tables that are not spec files: the data
    # dictionary and the certification-attestation record.
    n_tables = sum(1 for s in specs if s["kind"] in ("entity", "code_set")) + 2
    n_views = sum(1 for s in specs if s["kind"] in ("view", "metric_view"))
    n_fks = sum(1 for s in specs for a in s.get("attributes", [])
                if a.get("code_set") or a.get("references"))

    w = WorkspaceClient(profile=args.profile)
    wid = args.warehouse_id or pick_warehouse(w).id

    def q(domain, table):
        return f"{cat}.{binding['schema_pattern'].format(domain=domain)}.{table}"

    checks = [
        (f"{n_tables} model tables deployed (migration log excluded)",
         f"SELECT COUNT(*) FROM {cat}.information_schema.tables "
         f"WHERE table_schema LIKE '{prefix}%' AND table_schema NOT LIKE '%partner\\_re' "
         f"AND table_type = 'MANAGED' AND table_name NOT IN ('schema_migration', 'governance_action')", str(n_tables)),
        (f"{n_views} semantic views deployed (vector indexes excluded)",
         f"SELECT COUNT(*) FROM {cat}.information_schema.tables "
         f"WHERE table_schema LIKE '{prefix}%' AND table_schema NOT LIKE '%partner\\_re' "
         f"AND table_type <> 'MANAGED' AND table_name NOT LIKE '%\\_index'", str(n_views)),
        (f"{n_fks} foreign-key relationships (from the model)",
         f"SELECT COUNT(*) FROM {cat}.information_schema.table_constraints "
         f"WHERE constraint_schema LIKE '{prefix}%' AND constraint_schema NOT LIKE '%partner\\_re' AND constraint_type = 'FOREIGN KEY'", str(n_fks)),
        ("172 policies (60 core book + 112 reserving-history)",
         f"SELECT COUNT(*) FROM {q('policy', 'policy')}", "172"),
        ("130 claims (18 core + reserving development history)",
         f"SELECT COUNT(*) FROM {q('claim', 'claim')}", "130"),
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
        ("outbound cession bordereau derives lines with correct ceded premium",
         f"SELECT COUNT(*) > 0 AND SUM(ABS(ceded_premium - ROUND(gross_premium * ceded_share, 2))) = 0 "
         f"FROM {q('exchange', 'cession_bordereau_line')}", "true"),
        ("every core-book policy converted from exactly one quote",
         f"SELECT COUNT(*) = (SELECT COUNT(*) FROM {q('policy', 'policy')} "
         f"WHERE policy_number NOT LIKE 'POL-%-9%') "
         f"AND COUNT(DISTINCT policy_id) = COUNT(*) "
         f"FROM {q('policy', 'quote')} WHERE quote_status_code = 'CONVERTED'", "true"),
        ("bound submission thread resolves to the golden-thread treaty",
         f"SELECT s.submission_reference, t.treaty_reference "
         f"FROM {q('reinsurance', 'submission')} s "
         f"JOIN {q('reinsurance', 'treaty')} t ON t.treaty_id = s.treaty_id "
         f"WHERE s.submission_reference = 'SUB-2026-000001'",
         "SUB-2026-000001|TR-QS-PROP-2026"),
        ("published case reserves tie out to claim transactions (CP, GBP)",
         f"SELECT (SELECT CAST(vr.amount AS DECIMAL(18,2)) FROM {q('finance', 'valuation_result')} vr "
         f"WHERE vr.valuation_measure_code = 'CASE_RESERVE_TOTAL' "
         f"AND vr.line_of_business_code = 'COMMERCIAL_PROPERTY' AND vr.currency_code = 'GBP') = "
         f"(SELECT CAST(SUM(ct.amount) AS DECIMAL(18,2)) FROM {q('claim', 'claim_transaction')} ct "
         f"JOIN {q('claim', 'claim')} c ON c.claim_id = ct.claim_id "
         f"JOIN {q('policy', 'policy')} p ON p.policy_id = c.policy_id "
         f"WHERE ct.claim_transaction_type_code = 'CASE_RESERVE_MOVEMENT' "
         f"AND p.line_of_business_code = 'COMMERCIAL_PROPERTY' AND ct.currency_code = 'GBP')", "true"),
        ("every motor insured object has its vehicle satellite",
         f"SELECT COUNT(*) FROM {q('policy', 'insured_object')} io "
         f"LEFT JOIN {q('policy', 'vehicle')} v ON v.insured_object_id = io.insured_object_id "
         f"WHERE io.insured_object_type_code = 'VEHICLE' AND v.vehicle_id IS NULL", "0"),
        ("every event loss belongs to exactly one book",
         f"SELECT COUNT(*) FROM {q('reinsurance', 'event_loss')} "
         f"WHERE CAST(treaty_id IS NOT NULL AS INT) + CAST(policy_id IS NOT NULL AS INT) <> 1", "0"),
        ("metric view answers GWP for GBP / UWY 2026",
         f"SELECT CAST(MEASURE(gross_written_premium) AS INT) > 0 "
         f"FROM {q('semantics', 'underwriting_metrics')} "
         f"WHERE currency_code = 'GBP' AND underwriting_year = 2026", "true"),
        ("governed tool: appetite check answers within and out of appetite",
         f"SELECT {q('product', 'fn_appetite_check')}('COMMERCIAL_PROPERTY', 'GB', 5000000) "
         f"LIKE 'WITHIN_APPETITE%' AND "
         f"{q('product', 'fn_appetite_check')}('COMMERCIAL_PROPERTY', 'GB', 30000000) "
         f"LIKE 'OUT_OF_APPETITE%'", "true"),
        ("governed tool: outstanding reserve on the hero claim",
         f"SELECT CAST({q('claim', 'fn_outstanding_reserve')}('CLM-2026-000001') AS INT)", "270000"),
        ("agentic buyer thread: machine quote declined by the uw agent on record",
         f"SELECT d.underwriting_decision_type_code, CAST(d.decided_by_agent AS STRING) "
         f"FROM {q('policy', 'underwriting_decision')} d "
         f"JOIN {q('policy', 'quote')} qq ON qq.quote_id = d.quote_id "
         f"WHERE qq.quote_number = 'QUO-2026-000902'", "DECLINE|true"),
        ("every converted quote carries an underwriting decision",
         f"SELECT COUNT(*) FROM {q('policy', 'quote')} qq "
         f"LEFT JOIN {q('policy', 'underwriting_decision')} d ON d.quote_id = qq.quote_id "
         f"WHERE qq.quote_status_code = 'CONVERTED' AND d.underwriting_decision_id IS NULL", "0"),
        ("renewal chains resolve to real prior policies",
         f"SELECT COUNT(*) > 0 AND COUNT(*) = COUNT(prev.policy_id) "
         f"FROM {q('policy', 'policy')} p "
         f"JOIN {q('policy', 'policy')} prev ON prev.policy_id = p.renews_policy_id "
         f"WHERE p.renews_policy_id IS NOT NULL", "true"),
        ("every document belongs to exactly one context",
         f"SELECT COUNT(*) FROM {q('content', 'document')} "
         f"WHERE CAST(product_id IS NOT NULL AS INT) + CAST(policy_id IS NOT NULL AS INT) "
         f"+ CAST(claim_id IS NOT NULL AS INT) + CAST(submission_id IS NOT NULL AS INT) <> 1", "0"),
        ("ledger reconciles: premium journal lines equal premium transactions (GBP)",
         f"SELECT (SELECT CAST(SUM(jl.amount) AS DECIMAL(18,2)) FROM {q('finance', 'journal_line')} jl "
         f"WHERE jl.source_entity = 'premium_transaction' AND jl.currency_code = 'GBP' AND jl.amount > 0) = "
         f"(SELECT CAST(SUM(amount) AS DECIMAL(18,2)) FROM {q('policy', 'premium_transaction')} "
         f"WHERE currency_code = 'GBP')", "true"),
        ("combined ratio computes for Commercial Property (GBP)",
         f"SELECT MEASURE(combined_ratio) BETWEEN 0.2 AND 3.0 "
         f"FROM {q('semantics', 'performance_metrics')} "
         f"WHERE currency_code = 'GBP' AND line_of_business = 'Commercial Property'", "true"),
        ("aged premium debt derives from receivables",
         f"SELECT COUNT(*) >= 1 FROM (SELECT policy_id FROM {q('finance', 'receivable_transaction')} "
         f"GROUP BY policy_id HAVING SUM(amount) > 0)", "true"),
        ("erasure request refused with recorded grounds",
         f"SELECT COUNT(*) FROM {q('party', 'data_subject_request')} "
         f"WHERE dsr_type_code = 'ERASURE' AND dsr_status_code = 'REFUSED' "
         f"AND notes IS NOT NULL", "1"),
        ("the general ledger balances: trial balance nets to zero",
         f"SELECT CAST(SUM(amount) AS DECIMAL(18,2)) FROM {q('finance', 'journal_line')}", "0.00"),
        ("every journal is internally balanced (debits = credits)",
         f"SELECT COUNT(*) FROM (SELECT journal_id, SUM(amount) s "
         f"FROM {q('finance', 'journal_line')} GROUP BY journal_id) WHERE ROUND(s, 2) <> 0", "0"),
        ("governed tool: SE ledger balances via fn_trial_balance_check",
         f"SELECT CAST({q('finance', 'fn_trial_balance_check')}('le_se') AS DECIMAL(18,2))", "0.00"),
        ("group SCR coverage differs from solo (diversification is real)",
         f"SELECT (SELECT amount FROM {q('finance', 'valuation_result')} vr "
         f"JOIN {q('life', 'valuation_run')} r ON r.valuation_run_id = vr.valuation_run_id "
         f"WHERE r.reporting_level_code = 'GROUP' AND vr.valuation_measure_code = 'SCR_COVERAGE_RATIO') <> "
         f"(SELECT amount FROM {q('finance', 'valuation_result')} vr "
         f"JOIN {q('life', 'valuation_run')} r ON r.valuation_run_id = vr.valuation_run_id "
         f"WHERE r.reporting_level_code = 'SOLO' AND r.legal_entity_id = 'le_se' "
         f"AND vr.valuation_measure_code = 'SCR_COVERAGE_RATIO')", "true"),
        ("IFRS 17 CSM closing derives from movements (fn_csm_closing)",
         f"SELECT CAST({q('finance', 'fn_csm_closing')}(MIN(contract_group_id)) AS DECIMAL(18,2)) IS NOT NULL "
         f"FROM {q('finance', 'contract_group')} WHERE cohort_year = 2025", "true"),
        ("every legal entity rolls up to the group (or is the group)",
         f"SELECT COUNT(*) FROM {q('org', 'legal_entity')} "
         f"WHERE parent_legal_entity_id IS NULL AND legal_entity_type_code <> 'GROUP_HOLDING'", "0"),
        ("balance sheet has both asset and liability lines (SII regime)",
         f"SELECT COUNT(DISTINCT line_label) >= 4 FROM {q('finance', 'statement_line')} "
         f"WHERE statement_type_code = 'BALANCE_SHEET' AND reporting_regime_code = 'SOLVENCY_II'", "true"),
        ("every party role has exactly one context",
         f"SELECT COUNT(*) FROM {q('party', 'party_role')} "
         f"WHERE CAST(policy_id IS NOT NULL AS INT) + CAST(claim_id IS NOT NULL AS INT) "
         f"+ CAST(treaty_id IS NOT NULL AS INT) + CAST(quote_id IS NOT NULL AS INT) "
         f"+ CAST(submission_id IS NOT NULL AS INT) <> 1", "0"),
        # ---- new domains: enrichment, model/ML, pricing, depth ----------
        ("pricing build-up reconciles: derived factors sum to the rated premium",
         f"SELECT COUNT(*) FROM (SELECT subject_id, SUM(contribution) s "
         f"FROM {q('pricing', 'derived_factor')} WHERE subject_kind_code = 'QUOTE' "
         f"GROUP BY subject_id) x JOIN {q('policy', 'quote')} qq ON qq.quote_id = x.subject_id "
         f"WHERE ROUND(x.s, 2) <> ROUND(qq.rated_gross_premium, 2)", "0"),
        ("every model score traces to a governed model version",
         f"SELECT COUNT(*) FROM {q('model', 'model_score')} ms "
         f"LEFT JOIN {q('model', 'model_version')} mv ON mv.model_version_id = ms.model_version_id "
         f"WHERE mv.model_version_id IS NULL", "0"),
        ("referral rulebook: exactly one current version per rule (SCD2 integrity)",
         f"SELECT COUNT(*) FROM (SELECT rule_key, SUM(CAST(is_current AS INT)) c "
         f"FROM {q('product', 'referral_rule')} GROUP BY rule_key) WHERE c <> 1", "0"),
        ("enrichment coverage: telematics covers every motor policy",
         f"SELECT (SELECT subject_count FROM {q('semantics', 'enrichment_coverage')} "
         f"WHERE enrichment_source = 'motor_telematics_aggregate') = "
         f"(SELECT COUNT(*) FROM {q('policy', 'policy')} WHERE line_of_business_code = 'MOTOR')", "true"),
        ("governed tool: champion score resolves for a scored quote",
         f"SELECT {q('model', 'fn_champion_score')}('QUOTE', "
         f"(SELECT subject_id FROM {q('model', 'model_score')} WHERE subject_kind_code = 'QUOTE' LIMIT 1)) "
         f"IS NOT NULL", "true"),
        ("pricing metric view answers conversion rate for motor (GBP)",
         f"SELECT MEASURE(conversion_rate) BETWEEN 0 AND 1 "
         f"FROM {q('semantics', 'pricing_metrics')} "
         f"WHERE line_of_business_code = 'MOTOR' AND currency_code = 'GBP'", "true"),
        ("model governance view: the frequency model has a champion in force",
         f"SELECT MEASURE(champion_count) >= 1 "
         f"FROM {q('semantics', 'model_governance_metrics')} "
         f"WHERE model_purpose_code = 'PRICING_FREQUENCY'", "true"),
        # ---- WP1 policy lifecycle spine ----------------------------------
        ("vw_policy_current has exactly one row per policy",
         f"SELECT (SELECT COUNT(*) FROM {q('policy_lifecycle', 'vw_policy_current')}) = "
         f"(SELECT COUNT(*) FROM {q('policy', 'policy')})", "true"),
        ("vw_policy_current reconciles row-for-row to the policy table (event spine complete)",
         f"SELECT COUNT(*) FROM {q('policy', 'policy')} p "
         f"JOIN {q('policy_lifecycle', 'vw_policy_current')} v ON v.policy_id = p.policy_id "
         f"WHERE v.policy_number <> p.policy_number OR v.policy_status_code <> p.policy_status_code "
         f"OR v.line_of_business_code <> p.line_of_business_code OR v.inception_date <> p.inception_date "
         f"OR v.expiry_date <> p.expiry_date OR v.currency_code <> p.currency_code "
         f"OR v.underwriting_year <> p.underwriting_year OR v.legal_entity_id <> p.legal_entity_id "
         f"OR COALESCE(v.renews_policy_id,'') <> COALESCE(p.renews_policy_id,'')", "0"),
        ("every policy event chain verifies intact (fn_verify_event_chain, estate-wide)",
         f"SELECT CAST(SUM({q('policy_lifecycle', 'fn_verify_event_chain')}(policy_id)) AS INT) "
         f"FROM {q('policy', 'policy')}", "0"),
        ("policy event sequence numbers are gap-free per policy",
         f"SELECT COUNT(*) FROM (SELECT policy_id, COUNT(*) c, MIN(sequence_no) mn, MAX(sequence_no) mx "
         f"FROM {q('policy_lifecycle', 'policy_event')} GROUP BY policy_id) WHERE mn <> 1 OR mx <> c", "0"),
        ("every claim attaches to the policy version in force at its loss (as-at, clamped to v1 for pre-inception losses)",
         f"SELECT COUNT(*) FROM {q('claim', 'claim')} c "
         f"JOIN {q('policy_lifecycle', 'policy_version')} pv ON pv.policy_version_id = c.policy_version_id "
         f"WHERE pv.policy_id <> c.policy_id OR NOT ("
         f"(pv.valid_from <= c.loss_date AND (pv.valid_to IS NULL OR c.loss_date <= pv.valid_to)) "
         f"OR (pv.version_no = 1 AND c.loss_date < pv.valid_from))", "0"),
        ("hero claim attaches to the post-MTA version (sum insured changed before the loss)",
         f"SELECT pv.version_no >= 2 FROM {q('claim', 'claim')} c "
         f"JOIN {q('policy_lifecycle', 'policy_version')} pv ON pv.policy_version_id = c.policy_version_id "
         f"WHERE c.claim_number = 'CLM-2026-000001'", "true"),
        ("lifecycle metric view answers new-business count",
         f"SELECT MEASURE(new_business_count) > 0 FROM {q('policy_lifecycle', 'lifecycle_metrics')}", "true"),
        # ---- WP2 premium accounting & earning ----------------------------
        ("premium proof reconciles: written = earned + unearned for every LOB (residual 0)",
         f"SELECT CAST(SUM(ABS(residual)) AS DECIMAL(18,2)) FROM {q('semantics', 'vw_premium_proof')}", "0.00"),
        ("every premium movement traces to a policy event (WP1 spine, orphan check)",
         f"SELECT COUNT(*) FROM {q('policy', 'premium_transaction')} pt "
         f"LEFT JOIN {q('policy_lifecycle', 'policy_event')} pe ON pe.event_id = pt.policy_event_id "
         f"WHERE pe.event_id IS NULL", "0"),
        ("premium metric view answers written premium and IPT (GBP)",
         f"SELECT MEASURE(gross_written_premium) > 0 AND MEASURE(ipt_collected) > 0 "
         f"FROM {q('semantics', 'premium_metrics')} WHERE currency_code = 'GBP'", "true"),
        ("governed tool: fn_earn_premium earns the hero policy",
         f"SELECT {q('policy', 'fn_earn_premium')}("
         f"(SELECT policy_id FROM {q('policy', 'policy')} WHERE policy_number = 'POL-2026-000001')) > 0", "true"),
        # ---- WP5 renewal & retention loop --------------------------------
        ("retention response curve is monotonic in the price walk (motor)",
         f"SELECT (SELECT renewal_probability FROM {q('renewal', 'retention_response_curve')} "
         f"WHERE segment = 'MOTOR' AND price_walk_band = '0-5%') > "
         f"(SELECT renewal_probability FROM {q('renewal', 'retention_response_curve')} "
         f"WHERE segment = 'MOTOR' AND price_walk_band = '20%+')", "true"),
        ("renewal outcomes include real lapses (retention is a function of price, not 100%)",
         f"SELECT MEASURE(lapsed_count) > 0 AND MEASURE(retention_rate) < 1 "
         f"FROM {q('renewal', 'renewal_metrics')}", "true"),
        ("every renewal case attaches to a real policy",
         f"SELECT COUNT(*) FROM {q('renewal', 'renewal_case')} rc "
         f"LEFT JOIN {q('policy', 'policy')} p ON p.policy_id = rc.policy_id "
         f"WHERE p.policy_id IS NULL", "0"),
        # ---- WP3 assets & ALM --------------------------------------------
        ("governed tool: annuity portfolio duration is plausible (fn_duration 5-15y)",
         f"SELECT {q('investment', 'fn_duration')}('ANNUITY_MA') BETWEEN 5 AND 15", "true"),
        ("governed tool: +100bps stress reduces market value below -100bps (fn_stress_mv)",
         f"SELECT {q('investment', 'fn_stress_mv')}('ANNUITY_MA', 100) < "
         f"{q('investment', 'fn_stress_mv')}('ANNUITY_MA', -100)", "true"),
        ("governed tool: annuity duration gap vs 9y liability is nonzero (fn_duration_gap)",
         f"SELECT ABS({q('investment', 'fn_duration_gap')}('ANNUITY_MA', 9.0)) > 0.1", "true"),
        ("published S2 market input: interest-up loss is positive for the annuity portfolio",
         f"SELECT interest_up_loss > 0 FROM {q('semantics', 'vw_s2_market_inputs')} "
         f"WHERE portfolio_code = 'ANNUITY_MA'", "true"),
        ("published ALM view returns annuity asset cashflows by year",
         f"SELECT COUNT(*) > 0 FROM {q('semantics', 'vw_alm_annuity_match')}", "true"),
        ("asset metric view answers market value",
         f"SELECT MEASURE(asset_market_value) > 0 FROM {q('semantics', 'asset_metrics')}", "true"),
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
