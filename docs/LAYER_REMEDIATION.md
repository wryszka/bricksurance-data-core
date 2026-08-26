# Base data layer — remediation spec

*The definitive list of what must be **added** and **changed** in the Bricksurance
Data Core semantic layer so it is robust enough to host the whole workbench family
(pricing, claims, underwriting, reinsurance, reporting) — as first-class, governed
model-as-code, not per-demo patches. Migration of any workbench is downstream of this
and out of scope here. Companion to `docs/APP_PLAN.md`, `docs/REPORTING_WORKBENCH_PLAN.md`,
`docs/PRICING_GEN2_MIGRATION_PLAN.md` (parked).*

Status: **IMPLEMENTED in model v0.10.0** — deployed to serverless, smoke 40/40 pass
(2026-08-26). See the "What shipped" note at the end. The sections below are the spec
that was built to.

---

## 1. Why this document

The semantic layer is the priority; anything migrating onto it is secondary. Today the
layer is broad but has three cross-cutting holes and some depth gaps that would force
each migrating workbench to invent its own private structure — which is exactly the
island problem the Data Core exists to end. This spec closes the holes **in the model**,
so every workbench inherits governed rating / enrichment / ML / claims / underwriting
structure instead of re-modelling it.

## 2. Current state (grounded, 2026-08-26)

| | Count |
|---|---|
| Domains | 18 |
| Entities + derived views (non-fn) | 67 |
| Reference code sets | 52 |
| Functions (`fn_*`) | 9 |
| Semantic metric views | 11 |
| **Certified elements** | **12 entities + 6 metric views = 18** |

Certified entities today: `cession, claim, claim_transaction, coverage, legal_entity,
party, party_role, policy, premium_transaction, submission, treaty, treaty_layer`.
Certified metric views: `cession_metrics, financial_position, performance_metrics,
trial_balance, underwriting_metrics, valuation_metrics`. **Everything else is `draft`.**

## 3. Principles every addition must respect

- **Model-as-code.** New objects are YAML in `model/<domain>/`, compiled by
  `tools/generate.py`. No hand-written DDL.
- **Derived-never-stored.** Anything that can be recomputed (scores-in-aggregate, loss
  cost, exposure) is a metric view or function over transactions — not a stored balance.
- **Classification is mandatory.** Every attribute carries `classification`
  (`internal` / `confidential` / `pii`). Enrichment and ML data is classification-heavy
  and must be modelled that way, not incidentally.
- **Standards refs where they exist** (`standards: {acord, lloyds_cdr}`).
- **Single schema per domain, numbered tables** on generation; one catalog, portable.
- **Certification via `model/governance/attestations.json`** — an element is certified
  only if attested there, with owner + dated evidence.
- **Every new entity gets an owner** (a role, never a person).

---

## PART A — New domains & entities to ADD

### A1. `enrichment` domain — external risk & rating inputs *(unblocks pricing + underwriting)*

The biggest reuse win: pricing and underwriting both need external attributes keyed to a
governed `policy` / `party` / `insured_object`. One domain serves both. All PII/confidential.

| New entity | Grain | Key attributes | Classification |
|---|---|---|---|
| `motor_telematics_aggregate` | one row per policy per period | policy_id, period, mileage_band, harsh_braking_rate, night_driving_pct, telematics_score | confidential |
| `credit_bureau_summary` | one row per party per pull | party_id, pull_date, credit_score_band, ccj_count, electoral_roll_flag | **pii** |
| `geospatial_hazard` | one row per postcode/location | location_key, flood_band, subsidence_band, crime_index, coastal_flag | internal |
| `postcode_enrichment` | one row per postcode | postcode, urbanity, deprivation_decile, region_code | internal |
| `market_pricing_benchmark` | one row per LOB/segment/period | line_of_business_code, segment, period, market_median_premium, rank_percentile | confidential |
| `policy_demographics` | one row per policy | policy_id, age_band, tenure_band, prior_claims_band, occupation_class | **pii** |
| `sanctions_screen` | one row per party per screen | party_id, screen_date, ofsi_hit_flag, pep_flag, list_source | **pii** |

New code sets: `flood_band`, `subsidence_band`, `credit_score_band`, `urbanity`,
`hazard_source`, `mileage_band`, `sanctions_list`.

New semantic view: `enrichment_coverage` (share of policies with each enrichment source
present — a data-quality/completeness readout the governance page can surface).

