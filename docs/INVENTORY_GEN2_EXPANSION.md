# WP0 — Inventory & reconciliation (Gen2 Expansion)

*Read-only pass per `specs/SPEC_DATACORE_GEN2_EXPANSION.md` WP0. No model changes here.
This document is the Phase-1 gate: it reconciles every proposed work package against what
already exists in model v0.10.0, flags collisions, and states extend-vs-new with reasoning.
Decisions are logged in `DECISIONS.md`.*

Generated against **model v0.10.0** (2026-08-27).

---

## 1. Current manifest (authoritative dump from `model/`)

**20 domains · 80 entities · 73 code sets · 6 views · 12 metric views · 10 functions.**

| Domain | Entities | Views / metric views | Functions |
|---|---|---|---|
| reference | (73 code sets) | — | fn_define |
| org | legal_entity | — | — |
| party | party, party_role, contact_point, consent, data_subject_request | — | — |
| policy | policy, coverage, endorsement, insured_object, **premium_transaction**, quote, underwriting_decision, vehicle | — | fn_policy_snapshot |
| claim | claim, claim_transaction, claim_feature, claim_reserve_category, claim_recovery, litigation, claim_party_role, fraud_signal | — | fn_claim_status, fn_outstanding_reserve |
| reinsurance | treaty, treaty_layer, cession, submission, cat_event, event_loss | — | fn_cession_trace |
| reserving | reserve_estimate | loss_development, reserving_metrics | — |
| product | product, product_coverage, underwriting_question, appetite_rule, uw_submission, referral_rule, referral_event | — | fn_appetite_check, fn_indicative_quote |
| pricing | rating_factor, rating_factor_level, rating_engine_config, derived_factor, rating_factor_feature | — | — |
| enrichment | motor_telematics_aggregate, credit_bureau_summary, postcode_enrichment, geospatial_hazard, market_pricing_benchmark, policy_demographics, sanctions_screen | — | — |
| model | model_asset, model_version, feature_definition, feature_set, feature_set_member, model_score, model_monitor_metric | — | fn_champion_score |
| finance | chart_of_account, journal, journal_line, accounting_period, statement_line, **receivable_transaction**, expense_transaction, tax_transaction, fx_rate, financial_plan, valuation_result, contract_group, csm_movement | — | fn_trial_balance_check, fn_csm_closing |
| investment | **investment_holding, investment_transaction** | — | — |
| life | model_point, assumption_set, scenario_set, valuation_run, valuation_run_assumption | — | — |
| distribution | **commission_transaction** | — | — |
| conduct | **complaint** | — | — |
| content | document | — | — |
| events | **business_event** (append-only stream) | — | — |
| exchange | **premium_bordereau_line** | **cession_bordereau_line** | — |
| semantics | — | financial_transaction, premium_earning, underwriting_performance + 12 metric views (underwriting_metrics, performance_metrics, cession_metrics, submission_metrics, valuation_metrics, investment_metrics, financial_position, trial_balance, pricing_metrics, model_governance_metrics, accumulation_metrics, enrichment_coverage) | — |

**Bold** = entities/streams the spec proposes to (re)create under a new domain but which **already exist**.

## 2. Method scaffolding referenced by the spec — status in THIS repo

| File the spec cites | Exists here? | Note |
|---|---|---|
| `DEMO_BUILD_METHOD.md` | ❌ | Lives in the `bricksurance-playbook` repo, not here. This repo's method is in `docs/DESIGN.md` + `docs/EVOLUTION.md`. |
| `DECISIONS.md` | ❌ → **create in WP0** | Created this pass; decisions logged there. |
| `ESTATE_MANIFEST.yaml` | ❌ | The estate/spine manifest lives with the Group Control Tower (actuarial-workbench-hub), not in data-core. WP8's "add to ESTATE_MANIFEST" is a cross-repo action — logged as a decision. |
| `TWIN_COVERAGE.md` | ❌ → produce as a deliverable | Baseline drafted in WP0 §5 below; maintained per phase. |

**No blocker** — the method idioms (append-only, model-as-code, governed UC functions, one-schema-per-domain, honest certification) are all already practised in this repo; the named files are playbook/estate artifacts we map onto local equivalents.

