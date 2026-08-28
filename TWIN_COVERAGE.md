# TWIN_COVERAGE — Bricksurance digital-twin coverage map

*The org-chart view of the twin: which insurance functions are occupied, thin, or empty.
Kept current so "where are we on the twin" never needs an estate sweep. Maintained per
phase of `specs/SPEC_DATACORE_GEN2_EXPANSION.md`.*

Last updated: 2026-08-28 · model **v0.13.0** · after **WP1, WP2, WP5, WP3, WP4**.

| Function | Status | Backed by |
|---|---|---|
| Distribution / broking | 🟡 thin | distribution.commission_transaction; broker as party role |
| Underwriting / pricing | 🟢 occupied | product, appetite_rule, referral_rule/event, pricing (rating factors), enrichment |
| **Policy administration** | 🟢 **occupied (WP1)** | **policy_lifecycle: policy_event (hash-chained), policy_version (SCD2), renewal_chain; vw_policy_current; fn_verify_event_chain** |
| Premium / billing | 🟢 occupied (WP2) | premium_transaction (+IPT/commission/broker/event link), premium_earning, vw_premium_proof, premium_metrics, fn_earn_premium |
| Claims | 🟢 occupied | claim + feature + reserve_category + recovery + litigation + party_role + fraud_signal |
| Reinsurance | 🟢 occupied | treaty, layer, cession, submission, cat_event, event_loss |
| Reserving | 🟢 occupied | reserve_estimate, loss_development, reserving_metrics |
| Finance / IFRS17 / S2 (liabilities) | 🟢 occupied | ledger, valuation_result, contract_group, csm_movement, statement_line |
| Assets / ALM | 🟢 occupied (WP3) | instrument, position, asset_cashflow, asset_valuation_run; fn_duration/gap/stress; vw_s2_market_inputs, vw_alm_annuity_match (annuity gap ~0.8y) |
| Customer / conduct | 🟢 occupied (WP4) | customer (over party), fair_value_assessment (attested), complaint (+outcome/FOS), vw_fair_value_latest, conduct_metrics; one MONITOR amber |
| Renewal / retention | 🟢 occupied (WP5) | renewal_case, retention_response_curve, renewal_metrics; advance_period closed loop (retention responds to price: 3%→95%, 25%→54%) |
| Delegated authority | 🔴 empty | *WP6* |
| Model / AI governance | 🟢 occupied | model_asset/version, feature_*, model_score, monitor_metric |
| Investment income / valuation | 🟢 occupied (WP3) | positions time series + asset valuation runs |

**Legend:** 🟢 occupied · 🟡 thin (some data, not the full function) · 🔴 empty.

## Progress against the Gen2 Expansion spec

| WP | Function it fills | Status |
|---|---|---|
| WP0 | inventory & reconciliation | ✅ done (`docs/INVENTORY_GEN2_EXPANSION.md`) |
| WP1 | policy administration spine | ✅ **done** — deployed, smoke 47/47 |
| WP2 | premium accounting & earning | ✅ **done** — smoke 54/54 |
| WP5 | renewal & retention loop | ✅ **done** — advance_period deterministic; retention responds to price |
| WP3 | assets & ALM | ✅ **done** — duration gap ~0.8y, stress verified |
| WP4 | customer & conduct | ✅ **done** — fair value live + attested, PII-conformant |
| WP6 | delegated authority | ⬜ next |
| WP7/8 | semantics, Genie, golden-thread v2, publication contracts | ⬜ |

**Empty → occupied so far this spec:** policy administration (WP1), premium/billing (WP2),
renewal loop (WP5), assets/ALM (WP3), customer/conduct (WP4). **Still empty:** delegated authority (WP6) — next.
