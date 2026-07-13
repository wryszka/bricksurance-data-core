#!/usr/bin/env python3
"""Stand up a SECOND insurer from the ontology, locally, and exchange with it.

Meridian Mutual Insurance adopts the ontology the way any adopter would:
import the JSON, add a one-file binding (own schema prefix, own tag
namespace), generate, deploy. Same catalog for now — moving them to their own
workspace later changes the binding, nothing else.

Then the market-standard punchline: Meridian submits a premium bordereau from
THEIR canonical model into OURS as a column-aligned copy — when both parties
run the ontology, the mapping project disappears (contrast with the Atlas
coverholder CSV, which needed LLM mapping against the dictionary).

Usage:
    uv run --with databricks-sdk,pyyaml tools/create_second_company.py [--profile DEFAULT]
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy_databricks import pick_warehouse  # noqa: E402
from smoke_test import run_sql  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "build" / "second_company"

MERIDIAN_BDX = [
    ("mm_0001", "MER-CP-88101", "Roseline Bakeries Ltd", "COMMERCIAL_PROPERTY",
     "2026-06-01", "2027-05-31", 18400.00, 3220.00, "GB", "YO1 7HH"),
    ("mm_0002", "MER-CP-88102", "Tarn End Storage Ltd", "COMMERCIAL_PROPERTY",
     "2026-06-04", "2027-06-03", 24150.50, 4226.34, "GB", "CA1 2RS"),
    ("mm_0003", "MER-MT-88103", "Wrekin Couriers Ltd", "MOTOR",
     "2026-06-09", "2027-06-08", 11020.00, 1928.50, "GB", None),
    ("mm_0004", "MER-GL-88104", "Brandon Hill Events Ltd", "GENERAL_LIABILITY",
     "2026-06-15", "2027-06-14", 5330.00, 932.75, "GB", "BS8 1TH"),
    ("mm_0005", "MER-MC-88105", "Solent Chandlery Ltd", "MARINE_CARGO",
     "2026-06-21", "2027-06-20", 9640.00, 1687.00, "GB", "SO14 2AQ"),
    ("mm_0006", "MER-CP-88106", "Ferrous & Co Fabrication", "COMMERCIAL_PROPERTY",
     "2026-06-27", "2027-06-26", 31210.00, 5461.75, "GB", "S9 1XU"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--warehouse-id")
    ap.add_argument("--skip-deploy", action="store_true",
                    help="Estate already deployed; only reseed and exchange")
    args = ap.parse_args()

    binding = yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())
    cat = binding["catalog"]
    ours = f"{cat}.{binding['schema_pattern'].format(domain='exchange')}.premium_bordereau_line"
    theirs = f"{cat}.meridian_exchange.premium_bordereau_line"

    if not args.skip_deploy:
        # 1. adopt: import the ontology into a fresh repo layout
        if STAGE.exists():
            shutil.rmtree(STAGE)
        subprocess.run([sys.executable, str(ROOT / "tools" / "import_ontology.py"),
                        "--input", str(ROOT / "build" / "ontology" /
                                       "bricksurance-data-core.ontology.json"),
                        "--target", str(STAGE)], check=True)
        (STAGE / "bindings").mkdir()
        (STAGE / "bindings" / "databricks.yaml").write_text(
            "# Meridian Mutual Insurance — a second adopter of the same ontology.\n"
            f"platform: databricks\ncatalog: {cat}\n"
            'schema_pattern: "meridian_{domain}"\ntag_prefix: "mm_"\n')
        (STAGE / "tools").mkdir()
        for tool in ("generate.py", "deploy_databricks.py"):
            shutil.copy(ROOT / "tools" / tool, STAGE / "tools" / tool)
        # 2. generate + deploy THEIR estate from THEIR tree
        subprocess.run([sys.executable, str(STAGE / "tools" / "generate.py")], check=True)
        deploy = [sys.executable, str(STAGE / "tools" / "deploy_databricks.py"),
                  "--profile", args.profile]
        if args.warehouse_id:
            deploy += ["--warehouse-id", args.warehouse_id]
        subprocess.run(deploy, check=True)

    w = WorkspaceClient(profile=args.profile)
    wid = args.warehouse_id or pick_warehouse(w).id

    # 3. Meridian's own canonical bordereau (their book, their export)
    rows = ",\n".join(
        f"  ('{i}', DATE '2026-06-01', 'Meridian Mutual Insurance', '{pol}', '{ins}', "
        f"'{lob}', DATE '{inc}', DATE '{exp}', 'GBP', {gross}, {comm}, "
        f"{'NULL' if cc is None else repr(cc)}, {'NULL' if pc is None else repr(pc)}, "
        f"'COVERHOLDER_BDX')"
        for i, pol, ins, lob, inc, exp, gross, comm, cc, pc in MERIDIAN_BDX)
    run_sql(w, wid, f"INSERT OVERWRITE {theirs} (bordereau_line_id, reporting_month, "
                    f"coverholder_name, policy_number, insured_name, line_of_business_code, "
                    f"inception_date, expiry_date, currency_code, gross_premium, "
                    f"commission_amount, risk_country_code, risk_postcode, "
                    f"source_system_code) VALUES\n{rows}")

    # 4. THE EXCHANGE: column-aligned copy — no mapping, because same ontology
    run_sql(w, wid, f"DELETE FROM {ours} WHERE bordereau_line_id LIKE 'mm\\\\_%'")
    run_sql(w, wid, f"INSERT INTO {ours} SELECT * FROM {theirs}")

    got = run_sql(w, wid, f"SELECT COUNT(*), CAST(SUM(gross_premium) AS DECIMAL(18,2)) "
                          f"FROM {ours} WHERE bordereau_line_id LIKE 'mm\\\\_%'")
    sent = run_sql(w, wid, f"SELECT COUNT(*), CAST(SUM(gross_premium) AS DECIMAL(18,2)) "
                           f"FROM {theirs}")
    assert got == sent, f"exchange mismatch: sent {sent}, received {got}"
    print(f"\nMeridian -> Bricksurance: {got[0][0]} lines, gross {got[0][1]} — "
          f"column-aligned copy, zero mapping. Same ontology, same meaning.")
    print("Contrast: the Atlas coverholder CSV needed LLM mapping against the dictionary.")


if __name__ == "__main__":
    main()