### A2. `model` domain — ML / model-governance semantics *(the robustness gap; serves the whole estate)*

Today only `fraud_signal` (a single output flag) represents ML. The layer has **no**
concept of a model, its versions, its features, its scores or its monitoring — yet fraud,
triage, pricing GLMs, demand and elasticity all produce governed scores. This is the
conspicuous hole for a Databricks semantic layer, and deep-conform pricing cannot land
without it.

| New entity | Grain | Key attributes |
|---|---|---|
| `model_asset` | one row per registered model | model_id, name, model_type_code, purpose, owner, uc_registered_name, current_version |
| `model_version` | one row per version | model_version_id, model_id, version, trained_on, training_frame_ref, metrics_json, status_code (champion/challenger/retired) |
| `feature_definition` | one row per feature | feature_id, name, source_entity, expr_or_source, classification, pii_flag |
| `feature_set` | one row per set | feature_set_id, name, purpose, feature_ids[] |
| `model_score` | one row per scored subject per run | model_score_id, model_version_id, subject_kind (policy/claim/quote), subject_id, score, scored_at, source_system_code |
| `model_monitor_metric` | one row per model/metric/period | model_version_id, metric_code (auc/gini/psi/drift), period, value |

New code sets: `model_type` (glm/gbm/llm/rules), `model_status` (champion/challenger/retired/shadow),
`model_purpose` (pricing_frequency/pricing_severity/demand/fraud/triage/narration),
`monitor_metric_type`.

New function: `fn_champion_score(subject_kind, subject_id)` — latest champion score for a
subject, derived live (never a stored balance).

New semantic view: `model_governance_metrics` (models by status, features by
classification, monitoring freshness) — feeds the Atlas governance surface with an
AI-governance readout.

**Decision to confirm:** keep `fraud_signal` as-is (a business-facing indicator) and let
it become a *consumer* of `model_score`, rather than folding it in. Recommended — the
indicator has a distinct business meaning (SIU referral) from a raw score.

### A3. `pricing` domain — rating structure *(pricing-specific, foundational)*

| New entity | Grain | Key attributes |
|---|---|---|
| `rating_factor` | one row per factor per LOB | rating_factor_id, line_of_business_code, name, factor_kind (base/multiplicative/additive), classification |
| `rating_factor_level` | one row per factor level | rating_factor_id, level_code, relativity, effective_from, effective_to |
| `rating_engine_config` | one row per engine version | config_id, line_of_business_code, version, base_rate, model_version_id (→ A2), effective_from |
| `derived_factor` | one row per policy/quote per factor | subject_kind, subject_id, rating_factor_id, level_code, contribution |
| `feature_catalog_entry` | maps rating inputs → `feature_definition` (A2) | rating_factor_id, feature_id |

New code sets: `rating_factor_kind`.

New semantic view: `pricing_metrics` (rated premium, factor contribution, conversion by
segment) over quotes + derived factors — the readout the pricing workbench renders.

### A4. Claims depth *(medium — to host the CDA claims workbench)*

Today: `claim` + `claim_transaction` + `fraud_signal` only. Add reserve/recovery grain:

| New entity | Grain | Key attributes |
|---|---|---|
| `claim_feature` | one row per feature (head of damage) per claim | claim_feature_id, claim_id, feature_type_code, coverage_id, status_code |
| `claim_reserve_category` | reserve split | claim_feature_id, category_code (indemnity/expense/legal), amount, as_of |
| `recovery` | one row per recovery | recovery_id, claim_id, recovery_type_code (subrogation/salvage/contribution/reinsurance), amount, status |
| `litigation` | one row per suit | litigation_id, claim_id, status_code, jurisdiction, reserve_legal |
| `claim_party_role` | handler / adjuster / TP on a claim | claim_id, party_id, role_code |

New code sets: `claim_feature_type`, `reserve_category`, `recovery_type`,
`litigation_status`, `claim_party_role_type`.

(Reserve movements still flow through `claim_transaction`; these entities add the
*dimensional* grain the claims workbench needs, not a parallel financial store.)

### A5. Underwriting depth *(medium)*

