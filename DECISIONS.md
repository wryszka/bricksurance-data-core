# DECISIONS — Bricksurance Data Core

Design decisions and deviations, newest first. Each: context, decision, reasoning.
Started 2026-08-27 for the Gen2 Expansion (`specs/SPEC_DATACORE_GEN2_EXPANSION.md`);
back-references to earlier work live in the project history and `docs/EVOLUTION.md`.

---

## 2026-08-27 — Gen2 Expansion WP0 reconciliation (Phase-1 gate)

Full analysis in `docs/INVENTORY_GEN2_EXPANSION.md`. Decisions taken from it:

- **D1 — Method scaffolding.** `DEMO_BUILD_METHOD.md`, `ESTATE_MANIFEST.yaml`,
  `TWIN_COVERAGE.md` do not exist in this repo (they live in the playbook / Group
  Control Tower repos). Mapped onto local equivalents: method = `docs/DESIGN.md` +
  `docs/EVOLUTION.md`; `DECISIONS.md` created here; `TWIN_COVERAGE.md` produced as a
  phase deliverable. ESTATE_MANIFEST edits are cross-repo (see D6).

- **D2 — WP2 `premium_finance` is an EXTENSION, not a new domain.** `premium_transaction`
  (policy), `receivable_transaction` (finance), `premium_earning` (semantics view) and
  `gross_written_premium` (underwriting_metrics) already exist. Creating a `premium_finance`
  domain would fork premium truth. Instead: extend `policy.premium_transaction` (IPT,
  commission, broker, `policy_event_id`), add `finance.upr_snapshot`, add
  `earning_schedule` + `fn_earn_premium`, add GEP/commission/IPT metrics in `semantics`,
  rebase loss ratio on GEP under a governance attestation event.

- **D3 — WP3 `asset_alm` EXTENDS the `investment` domain.** `investment_holding` /
  `investment_transaction` exist. Add `instrument`, `position`, `asset_cashflow`,
  `asset_valuation_run` (renamed from the spec's `valuation_run` to avoid the clash with
  `life.valuation_run`), plus `fn_duration` / `fn_duration_gap` / `fn_stress_mv`. No new domain.

- **D4 — WP4 SPLITS.** `customer` + `fair_value_assessment` → new `customer` domain.
  `complaint` already exists in `conduct` → extend it there (add customer_id, outcome,
  redress, fos_referred), do not move or duplicate. One estate-wide `vulnerability_basis`
  code set created here (data-core), consumed by both this and the claims workbench.

- **D5 — WP1 policy refactor: FULL REWIRE (user choice 2026-08-27), realized within UC
  constraints.** User chose the cleanest end state: events are the source of truth and
  policy is fully derived. Unity Catalog informational FKs require the target to be a
  *keyed table*, not a view, so a literal "`policy` = pure view with all ~20 FKs repointed"
  is not buildable without discarding the FK graph (which the golden thread and the
  289-FK integrity story depend on). Faithful realization:
  (a) `policy_event` (append-only, hash-chained) + `policy_version` (SCD2 history) are the
      source-of-truth history, in a NEW `policy_lifecycle` domain;
  (b) `policy` remains a keyed table but becomes the **derived current projection** —
      `vw_policy_current` reconstructs current state from the event stream and MUST
      byte-match `policy` (reconciliation AC);
  (c) the concrete repoint the spec names is delivered: **claim → policy_version as-at
      loss date** (new relationship), so claims attach to the version in force at loss;
  (d) deeper repoint (moving other consumers off `policy.policy_id` onto version keys) is
      a later, workbench-by-workbench phase, not done blind now.
  `events.business_event` stays the lightweight near-real-time feed and references
  `policy_event`.

- **D9 — `payload` struct flattened.** The generator's type system is flat
  (string/int/bool/date/timestamp/decimal — no struct/array). `policy_event.payload` is
  flattened to typed columns (`premium_delta`, `sum_insured_delta`, `coverage_change_note`,
  `reason_code`). Same treatment for WP6 `lob_scope` (array → membership/CSV) when reached.

