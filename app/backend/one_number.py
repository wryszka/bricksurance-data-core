"""One Number: the governed loss-ratio demo for executives and actuaries.

One question ("What is our Commercial Property loss ratio?"), three team
answers, an AI with and without the company rulebook, and a Chief-Actuary
change that republishes the number everywhere.

The rulebook is semantics.loss_ratio_definition (versioned, maker/checker).
Approving a version republishes semantics.loss_ratio_metrics and rewrites the
governed Genie space's instructions, so the assistant and the metric always
agree. Shared with tools/one_number_setup.py and tools/one_number_genie.py.
"""

import json
import os
import re
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .db import CATALOG, client, run_sql, WAREHOUSE_ID, SERVING_ENDPOINT

S = f"{CATALOG}.bricksurance_semantics"
RAW_SPACE = os.environ.get("ONE_NUMBER_RAW_SPACE", "01f1c1a0a1e01f179ab9237da5ba42ee")
GOV_SPACE = os.environ.get("ONE_NUMBER_GOVERNED_SPACE", "01f1c1a0a23816179ff3850103e0fe6e")
QUESTION = "What is our Commercial Property loss ratio?"
STRESS_QUESTION = ("For Commercial Property, what is the loss ratio for clients under financial "
                   "stress compared with all other clients?")
CACHE_FILE = Path(__file__).parent / "data" / "one_number_cache.json"
DISCLAIMER = "Bricksurance is fictional; all data is synthetic."
FLAGS = ("include_case_reserves", "include_ibnr", "include_claims_handling_costs", "net_of_recoveries")


def t(domain, name):
    return f"{CATALOG}.bricksurance_{domain}.{name}"


# ---------------------------------------------------------------- definitions

def measure_expr(d):
    parts = ["SUM(claims_paid)"]
    if d["include_case_reserves"]:
        parts.append("SUM(case_reserves)")
    if d["include_ibnr"]:
        parts.append("SUM(ibnr)")
    if d["include_claims_handling_costs"]:
        parts.append("SUM(claims_handling_costs)")
    num = " + ".join(parts)
    if d["net_of_recoveries"]:
        num += " - SUM(recoveries)"
    den = "SUM(earned_premium)" if d["premium_basis"] == "EARNED" else "SUM(written_premium)"
    return f"({num}) / NULLIF({den}, 0)"


def metric_view_sql(d):
    text = d["definition_text"].replace("'", "")
    return f"""CREATE OR REPLACE VIEW {S}.loss_ratio_metrics
COMMENT 'THE company loss ratio. Use measure loss_ratio for any question about loss ratio - it is the definition approved by the {d["approved_by"]} (version {d["version"]}): {text} Always filter currency_code. The team views (finance_view_loss_ratio, underwriting_view_loss_ratio) exist only to explain why older reports differ - do not use them as the answer.'
WITH METRICS
LANGUAGE YAML
AS $$
version: 0.1
source: {S}.loss_ratio_components
dimensions:
  - name: line_of_business
    expr: line_of_business
  - name: line_of_business_code
    expr: line_of_business_code
  - name: underwriting_year
    expr: underwriting_year
  - name: currency_code
    expr: currency_code
  - name: client_name
    expr: client_name
  - name: industry_sector
    expr: industry_sector
  - name: financial_stress_band
    expr: financial_stress_band
  - name: annual_revenue_gbp
    expr: annual_revenue_gbp
measures:
  - name: loss_ratio
    expr: {measure_expr(d)}
  - name: written_premium
    expr: SUM(written_premium)
  - name: earned_premium
    expr: SUM(earned_premium)
  - name: claims_paid
    expr: SUM(claims_paid)
  - name: case_reserves
    expr: SUM(case_reserves)
  - name: ibnr
    expr: SUM(ibnr)
  - name: claims_handling_costs
    expr: SUM(claims_handling_costs)
  - name: recoveries
    expr: SUM(recoveries)
  - name: claim_count
    expr: SUM(claim_count)
  - name: finance_view_loss_ratio
    expr: SUM(claims_paid) / NULLIF(SUM(written_premium), 0)
  - name: underwriting_view_loss_ratio
    expr: (SUM(claims_paid) + SUM(case_reserves) - SUM(recoveries)) / NULLIF(SUM(written_premium), 0)
$$"""


