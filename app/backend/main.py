"""Bricksurance Data Core Atlas — FastAPI backend.

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

app = FastAPI(title="Bricksurance Data Core Atlas")


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
        f"CAST(MEASURE(loss_ratio_written) AS DECIMAL(10,4)), "
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


# --------------------------------------------------------------------------- #
# Atlas — search, detail, lineage, governance (served from the bundled ontology)
# --------------------------------------------------------------------------- #
from . import atlas  # noqa: E402

# A pre-filled Genie question per metric, so "Ask in Genie" lands on a real,
# reconciling question rather than an empty box.
GENIE_QUESTIONS = {
    "underwriting_metrics": "What is our gross written premium and written-basis loss ratio by line of business for underwriting year 2026 in GBP?",
    "performance_metrics": "What is our loss ratio, expense ratio and combined ratio by line of business in GBP?",
    "cession_metrics": "What gross and ceded premium did we cede by treaty this year?",
    "valuation_metrics": "What is our SCR and best-estimate liability by line of business at the latest valuation?",
    "trial_balance": "Does the trial balance net to zero by legal entity for the current period?",
    "financial_position": "What is our balance-sheet position by statement line for the group?",
    "submission_metrics": "How many reinsurance submissions are in each status?",
    "investment_metrics": "What is the market value of our investment holdings by asset class?",
}


@app.get("/api/atlas/meta")
def atlas_meta():
    m = atlas.meta()
    m["provenance"] = {"version": m["version"], "source": "bundled ontology export"}
    return m


@app.get("/api/atlas/search")
def atlas_search(q: str = "", limit: int = 30):
    return atlas.search(q, limit=limit)


@app.get("/api/atlas/entity/{name}")
def atlas_entity(name: str):
    d = atlas.entity_detail(name)
    if not d:
        raise HTTPException(404, f"No entity '{name}'")
    return d


@app.get("/api/atlas/metric/{name}")
def atlas_metric(name: str):
    d = atlas.metric_detail(name)
    if not d:
        raise HTTPException(404, f"No metric '{name}'")
    d["genie_question"] = GENIE_QUESTIONS.get(name)
    d["genie_space_url"] = GENIE_SPACE_URL
    return d


@app.get("/api/atlas/code_set/{name}")
def atlas_code_set(name: str):
    d = atlas.code_set_detail(name)
    if not d:
        raise HTTPException(404, f"No code set '{name}'")
    return d


@app.get("/api/atlas/function/{name}")
def atlas_function(name: str):
    d = atlas.function_detail(name)
    if not d:
        raise HTTPException(404, f"No function '{name}'")
    return d


@app.get("/api/atlas/lineage/{kind}/{name}")
def atlas_lineage(kind: str, name: str, depth: int = 1):
    return atlas.lineage(kind, name, depth=depth)


@app.get("/api/atlas/golden-thread")
def atlas_golden_thread():
    return atlas.golden_thread()


@app.get("/api/atlas/governance")
def atlas_governance():
    return atlas.governance()


@app.get("/api/atlas/regulatory/{regime}")
def atlas_regulatory(regime: str):
    d = atlas.regulatory(regime)
    if not d:
        raise HTTPException(404, f"No regime '{regime}'")
    return d


@app.get("/api/atlas/prove/{name}")
def atlas_prove(name: str):
    """Prove a metric live: run its MEASURE() against the warehouse and, where
    we can, show the bare-tables view of the same question so the semantic
    layer's value is visible. Degrades gracefully if the warehouse is cold."""
    d = atlas.metric_detail(name)
    if not d:
        raise HTTPException(404, f"No metric '{name}'")
    mv = q("semantics", name)
    measures = [m["name"] for m in d["measures"]][:4]
    result = {"metric": name, "ok": False, "measures": [], "error": None,
              "sql": None, "genie_question": GENIE_QUESTIONS.get(name),
              "genie_space_url": GENIE_SPACE_URL}
    select = ", ".join(f"CAST(MEASURE({m}) AS DECIMAL(18,4))" for m in measures)
    sql = f"SELECT {select} FROM {mv}"
    result["sql"] = sql
    try:
        rows = run_sql(sql)
        vals = rows[0] if rows else [None] * len(measures)
        result["ok"] = True
        result["measures"] = [
            {"name": measures[i],
             "value": float(vals[i]) if vals[i] is not None else None,
             "formula": next((m["expr"] for m in d["measures"] if m["name"] == measures[i]), None)}
            for i in range(len(measures))]
    except Exception as e:  # noqa: BLE001
        result["error"] = str(e)
    return result


