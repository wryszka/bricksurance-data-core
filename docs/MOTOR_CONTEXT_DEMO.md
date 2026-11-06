# "Why has our motor loss ratio deteriorated?" — the ACORD base + enterprise mapping + Genie Ontology demo

> Audience: insurance executives, architects and actuaries; 12–15 minutes. Second
> chapter of the context demo in the Data Core Console, beside One Number.
> Bricksurance SE is fictional; all data is synthetic. Spec: `specs/SPEC_MOTOR_CONTEXT_DEMO.md`.

## The message in one paragraph

You do not have to teach an AI insurance from scratch. Start from industry knowledge that
already exists (an open, ACORD-aligned base model), connect it to your own systems and
definitions (a mapping and a signed rulebook, governed in the catalog), and let the
platform learn the rest from how your people work (the automatic context layer). Then an
executive can ask a real question, get a quantified answer, drill into the drivers and
trace every number back to data.

## The track (6 beats, ~12 minutes)

| # | Beat | What is on screen | One line to say |
|---|---|---|---|
| 1 | The question | The CUO's question; three systems, three vocabularies for the same policy | "Every number is in there. Nothing says what any of it means." |
| 2 | AI without context | Raw agent asked three times; what it actually added up | "A confident guess is worse than no answer." |
| 3 | The answer | 64.0% → 72.0%, +8.0 pts; segment table; attribution bars; the governed agent's narrative | "Urban private and commercial motor are ~90% of it." |
| 4 | Drill down | Regions, frequency vs severity, large losses; three live follow-ups | "Every driver is a question, answered from data." |
| 5 | Two numbers, two questions | Approved loss ratio vs legacy claims-ops ratio | "Both right. Only one is the loss ratio. Someone has to sign it." |
| 6 | How it got there | Three layers; the crosswalk; native / ours / simulated | "Industry knowledge, your knowledge, discovered knowledge." |

Every beat has "What am I seeing / why it matters" and an "About this demo" disclaimer.
Product names stay under Explore.

## The numbers (deterministic, reproduced to the penny through SQL)

| Segment | Q2 EP | Q2 incurred | Q3 EP | Q3 incurred | LR Q2 | LR Q3 | Share of deterioration |
|---|---:|---:|---:|---:|---:|---:|---:|
| Urban private motor | 35.00 | 25.20 | 37.00 | 31.82 | 72.0% | 86.0% | 62% |
| Other private motor | 40.00 | 22.00 | 42.00 | 23.94 | 55.0% | 57.0% | 10% |
| Commercial motor | 25.00 | 16.80 | 26.00 | 19.84 | 67.2% | 76.3% | 28% |
| Total | 100.00 | 64.00 | 105.00 | 75.60 | 64.0% | 72.0% | |

GBP millions. Incurred = paid + outstanding case reserves + IBNR − recoveries (rulebook v1,
earned basis). Attribution holds each segment's Q3 earned premium and compares actual Q3
incurred with Q2 loss ratio × Q3 earned premium: +5.18m / +0.84m / +2.37m.

Evidence carried by the data (from `tools/motor_book.py`, seed 20261106):

| Driver | Q2 → Q3 |
|---|---|
| Urban theft frequency (claims per 100 vehicle-years) | 1.91 → 2.60 |
| Urban theft severity (avg net cost) | £7.8k → £9.2k |
| Urban theft, metro regions (London, West Midlands, Greater Manchester) | £4.0m → £7.6m incurred |
| Vehicle repair average cost, urban / other private | £2.6k → £2.9k / £2.0k → £2.3k |
| Commercial bodily-injury large losses (≥ £500k) | 3 claims £2.1m → 4 claims £3.2m |
| Overall frequency, urban private | 13.5 → 14.3 per 100 vehicle-years |

The Q3 excess over Q2 cost levels is allocated to exactly these drivers in the generator
(urban: theft 50%, repair 38%; commercial: large bodily injury 65%), so the headline and
the evidence are mechanically the same thing.

## Architecture (what sits where)

```
A. INDUSTRY BASE (open, ours)         B. ENTERPRISE SEMANTICS (the insurer's)        C. INFERRED (native, automatic)
bricksurance-data-core model-as-code  model/mappings/*.yaml  ->  generator  ->       Genie Ontology snippets from
Policy, Coverage, Insured Object,       comments + tags on source columns              dashboards, saved queries,
Vehicle, Party, Claim, Claim Txn,       conformed views (core names, core comments)    metric views, Genie agents;
Premium Txn, Premium Earning            motor_loss_ratio_components view               authority-ranked, permission-
ontology JSON, round-trip verified      motor_performance_metrics (metric view,        gated, cited in answers.
                                        published from the APPROVED rulebook)          Not authored, not exported.
                                        rulebook semantics.loss_ratio_definition
                                        governed Genie agent (instructions generated)
                                        certification tags
                                                       |
                                 CONSUMPTION: Genie Agent (curated), Genie One (workspace-wide), Genie Code
```