def governed_instructions(d):
    return f"""You answer questions from the board, executives and actuaries of Bricksurance SE.

THE COMPANY LOSS RATIO (in force now)
- Version {d["version"]}: "{d["name"]}", approved by the {d["approved_by"]} on {str(d["approved_at"])[:10]}.
- Definition: {d["definition_text"]}

RULES
- Always answer loss-ratio questions with MEASURE(loss_ratio) from {t('semantics', 'loss_ratio_metrics')}. It implements exactly the definition above.
- When you give a loss ratio, say in one plain sentence what it includes, and that it is version {d["version"]} approved by the {d["approved_by"]}.
- Never build your own loss ratio from raw tables. Do not give finance_view_loss_ratio or underwriting_view_loss_ratio as the answer; they only explain why older team reports differ.
- Always filter currency_code = 'GBP' unless asked otherwise, and say so.
- No year given means the whole book; filter underwriting_year only when the user names one.
- Filter lines with line_of_business labels such as 'Commercial Property'.

OUTSIDE COMPANY DATA
- industry_sector, annual_revenue_gbp and financial_stress_band come from an outside business-information provider (Dun & Bradstreet-style), matched to our clients by global company id. "Under financial stress" means financial_stress_band = 'High'.

STYLE
- Plain business English first, then the number as a percentage with one decimal place. Short.
{DISCLAIMER}"""


GOV_EXAMPLES = [
    (QUESTION,
     f"SELECT MEASURE(loss_ratio) AS loss_ratio FROM {t('semantics', 'loss_ratio_metrics')} "
     f"WHERE line_of_business = 'Commercial Property' AND currency_code = 'GBP'"),
    ("Loss ratio for clients under financial stress compared with the rest, Commercial Property",
     f"SELECT CASE WHEN financial_stress_band = 'High' THEN 'Under financial stress' ELSE 'All other clients' END AS client_group, "
     f"MEASURE(loss_ratio) AS loss_ratio, MEASURE(earned_premium) AS earned_premium "
     f"FROM {t('semantics', 'loss_ratio_metrics')} WHERE line_of_business = 'Commercial Property' AND currency_code = 'GBP' GROUP BY 1"),
]
RAW_TABLES = [t("policy", "policy"), t("policy", "premium_transaction"), t("claim", "claim"),
              t("claim", "claim_transaction"), t("party", "party"), t("party", "party_role")]
GOV_TABLES = [t("semantics", "loss_ratio_metrics"), t("semantics", "loss_ratio_definition"),
              t("enrichment", "business_firmographics")]


def _uid():
    return uuid.uuid4().hex


def governed_space_payload(d):
    ser = {"version": 2,
           "data_sources": {"tables": [{"identifier": i} for i in sorted(GOV_TABLES)]},
           "instructions": {
               "text_instructions": [{"id": _uid(), "content": [governed_instructions(d)]}],
               "example_question_sqls": sorted(
                   ({"id": _uid(), "question": [q], "sql": [s]} for q, s in GOV_EXAMPLES),
                   key=lambda x: x["id"])}}
    return {"title": "One Number — AI with the company rulebook",
            "description": f"The approved loss-ratio definition, the published metric and outside company data. {DISCLAIMER}",
            "warehouse_id": WAREHOUSE_ID, "serialized_space": json.dumps(ser)}


def raw_space_payload():
    ser = {"version": 2, "data_sources": {"tables": [{"identifier": i} for i in sorted(RAW_TABLES)]}}
    return {"title": "One Number — AI with no context",
            "description": f"Raw operational tables only: no business definitions, no instructions. {DISCLAIMER}",
            "warehouse_id": WAREHOUSE_ID, "serialized_space": json.dumps(ser)}


def _esc(s):
    return (s or "").replace("'", "''")


def rows(sql):
    return run_sql(sql)