# --------------------------------------------------------------------------- #
# Governance record layer — capture-only (proposals + issue flags)
# --------------------------------------------------------------------------- #
from . import governance_store  # noqa: E402


class ProposalRequest(BaseModel):
    element: str
    element_kind: str = "entity"
    field: str
    proposed_value: str
    rationale: str = ""
    raised_by: str = "steward"
    current_value: str = ""


class IssueRequest(BaseModel):
    element: str
    element_kind: str = "entity"
    rationale: str
    raised_by: str = "steward"


@app.get("/api/atlas/governance/actions")
def governance_actions():
    try:
        return {"actions": governance_store.list_actions()}
    except Exception as e:  # noqa: BLE001
        return {"actions": [], "error": str(e)}


@app.post("/api/atlas/governance/propose")
def governance_propose(p: ProposalRequest):
    try:
        return governance_store.propose(
            p.element, p.element_kind, p.field, p.proposed_value,
            p.rationale, p.raised_by, p.current_value)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Could not capture proposal: {e}")


@app.post("/api/atlas/governance/issue")
def governance_issue(p: IssueRequest):
    try:
        return governance_store.raise_issue(
            p.element, p.element_kind, p.rationale, p.raised_by)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Could not capture issue: {e}")


# --------------------------------------------------------------------------- #
# Reserving workbench — the living loss-development triangle over the layer
# --------------------------------------------------------------------------- #
RESERVING_LOBS = ["COMMERCIAL_PROPERTY", "MOTOR", "GENERAL_LIABILITY", "MARINE_CARGO"]
RESERVING_GENIE = (
    "https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/"
    "01f1878ac9df10aaa7ca6e31873f47ea")


