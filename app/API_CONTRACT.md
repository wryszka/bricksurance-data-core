# Data Core Atlas — frozen backend API contract

The backend (`app/backend/main.py` + `app/backend/atlas.py`) is DONE and tested.
Do not change it. Build the frontend against exactly these endpoints. All Atlas
endpoints read the bundled ontology (instant, no warehouse). Only `/api/atlas/prove/*`,
`/api/atlas/genie-health`, `/api/metrics`, and the `/api/exchange/*` + `/api/network`
endpoints touch the warehouse.

## Atlas endpoints (new — the heart of the app)

### `GET /api/atlas/meta`
```
{ name, title, version, standards_basis,
  counts: { domains, entities, code_sets, metric_views, functions, relationships },
  domains: [ {name, description}, ... ],
  provenance: { version, source } }
```

### `GET /api/atlas/search?q=<term>&limit=30`
```
{ query, roadmap: null | { term, note },
  results: [ { kind, name, title, domain, score, summary,
               // metric only: owner, certification, measure_names[]
               // entity only: owner, certification } ] }
```
`kind` ∈ `metric | entity | code_set | function | view`. Ranked, synonym-aware
(GWP, incurred, BEL, SCR, combined ratio…). `roadmap` is set for known-but-absent
terms (e.g. "combined ratio") — show it as an honest "on the roadmap" note.

### `GET /api/atlas/metric/{name}`  (the money screen)
```
{ name, title, domain, description, owner, certification, source,
  joins: [{name, source, condition}],
  dimensions: [{name, expr, description}],
  measures: [{name, expr, description}],       // expr = the exact SQL formula
  feeds_from: [{ref, role, entity, exists, join_name?}],  // clickable source tables
  genie_question, genie_space_url }
```

### `GET /api/atlas/entity/{name}`
```
{ name, title, domain, description, grain, owner, standards, tags:{maturity},
  attributes: [{name, type, required, description, classification, standards?}],
  keys: {primary[], natural?},
  quality: [{name, rule, description}],
  references: [{attribute, to, to_kind}],       // this entity's FKs (clickable)
  referenced_by: [{from, attribute}] }           // entities pointing here
```

### `GET /api/atlas/code_set/{name}`  → `{ name, title, description, codes:[{code,label,description}] }`
### `GET /api/atlas/function/{name}` → `{ name, title, domain, description, inputs, returns, sql }`

### `GET /api/atlas/lineage/{kind}/{name}?depth=1`  (focused subgraph)
`kind` ∈ `metric | entity | code_set`.
```
{ center: "kind:name",
  nodes: [{id:"entity:claim", kind, name, label, domain, certification?, owner?}],
  edges: [{source:"<id>", target:"<id>", label}] }
```
NEVER render all 195 edges. This returns only the focused neighbourhood; `depth`
adds one hop. Node id format is `"<kind>:<name>"`.

### `GET /api/atlas/golden-thread`  (saved one-click demo path)
Same shape as lineage plus `narrative`. Nodes = policy, coverage,
premium_transaction, claim, claim_transaction, cession, treaty, treaty_layer,
submission (the DEMOS.md golden thread).

### `GET /api/atlas/governance`
```
{ entities: {total, certified, draft, with_owner, with_standards, with_quality},
  metrics: {total, certified, draft, with_owner},
  attributes: {total, classification:{internal, confidential, pii, unassessed?}, unassessed},
  ownership_board: [{owner, count, elements:[{name, domain, certification}]}],
  attestations: [{element, element_kind, certification, owner, attested_by, attested_on, evidence}] }
```
Show the HONEST numbers (12/52 certified, etc.) with completeness gauges. Never
imply 52/52.

### `GET /api/atlas/regulatory/{regime}`  (`solvency_ii | ifrs_17 | gdpr`)
```
{ regime, title, blurb, consumed_by,
  resolved: [{kind, name, title, domain, owner?, certification?}] }
```

### `GET /api/atlas/prove/{name}`  (live number-proving)
```
{ metric, ok, error, sql,
  measures: [{name, value, formula}],
  genie_question, genie_space_url }
```
If `ok:false` (cold warehouse), show `sql` + `error` gracefully — the SQL is the
inline fallback so a cold workspace is never an on-stage 404.

### `GET /api/atlas/genie-health`  → `{ warehouse:"warm"|"cold", genie_space_url, ready, detail? }`

## Governance record layer (capture-only — the "propose a change" loop)

### `GET /api/atlas/governance/actions` → `{ actions: [ {action_id, action_type:"proposal"|"issue", element, element_kind, field, current_value, proposed_value, rationale, raised_by, raised_on, status, spec_diff} ], error? }`

### `POST /api/atlas/governance/propose`
Body: `{ element, element_kind:"entity"|"metric"|"attribute", field, proposed_value, rationale, raised_by, current_value }`
Returns: `{ action_id, status:"open", spec_diff, note }` — `spec_diff` is a
generated stub of the change to make in the source YAML (NOT applied). Show it
back to the user with a copy button and the note that the model is unchanged
until taken through the evolution contract.

### `POST /api/atlas/governance/issue`
Body: `{ element, element_kind, rationale, raised_by }` → `{ action_id, status:"open" }`

On the **Governance** view: add a "Propose a change" form (element + field +
proposed value + rationale) and show the returned `spec_diff`; list existing
actions from `/api/atlas/governance/actions` in a dated table. This is
capture-only — make clear in the UI that the model truth stays in the specs and
nothing is auto-applied. If the actions endpoint returns `error` (cold
warehouse), degrade gracefully — the capture form can still be shown.

## Kept endpoints (existing, still used by Exchange/Network)
`GET /api/metrics?currency=GBP&underwriting_year=` · `GET /api/exchange/outbound`
· `GET /api/exchange/sample` · `POST /api/exchange/map` · `POST /api/exchange/load`
· `GET /api/network` · `GET /api/health`
See the existing `app/frontend/src/api.ts` for their types (keep those working).
