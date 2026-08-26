# Pricing gen2 → Data Core — deep-conform migration plan

*Bringing pricing workbench gen2 into the serverless Data Core as the **first**
migrated workbench, under the **deep-conform** binding: pricing's policy / claim /
premium become base-ontology entities, and the pricing book is **generated from the
governed model at scale** — one source of truth, not an imported island. Plan for
review before build — like `docs/REPORTING_WORKBENCH_PLAN.md` and `docs/APP_PLAN.md`.*

---

## The decision, in one line

Pricing gen2 stops being a separate data estate. Its canonical rows are **generated
from the governed model** — the same YAML specs that produce the 172-policy narrative
book now also produce a 50k-motor **statistical** book — so a claim recorded on the
interactive spine flows into pricing's loss experience **by construction**, because
pricing's loss cost is a *view* over governed `claim_transaction`, not a stored table.

That is the whole reason to pay the deep-conform cost: interactivity, reconciliation
and governance are not wired per-workbench — they fall out of sharing the layer.

## Why deep-conform (and not the lighter options)

We considered three bindings; the user chose the heaviest deliberately.

- **Reference-only** (pricing keeps its data, links to the ontology): cheapest, but
  pricing stays an island — a spine claim never reaches it, and we'd maintain two
  policy tables. Rejected.
- **Bridge** (governed hero policies + a separate pricing mass, joined by a bridge
  table): interactive on the heroes only; two sources of "policy" still exist.
- **Deep-conform** (chosen): pricing's policy / claim / premium **are** base entities;
  the mass is generated from the model. One source of truth, cleanest end state,
  fully interactive — and the most work.

## The core tension this plan must resolve

The base layer and pricing gen2 are **two different data species**:

| | Base Data Core (today) | Pricing gen2 (today) |
|---|---|---|
| Purpose | Governed golden-thread narrative | Statistical modelling mass |
| Motor policies | 45 | 50,000 |
| Motor claims | 32 | 25,272 |
| GLM training frame | — | 500,000 rows (`unified_pricing_table`) |
| Quotes | narrative | 1,200,000 |
| Design goal | *every row tells a governed story* | *the aggregate fits a credible GLM* |

Deep-conform reconciles them by making the **generator** do both jobs: the same
model produces a small **narrative subset** (the hero policies you can point at in a
demo) embedded inside a large **statistical population** (the mass the GLMs learn
from). One generator, one ontology, two readouts.

**This is the make-or-break.** A governed generator that emits 50k policies where a
frequency GLM still recovers sensible factor effects and the demand model sees a
genuine price→conversion signal is materially harder than the narrative generator we
have. If the generated book is statistically flat, the pricing models look fake to an
actuary. **Phase 0 exists to prove this before we commit to the full build.**

---

## Six workstreams

### 1. Extend the ontology with pricing's canonical entities (model-as-code)

The base model already carries `policy`, `vehicle`, `coverage`, `premium_transaction`,
`quote`, `underwriting_decision`. Deep-conform adds pricing's canonical objects as
governed entities, in new `model/` domains, so they're first-class in the Atlas,
lineage and governance surfaces:

- **`pricing` domain** — `rating_factor`, `rating_engine_config`, `derived_factors`,
  `feature_catalog` (the rating structure), plus the pricing payload shape on the
  existing `quote` entity (rated premium, factor contributions, model version).
- **`enrichment` domain** — the six external inputs pricing joins to a policy:
  `motor_telematics_aggregate`, `credit_bureau`, `geospatial_hazard`,
  `postcode_enrichment`, `market_pricing_benchmark`, `policy_demographics`. Each keyed
  to the governed `policy` / `party`, each carrying classification (telematics/credit
  are `confidential`/PII — this must be modelled, not incidental) and ACORD/CDR refs
  where they exist.

Deliverable: YAML specs → `tools/generate.py` emits DDL, ontology JSON, docs, and the
entities appear in the Atlas with owner/certification like every other entity.

### 2. Scale the generator — *the crux*

Extend `tools/world_engine.py` with a **pricing-book mode** (behind the existing
`--scale`-style knob) that generates a statistically-designed motor portfolio:

- **Designed structure, not noise.** Frequency driven by real factor relationships
  (age, vehicle group, mileage, telematics score, geography); severity from a credible
  distribution; price→conversion elasticity so the demand model has signal. The factor
  effects are chosen so a GLM *recovers* them — that's the acceptance test.
- **Narrative subset embedded in the mass.** The hero/golden-thread policies remain the
  governed story (and stay the ones the spine writes to); they're a labelled subset of
  the population, not a separate table.
- **Deterministic + reproducible** (seeded), same as today, so the book rebuilds
  identically and the demo is stable.
