"""Motor loss ratio: the second context-demo chapter (see specs/SPEC_MOTOR_CONTEXT_DEMO.md).

One executive question ("Why has our motor loss ratio deteriorated this quarter,
and which segments are driving it?"), three disconnected source systems with
three vocabularies, an AI with and without the mapped, governed layer, the
evidence behind each driver, and two competing loss-ratio definitions.

Shares the One Number rulebook (semantics.loss_ratio_definition): the APPROVED
version is compiled into semantics.motor_performance_metrics (owned by the app
service principal) and into the governed Genie Agent's instructions. The source
mappings come from the bundled ontology (model/mappings/*.yaml -> ontology.json),
so the crosswalk the room sees is the same artefact the generator deploys.
"""

import json
import os
import time
import uuid
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .db import CATALOG, client, run_sql, WAREHOUSE_ID
from . import one_number as on

S = f"{CATALOG}.bricksurance_semantics"
MV = f"{S}.motor_performance_metrics"
RAW_SPACE = os.environ.get("MOTOR_RAW_SPACE", "")
GOV_SPACE = os.environ.get("MOTOR_GOVERNED_SPACE", "")
QUESTION = "Why has our motor loss ratio deteriorated this quarter, and which segments are driving it?"
FOLLOW_UPS = [
    {"key": "areas", "question": "Which geographical areas are responsible for the urban motor deterioration?"},
    {"key": "freq_sev", "question": "Is the increase in the motor loss ratio driven by claim frequency or severity?"},
    {"key": "large", "question": "How much of the commercial motor deterioration comes from large losses?"},
]
Q2, Q3 = "2026Q2", "2026Q3"
VALUATION = "2026-10-31"
CACHE_FILE = Path(__file__).parent / "data" / "motor_cache.json"
ONTOLOGY_FILE = Path(__file__).parent / "data" / "ontology.json"
DISCLAIMER = on.DISCLAIMER
LEGACY = {
    "name": "Claims operations ratio",
    "formula": "claims paid / written premium",
    "where": "The weekly claims-operations dashboard and the saved query behind it, in use since 2019.",
    "answers": "How much cash has gone out against the premium we have booked - a cash-flow and workload view.",
    "not": "Not the loss ratio: it ignores claims reported but unpaid, claims not yet reported, and premium not yet earned.",
}


# ---------------------------------------------------------------- ontology (bundled, platform-neutral)

@lru_cache(maxsize=1)
def _onto():
    return json.loads(ONTOLOGY_FILE.read_text())


def mappings():
    return _onto().get("mappings", [])


def metric_spec():
    return next(m for m in _onto()["metric_views"] if m["name"] == "motor_performance_metrics")


def t(domain, name):
    return f"{CATALOG}.bricksurance_{domain}.{name}"


def _words(s):
    return " ".join(str(s or "").split())


def systems():
    """The three source systems, in their own words, with the concept each table maps to."""
    out = []
    for m in mappings():
        tables = []
        for tb in m["tables"]:
            tables.append({
                "source": tb["source"], "concept": tb.get("concept"), "conformed_view": tb.get("conformed_view"),
                "grain": _words(tb.get("grain")), "description": _words(tb.get("description")),
                "columns": [{"source": c.get("source"), "attribute": c["attribute"], "note": _words(c.get("note"))}
                            for c in tb.get("columns", [])],
                "extensions": [{"name": x["name"], "source": x.get("source"), "definition": _words(x["definition"])}
                               for x in tb.get("extensions", [])],
            })
        out.append({"system": m["source_system"], "title": m["title"], "schema": f"bricksurance_{m['schema']}",
                    "owner": m.get("owner"), "certification": m.get("certification"),
                    "description": _words(m["description"]), "tables": tables})
    return out


