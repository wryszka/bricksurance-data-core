"""Bordereau ingest, reusing the tools/ingest_bordereau.py logic.

Contract (from the data dictionary) -> Claude mapping -> validation -> load.
The Console splits the tool's one-shot pipeline into two API steps: map (no
load) and load, so a person can review the mapping before anything is written.
"""

import json
import re
from datetime import date

from .db import q, run_sql, client, SERVING_ENDPOINT

TARGET_ENTITY = "premium_bordereau_line"
CODE_SET_COLUMNS = {
    "line_of_business_code": "line_of_business",
    "currency_code": "currency",
    "risk_country_code": "country",
    "source_system_code": "source_system",
}


def build_contract():
    """The target contract = data dictionary rows + allowed code values."""
    dictionary = run_sql(
        f"SELECT attribute_name, data_type, is_required, definition "
        f"FROM {q('reference', 'data_dictionary')} "
        f"WHERE entity_name = '{TARGET_ENTITY}' ORDER BY attribute_name")
    codes = {}
    for col, code_set in CODE_SET_COLUMNS.items():
        rows = run_sql(
            f"SELECT {code_set}_code, label FROM {q('reference', code_set)}")
        codes[col] = {r[0]: r[1] for r in rows}
    return dictionary, codes


def _ask_claude(prompt: str):
    w = client()
    resp = w.api_client.do(
        "POST", f"/serving-endpoints/{SERVING_ENDPOINT}/invocations",
        body={"messages": [{"role": "user", "content": prompt}],
              "max_tokens": 8000})
    text = resp["choices"][0]["message"]["content"]
    if isinstance(text, list):  # newer models return content blocks
        text = "".join(b.get("text", "") for b in text if b.get("type") == "text")
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise RuntimeError(f"Model did not return JSON:\n{text}")
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


def _build_prompt(raw, dictionary, codes):
    contract_lines = [
        f"- {r[0]} ({r[1]}{', REQUIRED' if r[2] in (True, 'true') else ''}): {r[3]}"
        for r in dictionary]
    code_lines = [f"- {col}: " + "; ".join(f"{c} = {label}" for c, label in cs.items())
                  for col, cs in codes.items()]
    return f"""You map inbound insurance bordereau files to a canonical data model.

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


def map_file(raw: str):
    """Map + validate a raw bordereau file. Does NOT load."""
    dictionary, codes = build_contract()
    result = _ask_claude(_build_prompt(raw, dictionary, codes))
    records = result.get("records", [])
    errors = validate(records, dictionary, codes)
    return {
        "mapping_notes": result.get("mapping_notes", {}),
        "records": records,
        "errors": errors,
        "valid": len(errors) == 0,
        "contract": [
            {"attribute": r[0], "type": r[1], "required": r[2] in (True, "true", "True"),
             "definition": r[3]}
            for r in dictionary],
    }


def load_records(records):
    """Validate again, then INSERT OVERWRITE the canonical target (same as the tool)."""
    dictionary, codes = build_contract()
    errors = validate(records, dictionary, codes)
    if errors:
        raise ValueError("Validation failed: " + "; ".join(errors))
    cols = [r[0] for r in dictionary]

    def lit(v):
        if v is None:
            return "NULL"
        if isinstance(v, (int, float)):
            return str(v)
        return "'" + str(v).replace("'", "''") + "'"

    values = ",\n".join(
        "  (" + ", ".join(lit(r.get(c)) for c in cols) + ")" for r in records)
    run_sql(f"INSERT OVERWRITE {q('exchange', TARGET_ENTITY)} "
            f"({', '.join(cols)}) VALUES\n{values}")
    total = run_sql(
        f"SELECT COUNT(*), CAST(SUM(gross_premium) AS DECIMAL(18,2)) "
        f"FROM {q('exchange', TARGET_ENTITY)}")
    return {"row_count": int(total[0][0]),
            "gross_premium_total": float(total[0][1]) if total[0][1] is not None else 0.0}