def definitions():
    cols = ["version", "status", "name", *FLAGS, "premium_basis", "definition_text", "rationale",
            "proposed_by", "approved_by", "proposed_at", "approved_at"]
    out = []
    for r in rows(f"SELECT {', '.join(cols)} FROM {S}.loss_ratio_definition ORDER BY version DESC"):
        d = dict(zip(cols, r))
        d["version"] = int(d["version"])
        for k in FLAGS:
            d[k] = str(d[k]).lower() == "true"
        out.append(d)
    return out


def approved():
    return next(d for d in definitions() if d["status"] == "APPROVED")


def publish():
    """Republish the metric view and the governed assistant from the APPROVED version."""
    d = approved()
    run_sql(metric_view_sql(d))
    client().api_client.do("PATCH", f"/api/2.0/genie/spaces/{GOV_SPACE}", body=governed_space_payload(d))
    return d


def definition_text(f):
    """Plain-words definition generated from the switches, so text and maths never drift."""
    parts = ["claims paid"]
    if f["include_case_reserves"]:
        parts.append("case reserves")
    if f["include_ibnr"]:
        parts.append("IBNR")
    if f["include_claims_handling_costs"]:
        parts.append("claims-handling costs (ALAE)")
    num = " + ".join(parts) + (" - recoveries" if f["net_of_recoveries"] else "")
    den = "earned premium" if f["premium_basis"] == "EARNED" else "written premium"
    text = f"Loss ratio = ({num}) / {den}."
    if f["include_ibnr"]:
        text += (" We count the ultimate cost of claims: claims known but not yet paid (case reserves)"
                 " and claims that have happened but are not yet reported (IBNR, set by the reserving team).")
    if f["include_claims_handling_costs"]:
        text += " Legal, surveyor and other costs of settling claims (ALAE) are part of the cost of claims."
    else:
        text += " Claims-handling costs (ALAE) are reported separately in the expense ratio."
    if f["premium_basis"] == "EARNED":
        text += " We divide by earned premium so that claims and premium describe the same period of cover."
    return text + " Applies to all lines; compare within one currency."


# ---------------------------------------------------------------- numbers

def _f(x):
    return float(x) if x not in (None, "") else 0.0


def book(line="Commercial Property", currency="GBP"):
    r = rows(f"""SELECT MEASURE(loss_ratio), MEASURE(written_premium), MEASURE(earned_premium),
                 MEASURE(claims_paid), MEASURE(case_reserves), MEASURE(ibnr),
                 MEASURE(claims_handling_costs), MEASURE(recoveries), MEASURE(claim_count)
                 FROM {S}.loss_ratio_metrics
                 WHERE line_of_business = '{_esc(line)}' AND currency_code = '{_esc(currency)}'""")[0]
    k = ["loss_ratio", "written_premium", "earned_premium", "claims_paid", "case_reserves", "ibnr",
         "claims_handling_costs", "recoveries", "claim_count"]
    return {a: _f(b) for a, b in zip(k, r)}


def ruleset_value(b, d):
    cost = b["claims_paid"]
    cost += b["case_reserves"] if d["include_case_reserves"] else 0
    cost += b["ibnr"] if d["include_ibnr"] else 0
    cost += b["claims_handling_costs"] if d["include_claims_handling_costs"] else 0
    cost -= b["recoveries"] if d["net_of_recoveries"] else 0
    return cost / (b["earned_premium"] if d["premium_basis"] == "EARNED" else b["written_premium"])


def team_views(b):
    """The three answers teams give today, all from the same building blocks."""
    wp, ep = b["written_premium"], b["earned_premium"]
    paid, case, ibnr = b["claims_paid"], b["case_reserves"], b["ibnr"]
    alae, rec = b["claims_handling_costs"], b["recoveries"]
    return [
        {"team": "Finance", "who": "Group Finance — monthly management accounts",
         "counts": "Claims actually paid out so far", "over": "Premium written",
         "value": paid / wp,
         "why": "Cash view: only what has left the bank, against everything we have sold."},
        {"team": "Underwriting", "who": "Commercial Property underwriting — portfolio review",
         "counts": "Claims paid + claims reported but not yet paid, less recoveries", "over": "Premium written",
         "value": (paid + case - rec) / wp,
         "why": "Adds the claims we know about, but ignores claims not yet reported and premium not yet earned."},
        {"team": "Actuarial", "who": "Reserving team — quarterly reserve review",
         "counts": "Ultimate cost: paid + reported + not-yet-reported (IBNR) + claims-handling costs, less recoveries",
         "over": "Premium earned",
         "value": (paid + case + ibnr + alae - rec) / ep,
         "why": "Full ultimate view, including the legal and surveyor costs of settling claims."},
    ]