| New entity | Grain | Key attributes |
|---|---|---|
| `uw_submission` | one row per submission (pre-quote) | uw_submission_id, party_id, line_of_business_code, received_date, status_code, channel |
| `referral_rule` | **SCD2** rulebook | referral_rule_id, name, condition_expr, action_code, version, effective_from, effective_to, is_current |
| `referral_event` | one row per fired referral | referral_event_id, subject_kind, subject_id, referral_rule_id, fired_at, outcome_code |

New code sets: `uw_submission_status`, `referral_action`, `referral_outcome`.

Note: `referral_rule` is the layer's first **SCD2** entity — `generate.py` must support a
`scd: type_2` flag (effective_from/to + is_current). This is a genuine generator change,
flagged in Part C.

### A6. Reinsurance accumulation & capital *(medium-low; may be measure-only)*

| Add | Form |
|---|---|
| Exposure accumulation by peril/zone | **semantic view** `accumulation_metrics` over `event_loss` + `cession` (derived, not stored) |
| Capital allocation by LOB/entity | new entity `capital_allocation` *only if* the reinsurance/reporting workbench needs entity-grain; otherwise a measure in `valuation_metrics` |

### A7. Solvency II structure *(low — decide entity vs measure)*

SCR risk-module breakdown and own-funds tiering are likely representable as **measures**
in `valuation_result` / `valuation_metrics` (measure codes, per the IFRS17 pattern) rather
than new entities. **Recommendation:** keep as measures; add `scr_risk_module` and
`own_funds_tier` code sets + measures, not tables, unless the reporting workbench proves it
needs the grain.

---

## PART B — CHANGES to existing entities

| Entity | Change | Why |
|---|---|---|
| `policy/quote` | Add: `rated_gross_premium`, `rating_engine_config_id` (→A3), `model_version_id` (→A2), `conversion_flag`. Promote `maturity: draft` → certified once attested. | Quote is the pricing payload carrier; today it has quoted premium only, no rating provenance. |
| `claim/claim` | Add: `handling_office`, `catastrophe_id` (→ reinsurance `cat_event`, nullable), `reopened_flag`. | CDA claims + cat linkage; ties a claim to an accumulation event. |
| `claim/fraud_signal` | Add: `model_version_id` (→A2) so a signal cites the model that raised it; keep business meaning. | Makes fraud auditable to a governed model version. |
| `policy/vehicle` | Add: `telematics_enrolled_flag`, `vehicle_group`, `abi_code`. | Rating needs vehicle group; telematics link to A1. |
| `policy/insured_object` | Add: `location_key` (→ A1 `geospatial_hazard`). | Lets property risk join hazard enrichment. |
| `party/party` | Confirm `party_id` is the stable join key for A1 credit/sanctions/demographics. | Enrichment keys to party; no schema change if already stable. |
| `semantics/underwriting_metrics` & peers | Add pricing/enrichment-aware dimensions where sensible (segment, telematics band) **without** breaking existing measures. | Keep the certified measures stable; extend dimensions only. |

---

## PART C — Generator & tooling changes (`tools/`)

1. **SCD2 support** in `generate.py` — a `scd: type_2` entity flag emitting
   effective_from/effective_to/is_current + the current-view. Needed by A5 `referral_rule`;
   reusable for `rating_factor_level`.
2. **`world_engine.py`** — generate the new domains' data (enrichment keyed to existing
   policies/parties; model_score rows for existing claims/quotes; rating factors + derived
   factors). Small, narrative-scale for now — **not** the pricing 50k mass (that's the
   parked migration plan). Build order stays: **generate → world_engine → deploy**.
3. **`smoke_test.py`** — new tie-outs: enrichment coverage ≥ threshold, every
   `model_score.model_version_id` resolves, referral_rule current-view has exactly one
   current row per rule, claim reserve categories sum to `claim_transaction` reserves.
4. **Atlas app** — the new domains/entities appear automatically via the ontology JSON;
   add a `model`-domain and `enrichment`-domain readout to the governance/engineers views
   (no new endpoints required if the meta/entity endpoints are domain-generic).

---

## PART D — Governance hardening (the second axis of "robust")

Coverage isn't enough if the surface is un-attested. Today **18 of ~80 elements** are
certified. Target end-state:

- **Every new entity** gets an owner + a `quality` rule + at least a `draft`→intended
  certification path in `attestations.json`.
- **Classification audit**: 100% of attributes classified (enrichment/ML forces the PII
  conversation — do it deliberately).
