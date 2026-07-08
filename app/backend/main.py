"""Bricksurance Data Core Console — FastAPI backend.

Serves a governance-and-exchange console over the deployed semantic model.
Everything shown is read live from the model on Databricks: the data
dictionary, the metric view, the outbound bordereau view, and the Delta Share.
"""

import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db import q, run_sql, client, CATALOG, SCHEMA_PATTERN
from . import ingest

APP_DIR = Path(__file__).resolve().parent.parent
FRONTEND = APP_DIR / "frontend" / "dist"
SAMPLE_FILE = APP_DIR / "data" / "inbound" / "atlas_bordereau_2026-06.csv"

GENIE_SPACE_URL = os.environ.get(
    "GENIE_SPACE_URL",
    "https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17ade46ec18bc8da2cb30b55a26a6")
MODEL_REPO_URL = os.environ.get(
    "MODEL_REPO_URL", "https://github.com/wryszka/bricksurance-data-core/tree/main/model")
SHARE_NAME = os.environ.get("EXCHANGE_SHARE_NAME", "bricksurance_re_exchange")

app = FastAPI(title="Bricksurance Data Core Console")


def as_bool(v) -> bool:
    # The SQL Statement Execution API returns every value as a string, so a
    # BOOLEAN column arrives as "true"/"false" — bool() on that is always True.
    return v in (True, "true", "True")


# --------------------------------------------------------------------------- #
# Tab 1 — Model (governance browser)
# --------------------------------------------------------------------------- #

# Which domain each entity is grouped under is intrinsic to the physical schema
# it lives in, so we derive it from the schema name — no hardcoded map.
DOMAIN_ORDER = ["reference", "party", "policy", "claim",
                "reinsurance", "exchange", "semantics"]
DOMAIN_TITLES = {
    "reference": "Reference", "party": "Party", "policy": "Policy",
    "claim": "Claim", "reinsurance": "Reinsurance", "exchange": "Exchange",
    "semantics": "Semantics",
}


@app.get("/api/model")
def get_model():
    prefix = SCHEMA_PATTERN.format(domain="")
    tables = run_sql(
        f"SELECT table_schema, table_name, table_type, comment "
        f"FROM {CATALOG}.information_schema.tables "
        f"WHERE table_schema LIKE '{prefix}%' ORDER BY table_schema, table_name")
    dictionary = run_sql(
        f"SELECT entity_name, attribute_name, data_type, is_required, definition, "
        f"data_classification, acord_ref, lloyds_cdr_ref "
        f"FROM {q('reference', 'data_dictionary')} "
        f"ORDER BY entity_name, attribute_name")

    attrs_by_entity: dict[str, list] = {}
    for e, a, dt, req, defn, cls, acord, cdr in dictionary:
        attrs_by_entity.setdefault(e, []).append({
            "attribute": a, "type": dt, "required": as_bool(req), "definition": defn,
            "classification": cls, "acord_ref": acord, "lloyds_cdr_ref": cdr})

    domains: dict[str, dict] = {}
    for schema, name, ttype, comment in tables:
        domain = schema[len(prefix):] if schema.startswith(prefix) else schema
        domains.setdefault(domain, {
            "domain": domain,
            "title": DOMAIN_TITLES.get(domain, domain.title()),
            "schema": schema,
            "entities": [],
        })
        domains[domain]["entities"].append({
            "name": name,
            "type": ttype,
            "comment": comment or "",
            "attributes": attrs_by_entity.get(name, []),
        })

    ordered = [domains[d] for d in DOMAIN_ORDER if d in domains]
    ordered += [v for k, v in domains.items() if k not in DOMAIN_ORDER]
    return {"domains": ordered, "model_repo_url": MODEL_REPO_URL}


# --------------------------------------------------------------------------- #
# Tab 2 — Numbers (semantics in action)
# --------------------------------------------------------------------------- #

@app.get("/api/metrics")
def get_metrics(currency: str = "GBP", underwriting_year: int | None = None):
    mv = q("semantics", "underwriting_metrics")
    cur = currency.replace("'", "")
    where = f"WHERE currency_code = '{cur}'"
    if underwriting_year:
        where += f" AND underwriting_year = {int(underwriting_year)}"

    kpis = run_sql(
        f"SELECT CAST(MEASURE(gross_written_premium) AS DECIMAL(18,2)), "
        f"CAST(MEASURE(claims_incurred) AS DECIMAL(18,2)), "
        f"CAST(MEASURE(outstanding_reserve) AS DECIMAL(18,2)), "
        f"CAST(MEASURE(loss_ratio) AS DECIMAL(10,4)), "
        f"MEASURE(policy_count), MEASURE(claim_count) FROM {mv} {where}")
    row = kpis[0] if kpis else [None] * 6

    def num(v):
        return float(v) if v is not None else 0.0

    by_lob = run_sql(
        f"SELECT line_of_business, CAST(MEASURE(gross_written_premium) AS DECIMAL(18,2)), "
        f"CAST(MEASURE(claims_incurred) AS DECIMAL(18,2)) FROM {mv} {where} "
        f"GROUP BY line_of_business ORDER BY 2 DESC")

    defs = {r[0]: r[1] for r in run_sql(
        f"SELECT attribute_name, definition FROM {q('reference', 'data_dictionary')} "
        f"WHERE entity_name = 'underwriting_metrics'")}

    currencies = [r[0] for r in run_sql(
        f"SELECT DISTINCT currency_code FROM {mv} ORDER BY 1")]
    years = [int(r[0]) for r in run_sql(
        f"SELECT DISTINCT underwriting_year FROM {mv} ORDER BY 1 DESC")]

    return {
        "currency": cur,
        "underwriting_year": underwriting_year,
        "currencies": currencies,
        "years": years,
        "kpis": {
            "gross_written_premium": num(row[0]),
            "claims_incurred": num(row[1]),
            "outstanding_reserve": num(row[2]),
            "loss_ratio": num(row[3]),
            "policy_count": int(num(row[4])),
            "claim_count": int(num(row[5])),
        },
        "definitions": defs,
        "by_line_of_business": [
            {"line_of_business": r[0], "gross_written_premium": num(r[1]),
             "claims_incurred": num(r[2])} for r in by_lob],
        "genie_space_url": GENIE_SPACE_URL,
    }


