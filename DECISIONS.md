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