- **Certification pass**: raise certified entities from 12 → the full golden-thread +
  pricing/enrichment/model core (target ~30), each with dated evidence tied to a
  `smoke_test` tie-out (the existing evidence pattern).
- **Quality rules**: add rules to entities that lack them (quote, vehicle, insured_object,
  all new entities) — the layer currently has quality rules on only a handful.

---

## PART E — Net impact

| | Now | After remediation |
|---|---|---|
| Domains | 18 | ~21 (+enrichment, +model, +pricing) |
| Entities | ~56 | ~56 + 26 new ≈ 82 |
| Code sets | 52 | ~52 + 22 new ≈ 74 |
| Semantic views | 11 | 11 + 4 (enrichment_coverage, model_governance_metrics, pricing_metrics, accumulation_metrics) ≈ 15 |
| Functions | 9 | 11 (+fn_champion_score, +referral current-view helper) |
| Certified elements | 18 | ~34 target |

---

## Build order (layer-first, gated)

1. **`enrichment` domain** — highest reuse (pricing + underwriting), cleanest to model.
2. **`model` domain** — the robustness gap; serves the whole estate.
3. **`pricing`/rating domain** — completes pricing's canonical structure.
4. **Claims + underwriting depth** (A4, A5) — incl. SCD2 generator change.
5. **Reinsurance/Solvency views** (A6, A7) — mostly measures/views, light.
6. **Governance hardening pass** (Part D) — certify/own/classify/quality across old + new,
   so the enlarged layer lands attested, not draft.

Acceptance for the whole programme: `generate.py` clean, `smoke_test.py` green on all new
tie-outs, every new element owned + classified, and the Atlas renders the three new domains
with lineage — **with zero rows imported from any workbench** (data is generated from the
model, per the derived-never-stored principle).

## Open decisions for you

1. **`fraud_signal`**: keep distinct and make it consume `model_score` (recommended), or
   fold into `model_score`?
2. **Solvency SCR/own-funds**: measures (recommended) vs entities?
3. **Scope of A4/A5**: full claims/underwriting depth now, or model the entities but leave
   deep narrative data to when those workbenches actually migrate?
4. **Certification target**: certify aggressively to ~34 now, or certify each domain only
   as its workbench lands?

---

## What shipped (model v0.10.0, 2026-08-26)

Built and deployed to serverless (`lr_serverless_aws_us_catalog`), smoke **40/40 pass**.
The four open decisions above were taken the "real company / most extensible" way:
fraud_signal stays a distinct indicator that *consumes* `model_score`; Solvency SCR/own
funds stay measures; entities modelled in full but data kept narrative-scale; certify
per-domain as it lands. SCD2 was done as explicit `effective_from`/`effective_to`/
`is_current` attributes + a natural key — no generator change, and portable to Snowflake.

- **3 new domains** — `enrichment` (7 entities), `model` (7 + `fn_champion_score`),
  `pricing` (5) — plus **claim depth** (5) and **product/underwriting depth** (3,
  incl. the SCD2 `referral_rule`). 27 new entities in all.
- **Part B changes** applied to `quote`, `claim`, `fraud_signal`, `vehicle`,
  `insured_object` (via `ALTER ADD COLUMNS` before redeploy).
- **4 new semantic assets**: `pricing_metrics`, `model_governance_metrics`,
  `accumulation_metrics` (metric views) + `enrichment_coverage` (view).
- **Governance**: 22 new code sets, all new entities owned + classified (PII/confidential
  modelled deliberately on telematics/credit/demographics/sanctions); 8 new attestations
  (certified elements 18 → 26).
- **Totals now**: 20 domains, 80 entities, 73 code sets, 6 views, 12 metric views,
  10 functions, 155 tables, 289 FK relationships. Ontology export regenerated to v0.10.0.
- **New tie-outs (all green)**: pricing build-up reconciles to rated premium; every
  `model_score` traces to a `model_version`; exactly one current version per referral
  rule (SCD2 integrity); telematics covers every motor policy; `fn_champion_score`
  resolves; `pricing_metrics` / `model_governance_metrics` answer via MEASURE().

**Deferred** (per "certify as workbench lands" / narrative-scale): the pricing 50k-motor
statistical mass (that's the parked `PRICING_GEN2_MIGRATION_PLAN.md`, Phase 0 first);
broader certification; retraining/serving of the models the `model` domain now describes.