def bridge(b, d):
    """Walk from the Finance number to the approved number, one step at a time."""
    wp, ep = b["written_premium"], b["earned_premium"]
    steps, cost = [], b["claims_paid"]
    steps.append({"label": "Claims paid ÷ written premium (Finance view)", "value": cost / wp, "kind": "start"})
    if d["include_case_reserves"]:
        cost += b["case_reserves"]
        steps.append({"label": "+ claims reported, not yet paid", "value": cost / wp, "kind": "step"})
    if d["net_of_recoveries"]:
        cost -= b["recoveries"]
        steps.append({"label": "− recoveries (salvage, third parties)", "value": cost / wp, "kind": "step"})
    if d["include_ibnr"]:
        cost += b["ibnr"]
        steps.append({"label": "+ claims happened, not yet reported (IBNR)", "value": cost / wp, "kind": "step"})
    if d["include_claims_handling_costs"]:
        cost += b["claims_handling_costs"]
        steps.append({"label": "+ claims-handling costs (ALAE)", "value": cost / wp, "kind": "step"})
    den = ep if d["premium_basis"] == "EARNED" else wp
    steps.append({"label": "÷ earned premium instead of written" if d["premium_basis"] == "EARNED"
                  else "÷ written premium", "value": cost / den, "kind": "step"})
    steps.append({"label": f"Company loss ratio (version {d['version']})", "value": cost / den, "kind": "end"})
    return steps


def stress_split():
    r = rows(f"""SELECT CASE WHEN financial_stress_band = 'High' THEN 'stressed' ELSE 'other' END g,
                 MEASURE(loss_ratio), MEASURE(earned_premium),
                 array_join(collect_set(client_name), ', ')
                 FROM {S}.loss_ratio_metrics
                 WHERE line_of_business = 'Commercial Property' AND currency_code = 'GBP' GROUP BY 1""")
    return {g: {"loss_ratio": _f(lr), "earned_premium": _f(ep), "clients": c} for g, lr, ep, c in r}


def firmographics():
    cols = ["client_name", "global_company_id", "industry_sector", "annual_revenue_gbp",
            "employee_count", "financial_stress_score", "financial_stress_band"]
    sql = (f"SELECT p.name, f.global_company_id, f.industry_sector, f.annual_revenue_gbp, f.employee_count, "
           f"f.financial_stress_score, f.financial_stress_band FROM {t('enrichment', 'business_firmographics')} f "
           f"JOIN {t('party', 'party')} p USING (party_id) WHERE f.party_id IN "
           f"(SELECT DISTINCT party_id FROM {t('party', 'party_role')} pr JOIN {t('policy', 'policy')} po "
           f"USING (policy_id) WHERE pr.party_role_type_code = 'POLICYHOLDER' "
           f"AND po.line_of_business_code = 'COMMERCIAL_PROPERTY' AND po.currency_code = 'GBP') "
           f"ORDER BY f.financial_stress_score DESC")
    return [dict(zip(cols, r)) for r in rows(sql)]


# ---------------------------------------------------------------- assistant

def _cache():
    try:
        return json.loads(CACHE_FILE.read_text())
    except Exception:
        return {}


def ask_genie(space_id, question, timeout=75):
    w = client()
    start = time.time()
    m = w.genie.start_conversation_and_wait(space_id, question)
    out = {"question": question, "text": [], "sql": None, "columns": [], "rows": [], "live": True,
           "seconds": round(time.time() - start, 1)}
    for a in m.attachments or []:
        if a.text and a.text.content:
            out["text"].append(a.text.content)
        if a.query:
            out["sql"] = a.query.query
            r = w.genie.get_message_attachment_query_result(space_id, m.conversation_id, m.id, a.attachment_id)
            sr = r.statement_response
            out["columns"] = [c.name for c in sr.manifest.schema.columns]
            out["rows"] = (sr.result.data_array or [])[:20]
    return out


