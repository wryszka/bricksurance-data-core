"""One Number demo: governed loss-ratio definitions on top of the Data Core.

Idempotent. It creates:
  semantics.loss_ratio_components  view: one row per policy with every loss-ratio
                                   building block, plus outside company data
  semantics.loss_ratio_definition  table: versioned, approved definitions
                                   (the "rulebook" the business owns)
  semantics.loss_ratio_metrics     metric view: published from the APPROVED
                                   definition (republished by publish())

Usage:
  uv run --system-certs --with databricks-sdk python tools/one_number_setup.py \
      [--profile fevm-lr-serverless-aws-us] [--reset]

NOTE: once the Data Core Console app has published, the app's service
principal owns loss_ratio_metrics (it must, to republish on approval). From
then on reset from the app: One Number -> step 6 -> Explore -> "Reset the
demo", or POST /api/one-number/reset. This script is for first-time setup.

--reset restores the seed rulebook (v1 approved, nothing pending) and
republishes the metric view and the governed Genie space. Run it before each
live run of the demo. The definition and publishing logic lives in
app/backend/one_number.py, shared with the app.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient

CAT = "lr_serverless_aws_us_catalog"
S = f"{CAT}.bricksurance_semantics"
WAREHOUSE = "ab79eced8207d29b"

COMPONENTS_VIEW = f"""
CREATE OR REPLACE VIEW {S}.loss_ratio_components
COMMENT 'One row per policy with every building block of a loss ratio, so any definition can be computed from the same numbers: written and earned premium, claims paid, case reserves, IBNR, claims-handling costs (ALAE) and recoveries. Includes who the client is according to outside company data. Amounts in policy currency; always filter currency_code. IBNR is the line-level actuarial IBNR allocated to policies in proportion to their open case reserves.'
AS
WITH ph AS (
  SELECT DISTINCT policy_id, party_id
  FROM {CAT}.bricksurance_party.party_role
  WHERE party_role_type_code = 'POLICYHOLDER' AND policy_id IS NOT NULL
),
ct AS (
  SELECT cl.policy_id, t.currency_code,
    SUM(CASE WHEN t.claim_transaction_type_code = 'INDEMNITY_PAYMENT' THEN t.amount ELSE 0 END) AS claims_paid,
    SUM(CASE WHEN t.claim_transaction_type_code = 'CASE_RESERVE_MOVEMENT' THEN t.amount ELSE 0 END) AS case_reserves,
    SUM(CASE WHEN t.claim_transaction_type_code = 'EXPENSE_PAYMENT' THEN t.amount ELSE 0 END) AS claims_handling_costs,
    -SUM(CASE WHEN t.claim_transaction_type_code = 'RECOVERY' THEN t.amount ELSE 0 END) AS recoveries,
    COUNT(DISTINCT cl.claim_id) AS claim_count
  FROM {CAT}.bricksurance_claim.claim cl
  JOIN {CAT}.bricksurance_claim.claim_transaction t USING (claim_id)
  GROUP BY ALL
),
base AS (
  SELECT pe.policy_id, pe.line_of_business_code, pe.underwriting_year, pe.currency_code,
         pe.written_premium, pe.earned_premium,
         COALESCE(ct.claims_paid, 0) AS claims_paid,
         COALESCE(ct.case_reserves, 0) AS case_reserves,
         COALESCE(ct.claims_handling_costs, 0) AS claims_handling_costs,
         COALESCE(ct.recoveries, 0) AS recoveries,
         COALESCE(ct.claim_count, 0) AS claim_count
  FROM {S}.premium_earning pe
  LEFT JOIN ct ON ct.policy_id = pe.policy_id AND ct.currency_code = pe.currency_code
),
ibnr AS (
  SELECT line_of_business_code, currency_code, SUM(amount) AS ibnr_total
  FROM {CAT}.bricksurance_finance.valuation_result
  WHERE valuation_measure_code = 'IBNR'
  GROUP BY ALL
),
case_tot AS (
  SELECT line_of_business_code, currency_code, SUM(case_reserves) AS case_total
  FROM base GROUP BY ALL
)
SELECT b.policy_id, b.line_of_business_code, lob.label AS line_of_business,
       b.underwriting_year, b.currency_code,
       pa.name AS client_name,
       f.global_company_id, f.industry_sector, f.annual_revenue_gbp,
       f.employee_count, f.financial_stress_score, f.financial_stress_band,
       b.written_premium, b.earned_premium, b.claims_paid, b.case_reserves,
       ROUND(COALESCE(i.ibnr_total, 0) * b.case_reserves / NULLIF(ct.case_total, 0), 2) AS ibnr,
       b.claims_handling_costs, b.recoveries, b.claim_count
