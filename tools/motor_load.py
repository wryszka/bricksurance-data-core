"""Load the motor experience book and apply the source mappings on Databricks.

Order of operations (idempotent, rerun-safe):
  1. CREATE SCHEMA for the three source extracts + a `landing` volume in each
  2. upload data/motor/<schema>/<table>.parquet to the volumes, CTAS each table
  3. apply build/databricks/mappings/50_mapping_*.sql (source comments + tags,
     conformed views in semantics) and 60_*.sql (motor_loss_ratio_components)
     - 70_*.sql (the metric view) is NOT applied by default: the Console app
       republishes it from the approved rulebook and must own it. Use
       --with-metric-view for a first smoke test, then DROP it before the app
       publishes (see docs/MOTOR_CONTEXT_DEMO.md).
  4. grant the app service principal USE SCHEMA + SELECT on the source schemas
  5. smoke: the six segment-quarter targets must reproduce to the penny

Usage:
  uv run --system-certs --with databricks-sdk --with pyyaml python tools/motor_load.py \
      [--profile fevm-lr-serverless-aws-us] [--data data/motor] [--skip-upload] [--with-metric-view]
Run tools/generate.py (then world_engine.py) and tools/motor_book.py first.
"""
import argparse
import os
import sys
import time
from pathlib import Path

from databricks.sdk import WorkspaceClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from deploy_databricks import statements  # noqa: E402  (splits a generated .sql file into statements)

CAT = "lr_serverless_aws_us_catalog"
WAREHOUSE = "ab79eced8207d29b"
APP_SP = "f1d8523e-773e-469f-abc2-0bd81945bf51"  # data-core-console service principal
SCHEMAS = {"src_pas": "bricksurance_src_pas", "src_claims": "bricksurance_src_claims",
           "src_actuarial": "bricksurance_src_actuarial"}
TARGETS = {("PMU", "2026Q2"): (35_000_000, 25_200_000), ("PMU", "2026Q3"): (37_000_000, 31_820_000),
           ("PMO", "2026Q2"): (40_000_000, 22_000_000), ("PMO", "2026Q3"): (42_000_000, 23_940_000),
           ("CMV", "2026Q2"): (25_000_000, 16_800_000), ("CMV", "2026Q3"): (26_000_000, 19_840_000)}


def run(w, stmt, wid):
    r = w.statement_execution.execute_statement(statement=stmt, warehouse_id=wid, wait_timeout="50s")
    while r.status.state.value in ("PENDING", "RUNNING"):
        time.sleep(2)
        r = w.statement_execution.get_statement(r.statement_id)
    if r.status.state.value != "SUCCEEDED":
        msg = r.status.error.message if r.status.error else r.status.state.value
        raise RuntimeError(f"{msg}\n--- statement:\n{stmt[:400]}")
    return r


def rows(w, stmt, wid):
    return run(w, stmt, wid).result.data_array or []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="fevm-lr-serverless-aws-us")
    ap.add_argument("--warehouse-id", default=WAREHOUSE)
    ap.add_argument("--data", default="data/motor")
    ap.add_argument("--skip-upload", action="store_true", help="tables already loaded; only apply mappings + smoke")
    ap.add_argument("--with-metric-view", action="store_true", help="also apply 70_*.sql (you will own the metric view)")
    ap.add_argument("--no-grants", action="store_true")
    a = ap.parse_args()
    os.environ["DATABRICKS_CONFIG_PROFILE"] = a.profile
    w = WorkspaceClient(profile=a.profile)
    wid = a.warehouse_id
    data = ROOT / a.data
    print(f"Workspace {w.config.host}, warehouse {wid}")

    # 1-2. schemas, volumes, tables
    if not a.skip_upload:
        for short, schema in SCHEMAS.items():
            run(w, f"CREATE SCHEMA IF NOT EXISTS {CAT}.{schema}", wid)
            run(w, f"CREATE VOLUME IF NOT EXISTS {CAT}.{schema}.landing "
                   f"COMMENT 'Landing files for the {short} source extract (synthetic motor book).'", wid)
            for pq in sorted((data / short).glob("*.parquet")):
                vol_path = f"/Volumes/{CAT}/{schema}/landing/{pq.name}"
                t0 = time.time()
                with pq.open("rb") as f:
                    w.files.upload(vol_path, f, overwrite=True)
                run(w, f"CREATE OR REPLACE TABLE {CAT}.{schema}.{pq.stem} AS SELECT * FROM parquet.`{vol_path}`", wid)
                n = rows(w, f"SELECT count(*) FROM {CAT}.{schema}.{pq.stem}", wid)[0][0]
                print(f"  {schema}.{pq.stem:28s} {int(n):>9,d} rows  ({time.time() - t0:4.1f}s)")

    # 3. mappings: source documentation + conformed views, then the components view
    mdir = ROOT / "build" / "databricks" / "mappings"
    files = sorted(mdir.glob("50_*.sql")) + sorted(mdir.glob("60_*.sql"))
    if a.with_metric_view:
        files += sorted(mdir.glob("70_*.sql"))
    for path in files:
        stmts = statements(path)
        t0 = time.time()
        for s in stmts:
            run(w, s, wid)
        print(f"  {path.name:52s} {len(stmts):3d} statements ({time.time() - t0:4.1f}s)")

    # 4. grants for the Console app's service principal
    if not a.no_grants:
        for schema in SCHEMAS.values():
            run(w, f"GRANT USE SCHEMA, SELECT ON SCHEMA {CAT}.{schema} TO `{APP_SP}`", wid)
        print(f"  granted USE SCHEMA, SELECT on {len(SCHEMAS)} source schemas to the app SP")

    # 5. smoke: targets to the penny, from the components view (what the metric view reads)
    print("\nSmoke: segment x quarter from semantics.motor_loss_ratio_components (GBP)")
    res = rows(w, f"""
        SELECT motor_segment_code, accident_quarter,
               SUM(earned_premium), SUM(claims_paid + case_reserves + ibnr - recoveries), SUM(claim_count)
        FROM {CAT}.bricksurance_semantics.motor_loss_ratio_components
        WHERE accident_quarter IN ('2026Q2', '2026Q3')
        GROUP BY 1, 2 ORDER BY 1, 2""", wid)
    ok = True
    for seg, q, ep, inc, n in res:
        ep, inc = float(ep), float(inc)
        tep, tinc = TARGETS[(seg, q)]
        good = abs(ep - tep) < 0.005 and abs(inc - tinc) < 0.005
        ok &= good
        print(f"  {seg} {q}: earned {ep:>15,.2f}  incurred {inc:>15,.2f}  LR {inc / ep:6.2%}  claims {int(n):5d}  "
              f"{'PASS' if good else 'FAIL (want ' + f'{tep:,.2f} / {tinc:,.2f}' + ')'}")
    tot = rows(w, f"""SELECT accident_quarter, SUM(earned_premium), SUM(claims_paid + case_reserves + ibnr - recoveries)
                      FROM {CAT}.bricksurance_semantics.motor_loss_ratio_components GROUP BY 1 ORDER BY 1""", wid)
    for q, ep, inc in tot:
        print(f"  TOTAL {q}: earned {float(ep):>15,.2f}  incurred {float(inc):>15,.2f}  LR {float(inc) / float(ep):6.2%}")
    print("\nEXACT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