def crosswalk():
    """One row per core attribute, one cell per source system - the same table as build/docs/mapping_catalog.md."""
    rows_, order = {}, []
    for m in mappings():
        for tb in m["tables"]:
            concept = tb.get("concept")
            for c in tb.get("columns", []):
                attr = c["attribute"]
                target = attr if "." in attr else f"{concept}.{attr}"
                if target not in rows_:
                    rows_[target] = {"concept": target.split(".")[0], "attribute": target.split(".")[-1], "systems": {}}
                    order.append(target)
                src = f"{tb['source']}.{c['source']}" if c.get("source") else f"constant {c.get('expr')}"
                rows_[target]["systems"][m["source_system"]] = {"source": src, "note": _words(c.get("note"))}
    rank = ["policy", "coverage", "vehicle", "insured_object", "premium_transaction", "premium_earning",
            "claim", "claim_transaction", "valuation_result", "postcode_enrichment"]
    key = lambda tgt: (rank.index(rows_[tgt]["concept"]) if rows_[tgt]["concept"] in rank else 99, order.index(tgt))
    return [rows_[k] for k in sorted(order, key=key)]


# ---------------------------------------------------------------- publish from the rulebook

def incurred_expr(d):
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
    return num


def metric_view_sql(d):
    spec = metric_spec()
    text = d["definition_text"].replace("'", "")
    lines = ["version: 0.1", f"source: {S}.motor_loss_ratio_components", "", "dimensions:"]
    for dim in spec["dimensions"]:
        lines += [f"  - name: {dim['name']}", f"    expr: {dim['expr']}"]
    lines += ["", "measures:"]
    for m in spec["measures"]:
        expr = m["expr"]
        if m["name"] == "loss_ratio":
            expr = on.measure_expr(d)
        elif m["name"] == "incurred_claims":
            expr = incurred_expr(d)
        lines += [f"  - name: {m['name']}", f"    expr: {expr}"]
    comment = (f"THE motor loss ratio and its drivers. Use measure loss_ratio for any question about the motor "
               f"loss ratio: it is the company definition approved by the {d['approved_by']} (version {d['version']}): "
               f"{text} Accident-quarter basis, valued {VALUATION}, GBP. Segment, quarter, region and urbanity work on "
               f"every measure; peril, head of damage and large-loss flag describe claims only. The "
               f"claims_operations_ratio (paid over WRITTEN premium) is the legacy weekly claims-ops number kept for "
               f"reconciliation; it answers a different question and is not the loss ratio.")
    body = "\n".join(lines)
    return f"CREATE OR REPLACE VIEW {MV}\nCOMMENT '{comment}'\nWITH METRICS\nLANGUAGE YAML\nAS $$\n{body}\n$$"


def vocabulary_lines(limit=60):
    out = []
    for m in mappings():
        out.append(f"- {m['title']} (schema bricksurance_{m['schema']}, source system {m['source_system']}):")
        for tb in m["tables"]:
            for c in tb.get("columns", []):
                if c.get("note"):
                    out.append(f"  - '{tb['source']}.{c.get('source') or c['attribute']}' means {c['attribute']}: {_words(c['note'])}")
            for x in tb.get("extensions", []):
                out.append(f"  - '{x['name']}' is an enterprise extension: {_words(x['definition'])}")
    return out[:limit]


def governed_instructions(d):
    vocab = "\n".join(vocabulary_lines())
    return f"""You answer questions from the Chief Underwriting Officer, executives and actuaries of Bricksurance SE about the MOTOR book.

THE COMPANY LOSS RATIO (in force now)
- Version {d["version"]}: "{d["name"]}", approved by the {d["approved_by"]} on {str(d["approved_at"])[:10]}.
- Definition: {d["definition_text"]}

RULES
- Always answer loss-ratio questions with MEASURE(loss_ratio) from {MV}. It implements exactly the definition above. Say in one sentence what it includes and that it is version {d["version"]} approved by the {d["approved_by"]}.
- "This quarter" is accident_quarter 2026Q3; "last quarter" is 2026Q2. Valuation date {VALUATION}. All amounts are GBP.
- For "why" questions: give the two quarters' loss ratios, the change in percentage points, earned premium and incurred claims growth, then the loss ratio by motor_segment for both quarters. Then attribute the deterioration: for each segment, hold its 2026Q3 earned premium and compare actual 2026Q3 incurred with 2026Q2 loss ratio x 2026Q3 earned premium. Report each segment's share of the total.
- Never build your own loss ratio from raw tables. Do not present claims_operations_ratio as the loss ratio: it is the legacy paid-over-written number and only answers a question about it by name.
- Peril (peril_code), head of damage (head_of_damage_code) and large_loss_flag describe CLAIMS only. Pair them with claim measures (incurred_claims, claim_count, severity). Frequency = claim_count / vehicle_years, grouped by segment and quarter.
- Urban means motor_segment 'Urban private motor'; region questions use region_name. Large losses are large_loss_flag = true (net incurred 500,000 GBP or more).
- Evidence first, causality carefully: say what the data shows (frequency, severity, mix, region, large losses) and that it indicates where to look rather than proving a cause.
- Filter segments with labels (motor_segment), e.g. 'Commercial motor'.

VOCABULARY OF THE SOURCE SYSTEMS (mapped to the core concepts)
{vocab}

STYLE
- Plain business English first, numbers as percentages with one decimal place and GBP in millions with one decimal place. Short paragraphs, then a compact table.
{DISCLAIMER}"""