FROM base b
LEFT JOIN ph USING (policy_id)
LEFT JOIN {CAT}.bricksurance_party.party pa ON pa.party_id = ph.party_id
LEFT JOIN {CAT}.bricksurance_enrichment.business_firmographics f ON f.party_id = ph.party_id
LEFT JOIN {CAT}.bricksurance_reference.line_of_business lob ON lob.line_of_business_code = b.line_of_business_code
LEFT JOIN ibnr i ON i.line_of_business_code = b.line_of_business_code AND i.currency_code = b.currency_code
LEFT JOIN case_tot ct ON ct.line_of_business_code = b.line_of_business_code AND ct.currency_code = b.currency_code
"""

DEFINITION_TABLE = f"""
CREATE TABLE IF NOT EXISTS {S}.loss_ratio_definition (
  version INT NOT NULL COMMENT 'Definition version, increasing.',
  status STRING NOT NULL COMMENT 'PROPOSED, APPROVED (the one in force) or SUPERSEDED.',
  name STRING NOT NULL COMMENT 'Short name of the definition.',
  include_case_reserves BOOLEAN NOT NULL COMMENT 'Count claims reported but not yet paid (case reserves).',
  include_ibnr BOOLEAN NOT NULL COMMENT 'Count claims incurred but not yet reported (IBNR).',
  include_claims_handling_costs BOOLEAN NOT NULL COMMENT 'Count allocated loss adjustment expenses (ALAE) such as legal and surveyor fees.',
  net_of_recoveries BOOLEAN NOT NULL COMMENT 'Deduct salvage, subrogation and other recoveries.',
  premium_basis STRING NOT NULL COMMENT 'EARNED or WRITTEN premium as the denominator.',
  definition_text STRING NOT NULL COMMENT 'The definition in plain words, as signed off.',
  rationale STRING COMMENT 'Why this version was made.',
  proposed_by STRING COMMENT 'Who drafted the version.',
  approved_by STRING COMMENT 'Who approved it - must differ from proposed_by.',
  proposed_at TIMESTAMP,
  approved_at TIMESTAMP
)
COMMENT 'The loss-ratio rulebook: every version of how the company defines its loss ratio, who proposed it and who approved it. Exactly one version is APPROVED at a time, and that version is what the published loss_ratio_metrics, the assistant and the board pack all use.'
"""

def sql(w, stmt):
    r = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE, statement=stmt, wait_timeout="50s")
    if r.status.state.value != "SUCCEEDED":
        raise RuntimeError(f"{r.status.error.message if r.status.error else r.status.state}\n{stmt[:300]}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="fevm-lr-serverless-aws-us")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--create-spaces", action="store_true",
                    help="Create the two Genie spaces (prints ids; set them in app.yaml)")
    a = ap.parse_args()
    os.environ["DATABRICKS_CONFIG_PROFILE"] = a.profile
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
    from backend import one_number as on  # shared with the app

    w = WorkspaceClient(profile=a.profile)
    sql(w, COMPONENTS_VIEW)
    sql(w, DEFINITION_TABLE)
    if a.create_spaces:
        for name, payload in (("raw", on.raw_space_payload()), ("governed", on.governed_space_payload(
                {**on.SEED_V1, "version": 1, "name": "seed", "approved_by": "Chief Actuary",
                 "approved_at": "2026-07-03", "definition_text": on.definition_text(on.SEED_V1)}))):
            payload["parent_path"] = "/Workspace/Shared/bricksurance-data-core"
            sid = w.api_client.do("POST", "/api/2.0/genie/spaces", body=payload)["space_id"]
            print(f"{name} space: {sid}")
        return
    w.api_client.do("PATCH", f"/api/2.0/genie/spaces/{on.RAW_SPACE}", body=on.raw_space_payload())
    n = int(sql(w, f"SELECT count(*) FROM {S}.loss_ratio_definition").result.data_array[0][0])
    st = on.reset() if (a.reset or n == 0) else (on.publish() and on.state())
    print(json.dumps({"published_version": st["approved"]["version"],
                      "company": round(st["book"]["loss_ratio"], 4),
                      "teams": {x["team"]: round(x["value"], 4) for x in st["teams"]}}))


if __name__ == "__main__":
    main()