# --------------------------------------------------------------------------- #
# Tab 3 — Exchange
# --------------------------------------------------------------------------- #

# The columns that travel on the outbound cession bordereau view.
CESSION_COLUMNS = [
    "treaty_reference", "reporting_month", "policy_number", "insured_name",
    "line_of_business_code", "inception_date", "expiry_date", "currency_code",
    "gross_premium", "ceded_share", "ceded_premium",
]
# Objects carried by the Delta Share (mirrors tools/create_share.py).
SHARE_OBJECTS = [
    ("exchange", "cession_bordereau_line", "VIEW"),
    ("reference", "data_dictionary", "TABLE"),
    ("reference", "line_of_business", "TABLE"),
    ("reference", "currency", "TABLE"),
]


@app.get("/api/exchange/outbound")
def exchange_outbound():
    rows = run_sql(
        f"SELECT {', '.join(CESSION_COLUMNS)} FROM {q('exchange', 'cession_bordereau_line')} "
        f"ORDER BY reporting_month, policy_number")
    records = [dict(zip(CESSION_COLUMNS, [str(v) if v is not None else None for v in r]))
               for r in rows]

    # "What travels": dictionary definitions for the shared columns.
    quoted = ", ".join(f"'{c}'" for c in CESSION_COLUMNS)
    dict_rows = run_sql(
        f"SELECT DISTINCT attribute_name, data_type, definition, data_classification "
        f"FROM {q('reference', 'data_dictionary')} WHERE attribute_name IN ({quoted})")
    by_attr = {r[0]: {"attribute": r[0], "type": r[1], "definition": r[2],
                      "classification": r[3]} for r in dict_rows}
    travels = [by_attr.get(c, {"attribute": c, "type": "", "definition":
               "Derived on the view (e.g. computed ceded amount).", "classification": None})
               for c in CESSION_COLUMNS]

    return {
        "columns": CESSION_COLUMNS,
        "rows": records,
        "travels": travels,
        "share_objects": [
            {"schema": SCHEMA_PATTERN.format(domain=d), "name": n, "type": t}
            for d, n, t in SHARE_OBJECTS],
        "share_name": SHARE_NAME,
    }


@app.get("/api/exchange/sample")
def exchange_sample():
    if not SAMPLE_FILE.exists():
        raise HTTPException(404, "Sample file not bundled.")
    return {"filename": SAMPLE_FILE.name, "content": SAMPLE_FILE.read_text()}


@app.post("/api/exchange/map")
async def exchange_map(file: UploadFile | None = File(None),
                       content: str | None = Form(None)):
    if file is not None:
        raw = (await file.read()).decode("utf-8", errors="replace")
    elif content:
        raw = content
    else:
        raise HTTPException(400, "Provide a CSV file or content.")
    try:
        return ingest.map_file(raw)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Mapping failed: {e}")


class LoadRequest(BaseModel):
    records: list[dict]


@app.post("/api/exchange/load")
def exchange_load(payload: LoadRequest):
    try:
        return ingest.load_records(payload.records)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Load failed: {e}")


# --------------------------------------------------------------------------- #
# Tab 4 — Network (federation picture)
# --------------------------------------------------------------------------- #

@app.get("/api/network")
def network():
    share_live = False
    detail = ""
    try:
        client().api_client.do(
            "GET", f"/api/2.1/unity-catalog/shares/{SHARE_NAME}")
        share_live = True
        detail = "share live"
    except Exception as e:  # noqa: BLE001
        detail = "pending"
        share_live = False

    return {
        "share_name": SHARE_NAME,
        "share_live": share_live,
        "share_detail": detail,
        "nodes": [
            {"id": "se", "label": "Bricksurance SE", "sub": "Retail — Databricks (serverless)",
             "platform": "Databricks", "status": "live"},
            {"id": "share", "label": f"Delta Share “{SHARE_NAME}”",
             "sub": "cession bordereau + data dictionary + code sets",
             "platform": "Delta Sharing", "status": "live" if share_live else "pending"},
            {"id": "re", "label": "Bricksurance Re", "sub": "Reinsurer — Databricks (dev workspace)",
             "platform": "Databricks", "status": "live" if share_live else "pending"},
            {"id": "specialty", "label": "Bricksurance Specialty", "sub": "Acquired specialty unit",
             "platform": "Snowflake", "status": "planned"},
            {"id": "centre", "label": "Group Centre", "sub": "Consolidated group reporting",
             "platform": "BigQuery", "status": "planned"},
        ],
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
# Static frontend
# --------------------------------------------------------------------------- #

if (FRONTEND / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")


@app.get("/")
def index():
    idx = FRONTEND / "index.html"
    if idx.exists():
        return FileResponse(idx)
    return JSONResponse({"status": "frontend not built"}, status_code=200)


@app.get("/{full_path:path}")
def spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(404, "Not found")
    candidate = FRONTEND / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    idx = FRONTEND / "index.html"
    if idx.exists():
        return FileResponse(idx)
    raise HTTPException(404, "Not found")