def _num(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


@app.get("/api/atlas/reserving")
def atlas_reserving(line_of_business: str = "COMMERCIAL_PROPERTY",
                    currency: str = "GBP", method: str = "CHAIN_LADDER"):
    """The reserving workbench: the governed loss-development triangle, the
    chain-ladder / BF reserve estimates, and the penny-perfect reconciliation
    to the claims ledger. Everything derived live from the semantic layer."""
    lob = line_of_business if line_of_business in RESERVING_LOBS else "COMMERCIAL_PROPERTY"
    cur = currency.replace("'", "")[:3] or "GBP"
    meth = method if method in ("CHAIN_LADDER", "BORNHUETTER_FERGUSON") else "CHAIN_LADDER"
    dev = q("reserving", "loss_development")
    est = q("reserving", "reserve_estimate")

    # the triangle (cumulative paid + incurred by accident year x development lag)
    tri = run_sql(
        f"SELECT accident_year, development_lag, "
        f"CAST(cumulative_paid AS DECIMAL(18,2)), CAST(cumulative_incurred AS DECIMAL(18,2)) "
        f"FROM {dev} WHERE line_of_business_code = '{lob}' AND currency_code = '{cur}' "
        f"ORDER BY accident_year, development_lag")
    cells = [{"accident_year": int(r[0]), "development_lag": int(r[1]),
              "cumulative_paid": _num(r[2]), "cumulative_incurred": _num(r[3])}
             for r in tri]
    years = sorted({c["accident_year"] for c in cells})
    max_lag = max((c["development_lag"] for c in cells), default=0)
    # the latest observed diagonal per accident year = the actual/projected frontier
    latest_lag = {}
    for c in cells:
        ay = c["accident_year"]
        latest_lag[ay] = max(latest_lag.get(ay, -1), c["development_lag"])

    # published reserve estimates for the chosen method
    est_rows = run_sql(
        f"SELECT accident_year, CAST(paid_to_date AS DECIMAL(18,2)), "
        f"CAST(case_reserves AS DECIMAL(18,2)), CAST(ultimate_loss AS DECIMAL(18,2)), "
        f"CAST(ibnr AS DECIMAL(18,2)), CAST(outstanding AS DECIMAL(18,2)) "
        f"FROM {est} WHERE line_of_business_code = '{lob}' AND currency_code = '{cur}' "
        f"AND reserving_method_code = '{meth}' ORDER BY accident_year")
    estimates = [{"accident_year": int(r[0]), "paid_to_date": _num(r[1]),
                  "case_reserves": _num(r[2]), "ultimate_loss": _num(r[3]),
                  "ibnr": _num(r[4]), "outstanding": _num(r[5])} for r in est_rows]

    def total(k):
        return round(sum(e[k] or 0 for e in estimates), 2)

    # which methods are actually available for this LOB
    methods = [r[0] for r in run_sql(
        f"SELECT DISTINCT reserving_method_code FROM {est} "
        f"WHERE line_of_business_code = '{lob}' AND currency_code = '{cur}'")]

    # the money shot: triangle paid must equal the claims ledger paid
    recon = run_sql(
        f"SELECT CAST((SELECT SUM(incremental_paid) FROM {dev} "
        f"WHERE line_of_business_code = '{lob}' AND currency_code = '{cur}') AS DECIMAL(18,2)), "
        f"CAST((SELECT SUM(amount) FROM {q('claim','claim_transaction')} ct "
        f"JOIN {q('claim','claim')} c ON c.claim_id = ct.claim_id "
        f"JOIN {q('policy','policy')} p ON p.policy_id = c.policy_id "
        f"WHERE p.line_of_business_code = '{lob}' AND ct.currency_code = '{cur}' "
        f"AND ct.claim_transaction_type_code IN "
        f"('INDEMNITY_PAYMENT','EXPENSE_PAYMENT','RECOVERY')) AS DECIMAL(18,2))")
    tri_paid, ledger_paid = (_num(recon[0][0]), _num(recon[0][1])) if recon else (None, None)

    return {
        "line_of_business": lob,
        "currency": cur,
        "method": meth,
        "methods_available": methods,
        "lines_available": RESERVING_LOBS,
        "accident_years": years,
        "max_lag": max_lag,
        "latest_lag": latest_lag,
        "triangle": cells,
        "estimates": estimates,
        "reserve_walk": {
            "paid_to_date": total("paid_to_date"),
            "case_reserves": total("case_reserves"),
            "ibnr": total("ibnr"),
            "ultimate_loss": total("ultimate_loss"),
            "outstanding": total("outstanding"),
        },
        "reconciliation": {
            "triangle_paid": tri_paid, "ledger_paid": ledger_paid,
            "reconciles": (tri_paid is not None and ledger_paid is not None
                           and abs(tri_paid - ledger_paid) < 0.01),
        },
        "genie_url": RESERVING_GENIE,
        "genie_question": (
            f"What is the total IBNR across accident years for "
            f"{lob.replace('_',' ').title()} in {cur}, chain-ladder basis?"),
        "provenance": "reserving.loss_development · reserving.reserve_estimate (v0.9.0)",
    }


# --------------------------------------------------------------------------- #
# Underwriting workbench — one decision, three scopes (submission/team/enterprise)
# The through-line: the SAME agentic underwriting decision that Anthropic would
# do in a spreadsheet becomes a governed fact, then the team's portfolio, then
# the enterprise's numbers — because it lives on the layer, not in a file.
# --------------------------------------------------------------------------- #
UNDERWRITING_GENIE = (
    "https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/"
    "01f17ec37dd71693a552cac8383e1651")  # Distribution, Underwriting & Conduct


@app.get("/api/atlas/underwriting")
def atlas_underwriting(currency: str = "GBP"):
    """The underwriting workbench across three scopes. Submission: the agentic
    machine-buyer decisions (accept/decline/refer). Team: the portfolio roll-up
    of every decision. Enterprise: the same written premium flowing live to the
    finance close, reinsurance and reserving — reconciling, never re-keyed."""
    cur = currency.replace("'", "")[:3] or "GBP"

    # ---- SCOPE 1: submission — the agentic buyer thread (accept / decline / refer)
    subs = run_sql(
        f"SELECT q.quote_number, q.line_of_business_code, "
        f"CAST(q.quoted_gross_premium AS DECIMAL(18,2)), q.quote_status_code, "
        f"ud.underwriting_decision_type_code, ud.decided_by_agent, ud.decided_by, "
        f"ud.rationale FROM {q('policy','quote')} q "
        f"JOIN {q('policy','underwriting_decision')} ud ON ud.quote_id = q.quote_id "
        f"WHERE q.distribution_channel_code = 'MACHINE_AGENT' ORDER BY q.quote_number")
    submissions = [{
        "quote_number": r[0], "line_of_business": (r[1] or "").replace("_", " ").title(),
        "quoted_premium": _num(r[2]), "quote_status": r[3],
        "decision": r[4], "by_agent": as_bool(r[5]), "decided_by": r[6],
        "rationale": r[7]} for r in subs]

    # ---- SCOPE 2: team — the portfolio roll-up of all decisions
    dec = run_sql(
        f"SELECT underwriting_decision_type_code, decided_by_agent, COUNT(*) "
        f"FROM {q('policy','underwriting_decision')} "
        f"GROUP BY 1, 2 ORDER BY 1, 2")
    decisions = [{"decision": r[0], "by_agent": as_bool(r[1]), "count": int(r[2])}
                 for r in dec]
    total_dec = sum(d["count"] for d in decisions)
    agent_dec = sum(d["count"] for d in decisions if d["by_agent"])
    conv = run_sql(
        f"SELECT quote_status_code, COUNT(*) FROM {q('policy','quote')} GROUP BY 1")
    quote_status = {r[0]: int(r[1]) for r in conv}
    converted = quote_status.get("CONVERTED", 0)
    total_quotes = sum(quote_status.values())
    # book being built: GWP by line of business (the team's exposure forming)
    book = run_sql(
        f"SELECT line_of_business, CAST(MEASURE(gross_written_premium) AS DECIMAL(18,2)), "
        f"MEASURE(policy_count) FROM {q('semantics','underwriting_metrics')} "
        f"WHERE currency_code = '{cur}' GROUP BY line_of_business ORDER BY 2 DESC")
    portfolio = [{"line_of_business": r[0], "gwp": _num(r[1]),
                  "policy_count": int(_num(r[2]) or 0)} for r in book]

    # ---- SCOPE 3: enterprise — the same GWP flowing to three consumers, live
    gwp = run_sql(
        f"SELECT CAST(MEASURE(gross_written_premium) AS DECIMAL(18,2)) "
        f"FROM {q('semantics','underwriting_metrics')} WHERE currency_code = '{cur}'")
    uw_gwp = _num(gwp[0][0]) if gwp else None
    fin = run_sql(
        f"SELECT CAST(SUM(-jl.amount) AS DECIMAL(18,2)) "
        f"FROM {q('finance','journal_line')} jl "
        f"JOIN {q('finance','chart_of_account')} coa ON coa.account_id = jl.account_id "
        f"WHERE jl.source_entity = 'premium_transaction' AND jl.currency_code = '{cur}' "
        f"AND coa.account_number = '4000'")
    finance_premium = _num(fin[0][0]) if fin else None
    # MEASURE() is itself an aggregate — sum the per-treaty results outside it.
    ceded = run_sql(
        f"SELECT treaty_reference, CAST(MEASURE(ceded_premium) AS DECIMAL(18,2)) "
        f"FROM {q('semantics','cession_metrics')} GROUP BY treaty_reference")
    ceded_premium = round(sum(_num(r[1]) or 0 for r in ceded), 2) if ceded else None
    resv = run_sql(
        f"SELECT CAST(SUM(ultimate_loss) AS DECIMAL(18,2)), CAST(SUM(ibnr) AS DECIMAL(18,2)) "
        f"FROM {q('reserving','reserve_estimate')} WHERE currency_code = '{cur}' "
        f"AND reserving_method_code = 'CHAIN_LADDER'")
    resv_ult = _num(resv[0][0]) if resv else None
    resv_ibnr = _num(resv[0][1]) if resv else None

    return {
        "currency": cur,
        "submission": {
            "cases": submissions,
            "note": ("A machine buyer agent submits; fn_appetite_check decides "
                     "accept, decline or refer — the same agentic act Anthropic "
                     "shows in a spreadsheet, but recorded as a governed decision."),
        },
        "team": {
            "total_decisions": total_dec,
            "agent_decisions": agent_dec,
            "human_decisions": total_dec - agent_dec,
            "decisions": decisions,
            "converted": converted,
            "total_quotes": total_quotes,
            "conversion_rate": round(converted / total_quotes, 3) if total_quotes else None,
            "portfolio": portfolio,
            "note": ("Every underwriter's and agent's decision rolls up live — the "
                     "book forms in real time, no one collated a spreadsheet."),
        },
        "enterprise": {
            "underwriting_gwp": uw_gwp,
            "finance_premium_income": finance_premium,
            "finance_reconciles": (uw_gwp is not None and finance_premium is not None
                                   and abs(uw_gwp - finance_premium) < 0.01),
            "reinsurance_ceded": ceded_premium,
            "reserving_ultimate": resv_ult,
            "reserving_ibnr": resv_ibnr,
            "note": ("The same written premium the underwriter just bound flows, "
                     "with no re-key, to the finance close, the reinsurance "
                     "programme and the reserving triangle — reconciling by "
                     "construction."),
        },
        "genie_url": UNDERWRITING_GENIE,
        "genie_question": "How many quotes came from a machine buyer agent, and what did we decide?",
        "provenance": "policy.underwriting_decision · semantics.underwriting_metrics · finance.journal_line · reserving.reserve_estimate (v0.9.0)",
    }


# --------------------------------------------------------------------------- #
# Model-swap demonstrator — context is the moat, the model is a dial
# The governed DECISION is deterministic (fn_appetite_check + recorded
# underwriting_decision). The LLM only NARRATES it in English — and which LLM
# is a swappable choice, or none at all. Proves: (1) regulators get a
# deterministic, auditable decision, not a black box; (2) no lock-in to any
# one model; (3) the value is the governed context, not the model.
# --------------------------------------------------------------------------- #

# The dial: a spectrum from frontier → cheap → open-weight → off. Every one is
# a real Foundation Model API endpoint on this workspace, model-agnostic.
NARRATION_MODELS = [
    {"id": "databricks-claude-sonnet-5", "label": "Claude Sonnet 5",
     "tier": "frontier", "note": "Anthropic, via Databricks FMAPI"},
    {"id": "databricks-llama-4-maverick", "label": "Llama 4 Maverick",
     "tier": "open", "note": "open weights — run it in your own VPC"},
    {"id": "databricks-gpt-oss-120b", "label": "GPT-OSS 120B",
     "tier": "open", "note": "open weights, no vendor dependency"},
    {"id": "databricks-meta-llama-3-1-8b-instruct", "label": "Llama 3.1 8B",
     "tier": "cheap", "note": "small + cheap — the number is unchanged"},
    {"id": "none", "label": "None — deterministic only",
     "tier": "none", "note": "no LLM in the path; the decision still stands"},
]
_MODEL_IDS = {m["id"] for m in NARRATION_MODELS}


def _narrate(endpoint: str, prompt: str) -> str:
    w = client()
    resp = w.api_client.do(
        "POST", f"/serving-endpoints/{endpoint}/invocations",
        body={"messages": [{"role": "user", "content": prompt}], "max_tokens": 220})
    text = resp["choices"][0]["message"]["content"]
    if isinstance(text, list):
        text = "".join(b.get("text", "") for b in text if b.get("type") == "text")
    return text.strip()


@app.get("/api/atlas/model-swap/config")
def atlas_model_swap_config():
    return {"models": NARRATION_MODELS}


@app.get("/api/atlas/model-swap")
def atlas_model_swap(model: str = "databricks-claude-sonnet-5"):
    """Run one governed underwriting decision and narrate it with the chosen
    model. The DECISION and the numbers come from the data (deterministic); only
    the narration changes with the model — or disappears if model=none."""
    mdl = model if model in _MODEL_IDS else "databricks-claude-sonnet-5"

    # THE GOVERNED FACT — read from the data, decided by fn_appetite_check, not the LLM.
    rows = run_sql(
        f"SELECT q.quote_number, q.line_of_business_code, "
        f"CAST(q.quoted_gross_premium AS DECIMAL(18,2)), "
        f"ud.underwriting_decision_type_code, ud.decided_by, ud.decided_by_agent, "
        f"ud.rationale FROM {q('policy','quote')} q "
        f"JOIN {q('policy','underwriting_decision')} ud ON ud.quote_id = q.quote_id "
        f"WHERE q.quote_number = 'QUO-2026-000901'")
    if not rows:
        raise HTTPException(404, "governed decision not found")
    r = rows[0]
    fact = {
        "quote_number": r[0],
        "line_of_business": (r[1] or "").replace("_", " ").title(),
        "quoted_premium": _num(r[2]),
        "decision": r[3],
        "decided_by": r[4],
        "by_agent": as_bool(r[5]),
        "rationale": r[6],
        "decided_by_engine": "fn_appetite_check (governed UC function)",
    }

    result = {
        "model": mdl,
        "model_label": next((m["label"] for m in NARRATION_MODELS if m["id"] == mdl), mdl),
        "fact": fact,
        "decision_source": "deterministic — fn_appetite_check + recorded underwriting_decision",
        "narration": None,
        "narration_error": None,
        "contract": ("The decision and the numbers are identical regardless of model — "
                     "they are governed facts. The LLM only phrases the explanation, and "
                     "which LLM (or none) is your choice."),
    }
    if mdl == "none":
        result["narration"] = None
        result["narration_note"] = (
            "No LLM in the path. The decision (" + fact["decision"] +
            ") and its recorded rationale still stand — fully auditable, "
            "regulator-ready, no model involved.")
        return result

    prompt = (
        "You are explaining, in two plain-English sentences for an underwriter, a "
        "decision that has ALREADY been made by a governed rules function. Do not "
        "change or second-guess the decision. Decision facts:\n"
        f"- Quote {fact['quote_number']}, {fact['line_of_business']}, premium "
        f"{fact['quoted_premium']}.\n"
        f"- Decision: {fact['decision']} (made by {fact['decided_by_engine']}).\n"
        f"- Recorded rationale: {fact['rationale']}\n"
        "Write only the two-sentence explanation.")
    try:
        result["narration"] = _narrate(mdl, prompt)
    except Exception as e:  # noqa: BLE001
        result["narration_error"] = str(e)
    return result


@app.get("/api/atlas/genie-health")
def atlas_genie_health():
    """Is the Genie loop demonstrable right now? Checks the warehouse is warm.
    The frontend uses this to decide between the live 'Ask in Genie' button and
    the inline-SQL fallback, so a cold workspace never becomes an on-stage 404."""
    try:
        run_sql("SELECT 1")
        return {"warehouse": "warm", "genie_space_url": GENIE_SPACE_URL, "ready": True}
    except Exception as e:  # noqa: BLE001
        return {"warehouse": "cold", "genie_space_url": GENIE_SPACE_URL,
                "ready": False, "detail": str(e)}


@app.get("/api/health")
def health():
    return {"status": "ok", "version": atlas.meta()["version"]}


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