def explain_sql(sql, governed):
    """Plain-English 'what did it actually count' for executives, via Claude."""
    if not sql:
        return []
    prompt = (
        "You are explaining to an insurance CEO and Chief Actuary what an AI assistant actually "
        "calculated. Read the SQL and give 2-4 short bullet points in plain business English (no SQL, "
        "no table names). " + (
            "Confirm what it used and that it followed the approved company definition."
            if governed else
            "Be specific about what it added up and divided by, and flag anything an actuary would object "
            "to - e.g. mixing currencies, counting reserve movements or fees as claims, using written instead "
            "of earned premium, ignoring claims not yet reported.") +
        " Each bullet at most 22 words, no hedging words like 'likely' or 'could'." +
        " Return ONLY a JSON array of strings.\n\nSQL:\n" + sql)
    try:
        resp = client().api_client.do(
            "POST", f"/serving-endpoints/{SERVING_ENDPOINT}/invocations",
            body={"messages": [{"role": "user", "content": prompt}], "max_tokens": 400})
        c = resp["choices"][0]["message"]["content"]
        if isinstance(c, list):  # sonnet-5 returns content as a list of blocks
            c = "".join(p.get("text", "") for p in c if isinstance(p, dict))
        m = re.search(r"\[.*\]", c, re.S)
        return json.loads(m.group(0)) if m else [c.strip()]
    except Exception as e:  # never break the room
        return [f"(explanation unavailable: {type(e).__name__})"]


def currency_facts(answers):
    """A checked fact, not an AI opinion: did the assistant add currencies together?"""
    mixed = [a for a in answers if a["sql"] and "currency" not in a["sql"].lower() and a["rows"] and a["rows"][0][-1]]
    if not mixed:
        return []
    ccy = [r[0] for r in rows(f"SELECT DISTINCT currency_code FROM {t('policy', 'policy')} "
                              f"WHERE line_of_business_code = 'COMMERCIAL_PROPERTY' ORDER BY 1")]
    if len(ccy) < 2:
        return []
    return [f"Checked against the data: our Commercial Property book is written in {', '.join(ccy[:-1])} and {ccy[-1]}. "
            f"The assistant added them together as if they were one currency."]


# ---------------------------------------------------------------- API

router = APIRouter(prefix="/api/one-number")


@router.get("/state")
def state():
    from concurrent.futures import ThreadPoolExecutor
    client().config.authenticate()  # warm the token before threads share it
    with ThreadPoolExecutor(4) as ex:
        f_defs, f_book, f_stress, f_firm = (ex.submit(definitions), ex.submit(book),
                                            ex.submit(stress_split), ex.submit(firmographics))
        defs, b = f_defs.result(), f_book.result()
        stress, firms = f_stress.result(), f_firm.result()
    d = next(x for x in defs if x["status"] == "APPROVED")
    pending = next((x for x in defs if x["status"] == "PROPOSED"), None)
    out = {"question": QUESTION, "stress_question": STRESS_QUESTION, "approved": d, "pending": pending,
           "history": defs, "book": b, "teams": team_views(b), "bridge": bridge(b, d),
           "stress": stress, "firmographics": firms,
           "spaces": {"raw": RAW_SPACE, "governed": GOV_SPACE},
           "host": client().config.host}
    if pending:
        # what the number WOULD be: same building blocks, the proposed rule
        out["pending_value"] = ruleset_value(b, pending)
    return out


class AskBody(BaseModel):
    space: str  # raw | governed
    question: str = QUESTION
    times: int = 1  # ask the same question N times in parallel (max 3)
    live: bool = True


def _cache_key(space, question):
    v = approved()["version"] if space == "governed" else 0
    return f"{space}::v{v}::{question}"


