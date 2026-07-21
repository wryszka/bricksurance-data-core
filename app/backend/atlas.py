"""Data Core Atlas — the ontology intelligence layer.

Loads the bundled, self-describing ontology JSON once at startup and serves it
as a searchable knowledge graph: search, entity/metric detail, focused lineage
subgraphs, and governance rollups. All of this is warehouse-free — instant and
resilient — because the ontology travels with the app. The warehouse is touched
only to *prove numbers live* (see prove_metric in main.py) and Genie only for
the "ask it" loop.

Design notes:
- Search returns a ranked, mixed result set (metric / entity / term / code_set /
  function / domain), insurance-synonym-aware.
- Lineage is always a FOCUSED subgraph (a node + its neighbours, one hop at a
  time) — never the whole 195-edge graph.
- Governance rollups surface the HONEST state: owners, certification counts,
  classification coverage with an explicit unassessed count.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "ontology.json"

# Insurance vocabulary → the canonical model term(s) a user probably means.
# An actuary types "GWP" or "incurred"; a CFO types "combined ratio". These
# map colloquial/abbreviated terms onto the names that actually exist in the
# model so search feels like it speaks insurance.
SYNONYMS = {
    "gwp": ["gross_written_premium", "gross written premium", "premium"],
    "gross written premium": ["gross_written_premium"],
    "nep": ["net_earned_premium", "earned premium"],
    "loss ratio": ["loss_ratio", "performance_metrics", "loss_ratio_written", "underwriting_metrics"],
    "combined ratio": ["combined_ratio", "performance_metrics"],
    "expense ratio": ["expense_ratio", "performance_metrics"],
    "earned premium": ["earned_premium", "performance_metrics"],
    "incurred": ["claims_incurred", "incurred", "claim_transaction"],
    "outstanding": ["outstanding_reserve", "reserve"],
    "reserve": ["outstanding_reserve", "claim_transaction"],
    "bel": ["valuation_metrics", "best estimate liability", "valuation_result"],
    "best estimate liability": ["valuation_metrics", "valuation_result"],
    "scr": ["valuation_metrics", "solvency capital requirement", "valuation_result"],
    "mcr": ["valuation_metrics", "valuation_result"],
    "csm": ["csm_movement", "valuation_metrics", "contractual service margin"],
    "technical provisions": ["valuation_metrics", "valuation_result"],
    "ceded": ["cession_metrics", "cession", "ceded_premium"],
    "cession": ["cession_metrics", "cession"],
    "reinsurance": ["cession_metrics", "treaty", "cession", "submission"],
    "solvency": ["valuation_metrics", "valuation_result", "reporting_regime"],
    "solvency ii": ["valuation_metrics", "valuation_result"],
    "ifrs 17": ["csm_movement", "contract_group", "valuation_metrics"],
    "ifrs17": ["csm_movement", "contract_group", "valuation_metrics"],
    "premium": ["premium_transaction", "gross_written_premium"],
    "claim": ["claim", "claim_transaction", "claims_incurred"],
    "policy": ["policy", "coverage"],
    "trial balance": ["trial_balance"],
    "balance sheet": ["financial_position", "investment_holding"],
    "p&l": ["performance_metrics", "financial_position"],
    "pnl": ["performance_metrics"],
    "expense ratio": ["performance_metrics", "expense_transaction"],
    "complaint": ["complaint"],
    "conduct": ["complaint"],
    "fraud": ["fraud_signal"],
    "commission": ["commission_transaction"],
    "broker": ["party", "party_role", "distribution_channel"],
    "pii": ["party", "contact_point"],
    "personal data": ["party", "contact_point", "vehicle"],
    "gdpr": ["data_subject_request", "consent", "party"],
    "dsar": ["data_subject_request"],
}

# Known-but-absent terms — answered honestly rather than with a blank. Keeps
# the actuary's trust: "we don't have that yet, here's why / what's near it".
ROADMAP = {
    "reserving triangle": "On the roadmap — a development-triangle view over claim_transaction.",
    "ecl": "Not modelled — expected credit loss is out of current scope.",
}

# Which model elements serve each regulatory regime, for the regulatory-lineage
# view. Values are entity/metric names that exist in the model.
REGIMES = {
    "solvency_ii": {
        "title": "Solvency II",
        "blurb": "Solo and group technical provisions, SCR/MCR and own funds — reported at legal-entity level.",
        "elements": ["valuation_result", "valuation_metrics", "valuation_run",
                     "legal_entity", "reporting_level", "reporting_regime",
                     "line_of_business", "financial_position"],
        "consumed_by": "Solvency II QRT workbench",
    },
    "ifrs_17": {
        "title": "IFRS 17",
        "blurb": "Groups of contracts, CSM movement and onerous-contract testing — the measurement unit of account.",
        "elements": ["contract_group", "csm_movement", "valuation_result",
                     "valuation_metrics", "measurement_model", "fn_csm_closing"],
        "consumed_by": "IFRS 17 workbench",
    },
    "gdpr": {
        "title": "GDPR",
        "blurb": "Where personal data lives, the lawful basis for it, and the erasure/DSAR machinery.",
        "elements": ["party", "contact_point", "vehicle", "consent",
                     "data_subject_request", "premium_bordereau_line"],
        "consumed_by": "Privacy / DSAR handling",
    },
}


@lru_cache(maxsize=1)
def ontology() -> dict:
    return json.loads(DATA.read_text())


@lru_cache(maxsize=1)
def index() -> dict:
    """Build lookup indexes over the ontology once."""
    o = ontology()
    ent = {e["name"]: e for e in o["entities"]}
    cs = {c["name"]: c for c in o["code_sets"]}
    mv = {m["name"]: m for m in o["metric_views"]}
    vw = {v["name"]: v for v in o.get("views", [])}
    fn = {f["name"]: f for f in o.get("functions", [])}
    # Relationship adjacency (both directions) for lineage.
    out_edges: dict[str, list] = {}
    in_edges: dict[str, list] = {}
    for r in o["relationships"]:
        out_edges.setdefault(r["from_entity"], []).append(r)
        in_edges.setdefault(r["to"], []).append(r)
    # Attribute → measure map: which measures reference which columns (for
    # metric lineage to source columns).
    return {
        "entities": ent, "code_sets": cs, "metric_views": mv,
        "views": vw, "functions": fn,
        "out_edges": out_edges, "in_edges": in_edges,
    }


# --------------------------------------------------------------------------- #
# Search
# --------------------------------------------------------------------------- #
def _score(term: str, name: str, title: str, text: str) -> int:
    """Cheap relevance score; higher is better. 0 = no match."""
    t, n, ti, tx = term.lower(), name.lower(), (title or "").lower(), (text or "").lower()
    if t == n or t == ti:
        return 100
    if n.startswith(t) or ti.startswith(t):
        return 80
    if t in n or t in ti:
        return 60
    # whole-word hit in the description
    if re.search(rf"\b{re.escape(t)}\b", tx):
        return 40
    if t in tx:
        return 20
    return 0


def _expand(term: str) -> list[str]:
    """Term plus any synonym expansions."""
    t = term.lower().strip()
    seeds = {t}
    for key, vals in SYNONYMS.items():
        if key == t or key in t or t in key:
            seeds.update(v.lower() for v in vals)
    return list(seeds)


def search(term: str, limit: int = 30) -> dict:
    if not term or not term.strip():
        return {"query": term, "results": [], "roadmap": None}
    ix = index()
    seeds = _expand(term)
    hits: dict[tuple, dict] = {}

    def consider(kind, name, title, text, domain, extra=None):
        best = max((_score(s, name, title, text) for s in seeds), default=0)
        if best <= 0:
            return
        key = (kind, name)
        if key not in hits or hits[key]["score"] < best:
            hits[key] = {"kind": kind, "name": name, "title": title or name,
                         "domain": domain, "score": best,
                         "summary": " ".join((text or "").split())[:220],
                         **(extra or {})}

    for m in ix["metric_views"].values():
        meas = " ".join(x["name"] + " " + x["description"] for x in m["measures"])
        dims = " ".join(x["name"] for x in m["dimensions"])
        consider("metric", m["name"], m.get("title"),
                 m["description"] + " " + meas + " " + dims, m["domain"],
                 {"owner": m.get("owner"), "certification": m.get("certification"),
                  "measure_names": [x["name"] for x in m["measures"]]})
    for e in ix["entities"].values():
        attrs = " ".join(a["name"] + " " + a.get("description", "") for a in e["attributes"])
        consider("entity", e["name"], e.get("title"),
                 e["description"] + " " + attrs, e["domain"],
                 {"owner": e.get("owner"),
                  "certification": (e.get("tags", {}) or {}).get("maturity")})
    for c in ix["code_sets"].values():
        codes = " ".join(x.get("code", "") + " " + x.get("label", "") for x in c.get("codes", []))
        consider("code_set", c["name"], c.get("title"),
                 c.get("description", "") + " " + codes, "reference")
    for f in ix["functions"].values():
        consider("function", f["name"], f.get("title"),
                 f.get("description", ""), f["domain"])
    for v in ix["views"].values():
        consider("view", v["name"], v.get("title"),
                 v.get("description", ""), v["domain"])

    ranked = sorted(hits.values(), key=lambda h: (-h["score"], h["kind"], h["name"]))[:limit]
    roadmap = None
    for key, msg in ROADMAP.items():
        if key in term.lower() or term.lower() in key:
            roadmap = {"term": term, "note": msg}
            break
    return {"query": term, "results": ranked, "roadmap": roadmap}


# --------------------------------------------------------------------------- #
# Detail
# --------------------------------------------------------------------------- #
def entity_detail(name: str) -> dict | None:
    e = index()["entities"].get(name)
    if not e:
        return None
    rels_out = index()["out_edges"].get(name, [])
    rels_in = index()["in_edges"].get(name, [])
    return {
        **e,
        "references": [{"attribute": r["attribute"], "to": r["to"], "to_kind": r["to_kind"]}
                       for r in rels_out],
        "referenced_by": [{"from": r["from_entity"], "attribute": r["attribute"]}
                          for r in rels_in if r["to_kind"] == "entity"],
    }


def metric_detail(name: str) -> dict | None:
    ix = index()
    m = ix["metric_views"].get(name)
    if not m:
        return None
    # Source + joined tables, each clickable back into the graph.
    src = m["source"]
    tables = [{"ref": src, "role": "source",
               "entity": src.split(".")[-1],
               "exists": src.split(".")[-1] in ix["entities"]}]
    for j in m.get("joins", []):
        jt = j["source"]
        tables.append({"ref": jt, "role": "join", "join_name": j["name"],
                       "entity": jt.split(".")[-1],
                       "exists": jt.split(".")[-1] in ix["entities"]})
    return {**m, "feeds_from": tables}


def code_set_detail(name: str) -> dict | None:
    return index()["code_sets"].get(name)


def function_detail(name: str) -> dict | None:
    return index()["functions"].get(name)


# --------------------------------------------------------------------------- #
# Lineage — focused subgraph, never the whole thing
# --------------------------------------------------------------------------- #
def _node(kind: str, name: str) -> dict:
    ix = index()
    if kind == "metric":
        m = ix["metric_views"].get(name, {})
        return {"id": f"metric:{name}", "kind": "metric", "name": name,
                "label": m.get("title", name), "domain": m.get("domain", "semantics"),
                "certification": m.get("certification"), "owner": m.get("owner")}
    if kind == "code_set":
        c = ix["code_sets"].get(name, {})
        return {"id": f"code_set:{name}", "kind": "code_set", "name": name,
                "label": c.get("title", name), "domain": "reference"}
    e = ix["entities"].get(name, {})
    return {"id": f"entity:{name}", "kind": "entity", "name": name,
            "label": e.get("title", name), "domain": e.get("domain", ""),
            "certification": (e.get("tags", {}) or {}).get("maturity"),
            "owner": e.get("owner")}


def lineage(kind: str, name: str, depth: int = 1) -> dict:
    """A focused subgraph centred on one node, expanded `depth` hops."""
    ix = index()
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(k, n):
        node = _node(k, n)
        nodes[node["id"]] = node
        return node["id"]

    def kind_of(target_name, to_kind):
        return "code_set" if to_kind == "code_set" else "entity"

    if kind == "metric":
        center = add_node("metric", name)
        m = ix["metric_views"].get(name)
        frontier = []
        if m:
            for t in [m["source"]] + [j["source"] for j in m.get("joins", [])]:
                en = t.split(".")[-1]
                tid = add_node("entity" if en in ix["entities"] else "code_set", en)
                edges.append({"source": tid, "target": center, "label": "feeds"})
                frontier.append(en)
    else:
        center_name = name
        add_node(kind if kind == "code_set" else "entity", center_name)
        frontier = [center_name]

    seen = set(frontier)
    for _ in range(max(0, depth)):
        nxt = []
        for ename in frontier:
            src_id = f"entity:{ename}"
            for r in ix["out_edges"].get(ename, []):
                tkind = kind_of(r["to"], r["to_kind"])
                tid = add_node(tkind, r["to"])
                edges.append({"source": src_id, "target": tid, "label": r["attribute"]})
                if r["to"] not in seen and tkind == "entity":
                    seen.add(r["to"]); nxt.append(r["to"])
            for r in ix["in_edges"].get(ename, []):
                if r["to_kind"] != "entity":
                    continue
                fid = add_node("entity", r["from_entity"])
                edges.append({"source": fid, "target": src_id, "label": r["attribute"]})
                if r["from_entity"] not in seen:
                    seen.add(r["from_entity"]); nxt.append(r["from_entity"])
        frontier = nxt

    # De-dup edges
    uniq = {(e["source"], e["target"], e["label"]): e for e in edges}
    return {"center": f"{kind}:{name}", "nodes": list(nodes.values()),
            "edges": list(uniq.values())}


# The golden thread — the exact DEMOS.md narrative path, as a saved one-click
# lineage. policy -> claim -> cession -> treaty -> submission.
GOLDEN_THREAD = ["policy", "coverage", "premium_transaction", "claim",
                 "claim_transaction", "cession", "treaty", "treaty_layer",
                 "submission"]


def golden_thread() -> dict:
    ix = index()
    nodes, edges = {}, []
    for n in GOLDEN_THREAD:
        node = _node("entity", n)
        nodes[node["id"]] = node
    for ename in GOLDEN_THREAD:
        for r in ix["out_edges"].get(ename, []):
            if r["to_kind"] == "entity" and r["to"] in GOLDEN_THREAD:
                edges.append({"source": f"entity:{ename}", "target": f"entity:{r['to']}",
                              "label": r["attribute"]})
    uniq = {(e["source"], e["target"], e["label"]): e for e in edges}
    return {"center": "thread", "nodes": list(nodes.values()),
            "edges": list(uniq.values()),
            "narrative": ("The golden thread: a policy is written, a claim lands "
                          "against it, the loss is ceded under a treaty, and the "
                          "treaty traces to the reinsurance submission — one "
                          "connected story across five domains.")}


# --------------------------------------------------------------------------- #
# Governance rollups — the honest state
# --------------------------------------------------------------------------- #
def governance() -> dict:
    o = ontology()
    ents = o["entities"]
    mvs = o["metric_views"]
    attrs = [a for e in ents for a in e["attributes"]]

    def maturity(e):
        return (e.get("tags", {}) or {}).get("maturity", "draft")

    cls_counts: dict[str, int] = {}
    for a in attrs:
        c = a.get("classification") or "unassessed"
        cls_counts[c] = cls_counts.get(c, 0) + 1

    # Ownership board grouped by owner role.
    owners: dict[str, list] = {}
    for e in ents:
        owners.setdefault(e.get("owner", "unassigned"), []).append(
            {"name": e["name"], "domain": e["domain"], "certification": maturity(e)})

    ent_certified = sum(1 for e in ents if maturity(e) == "certified")
    mv_certified = sum(1 for m in mvs if m.get("certification") == "certified")

    return {
        "entities": {
            "total": len(ents),
            "certified": ent_certified,
            "draft": len(ents) - ent_certified,
            "with_owner": sum(1 for e in ents if e.get("owner")),
            "with_standards": sum(1 for e in ents if e.get("standards")),
            "with_quality": sum(1 for e in ents if e.get("quality")),
        },
        "metrics": {
            "total": len(mvs),
            "certified": mv_certified,
            "draft": len(mvs) - mv_certified,
            "with_owner": sum(1 for m in mvs if m.get("owner")),
        },
        "attributes": {
            "total": len(attrs),
            "classification": cls_counts,
            "unassessed": cls_counts.get("unassessed", 0),
        },
        "ownership_board": [
            {"owner": k, "count": len(v), "elements": sorted(v, key=lambda x: x["name"])}
            for k, v in sorted(owners.items())
        ],
        "attestations": o.get("attestations", []),
    }


def regulatory(regime: str) -> dict | None:
    r = REGIMES.get(regime)
    if not r:
        return None
    ix = index()
    resolved = []
    for name in r["elements"]:
        if name in ix["entities"]:
            e = ix["entities"][name]
            resolved.append({"kind": "entity", "name": name, "title": e.get("title", name),
                             "domain": e["domain"], "owner": e.get("owner"),
                             "certification": (e.get("tags", {}) or {}).get("maturity")})
        elif name in ix["metric_views"]:
            m = ix["metric_views"][name]
            resolved.append({"kind": "metric", "name": name, "title": m.get("title", name),
                             "domain": m["domain"], "owner": m.get("owner"),
                             "certification": m.get("certification")})
        elif name in ix["code_sets"]:
            c = ix["code_sets"][name]
            resolved.append({"kind": "code_set", "name": name,
                             "title": c.get("title", name), "domain": "reference"})
        elif name in ix["functions"]:
            f = ix["functions"][name]
            resolved.append({"kind": "function", "name": name,
                             "title": f.get("title", name), "domain": f["domain"]})
    return {"regime": regime, **r, "resolved": resolved}


def meta() -> dict:
    o = ontology()
    return {
        "name": o["name"], "title": o["title"], "version": o["version"],
        "standards_basis": o["standards_basis"],
        "counts": {
            "domains": len(o["domains"]), "entities": len(o["entities"]),
            "code_sets": len(o["code_sets"]), "metric_views": len(o["metric_views"]),
            "functions": len(o["functions"]), "relationships": len(o["relationships"]),
        },
        "domains": o["domains"],
    }