### The three source systems

| Schema | System | Tables | Its words |
|---|---|---|---|
| `bricksurance_src_pas` | Policy administration (PAS_MOTOR) | pol_master, pol_vehicle, pol_cover, pol_premium_txn | contract_reference, product_cd PMU/PMO/CMV, cover_start_dt, annual_prem_amt |
| `bricksurance_src_claims` | Claims management (CLM_MOTOR) | clm_header, clm_movement | claim_ref, policy_no, peril_cd, head_of_damage, movement_type PAID/RESERVE/RECOVERY/FEE |
| `bricksurance_src_actuarial` | Actuarial warehouse (ACT_DW) | earned_premium_monthly, ibnr_estimate, segment_dim, postcode_region_dim | pol_ref, yyyymm, ep_amt, veh_years, acc_qtr |

### The mapping mechanism (reusable)

`kind: mapping` specs (`model/mappings/pas_motor.yaml`, `clm_motor.yaml`, `actuarial_motor.yaml`)
map source columns to core attributes with optional `expr` / `value_map`, keep insurer-specific
columns as `extensions`, and let a table override the conformed SQL when the shape differs
(the policy system's one cover code becomes two coverage rows; the claims system's payments
gain the core's reserve-release convention). The generator emits:

- `build/databricks/mappings/50_mapping_<name>.sql`: schema, source table/column comments
  ("Maps to claim.claim_number (ACORD ClaimNumber): ..."), `bxc_concept` tags, conformed
  views in `bricksurance_semantics` with core column comments, view tags.
- `build/docs/mapping_catalog.md`: the crosswalk (one row per core attribute, one column
  per system) plus the extensions. This is Page-ready content for Unity Catalog Pages.
- `build/genie/vocabulary_<name>.md`: the same, as Genie instructions.
- The ontology JSON carries the mappings (platform-neutral, round-trip verified).

Two semantic specs sit after the mappings: `semantics/motor_loss_ratio_components` (view,
`after_mappings: true`) and `semantics/motor_performance_metrics` (metric view,
`published_by: rulebook`). The Console republishes the metric view from the approved
rulebook version, so approving a rule change in One Number changes the motor number too:
one rulebook, every line.

### Genie

- Raw agent "Motor — AI with no context": the ten source tables, no instructions.
- Governed agent "Motor — AI with the mapped, governed layer": metric view, components,
  rulebook, conformed views; instructions generated from the approved definition and the
  mapping vocabulary; six benchmark questions with SQL.
- Genie One (workspace-wide, ontology-grounded) as a third arm under Explore on beat 5,
  showing which sources it cites. We report what it does, not what we hope.

### What is native, ours, simulated

| Capability | Nature |
|---|---|
| Metric views, comments, tags, certification tags, FK constraints, Genie agents + API, dashboards | Native |
| Genie Ontology inferred snippets and citations | Native, automatic; we seed sources and observe |
| Genie One API | Native, preview; used if enabled in the workspace |
| Pages, Domains | Native, account-level previews not enabled here; the crosswalk is the ready content |
| Model-as-code, mapping spec kind, generator, rulebook with maker/checker, republish-on-approval | Ours, open source |
| Motor experience book | Synthetic, deterministic, labelled; not posted to the group ledger |

## Running it

Build order (local): `tools/generate.py` → `tools/world_engine.py` → `tools/motor_book.py`.
Workspace: `tools/motor_load.py` (schemas, volumes, tables, mappings, components, grants,
penny smoke) → `tools/motor_setup.py --create-spaces` (ids into `app/app.yaml`) → deploy the
Console → `POST /api/motor/reset` (the app must own the metric view) → `motor_setup.py --acceptance`.

Before a room: open `#/motor`, beat 6 → Explore → Reset; ask once on beat 3 to warm the
warehouse. Run the motor chapter BEFORE the One Number rule change, or reset One Number
after: both read the same rulebook.

## Status

- 2026-11-06: data generator, mapping spec kind, three mappings, semantic specs, backend
  (`app/backend/motor.py`), frontend (`MotorView.tsx`), loader and setup CLI built and
  verified locally (targets exact, frontend builds, ontology round-trip OK, v0.17.0).
  Workspace steps pending re-authentication of the serverless profile.
- Pending: load + smoke on serverless, Genie agents, Genie One preview check, snippet
  seeding (certified motor dashboard + legacy claims-ops query), app deploy, acceptance
  run, saved answers, second-insurer mapping (Harbour Mutual), Google Doc mirror,
  Console Documents panel + hub tile.