def gov_examples():
    return [
        (QUESTION,
         f"SELECT accident_quarter, motor_segment, MEASURE(earned_premium) AS earned_premium, "
         f"MEASURE(incurred_claims) AS incurred_claims, MEASURE(loss_ratio) AS loss_ratio "
         f"FROM {MV} WHERE accident_quarter IN ('2026Q2', '2026Q3') GROUP BY 1, 2 ORDER BY 2, 1"),
        ("What is our motor loss ratio this quarter compared with last quarter?",
         f"SELECT accident_quarter, MEASURE(earned_premium) AS earned_premium, MEASURE(incurred_claims) AS incurred_claims, "
         f"MEASURE(loss_ratio) AS loss_ratio FROM {MV} WHERE accident_quarter IN ('2026Q2', '2026Q3') GROUP BY 1 ORDER BY 1"),
        (FOLLOW_UPS[0]["question"],
         f"SELECT region_name, accident_quarter, MEASURE(earned_premium) AS earned_premium, MEASURE(incurred_claims) AS incurred_claims, "
         f"MEASURE(loss_ratio) AS loss_ratio, MEASURE(claim_count) AS claims FROM {MV} "
         f"WHERE motor_segment = 'Urban private motor' AND accident_quarter IN ('2026Q2', '2026Q3') GROUP BY 1, 2 ORDER BY 1, 2"),
        (FOLLOW_UPS[1]["question"],
         f"SELECT motor_segment, accident_quarter, MEASURE(claim_count) AS claims, MEASURE(vehicle_years) AS vehicle_years, "
         f"MEASURE(frequency) * 100 AS claims_per_100_vehicle_years, MEASURE(severity) AS average_cost_per_claim "
         f"FROM {MV} WHERE accident_quarter IN ('2026Q2', '2026Q3') GROUP BY 1, 2 ORDER BY 1, 2"),
        (FOLLOW_UPS[2]["question"],
         f"SELECT accident_quarter, large_loss_flag, MEASURE(claim_count) AS claims, MEASURE(incurred_claims) AS incurred_claims "
         f"FROM {MV} WHERE motor_segment = 'Commercial motor' AND component_kind = 'CLAIM' "
         f"AND accident_quarter IN ('2026Q2', '2026Q3') GROUP BY 1, 2 ORDER BY 1, 2"),
        ("Which perils drove the urban private motor deterioration?",
         f"SELECT peril_code, accident_quarter, MEASURE(claim_count) AS claims, MEASURE(incurred_claims) AS incurred_claims, "
         f"MEASURE(severity) AS average_cost FROM {MV} WHERE motor_segment = 'Urban private motor' AND component_kind = 'CLAIM' "
         f"AND accident_quarter IN ('2026Q2', '2026Q3') GROUP BY 1, 2 ORDER BY 1, 2"),
    ]


GOV_TABLES = [MV, f"{S}.motor_loss_ratio_components", f"{S}.loss_ratio_definition", f"{S}.vw_motor_segment",
              f"{S}.vw_motor_postcode_region", f"{S}.vw_motor_policy", f"{S}.vw_motor_claim",
              f"{S}.vw_motor_claim_transaction", f"{S}.vw_motor_earned_premium"]