## 3. Naming collisions & grain conflicts (must resolve before build)

| Proposed (spec) | Collides with (exists) | Conflict |
|---|---|---|
| WP2 `premium_finance.premium_transaction` | `policy.premium_transaction` | **Same name, same concept.** Existing has policy_id, type, amount, currency, date, source. Spec adds policy_event_id, IPT, commission, broker, inception/expiry. → **extend the existing entity**, do not create a second. |
| WP2 `premium_finance.receivable` | `finance.receivable_transaction` | Same concept (instalments/aged debt). → extend/alias, don't duplicate. |
| WP2 `earning_schedule` / GEP metrics | `semantics.premium_earning` (view, straight-line daily) + `performance_metrics.gross_earned_premium` | Earning already modelled as a view. Spec wants a materialised schedule + `fn_earn_premium`. → extend: keep the view, add the function + schedule, reconcile GEP metric. |
| WP2 `gross_written_premium` | `underwriting_metrics.gross_written_premium` | Exists. → reuse; do not redefine. |
| WP3 `asset_alm.instrument` / `position` | `investment.investment_holding` / `investment_transaction` | Holdings exist. Spec adds instrument reference detail, positions time series, cashflows, ALM functions. → **extend the investment domain**. |
| WP3 `asset_alm.valuation_run` | `life.valuation_run` | Name clash, different concept (asset valuation vs actuarial run). → name asset one `asset_valuation_run` to avoid collision. |
| WP4 `customer.complaint` | `conduct.complaint` | Exists. → extend conduct's complaint (add customer_id, outcome, redress, fos); keep it in conduct. |
| WP4 vulnerability taxonomy | none in data-core (claims workbench is a separate repo) | No `vulnerability_basis` code set exists here yet. → **create it here** as the single estate-wide code set. |
| WP1 `policy_lifecycle.policy_event` | `events.business_event` (append-only stream) | Overlap: business_event is the lightweight near-real-time stream. policy_event is the governed, hash-chained, SCD2-backing spine. → **new `policy_lifecycle` domain**; business_event stays the lightweight feed and references policy_event. |
| WP1 `renewal_chain` | `policy.renews_policy_id` + world_engine renewal chains | Linkage exists as a column. → formalise as `renewal_chain` entity built from the existing linkage; don't invent parallel truth. |
| WP1 `policy_version` vs existing `policy` | `policy.policy` (mutable current table) | Spec: `policy` becomes a *current view* over `policy_version`. **Highest-risk refactor** — 20+ FKs point at policy.policy_id. → keep `policy` table as-is (the current row), add `policy_version` (history) + `vw_policy_current`; do NOT rewire existing FKs in this phase. |
| WP6 `delegated_authority.bordereau_*` | `exchange.premium_bordereau_line`, `cession_bordereau_line` | Bordereaux partly exist (premium + cession lines). Spec adds risk/claims bordereaux, coverholders, binders, breaches. → **new `delegated_authority` domain** for coverholder/binder/breach; reconcile bordereau row shapes with the exchange lines (reuse CDR mapping). |

## 4. Per-WP verdict: extend vs new

- **WP1 — `policy_lifecycle`: NEW domain.** Genuinely absent (no event spine, no SCD2 policy history, no hash chain). The append-only idiom exists (events.business_event, referral_rule SCD2) but not for policy administration. Caveat: the `policy`→`policy_version` refactor is the single riskiest change in the whole spec (FK blast radius); do it additively (add version + view, leave `policy` as the current row) — full rewire is a later, separate decision.

- **WP2 — `premium_finance`: EXTEND, do NOT create a new domain.** `premium_transaction`, `receivable_transaction`, `premium_earning`, and `gross_written_premium` all exist. The real new work is: enrich `premium_transaction` (IPT/commission/broker/event link), add `earning_schedule` + `fn_earn_premium`, add `upr_snapshot`, add GEP/commission/IPT metrics, and rebase loss ratio on GEP under a governance event. Home: `policy` (premium_transaction), `finance` (upr/receivable), `semantics` (metrics). A separate `premium_finance` domain would fork premium truth — rejected.