- **Volume target:** ~50k motor policies / ~25k claims / ~1.2M quotes, generated —
  never imported.

Build-order gotcha stays: **generate → world_engine → deploy**.

### 3. Make the GLM training frame a derived view

`unified_pricing_table` (500k rows today) becomes a **generated view / materialization**
over governed `policy` + `claim`/`claim_transaction` + the enrichment domain — not a
stored island. Consequences:

- It's reproducible from the model (no orphaned training data).
- A new governed claim flows into it → the training frame and monitoring move with the
  estate. This is what makes pricing *interactive*.

### 4. Retrain / re-register the 15 models on the governed data

Because the training data changes, the models must be **retrained**, not copied:

- Freq / severity GLMs, demand & fraud GBMs, elasticity, the `pwg2` scorers, and the
  chat + governance agents.
- Register in serverless UC; recreate serving endpoints (FMAPI-served where LLM-backed,
  per the model-agnostic pattern already in the Atlas Model dial).
- **Acceptance gate:** the retrained freq GLM recovers the factor effects the generator
  designed in (Phase 0 proves this on one model first).

### 5. Migrate the compute that stays pricing-side

Move to serverless and repoint at governed inputs:

- The **24-table optimisation module** (pricing-run outputs — stay pricing-side, consume
  governed inputs).
- Model factory, governance packs, quotes, the **6 volumes**.
- The **pricing gen2 app** → deployed to serverless, or folded in as an Atlas workbench
  view (`#/pricing`) in the house style like reserving/underwriting/reinsurance — to be
  decided at Phase 4.

### 6. The interactive bridge — free, by construction

Because pricing's claims **are** governed `claim_transaction` rows and its loss cost is a
view, recording a large claim on a hero motor policy via the existing spine
(`app/backend/claim_events.py`) automatically moves pricing's loss experience, loss-cost
monitoring and re-price signal — with **no** pricing-specific write path. Verify this
end-to-end as the closing beat: *one claim → claims, reserving, finance, reinsurance
**and** pricing loss cost, all at once.*

Note: the spine currently grants the app SP `MODIFY` on `bricksurance_claim` +
`bricksurance_finance`. Pricing adds read surface (enrichment/pricing schemas) but the
write path is unchanged — pricing reacts, it isn't written to directly.

---

## Sequencing (phase gates)

| Phase | Goal | Gate to proceed |
|---|---|---|
| **0 — De-risk** | Prototype the scaled governed motor generator; fit **one** freq GLM; confirm factors recover + demand signal is real | GLM recovers designed factors → commit to full build. **If flat, stop and rethink binding.** |
| **1 — Ontology** | `pricing` + `enrichment` domains as model-as-code; entities live in Atlas | `generate.py` clean; entities visible w/ owner/certification |
| **2 — Data** | Generate the conformed book at scale; GLM frame as a view | Volumes hit; view reconciles to governed claims |
| **3 — Models** | Retrain + re-register all 15; serving endpoints | Acceptance metrics ≈ current gen2; endpoints live |
| **4 — App + rest** | Optimisation, volumes, pricing app/view to serverless | Pricing surface works on serverless |
| **5 — Interactive + verify** | Prove a spine claim ripples into pricing loss cost | Live demo: one claim → 5 domains incl. pricing |

**Phase 0 is a hard gate** — it's cheap relative to the full migration and it retires
the only risk that can sink deep-conform.

## What we are NOT doing

- **Not importing** the 500k/1.2M pricing rows — they're generated. Copying them would
  recreate the island we're dissolving.
- **Not collapsing** pricing onto the 172 base rows — the mass is generated *around* the
  narrative subset, not squeezed into it.
- **Not migrating** until Phase 0 passes and the plan is approved (per "no migration yet").

## Cost & guardrails

- Serverless-only, scale-to-zero (per standing cost rule); generation is batch, not
  always-on.
- Every pricing surface keeps the **"About this demo"** synthetic-data disclaimer and
  page explainers.
- Claude via FMAPI for any LLM-backed model/agent; models registered in UC.
- Classification modelled on telematics/credit/demographics (PII/confidential) — not an
  afterthought, since deep-conform makes these governed entities.

## Open questions for you

1. **Pricing app**: standalone Databricks App on serverless, or a `#/pricing` workbench
   view inside the Atlas (house style)? (Recommend the Atlas view — consistent with the
   consolidation thesis.)
2. **Scope of the generated mass**: motor only for v1 (cleanest GLM story), or motor +
   home from the start?
3. **Phase 0 first?** I recommend building Phase 0 as a spike before anything else, since
   it's the one thing that can invalidate the approach.