RAW_TABLES = [t("src_pas", x) for x in ("pol_master", "pol_vehicle", "pol_cover", "pol_premium_txn")] + \
             [t("src_claims", x) for x in ("clm_header", "clm_movement")] + \
             [t("src_actuarial", x) for x in ("earned_premium_monthly", "ibnr_estimate", "segment_dim", "postcode_region_dim")]


def _uid():
    return uuid.uuid4().hex


def governed_space_payload(d):
    ser = {"version": 2,
           "data_sources": {"tables": [{"identifier": i} for i in sorted(GOV_TABLES)]},
           "instructions": {
               "text_instructions": [{"id": _uid(), "content": [governed_instructions(d)]}],
               "example_question_sqls": sorted(({"id": _uid(), "question": [q], "sql": [s]} for q, s in gov_examples()),
                                               key=lambda x: x["id"])}}
    return {"title": "Motor — AI with the mapped, governed layer",
            "description": f"The motor book conformed to the core concepts, the approved loss-ratio definition and the published metric. {DISCLAIMER}",
            "warehouse_id": WAREHOUSE_ID, "serialized_space": json.dumps(ser)}


def raw_space_payload():
    ser = {"version": 2, "data_sources": {"tables": [{"identifier": i} for i in sorted(RAW_TABLES)]}}
    return {"title": "Motor — AI with no context",
            "description": f"The three source systems as extracted: ten tables, three vocabularies, no definitions, no instructions. {DISCLAIMER}",
            "warehouse_id": WAREHOUSE_ID, "serialized_space": json.dumps(ser)}


def publish(d=None):
    """Republish the motor metric view and the governed agent from the APPROVED rulebook version."""
    d = d or on.approved()
    run_sql(metric_view_sql(d))
    if GOV_SPACE:
        client().api_client.do("PATCH", f"/api/2.0/genie/spaces/{GOV_SPACE}", body=governed_space_payload(d))
    return d


# ---------------------------------------------------------------- numbers (always live, from the metric view)

def _f(x):
    return float(x) if x is not None else 0.0


def _measures(group_by, where=""):
    cols = ["earned_premium", "written_premium", "incurred_claims", "loss_ratio", "claims_paid", "case_reserves",
            "ibnr", "recoveries", "claims_handling_costs", "claim_count", "vehicle_years", "claims_operations_ratio"]
    sql = (f"SELECT {', '.join(group_by)}, " + ", ".join(f"MEASURE({c})" for c in cols) +
           f" FROM {MV} WHERE accident_quarter IN ('{Q2}', '{Q3}') {('AND ' + where) if where else ''} "
           f"GROUP BY {', '.join(str(i + 1) for i in range(len(group_by)))} ORDER BY {', '.join(str(i + 1) for i in range(len(group_by)))}")
    out = []
    for r in run_sql(sql):
        keys = dict(zip(group_by, r[:len(group_by)]))
        vals = {c: _f(v) for c, v in zip(cols, r[len(group_by):])}
        out.append({**keys, **vals})
    return out


def headline():
    by_q = {r["accident_quarter"]: r for r in _measures(["accident_quarter"])}
    a, b = by_q.get(Q2, {}), by_q.get(Q3, {})
    return {"q2": a, "q3": b,
            "delta_points": (b.get("loss_ratio", 0) - a.get("loss_ratio", 0)) * 100,
            "incurred_growth": b.get("incurred_claims", 0) / a.get("incurred_claims", 1) - 1,
            "earned_growth": b.get("earned_premium", 0) / a.get("earned_premium", 1) - 1}