- **WP3 — `asset_alm`: EXTEND the `investment` domain.** Holdings/transactions exist. Add `instrument`, `position` (time series), `asset_cashflow`, `asset_valuation_run` (renamed to avoid the life clash), the three ALM UC functions, and metrics — all in `investment`. New domain rejected (would orphan the existing holdings).

- **WP4 — `customer`: SPLIT.** `customer` (thin dimension over party) + `fair_value_assessment` are genuinely new → **new `customer` domain**. `complaint` already exists → **extend it in `conduct`** (don't move it). Vulnerability code set created here once, consumed by both.

- **WP5 — `renewal`: NEW thin domain.** Nothing exists. Depends on WP1 `renewal_chain` and the gen2 elasticity module (separate repo — cite, don't re-derive). Ships `job_advance_period` — the estate's first closed loop.

- **WP6 — `delegated_authority`: NEW domain + reconcile exchange.** coverholder/binding_authority/bordereau_submission/breach are new. bordereau row shapes reconcile with the existing exchange lines and reuse the CDR crosswalk. Highest GTM value; can be pulled forward independently.

- **WP7/WP8 — semantics + publication views: mostly new views** over the above, registered in `semantics/` (uncertified to start). ESTATE_MANIFEST edits are cross-repo (Group Control Tower) — logged as a decision, not done blind here.

**Net reshaping:** the spec's "7 new domains" is really **2 new domains (`policy_lifecycle`, `delegated_authority`) + 1 new thin domain (`renewal`) + 1 new split domain (`customer`) + significant extensions to 4 existing domains (policy, finance/investment, conduct, exchange)**. Building all 7 as greenfield domains would duplicate ~15 existing entities and fork premium/complaint/investment truth.

## 5. TWIN_COVERAGE baseline (org-chart view — occupied / thin / empty)

| Function | Coverage today | After this spec |
|---|---|---|
| Distribution / broking | thin (commission only) | thin (+broker on premium) |
| Underwriting / pricing | **occupied** (product, appetite, rating, referral, enrichment) | occupied |
| Policy administration | **EMPTY** | **occupied** (WP1 spine) |
| Premium / billing | thin (premium_transaction, receivables) | **occupied** (WP2 earning/UPR/IPT) |
| Claims | **occupied** (claim + features + recovery + litigation + fraud) | occupied |
| Reinsurance | occupied | occupied |
| Reserving | occupied | occupied |
| Finance / IFRS17 / S2 | occupied (liabilities), **assets EMPTY** | **occupied** (WP3 assets/ALM) |
| Investment / ALM | thin (holdings only) | occupied (WP3) |
| Customer / conduct | thin (complaint only) | **occupied** (WP4 customer + fair value) |
| Renewal / retention | **EMPTY** | occupied (WP5 loop) |
| Delegated authority | **EMPTY** | **occupied** (WP6) |
| Model / AI governance | occupied | occupied |

Empty→occupied this spec: **policy admin, renewal, delegated authority, asset side.** These are the true gaps.

## 6. Recommended build order (unchanged from spec, with the reconciliation folded in)

WP1 (new domain) → WP2 (extend) → WP5 (new, needs WP1) → WP3 (extend investment) → WP4 (split) → WP6 (new) → WP7–8. WP6 may be pulled forward independently for a Howden/Lloyd's conversation.

## 7. Open decisions requiring a nod before Phase 2 (see DECISIONS.md)

1. **WP2/WP3/WP4 as extensions, not new domains** — collapses `premium_finance`→policy/finance, `asset_alm`→investment, `complaint`→conduct. (Recommended; the spec's own WP0 instruction anticipates this.)
2. **`policy` refactor scope** — additive (`policy` stays the current row; add `policy_version`+`vw_policy_current`) vs full rewire of `policy` into a pure view now. (Recommend additive; full rewire is a later phase.)
3. **ESTATE_MANIFEST edits** are cross-repo (Group Control Tower) — do them there, or stub a local `estate_published_surfaces.yaml` in data-core. (Recommend local stub now, wire to the tower later.)
