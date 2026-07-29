# Reporting workbench — merge plan

*Merging the Solvency II and IFRS 17 "reporting workbenches" into one Reporting
workbench with a regime lens, over the shared valuation spine. Plan for review
before build — like docs/APP_PLAN.md.*

## The idea, in one line

Solvency II, IFRS 17 and Statutory are not three reporting systems — they are
**three regulatory lenses on one governed valuation spine.** The model already
proves it: SII *and* IFRS 17 measures live in the **same** `finance.valuation_result`
table (measure codes, not separate tables), and both tie to the **same**
`finance.trial_balance` that nets to zero. So merging isn't a compromise — it
surfaces what the data already is, and it's the strongest top-of-estate demo:
*"two regimes that need two teams and two reconciliations, computed from one
governed close — flip the lens, the source doesn't move."*

## Why merge (not two apps)

- **Proves the thesis hardest.** One valuation run → SII own funds *and* IFRS 17
  equity, both reconciling to one trial balance (0.00). No other workbench makes
  "govern by business meaning, not by tool" this concrete for a CFO/Chief Actuary.
- **It's where the estate lands.** Underwriting → premium → the close; reserving
  IBNR → `valuation_result`; the same governed number flowing into *both* regimes'
  reports. Reporting is the natural top of the workbench family.
- **Composes with the built pattern** — same "workbench = governed view on the
  layer" shell as reserving / underwriting / reinsurance, with a regime lens.

## The design

**One Reporting workbench** (`#/reporting`), house style, a regime lens
(same control as reinsurance's), plus a **persistent reconciliation strip** that
stays true as you switch regime:

- **Lens · Solvency II** — own funds (by tier), SCR / MCR, **coverage ratio solo
  vs group** (diversification is real: solo ≠ group), technical provisions =
  BEL + risk margin. The QRT-shaped view.
- **Lens · IFRS 17** — the **CSM movement waterfall** (opening → new business →
  interest accretion → experience adjustment → release → closing), contract
  groups, onerous / loss-component, LRC / LIC. The disclosure view.
- **Lens · Statutory** — the balance sheet + income statement from
  `statement_line`, and the **trial balance that nets to zero** — the beat that
  ties the other two together.
- **Reconciliation strip (always visible):** "One valuation spine — SII own funds
  and IFRS 17 equity both trace to the same trial balance (0.00)." The proof the
  regimes can't disagree, because they share a source.

Honest guardrail (the caution): **shared spine, distinct regime views** — not a
generic reporting page. Each lens shows what a practitioner in that regime
expects; the merge works because the lens keeps them distinct while the strip
proves they reconcile. Flattening into one table would read as thin.

## Data top-up needed (verified gaps, 2026-07-24)

The spine is live but thin in three spots — a one-pass world_engine top-up
(same approach as reinsurance) makes each lens credible:

| Gap (today) | Top-up |
|---|---|
| **No IFRS_17 valuation runs** — all 5 runs are `SOLVENCY_II` | Add IFRS 17 valuation run(s) so the IFRS 17 lens has its own governed run, not borrowed |
| **CSM waterfall incomplete** — 3 contract groups; movement types missing onerous/loss-component | Add contract groups + a full CSM waterfall incl. an onerous group (loss component), so the §57/§80-style story is real |
| **Own funds has no tier split** — only `ELIGIBLE_OWN_FUNDS_T1`; SCR/MCR one row each | Add T2/T3 tiers + a fuller own-funds breakdown, solo and group, so the SII coverage view looks like a real QRT |
| Statement lines: 8 balance-sheet + 6 income — adequate | (leave; already balances) |

All additive, deterministic, reconciling to the trial balance (which must stay
0.00). No new entities needed — `valuation_result` / `csm_movement` /
`statement_line` already carry the shapes; we add rows + measure codes/tiers.
Likely a couple of new reference codes (own-funds tier, CSM onerous movement).

## Build sequence (after your go)

1. **Data top-up** — world_engine: IFRS 17 run(s), fuller CSM waterfall + onerous
   group, own-funds tiers solo/group. Generate → world_engine → targeted deploy
   (big-INSERT gotcha: apply changed demo-data tables via targeted async) → smoke
   green, trial balance 0.00.
2. **Backend** — `/api/atlas/reporting?regime=` returning the three lenses over
   `valuation_result` / `csm_movement` / `statement_line` / `trial_balance`, plus
   the reconciliation figures (SII own funds, IFRS 17 equity, trial balance).
3. **Frontend** — Reporting view, regime lens + reconciliation strip, house style.
   New nav item + route.
4. **Genie** — reuse / point at the Capital, Investments & IFRS 17 (Group) and
   Finance & Controllership spaces; add a couple of cross-regime benchmark Qs.
5. **Retire / fold** — the separate SII and IFRS 17 tiles/pages in the hub point
   here (supersede-in-place, keep any deep links working).
6. Demo doc (Google Doc), deploy, verify in browser, commit, push, mirror to Drive.

## What this does NOT change

- The `valuation_result` "one shape, many regimes" model — we're surfacing it,
  not re-modelling. New regimes still add measure codes, not tables.
- The existing standalone Solvency II / IFRS 17 demos elsewhere in the estate
  keep working; this is the *governed-layer* reporting view, the reference for
  how they'd consolidate onto the shared model.

## Open question for you

- **Scope:** all three lenses (SII / IFRS 17 / **Statutory**), or just the two
  regulatory regimes? Recommendation: all three — Statutory's balance-sheet +
  trial-balance-nets-to-zero is the beat that ties the reconciliation together.
- **Name:** "Reporting", or "Close & Disclosure"? (leaning Reporting for clarity)