def segments():
    rows_ = _measures(["motor_segment_code", "motor_segment", "accident_quarter"])
    by = {}
    for r in rows_:
        by.setdefault((r["motor_segment_code"], r["motor_segment"]), {})[r["accident_quarter"]] = r
    out, total = [], 0.0
    for (code, label), qs in by.items():
        a, b = qs.get(Q2, {}), qs.get(Q3, {})
        lr2 = a.get("loss_ratio", 0)
        contrib = b.get("incurred_claims", 0) - lr2 * b.get("earned_premium", 0)
        total += contrib
        out.append({"code": code, "label": label, "q2": a, "q3": b, "contribution": contrib,
                    "delta_points": (b.get("loss_ratio", 0) - lr2) * 100})
    for s in out:
        s["share"] = s["contribution"] / total if total else 0
    order = {"PMU": 0, "CMV": 1, "PMO": 2}
    return sorted(out, key=lambda s: order.get(s["code"], 9))


def evidence():
    """The drivers, each as a Q2 vs Q3 comparison from the metric view - nothing narrated."""
    def pivot(rows_, keys):
        out = {}
        for r in rows_:
            k = tuple(r[x] for x in keys)
            out.setdefault(k, {})[r["accident_quarter"]] = r
        return [{**dict(zip(keys, k)), "q2": v.get(Q2, {}), "q3": v.get(Q3, {})} for k, v in out.items()]

    regions = pivot(_measures(["region_name", "accident_quarter"], "motor_segment_code = 'PMU'"), ["region_name"])
    for r in regions:
        r["delta_points"] = (r["q3"].get("loss_ratio", 0) - r["q2"].get("loss_ratio", 0)) * 100
        r["extra_incurred"] = r["q3"].get("incurred_claims", 0) - r["q2"].get("loss_ratio", 0) * r["q3"].get("earned_premium", 0)
    regions.sort(key=lambda r: -r["extra_incurred"])
    exposure = {(r["motor_segment_code"], r["accident_quarter"]): r for r in _measures(["motor_segment_code", "accident_quarter"])}
    theft = pivot(_measures(["motor_segment_code", "accident_quarter"], "peril_code = 'THEFT'"), ["motor_segment_code"])
    for r in theft:
        for q in ("q2", "q3"):
            vy = exposure.get((r["motor_segment_code"], Q2 if q == "q2" else Q3), {}).get("vehicle_years", 0)
            n = r[q].get("claim_count", 0)
            r[q]["per_100_vy"] = 100 * n / vy if vy else 0
            r[q]["severity"] = (r[q].get("claims_paid", 0) + r[q].get("case_reserves", 0) - r[q].get("recoveries", 0)) / n if n else 0
    repair = pivot(_measures(["motor_segment_code", "accident_quarter"], "head_of_damage_code = 'VEHICLE_REPAIR'"), ["motor_segment_code"])
    for r in repair:
        for q in ("q2", "q3"):
            n = r[q].get("claim_count", 0)
            r[q]["severity"] = (r[q].get("claims_paid", 0) + r[q].get("case_reserves", 0) - r[q].get("recoveries", 0)) / n if n else 0
    large = pivot(_measures(["large_loss_flag", "accident_quarter"],
                            "motor_segment_code = 'CMV' AND component_kind = 'CLAIM'"), ["large_loss_flag"])
    freq_sev = pivot(_measures(["motor_segment_code", "motor_segment", "accident_quarter"]), ["motor_segment_code", "motor_segment"])
    for r in freq_sev:
        for q in ("q2", "q3"):
            vy, n = r[q].get("vehicle_years", 0), r[q].get("claim_count", 0)
            r[q]["per_100_vy"] = 100 * n / vy if vy else 0
            r[q]["severity"] = (r[q].get("claims_paid", 0) + r[q].get("case_reserves", 0) - r[q].get("recoveries", 0)) / n if n else 0
    perils = pivot(_measures(["peril_code", "accident_quarter"], "motor_segment_code = 'PMU' AND component_kind = 'CLAIM'"), ["peril_code"])
    return {"regions": regions, "theft": theft, "repair": repair, "large": large, "freq_sev": freq_sev, "perils": perils}


def definitions_compare(h):
    return {
        "approved": {"q2": h["q2"].get("loss_ratio"), "q3": h["q3"].get("loss_ratio")},
        "legacy": {**LEGACY, "q2": h["q2"].get("claims_operations_ratio"), "q3": h["q3"].get("claims_operations_ratio")},
    }


