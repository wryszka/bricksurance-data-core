# TWIN_COVERAGE — Bricksurance digital-twin coverage map

*The org-chart view of the twin: which insurance functions are occupied, thin, or empty.
Kept current so "where are we on the twin" never needs an estate sweep. Maintained per
phase of `specs/SPEC_DATACORE_GEN2_EXPANSION.md`.*

Last updated: 2026-08-27 · model **v0.11.0** · after **WP1 (Policy Lifecycle Spine)**.

| Function | Status | Backed by |
|---|---|---|
| Distribution / broking | 🟡 thin | distribution.commission_transaction; broker as party role |
| Underwriting / pricing | 🟢 occupied | product, appetite_rule, referral_rule/event, pricing (rating factors), enrichment |
| **Policy administration** | 🟢 **occupied (WP1)** | **policy_lifecycle: policy_event (hash-chained), policy_version (SCD2), renewal_chain; vw_policy_current; fn_verify_event_chain** |
| Premium / billing | 🟡 thin | policy.premium_transaction, finance.receivable_transaction, semantics.premium_earning — *WP2 will occupy* |
| Claims | 🟢 occupied | claim + feature + reserve_category + recovery + litigation + party_role + fraud_signal |
| Reinsurance | 🟢 occupied | treaty, layer, cession, submission, cat_event, event_loss |
| Reserving | 🟢 occupied | reserve_estimate, loss_development, reserving_metrics |
| Finance / IFRS17 / S2 (liabilities) | 🟢 occupied | ledger, valuation_result, contract_group, csm_movement, statement_line |
| Assets / ALM | 🟡 thin | investment_holding, investment_transaction — *WP3 will occupy* |
| Customer / conduct | 🟡 thin | conduct.complaint, party — *WP4 will occupy (customer + fair value)* |
| Renewal / retention | 🔴 empty | renewal_chain exists (WP1); *WP5 builds the loop + advance_period* |
| Delegated authority | 🔴 empty | *WP6* |
| Model / AI governance | 🟢 occupied | model_asset/version, feature_*, model_score, monitor_metric |
| Investment income / valuation | 🟡 thin | investment_transaction — *WP3* |

**Legend:** 🟢 occupied · 🟡 thin (some data, not the full function) · 🔴 empty.

## Progress against the Gen2 Expansion spec

| WP | Function it fills | Status |
|---|---|---|
| WP0 | inventory & reconciliation | ✅ done (`docs/INVENTORY_GEN2_EXPANSION.md`) |
| WP1 | policy administration spine | ✅ **done** — deployed, smoke 47/47 |
| WP2 | premium accounting & earning | ⬜ next |
| WP5 | renewal & retention loop | ⬜ (needs WP1 ✓ + WP2) |
| WP3 | assets & ALM | ⬜ |
| WP4 | customer & conduct | ⬜ |
| WP6 | delegated authority | ⬜ (independent; pull-forward candidate) |
| WP7/8 | semantics, Genie, golden-thread v2, publication contracts | ⬜ |

**Empty → occupied so far this spec:** policy administration. **Still empty:** renewal loop,
delegated authority. **Still thin (assets, customer/conduct, premium):** WP2/WP3/WP4.
