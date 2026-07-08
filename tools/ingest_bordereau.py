#!/usr/bin/env python3
"""Ingest a messy inbound bordereau into the canonical model — no middleware.

Takes a coverholder's spreadsheet-shaped CSV as it actually arrives (title
rows, DD/MM/YYYY dates, thousands separators, home-grown class names) and maps
it into exchange.premium_bordereau_line using an LLM (Claude on the Databricks
Foundation Model API) with the generated DATA DICTIONARY as the contract:
the model is prompted with each target attribute's business definition and
the allowed code values, returns conforming records, and the tool validates
every record against the contract before loading a single row.

Usage:
    uv run --with databricks-sdk,pyyaml tools/ingest_bordereau.py \
        --file data/inbound/atlas_bordereau_2026-06.csv \
        [--profile DEFAULT] [--endpoint databricks-claude-sonnet-5]
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy_databricks import pick_warehouse  # noqa: E402
from smoke_test import run_sql  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TARGET_ENTITY = "premium_bordereau_line"
CODE_SET_COLUMNS = {"line_of_business_code": "line_of_business",
                    "currency_code": "currency",
                    "risk_country_code": "country",
                    "source_system_code": "source_system"}


def build_contract(w, wid, q):
    """The target contract = data dictionary rows + allowed code values."""
    dictionary = run_sql(
        w, wid,
        f"SELECT attribute_name, data_type, is_required, definition "
        f"FROM {q('reference', 'data_dictionary')} "
        f"WHERE entity_name = '{TARGET_ENTITY}' ORDER BY attribute_name")
    codes = {}
    for col, code_set in CODE_SET_COLUMNS.items():
        rows = run_sql(w, wid,
                       f"SELECT {code_set}_code, label FROM {q('reference', code_set)}")
        codes[col] = {r[0]: r[1] for r in rows}
    return dictionary, codes


def ask_claude(w, endpoint, prompt):
    resp = w.api_client.do(
        "POST", f"/serving-endpoints/{endpoint}/invocations",
        body={"messages": [{"role": "user", "content": prompt}],
              "max_tokens": 8000})
    text = resp["choices"][0]["message"]["content"]
    if isinstance(text, list):  # newer models return content blocks
        text = "".join(b.get("text", "") for b in text if b.get("type") == "text")
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        sys.exit(f"Model did not return JSON:\n{text}")
    return json.loads(match.group(0))


def validate(records, dictionary, codes):
    """Every record must conform to the dictionary contract."""
    spec = {r[0]: {"type": r[1], "required": r[2] in (True, "true")} for r in dictionary}
    errors = []
    for i, rec in enumerate(records):
        for attr, meta in spec.items():
            v = rec.get(attr)
            if v in (None, ""):
                if meta["required"]:
                    errors.append(f"row {i + 1}: required {attr} missing")
                continue
            if attr in codes and str(v) not in codes[attr]:
                errors.append(f"row {i + 1}: {attr}={v!r} not an allowed code")
            if meta["type"] == "date":
                try:
                    date.fromisoformat(str(v))
                except ValueError:
                    errors.append(f"row {i + 1}: {attr}={v!r} is not an ISO date")
            if meta["type"].startswith("decimal"):
                try:
                    float(v)
                except (TypeError, ValueError):
                    errors.append(f"row {i + 1}: {attr}={v!r} is not numeric")
        unknown = set(rec) - set(spec)
        if unknown:
            errors.append(f"row {i + 1}: unknown attributes {sorted(unknown)}")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--warehouse-id")
    ap.add_argument("--endpoint", default="databricks-claude-sonnet-5")
    args = ap.parse_args()

    binding = yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())

    def q(domain, name):
        return f"{binding['catalog']}.{binding['schema_pattern'].format(domain=domain)}.{name}"

    w = WorkspaceClient(profile=args.profile)
    wid = args.warehouse_id or pick_warehouse(w).id
    raw = Path(args.file).read_text()

    print("1/4 Building the contract from the data dictionary...")
    dictionary, codes = build_contract(w, wid, q)

    contract_lines = [f"- {r[0]} ({r[1]}{', REQUIRED' if r[2] in (True, 'true') else ''}): {r[3]}"
                      for r in dictionary]
    code_lines = [f"- {col}: " + "; ".join(f"{c} = {label}" for c, label in cs.items())
                  for col, cs in codes.items()]
    prompt = f"""You map inbound insurance bordereau files to a canonical data model.

TARGET CONTRACT — every output record must have exactly these attributes
(entity {TARGET_ENTITY}; definitions from the model's data dictionary):
{chr(10).join(contract_lines)}

ALLOWED CODE VALUES (map the file's own wording to the closest code):
{chr(10).join(code_lines)}

RULES:
- Dates as ISO YYYY-MM-DD (the file may use DD/MM/YYYY).
- Amounts as plain numbers, no thousands separators.
- commission_amount is an amount: if the file reports a commission percentage,
  compute gross_premium * percentage / 100, rounded to 2 decimals.
- reporting_month is the first day of the month the bordereau covers.
- bordereau_line_id: use bdx_atlas_202606_NNN with NNN as the line number.
- source_system_code is always COVERHOLDER_BDX.
- Skip title, blank and total rows; map only real bordereau lines.
- If a value is genuinely absent, use null. Invent nothing.

FILE (verbatim):
{raw}

Return ONLY JSON: {{"mapping_notes": {{"<file column>": "<target attribute and any transform>"}}, "records": [{{...}}]}}"""

    print(f"2/4 Asking {args.endpoint} to map the file against the contract...")
    result = ask_claude(w, args.endpoint, prompt)
    records = result["records"]
    print("    Mapping proposed by the model:")
    for src, tgt in result.get("mapping_notes", {}).items():
        print(f"      {src!r:28s} -> {tgt}")

    print(f"3/4 Validating {len(records)} records against the dictionary contract...")
    errors = validate(records, dictionary, codes)
    if errors:
        sys.exit("VALIDATION FAILED:\n  " + "\n  ".join(errors))
    print("    All records conform.")

    print("4/4 Loading into the canonical model...")
    entity = yaml.safe_load((ROOT / "model" / "exchange" / f"{TARGET_ENTITY}.yaml").read_text())
    cols = [a["name"] for a in entity["attributes"]]

    def lit(v):
        if v is None:
            return "NULL"
        if isinstance(v, (int, float)):
            return str(v)
        return "'" + str(v).replace("'", "''") + "'"

    values = ",\n".join("  (" + ", ".join(lit(r.get(c)) for c in cols) + ")" for r in records)
    run_sql(w, wid, f"INSERT OVERWRITE {q('exchange', TARGET_ENTITY)} "
                    f"({', '.join(cols)}) VALUES\n{values}")
    total = run_sql(w, wid, f"SELECT COUNT(*), SUM(gross_premium) FROM {q('exchange', TARGET_ENTITY)}")
    print(f"    Loaded {total[0][0]} lines, gross premium {total[0][1]}.")


if __name__ == "__main__":
    main()