- **D6 — ESTATE_MANIFEST is cross-repo.** The estate/spine manifest lives with the Group
  Control Tower (actuarial-workbench-hub). WP8 will publish a local
  `estate_published_surfaces.yaml` stub in data-core listing the published views; wiring
  the tower's manifest is a separate cross-repo action, not done blind from here.

- **D7 — Domain shape.** Confirmed new domains: `policy_lifecycle` (WP1), `renewal` (WP5),
  `delegated_authority` (WP6), `customer` (WP4 split). Extensions: `policy`, `finance`,
  `investment`, `conduct`, `exchange`, `semantics`. This replaces the spec's nominal
  "7 new domains".

- **D8 — ACORD posture held.** New entities carry `crosswalk_status: candidate` at concept
  level (no fabricated element codes). WP6 bordereau rows map precisely to public Lloyd's
  CDR v3.x field names (`crosswalk_status: mapped`).

Status: confirmed by user 2026-08-27 — D2/D3/D4 = **extend existing**; D5 = **full rewire**
(realized within the UC keyed-table-FK constraint as above). Phase 1 gate cleared.

---

## 2026-08-27 — Phase 2 (WP1 Policy Lifecycle Spine) COMPLETE

Built model v0.11.0, deployed to serverless, **smoke 47/47 pass** (40 prior + 7 WP1).
- New `policy_lifecycle` domain: `policy_event` (append-only, hash-chained, seq-gap-free),
  `policy_version` (SCD2 history), `renewal_chain`; view `vw_policy_current`; metric view
  `lifecycle_metrics`; function `fn_verify_event_chain`. Code sets: policy_event_type,
  event_source_system, actor_type. `claim.policy_version_id` added (as-at attach).
- world_engine `add_lifecycle()` back-generates events+versions+chains for all 172 policies
  (deterministic; no rng — MTA by policy-id parity). Hero POL-2026-000001 gets an MTA_APPLIED
  on 2026-02-14 (v2), and the golden-thread claim CLM-2026-000001 (loss 2026-03-14) attaches
  to v2 — cover read as at the loss. **This is the WP1 demo beat.**
- **Hash canonical excludes free text** (reason_code): a cancellation reason with an
  apostrophe made the Python-stored hash diverge from the Spark recompute on one event.
  Canonical is now structured identity only (policy_id|seq|type|effective_from) — collision-
  proof and deterministic across Python/Spark. (Fix logged; both world_engine and
  fn_verify_event_chain updated.)
- **As-at attach clamps to v1** when a loss predates inception (40 reserving-history claims
  have loss_date < inception — a pre-existing data trait); smoke accepts the clamp.
- ACs met: vw_policy_current byte-matches policy (0 mismatches, 172/172); chain verifies
  estate-wide (SUM fn_verify_event_chain = 0); sequences gap-free; hero→v2.
- Retention dynamics are thin (6 invited / 6 renewed / 0 lapsed) because the base book has
  no LAPSED-status policies — **WP5's advance_period is what populates real lapse dynamics**;
  left honest rather than fabricating lapses inconsistent with policy status.
- App refreshed to v0.11.0 and redeployed; SP granted on bricksurance_policy_lifecycle.
- Deploy gotcha reconfirmed: `claim` needed ALTER ADD COLUMN policy_version_id before deploy.

---

## 2026-08-28 — Phase 3 (WP2 Premium) + Phase 4 (WP5 Renewal) COMPLETE

Model v0.12.0, deployed, **smoke 54/54 pass**.
- **WP2 (extend, per D2):** premium_transaction gained policy_event_id (spine link),
  ipt_amount, commission_amount/rate, broker_party_id, inception/expiry. Added
  fn_earn_premium (governed earning engine, mirrors premium_earning), vw_premium_proof
  (written = earned + unearned, residual 0 by LOB), premium_metrics (GWP/IPT/commission).
  world_engine.add_premium_finance() sets IPT@12% GBP, commission from the sub-ledger,
  event link = bind event evt_{pid}_02 (orphan check 0). Loss-ratio-on-earned already
  lived in performance_metrics — no certified metric disturbed (logged, not forced).
  Kept premium_transaction_type codes as-is (WRITTEN/ADJUSTMENT/RETURN; spec's
  ADDITIONAL/REINSTATEMENT not added — ADJUSTMENT covers additional).