@router.post("/ask")
def ask(body: AskBody):
    from concurrent.futures import ThreadPoolExecutor
    space_id = RAW_SPACE if body.space == "raw" else GOV_SPACE
    key = _cache_key(body.space, body.question)
    n = max(1, min(3, body.times))
    if body.live:
        try:
            client().config.authenticate()  # warm the token before threads share it
            with ThreadPoolExecutor(n) as ex:
                answers = list(ex.map(lambda _: ask_genie(space_id, body.question), range(n)))
            explain = explain_sql(next((a["sql"] for a in reversed(answers) if a["rows"] and a["rows"][0][-1]), answers[0]["sql"]),
                                  body.space == "governed")
            if body.space == "raw":
                explain = currency_facts(answers) + explain
            return {"answers": answers, "explain": explain, "live": True}
        except Exception as e:
            fallback = _cache().get(key)
            if fallback:
                return {**fallback, "live": False,
                        "note": f"Live call failed ({type(e).__name__}); showing the last verified answer."}
            raise HTTPException(502, f"Assistant unavailable: {e}")
    fallback = _cache().get(key)
    if not fallback:
        raise HTTPException(404, "No saved answer for this question.")
    return {**fallback, "live": False, "note": "Saved answer from a verified earlier run."}


class ProposeBody(BaseModel):
    include_case_reserves: bool = True
    include_ibnr: bool = True
    include_claims_handling_costs: bool = True
    net_of_recoveries: bool = True
    premium_basis: str = "EARNED"
    rationale: str = ""
    proposed_by: str = "Reserving Manager"


@router.post("/propose")
def propose(body: ProposeBody):
    if body.premium_basis not in ("EARNED", "WRITTEN"):
        raise HTTPException(400, "premium_basis must be EARNED or WRITTEN")
    f = body.model_dump()
    v = max(d["version"] for d in definitions()) + 1
    run_sql(f"DELETE FROM {S}.loss_ratio_definition WHERE status = 'PROPOSED'")
    name = "Ultimate loss ratio incl. claims-handling costs" if body.include_claims_handling_costs \
        else "Ultimate loss ratio (earned basis)"
    run_sql(f"""INSERT INTO {S}.loss_ratio_definition VALUES (
        {v}, 'PROPOSED', '{_esc(name)}', {str(body.include_case_reserves).upper()}, {str(body.include_ibnr).upper()},
        {str(body.include_claims_handling_costs).upper()}, {str(body.net_of_recoveries).upper()}, '{body.premium_basis}',
        '{_esc(definition_text(f))}', '{_esc(body.rationale)}', '{_esc(body.proposed_by)}', NULL,
        current_timestamp(), NULL)""")
    return state()


class ApproveBody(BaseModel):
    approved_by: str = "Chief Actuary"


@router.post("/approve")
def approve(body: ApproveBody):
    p = next((d for d in definitions() if d["status"] == "PROPOSED"), None)
    if not p:
        raise HTTPException(400, "Nothing is waiting for approval.")
    if body.approved_by.strip().lower() == (p["proposed_by"] or "").strip().lower():
        raise HTTPException(400, "The person approving must be different from the person who proposed it.")
    run_sql(f"UPDATE {S}.loss_ratio_definition SET status = 'SUPERSEDED' WHERE status = 'APPROVED'")
    run_sql(f"""UPDATE {S}.loss_ratio_definition SET status = 'APPROVED', approved_by = '{_esc(body.approved_by)}',
                approved_at = current_timestamp() WHERE version = {p['version']}""")
    publish()
    return state()


@router.post("/reject")
def reject():
    run_sql(f"DELETE FROM {S}.loss_ratio_definition WHERE status = 'PROPOSED'")
    return state()


SEED_V1 = {
    "include_case_reserves": True, "include_ibnr": True, "include_claims_handling_costs": False,
    "net_of_recoveries": True, "premium_basis": "EARNED"}


@router.post("/reset")
def reset():
    run_sql(f"DELETE FROM {S}.loss_ratio_definition")
    run_sql(f"""INSERT INTO {S}.loss_ratio_definition VALUES (
        1, 'APPROVED', 'Ultimate loss ratio (earned basis)', TRUE, TRUE, FALSE, TRUE, 'EARNED',
        '{_esc(definition_text(SEED_V1))}',
        'One company-wide definition replacing team-by-team spreadsheets.',
        'Reserving Manager', 'Chief Actuary', TIMESTAMP'2026-07-01 09:00:00', TIMESTAMP'2026-07-03 16:30:00')""")
    publish()
    return state()
