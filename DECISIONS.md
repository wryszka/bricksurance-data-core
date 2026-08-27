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

- **D5 — WP1 `policy` refactor is ADDITIVE.** `policy.policy` is referenced by 20+ FKs.
  Add `policy_version` (SCD2 history) + `vw_policy_current`; keep `policy` as the current
  row so no existing consumer breaks. Full rewire of `policy` into a pure view is deferred
  to a later, separate decision. `policy_event` is a NEW `policy_lifecycle` domain
  (distinct from the lightweight `events.business_event` stream, which will reference it).

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

Status: **proposed, pending user confirmation on D2/D3/D4/D5** (the extend-vs-new and
refactor-scope calls) before Phase 2 build begins, per the Phase-1 gate
("inventory doc reviewed").