- **WP5 (new thin domain):** renewal_case + retention_response_curve + renewal_metrics;
  renewal_outcome code set. world_engine.add_renewal() draws each policy's outcome from
  the curve given a deterministic price walk -> real lapses, retention < 100%.
  **tools/advance_period.py = the estate's first closed loop:** retention responds to
  price monotonically (3%->95.5%, 8%->90.9%, 15%->72.7%, 25%->54.5%) and is byte-identical
  across two runs. **Bug fixed at source: build_world() now reseeds the RNG on entry** so
  it is deterministic per call (was drifting across repeated in-process calls).
- Live-workspace form of advance_period (appending RENEWED/LAPSED onto the hash-chained
  spine + re-materialising versions) is intentionally deferred to a workbench runtime;
  data-core stays declarative and rebuildable.
- App refreshed to v0.12.0 + redeployed.

---

## 2026-08-28 — Phase 5 (WP3 Assets & ALM) COMPLETE

Model v0.13.0, deployed, **smoke 60/60 pass**. Extended the `investment` domain (D3).
- Entities: instrument, position (time series), asset_cashflow, asset_valuation_run
  (renamed from spec's valuation_run to avoid the life.valuation_run clash). Code sets:
  instrument_type, credit_rating, portfolio.
- Governed tools: fn_duration (cashflow-weighted mean time, stylised Macaulay, labelled),
  fn_duration_gap, fn_stress_mv (first-order duration sensitivity, no convexity, labelled).
- Publication views: vw_s2_market_inputs (S2 market-risk inputs), vw_alm_annuity_match
  (annuity asset cashflows by year). Metric: asset_metrics.
- Seed: 200 instruments, 3 portfolios, 6 month-ends of positions, bond cashflows. The
  ANNUITY_MA portfolio built long so **asset duration ~9.76y vs a 9.0y liability -> gap
  ~0.76y** (nonzero and interesting, per spec ~0.8y target).
- **GOTCHA (important, cost two redeploys):** the deploy applies files in SORTED order, so
  `30_` views deploy BEFORE `40_` functions -> a view that CALLS a UC function fails
  ("UNRESOLVED_ROUTINE") and aborts the whole deploy mid-run (FKs + demo data after it
  never apply). Fix: **views must not call UC functions** — inline the math (vw_s2_market_inputs
  now inlines duration/stress; fn_* remain as callable tools for smoke/apps). Applies to all
  future WPs (e.g. WP6 breach views).
- **GOTCHA reconfirmed:** generate.py wipes build/ incl. 95_demo_data.sql -> ALWAYS run
  world_engine BEFORE deploy, or new tables deploy empty (WP3 tables were empty until
  world_engine re-run).
- S2 workbench migration and ESTATE_MANIFEST wiring remain out of scope (publish-only).

---

## 2026-08-28 — Phase 6 (WP4 Customer & Conduct) COMPLETE

Model v0.14.0, deployed, **smoke 67/67 pass**. New `customer` domain + extend `conduct` (D4).
- Entities: customer (thin over party; vulnerable_flag/basis + marketing_consent all PII;
  NO protected-characteristic proxies by design), fair_value_assessment (attested Consumer
  Duty artifact). Extended conduct.complaint (+complaint_outcome_code, +fos_referred).
  Code sets: vulnerability_basis (FCA 4-driver, the single estate-wide taxonomy),
  complaint_outcome, fair_value_outcome.
- vw_fair_value_latest computes fair value LIVE per LOB from premium_earning + claims +
  complaints (no hardcoded numbers). conduct_metrics (uphold rate, FOS, redress).
- **Fair value is price AND benefit AND service:** MONITOR fires on thin benefit
  (<0.15) OR poor claims acceptance (<0.90) OR high complaints (>10/1000). Commercial
  Property lands MONITOR honestly via its complaint ratio (18.9/1000) — the demo amber,
  data-driven not fabricated. Seed entity outcome == live view outcome (same rule, smoke
  checks they agree).
- PII conformance smoke checks: no protected-characteristic proxy columns; vulnerable_flag
  classified pii (codifies pricing gen1's C6 lesson as a design rule).
- App refreshed to v0.14.0. Vulnerability taxonomy created here as the canonical estate-wide
  code set (claims workbench to consume the same when it migrates).

## 2026-08-28 — Ontos adoption (planned, not built)

User decided to adopt **Ontos** (databrickslabs/ontos) — see [[reference-ontos-databricks-labs]].
**Chosen approach = Track B (deploy-first):** stand Ontos up on serverless first, THEN make
our model compatible with it. **Atlas stays as-is — do NOT slim or change it** (user:
"atlas stays for now, we don't need to change it").
- Our ontology JSON stays canonical/open; Ontos is a NEW export target (like the
  databricks/snowflake bindings) — nothing existing is lost.
- Track B steps: provision Lakebase (FEVM addon) → clone databrickslabs/ontos → configure
  its DAB (catalog/schema vars + .env) → deploy as a DBX App → grant SP read on bricksurance_*.
- Then compatibility: tools/export_ontos.py emits ODCS contracts + ODPS products + RDF/SKOS
  concepts from build/ontology JSON and loads them via Ontos's REST API (confirm exact
  create endpoints via its /docs).
- Ontos is Databricks-licensed (proprietary); our model stays Apache-open. Ontos needs
  Postgres/Lakebase (more infra than Atlas).
- **Decisions 2026-08-28:** (1) provision a **NEW DEDICATED Lakebase instance** for Ontos —
  the two existing instances (motor-pricing-online-store, pricing-upt-online-store-live)
  are the pricing workbench's, don't co-opt them; (2) **use the smallest capacity + every
  scale-to-zero / auto-stop option** (instances expose effective_stopped; stop when idle —
  do NOT run nonstop unless crucial) per the cost pillar; (3) **sequencing: finish the Gen2
  WPs (WP6, WP7/8) FIRST**, then do the Ontos deploy as a clean separate spike.
- Ontos repo cloned to ~/vibe/ontos for inspection. Deploy = its own DAB (`src/databricks.yaml`,
  bundle deploy) → App named "ontos"; requires a UC volume + Lakebase; auth via App implicit SDK.

---

## 2026-08-28 — Phase 7 (WP6 Delegated Authority) COMPLETE

Model v0.15.0, deployed, **smoke 74/74 pass**. New `delegated_authority` domain (the spec's
GTM prize).
- Entities: coverholder, binding_authority (+binding_authority_lob membership, flattening
  lob_scope per D9), bordereau_submission, bordereau_risk_row / bordereau_premium_row /
  bordereau_claim_row (**mapped attribute-by-attribute to Lloyd's CDR v3.x**, crosswalk_status:
  mapped — the generated data_dictionary IS the CDR crosswalk), authority_breach.
  Code sets: coverholder_status, bordereau_type, bordereau_status, breach_type, breach_status.
- vw_authority_breach = LIVE detection (LINE_SIZE + LOB, inline — no fn call per the deploy-order
  rule). da_metrics (submissions, lag, DQ). authority_breach carries the maker/checker waiver.
- **Delegated business enters the WP1 spine:** add_delegated runs BEFORE add_lifecycle, mints
  12 delegated policies (POL-BDX, non-CP LOBs to protect WP4's amber) whose BOUND event is
  stamped source=BORDEREAU. Deliberate dirt: 2 late submissions, 1 quarantined column-drift,
  1 line-size breach (8m > 5m), 1 LOB breach (GL under a MOTOR-only binder). One breach WAIVED.
- Policy count 172 → **184**; updated the hardcoded smoke count + excluded POL-BDX from the
  core-book-quote check and the telematics-coverage check (delegated/bordereau motor arrives
  without telematics — realistic; the coverholder doesn't send it).
- App refreshed to v0.15.0. NON-GOAL held: no DA workbench app, no un-stubbing the console's
  LLM mapping (that's an Atlas change — Atlas stays untouched per user).