# ---------------------------------------------------------------- Genie One (optional third arm)

def ask_genie_one(question, timeout=90):
    """Workspace-wide Genie One over the ontology. Preview API; best effort, never breaks the room."""
    import requests
    w = client()
    headers = {**w.config.authenticate(), "Content-Type": "application/json", "Accept": "text/event-stream"}
    url = f"{w.config.host}/api/2.0/genie/one/responses"
    t0 = time.time()
    r = requests.post(url, headers=headers, json={"input": question, "warehouse_id": WAREHOUSE_ID}, stream=True, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"Genie One API {r.status_code}: {r.text[:200]}")
    final, citations = "", []
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            ev = json.loads(payload)
        except Exception:
            continue
        item = ev.get("item") or ev.get("output_item") or {}
        if item.get("phase") == "final_answer" or ev.get("type") == "response.output_item.done":
            for part in item.get("content", []) or []:
                if part.get("type") == "output_text":
                    final = part.get("text", final)
                    citations = part.get("annotations", citations) or citations
    return {"question": question, "text": final, "citations": citations, "seconds": round(time.time() - t0, 1)}


# ---------------------------------------------------------------- API

router = APIRouter(prefix="/api/motor")


def _cache():
    try:
        return json.loads(CACHE_FILE.read_text())
    except Exception:
        return {}


@router.get("/state")
def state():
    from concurrent.futures import ThreadPoolExecutor
    client().config.authenticate()
    with ThreadPoolExecutor(3) as ex:
        f_defs, f_head, f_seg = ex.submit(on.definitions), ex.submit(headline), ex.submit(segments)
        defs, h, seg = f_defs.result(), f_head.result(), f_seg.result()
    d = next(x for x in defs if x["status"] == "APPROVED")
    return {"question": QUESTION, "follow_ups": FOLLOW_UPS, "valuation_date": VALUATION,
            "approved": d, "headline": h, "segments": seg, "definitions": definitions_compare(h),
            "systems": systems(), "crosswalk": crosswalk(),
            "spaces": {"raw": RAW_SPACE, "governed": GOV_SPACE}, "host": client().config.host}


@router.get("/evidence")
def evidence_api():
    client().config.authenticate()
    return evidence()


class AskBody(BaseModel):
    space: str  # raw | governed | one
    question: str = QUESTION
    times: int = 1
    live: bool = True


def _cache_key(space, question):
    v = on.approved()["version"] if space != "raw" else 0
    return f"{space}::v{v}::{question}"


@router.post("/ask")
def ask(body: AskBody):
    from concurrent.futures import ThreadPoolExecutor
    key = _cache_key(body.space, body.question)
    if body.live:
        try:
            client().config.authenticate()
            if body.space == "one":
                a = ask_genie_one(body.question)
                return {"answers": [{**a, "sql": None, "columns": [], "rows": [], "live": True}], "explain": [], "live": True}
            space_id = RAW_SPACE if body.space == "raw" else GOV_SPACE
            if not space_id:
                raise RuntimeError("Genie agent not configured (MOTOR_RAW_SPACE / MOTOR_GOVERNED_SPACE)")
            n = max(1, min(3, body.times))
            with ThreadPoolExecutor(n) as ex:
                answers = list(ex.map(lambda _: on.ask_genie(space_id, body.question), range(n)))
            best = next((a["sql"] for a in reversed(answers) if a["rows"]), answers[0]["sql"])
            explain = on.explain_sql(best, body.space == "governed")
            return {"answers": answers, "explain": explain, "live": True}
        except Exception as e:
            fallback = _cache().get(key)
            if fallback:
                return {**fallback, "live": False, "note": f"Live call failed ({type(e).__name__}); showing the last verified answer."}
            raise HTTPException(502, f"Assistant unavailable: {e}")
    fallback = _cache().get(key)
    if not fallback:
        raise HTTPException(404, "No saved answer for this question.")
    return {**fallback, "live": False, "note": "Saved answer from a verified earlier run."}


@router.post("/reset")
def reset():
    """Republish the metric view and the governed agent from the approved rulebook (run before each room)."""
    publish()
    return state()
