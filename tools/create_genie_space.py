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
                        ("semantics", "performance_metrics"),
                        ("semantics", "premium_earning"),
                        ("claim", "fraud_signal"),
                        ("reference", "data_dictionary")],
            "examples": [
                ("Gross written premium and written-basis loss ratio by line of business (GBP, UWY 2026)",
                 f"SELECT line_of_business, MEASURE(gross_written_premium) AS gwp, "
                 f"MEASURE(loss_ratio_written) AS loss_ratio_written FROM {t('semantics', 'underwriting_metrics')} "
                 f"WHERE currency_code = 'GBP' AND underwriting_year = 2026 GROUP BY line_of_business",
                 "KPI questions use the metric view with MEASURE(); constrain currency_code before summing money. The canonical (earned-basis) loss ratio is MEASURE(loss_ratio) on performance_metrics."),
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
        "distribution": {
            "title": "Bricksurance — Distribution, Underwriting & Conduct",
            "description": ("The front of the business: products and appetite as data, the "
                            "quote funnel across channels (including machine buyer agents), "
                            "audited underwriting decisions, commissions, complaints and the "
                            f"business event stream. {DISCLAIMER}"),
            "objects": [("product", "product"), ("product", "product_coverage"),
                        ("product", "underwriting_question"), ("product", "appetite_rule"),
                        ("policy", "quote"), ("policy", "underwriting_decision"),
                        ("policy", "policy"), ("distribution", "commission_transaction"),
                        ("conduct", "complaint"), ("events", "business_event"),
                        ("party", "party"), ("party", "party_role"),
                        ("reference", "data_dictionary")],
            "examples": [
                ("Quote funnel by channel",
                 f"SELECT distribution_channel_code, quote_status_code, COUNT(*) AS quotes "
                 f"FROM {t('policy', 'quote')} GROUP BY 1, 2 ORDER BY 1, 2",
                 "Machine agents (MACHINE_AGENT) are a channel like any other."),
                ("Agent vs human underwriting decisions",
                 f"SELECT decided_by_agent, underwriting_decision_type_code, COUNT(*) "
                 f"FROM {t('policy', 'underwriting_decision')} GROUP BY 1, 2",
                 "Machine decisions are audited identically to human ones."),
            ],
            "benchmarks": [
                ("Which quotes came from machine buyer agents and what was decided?",
                 f"SELECT qq.quote_number, qq.quote_status_code, d.underwriting_decision_type_code, d.rationale "
                 f"FROM {t('policy', 'quote')} qq "
                 f"LEFT JOIN {t('policy', 'underwriting_decision')} d ON d.quote_id = qq.quote_id "
                 f"WHERE qq.distribution_channel_code = 'MACHINE_AGENT' ORDER BY qq.quote_number"),
                ("How much commission did we pay each broker, including clawbacks?",
                 f"SELECT pt.name, SUM(ct.amount) AS net_commission "
                 f"FROM {t('distribution', 'commission_transaction')} ct "
                 f"JOIN {t('party', 'party')} pt ON pt.party_id = ct.party_id "
                 f"GROUP BY pt.name ORDER BY net_commission DESC"),
                ("How many complaints were upheld and what redress did we pay?",
                 f"SELECT complaint_status_code, COUNT(*) AS complaints, SUM(redress_amount) AS redress "
                 f"FROM {t('conduct', 'complaint')} GROUP BY complaint_status_code"),
                ("What is our quote-to-policy retention: how many 2026 policies are renewals?",
                 f"SELECT COUNT(*) AS policies, COUNT(renews_policy_id) AS renewals "
                 f"FROM {t('policy', 'policy')} WHERE underwriting_year = 2026"),
            ],
        },
        "customer": {
            "title": "Bricksurance — Customer & Privacy",
            "description": ("Parties and their contact points, consents per processing "
                            "purpose, GDPR data subject requests and complaints - the "
                            f"customer-360 and privacy-office view. {DISCLAIMER}"),
            "objects": [("party", "party"), ("party", "party_role"),
                        ("party", "contact_point"), ("party", "consent"),
                        ("party", "data_subject_request"), ("conduct", "complaint"),
                        ("finance", "receivable_transaction"), ("policy", "policy"),
                        ("reference", "data_dictionary")],
            "examples": [
                ("A party's consents and requests",
                 f"SELECT pt.name, c.consent_purpose_code, c.consent_status_code, c.withdrawn_at "
                 f"FROM {t('party', 'consent')} c JOIN {t('party', 'party')} pt "
                 f"ON pt.party_id = c.party_id ORDER BY pt.name",
                 "Withdrawal is a state change with a timestamp, never a deletion."),
            ],
            "benchmarks": [
                ("Who has withdrawn marketing consent?",
                 f"SELECT pt.name, c.withdrawn_at FROM {t('party', 'consent')} c "
                 f"JOIN {t('party', 'party')} pt ON pt.party_id = c.party_id "
                 f"WHERE c.consent_purpose_code = 'MARKETING' AND c.consent_status_code = 'WITHDRAWN'"),
                ("What data subject requests are open or refused, and why?",
                 f"SELECT pt.name, r.dsr_type_code, r.dsr_status_code, r.notes "
                 f"FROM {t('party', 'data_subject_request')} r "
                 f"JOIN {t('party', 'party')} pt ON pt.party_id = r.party_id "
                 f"WHERE r.dsr_status_code <> 'COMPLETED'"),
                ("Which policyholders owe us premium (aged debt)?",
                 f"SELECT pt.name, p.policy_number, SUM(rt.amount) AS outstanding "
                 f"FROM {t('finance', 'receivable_transaction')} rt "
                 f"JOIN {t('policy', 'policy')} p ON p.policy_id = rt.policy_id "
                 f"JOIN {t('party', 'party_role')} pr ON pr.policy_id = p.policy_id "
                 f"AND pr.party_role_type_code = 'POLICYHOLDER' "
                 f"JOIN {t('party', 'party')} pt ON pt.party_id = pr.party_id "
                 f"GROUP BY pt.name, p.policy_number HAVING SUM(rt.amount) > 0 "
                 f"ORDER BY outstanding DESC"),
            ],
        },
        "finance": {
            "title": "Bricksurance — Finance & Controllership",
            "description": ("The finance function: a real double-entry ledger (chart of "
                            "accounts, balanced journals, periods), trial balance and "
                            "financial statements by legal entity and regime, receivables, "
                            "expenses, tax and budget-vs-actual. Solo and group. "
                            f"{DISCLAIMER}"),
            "objects": [("org", "legal_entity"), ("finance", "chart_of_account"),
                        ("finance", "accounting_period"), ("finance", "journal"),
                        ("finance", "journal_line"), ("finance", "statement_line"),
                        ("finance", "receivable_transaction"), ("finance", "expense_transaction"),
                        ("finance", "tax_transaction"), ("finance", "financial_plan"),
                        ("finance", "fx_rate"), ("semantics", "trial_balance"),
                        ("semantics", "financial_position"), ("semantics", "performance_metrics"),
                        ("reference", "data_dictionary")],
            "examples": [
                ("Trial balance for a legal entity (nets to zero)",
                 f"SELECT account_name, MEASURE(net_movement) AS movement "
                 f"FROM {t('semantics', 'trial_balance')} WHERE currency_code = 'GBP' "
                 f"GROUP BY account_name ORDER BY account_name",
                 "Sum of net_movement across all accounts is zero - the balancing check."),
                ("Income statement (Solvency II presentation)",
                 f"SELECT line_label, MEASURE(line_amount) AS amount "
                 f"FROM {t('semantics', 'financial_position')} "
                 f"WHERE statement_type = 'INCOME_STATEMENT' AND reporting_regime = 'SOLVENCY_II' "
                 f"AND currency_code = 'GBP' GROUP BY line_label",
                 "Statements are the ledger rolled up through the statement mapping."),
            ],
            "benchmarks": [
                ("Does the general ledger balance in GBP?",
                 f"SELECT ROUND(SUM(amount), 2) AS trial_balance FROM {t('finance', 'journal_line')} "
                 f"WHERE currency_code = 'GBP'"),
                ("Show the income statement lines under Solvency II in GBP",
                 f"SELECT line_label, MEASURE(line_amount) AS amount "
                 f"FROM {t('semantics', 'financial_position')} "
                 f"WHERE statement_type = 'INCOME_STATEMENT' AND reporting_regime = 'SOLVENCY_II' "
                 f"AND currency_code = 'GBP' GROUP BY line_label"),
                ("How much insurance premium tax have we booked?",
                 f"SELECT tax_type_code, SUM(amount) AS tax FROM {t('finance', 'tax_transaction')} "
                 f"WHERE tax_type_code = 'IPT' GROUP BY tax_type_code"),
                ("Budget vs actual gross written premium by line for 2026 (GBP)",
                 f"SELECT fp.line_of_business_code, fp.amount AS plan_gwp, "
                 f"MEASURE(m.gross_written_premium) AS actual_gwp "
                 f"FROM {t('finance', 'financial_plan')} fp "
                 f"JOIN {t('semantics', 'underwriting_metrics')} m "
                 f"ON m.line_of_business_code = fp.line_of_business_code AND m.currency_code = 'GBP' "
                 f"WHERE fp.plan_measure = 'gross_written_premium' GROUP BY fp.line_of_business_code, fp.amount"),
            ],
        },
        "capital": {
            "title": "Bricksurance — Capital, Investments & IFRS 17 (Group)",
            "description": ("The group CRO/CFO view: Solvency II capital solo and consolidated "
                            "(SCR, MCR, own funds, coverage ratio), the investment portfolio, "
                            "and IFRS 17 contract groups with the CSM roll-forward. "
                            f"{DISCLAIMER}"),
            "objects": [("org", "legal_entity"), ("life", "valuation_run"),
                        ("finance", "valuation_result"), ("finance", "contract_group"),
                        ("finance", "csm_movement"), ("investment", "investment_holding"),
                        ("investment", "investment_transaction"),
                        ("semantics", "valuation_metrics"), ("semantics", "investment_metrics"),
                        ("reference", "valuation_measure"), ("reference", "data_dictionary")],
            "examples": [
                ("Solvency II coverage ratio, solo vs group",
                 f"SELECT le.name, r.reporting_level_code, vr.amount AS coverage_ratio "
                 f"FROM {t('finance', 'valuation_result')} vr "
                 f"JOIN {t('life', 'valuation_run')} r ON r.valuation_run_id = vr.valuation_run_id "
                 f"JOIN {t('org', 'legal_entity')} le ON le.legal_entity_id = r.legal_entity_id "
                 f"WHERE vr.valuation_measure_code = 'SCR_COVERAGE_RATIO'",
                 "The group is not the sum of solos - diversification reduces group SCR."),
                ("CSM roll-forward for a contract group",
                 f"SELECT cm.csm_movement_type_code, cm.amount FROM {t('finance', 'csm_movement')} cm "
                 f"JOIN {t('finance', 'contract_group')} cg ON cg.contract_group_id = cm.contract_group_id "
                 f"WHERE cg.cohort_year = 2025 AND cg.line_of_business_code = 'TERM_LIFE'",
                 "Closing CSM is the signed sum of the movements - derived, never stored."),
            ],
            "benchmarks": [
                ("What is our Solvency II SCR coverage ratio at group level?",
                 f"SELECT vr.amount FROM {t('finance', 'valuation_result')} vr "
                 f"JOIN {t('life', 'valuation_run')} r ON r.valuation_run_id = vr.valuation_run_id "
                 f"WHERE r.reporting_level_code = 'GROUP' AND vr.valuation_measure_code = 'SCR_COVERAGE_RATIO'"),
                ("What is the market value of our investment portfolio by asset class (EUR)?",
                 f"SELECT asset_class, MEASURE(market_value) AS mv FROM {t('semantics', 'investment_metrics')} "
                 f"WHERE currency_code = 'EUR' GROUP BY asset_class ORDER BY mv DESC"),
                ("Show the CSM roll-forward for the 2025 term life cohort",
                 f"SELECT cm.csm_movement_type_code, cm.amount FROM {t('finance', 'csm_movement')} cm "
                 f"JOIN {t('finance', 'contract_group')} cg ON cg.contract_group_id = cm.contract_group_id "
                 f"WHERE cg.cohort_year = 2025 AND cg.line_of_business_code = 'TERM_LIFE'"),
                ("Which contract groups are onerous?",
                 f"SELECT line_of_business_code, cohort_year, measurement_model_code "
                 f"FROM {t('finance', 'contract_group')} WHERE onerous = true"),
            ],
        },
        "governance": {
            "title": "Bricksurance — Data Governance",
            "description": ("The model explaining itself: every entity and attribute with its "
                            "business definition, classification and standards crosswalk, plus "
                            f"the applied schema-migration history. {DISCLAIMER}"),
            "objects": [("reference", "data_dictionary"), ("reference", "schema_migration")],
            "examples": [
                ("Every PII attribute in the model",
                 f"SELECT entity_name, attribute_name, definition "
                 f"FROM {t('reference', 'data_dictionary')} "
                 f"WHERE data_classification = 'pii' ORDER BY entity_name",
                 "Classification is declared in the specs and generated everywhere."),
            ],
            "benchmarks": [
                ("Which attributes hold PII?",
                 f"SELECT entity_name, attribute_name FROM {t('reference', 'data_dictionary')} "
                 f"WHERE data_classification = 'pii' ORDER BY entity_name, attribute_name"),
                ("What schema migrations have been applied and when?",
                 f"SELECT from_version, to_version, classification, applied_at "
                 f"FROM {t('reference', 'schema_migration')} ORDER BY applied_at"),
                ("How many attributes does each entity have, by ACORD crosswalk coverage?",
                 f"SELECT entity_name, COUNT(*) AS attributes, "
                 f"COUNT(CASE WHEN acord_ref <> '' THEN 1 END) AS with_acord_ref "
                 f"FROM {t('reference', 'data_dictionary')} GROUP BY entity_name ORDER BY entity_name"),
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
        "reserving": {
            "title": "Bricksurance — Reserving",
            "description": ("Actuarial reserving over the governed loss-development triangle: "
                            "paid and incurred by accident year and development lag, IBNR and "
                            "ultimate losses, chain-ladder and Bornhuetter-Ferguson estimates. "
                            "The triangle is derived from claim movements and reconciles to the "
                            f"claims sub-ledger by construction. {DISCLAIMER}"),
            "objects": [("reserving", "loss_development"),
                        ("reserving", "reserving_metrics"),
                        ("reserving", "reserve_estimate"),
                        ("claim", "claim"), ("claim", "claim_transaction"),
                        ("reference", "data_dictionary")],
            "examples": [
                ("Cumulative paid development for an accident year (the triangle)",
                 f"SELECT development_lag, MEASURE(paid_to_date) AS cumulative_paid "
                 f"FROM {t('reserving', 'reserving_metrics')} "
                 f"WHERE line_of_business = 'Commercial Property' AND currency_code = 'GBP' "
                 f"AND accident_year = 2022 GROUP BY development_lag ORDER BY development_lag",
                 "The triangle is a metric view over claim movements; MEASURE(paid_to_date) sums cumulative paid. Constrain currency_code."),
                ("IBNR and ultimate by accident year and method",
                 f"SELECT accident_year, reserving_method_code, ultimate_loss, ibnr "
                 f"FROM {t('reserving', 'reserve_estimate')} "
                 f"WHERE line_of_business_code = 'COMMERCIAL_PROPERTY' AND currency_code = 'GBP' "
                 f"ORDER BY accident_year, reserving_method_code",
                 "reserve_estimate holds one row per method per accident year, so chain-ladder and BF sit side by side; nothing is overwritten."),
            ],
            "benchmarks": [
                ("What is our paid-to-incurred ratio by accident year for commercial property in GBP?",
                 f"SELECT accident_year, MEASURE(paid_ratio) AS paid_ratio "
                 f"FROM {t('reserving', 'reserving_metrics')} "
                 f"WHERE line_of_business = 'Commercial Property' AND currency_code = 'GBP' "
                 f"GROUP BY accident_year ORDER BY accident_year"),
                ("What is the total IBNR across accident years for commercial property, chain-ladder basis?",
                 f"SELECT SUM(ibnr) AS total_ibnr FROM {t('reserving', 'reserve_estimate')} "
                 f"WHERE line_of_business_code = 'COMMERCIAL_PROPERTY' AND currency_code = 'GBP' "
                 f"AND reserving_method_code = 'CHAIN_LADDER'"),
            ],
        },
    }


def uid():
    return uuid.uuid4().hex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", required=True, choices=["pnc", "reinsurance", "life", "distribution", "governance", "customer", "finance", "capital", "reserving"])
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
