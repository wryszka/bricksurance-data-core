# Finance Review — can we build a finance reporting system on this?

*Reviewed 2026-07-13, model v0.8.0. Verdict: yes — the three layers a finance
function runs on are now present, at solo and group level.*

## Why this review exists

An insurance account team expands into the CFO org: financial controller,
group reporting, IFRS 17 reporting manager, Solvency II regulatory reporting,
head of investments/ALM, tax, FP&A, group consolidation. Before v0.8.0 the
model spoke fluently to actuaries and the underwriting-result crowd, but would
have been exposed to the controller ("where's the double entry?"), the CIO
("where are the assets?") and the group CFO ("give me one consolidated
number"). This documents what closed those gaps.

## The three layers of finance — all present now

1. **Sub-ledgers (operational money)** — premium, claims, commission, expense,
   receivables, tax, investment transactions. Every movement signed and dated.
2. **The general ledger (double-entry)** — `chart_of_account` (typed,
   statement-mapped), `journal` + `journal_line` (debits positive, credits
   negative, **every journal nets to zero**), `accounting_period`
   (open/closed/locked). Journal lines carry their source operational row, so
   the ledger reconciles to the sub-ledgers by construction. `fn_trial_balance_check`
   answers the controller's first question live.
3. **Statements & measures** — `statement_line` maps accounts to balance
   sheet / income statement lines *per regime*; `trial_balance` and
   `financial_position` metric views produce the statements in business
   language. `valuation_result` carries the actuarial/regulatory measures.

## The group / subsidiary picture (the part most models miss)

An insurer is not one balance sheet — it is a **hierarchy of reporting
entities**, and Solvency II reports at **solo** (each regulated subsidiary)
and **group** (consolidated) level. The model makes this real:

- `legal_entity` is a self-referencing tree: **Bricksurance Group NV**
  (holding, EUR presentation) consolidates **Bricksurance SE** (P&C, EUR),
  **Bricksurance Re AG** (CHF) and **Bricksurance Life Ltd** (GBP).
- `policy`, `valuation_run`, `journal`, `accounting_period`,
  `investment_holding`, `financial_plan` and the finance sub-ledgers all carry
  `legal_entity_id`. Solo reporting filters to one entity; group reporting
  consolidates up the tree.
- `valuation_run` carries `reporting_level_code` (SOLO/GROUP) and
  `reporting_regime_code`. The world holds an SE **solo** SCR run *and* a
  **group** consolidated run — and the group is deliberately **not the sum of
  solos**: diversification benefit makes group SCR lower and the coverage
  ratio different (a smoke check enforces they differ). That is the exact
  conversation a group CRO has.
- `fx_rate` translates subsidiary functional currencies to the group
  presentation currency — consolidation is a real number, not a caveat.

**Any existing demo fits this picture without missing data:** the Solvency II
workbench reads solo + group capital measures; the IFRS 17 workbench reads
`contract_group` + `csm_movement`; LifeCast's valuations are `valuation_run`s
against `le_life`; the reinsurance workbench's cessions sit under `le_re`;
claims/pricing sit under `le_se`. Every workbench now has a legal entity to
belong to.

## What a finance reporting system needs — checklist

| Need | Status | Asset |
|---|---|---|
| Double-entry ledger that balances | ✅ | chart_of_account, journal, journal_line, `fn_trial_balance_check` |
| Chart of accounts, typed, hierarchical | ✅ | chart_of_account (account_type, parent, statement_type) |
| Accounting periods / close | ✅ | accounting_period (open/closed/locked) |
| Balance sheet, income statement | ✅ | statement_line + `financial_position` metric view |
| The asset side / investments | ✅ | investment_holding, investment_transaction, `investment_metrics` |
| Solvency II solo + group capital | ✅ | valuation_run (level/regime) + SCR/MCR/own funds/coverage measures |
| IFRS 17 CSM roll-forward | ✅ | contract_group, csm_movement, `fn_csm_closing` |
| DAC / UPR / LRC / LIC | ✅ | valuation_measure codes (booked via valuation_result) |
| Tax (IPT, corp, deferred) | ✅ | tax_transaction |
| Budget vs actual | ✅ | financial_plan (vs the actuals metric views) |
| FX / presentation currency | ✅ | fx_rate |
| Reserving triangles | ⚠️ derivable | claim_transaction by origin × development — view not yet built |
| QRT / SFCR line templates | ⚠️ partial | statement_line pattern extends to QRT; templates not seeded |
| Cash flow statement | ⚠️ partial | statement_type has CASH_FLOW; mapping not yet seeded |
| Reinsurance recoverables as ledger asset | ⚠️ | cessions exist; not yet posted to a recoverable account |

**Answer: yes, you could build a finance reporting system on this today** —
ledger, statements, capital (solo+group), investments, IFRS 17 and tax are all
present and reconciling. The ⚠️ items are presentation templates and derived
views (triangles, cash-flow mapping, QRT line sets), not missing foundations —
each is a small additive build under the evolution contract.

## Remaining gaps (named, prioritised)

1. **Reserving triangle view** — origin × development over claim_transaction. THE reserving artifact; a view, not new entities.
2. **QRT / SFCR templates** — seed statement_line sets for the Solvency II quantitative templates (S.02.01 balance sheet, S.25 SCR, S.17 technical provisions).
3. **Cash flow statement mapping** — statement_line rows for the CASH_FLOW type.
4. **Reinsurance recoverables** — post ceded reserves to a balance-sheet recoverable asset so the net position is a ledger figure.
5. **Intra-group eliminations** — for a fully honest group consolidation (currently group capital is calibrated, not eliminated up from solos).

None blocks a credible finance-reporting demo; all are on the backlog with a clear home.
