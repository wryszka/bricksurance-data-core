# Metrics Strategy

How business measures are defined, owned and served — once — and why that is
the difference between an LLM that answers and an LLM that guesses.

## 1. Principles

1. **A metric is defined exactly once**, in a `metric_view` spec in the model,
   compiled to a Unity Catalog metric view. Apps, dashboards, Genie and agents
   all query the same `MEASURE()` — nobody re-implements *loss ratio* in a
   BI tool or a notebook.
2. **Balances are derived, never stored.** GWP, outstanding reserves,
   incurred: all sums over signed transactions. Any published figure (e.g. a
   quarter-end case-reserve total) must tie back to the transactions that
   produced it — and the smoke tests enforce exactly that.
3. **Every measure carries an honest definition** including its limits:
   our loss ratio states it is not earned-adjusted; every money measure
   states its currency discipline. A metric that hides its caveats is a
   governance incident in waiting.
4. **Ownership is named per domain.** Underwriting metrics belong to the
   underwriting data owner, valuation measures to the chief actuary's office.
   Changing a measure definition follows the evolution contract
   ([EVOLUTION.md](EVOLUTION.md)) — a definition change is a versioned event,
   not an edit.

## 2. The metric estate

| Metric view | Domain scope | Measures |
|---|---|---|
| `underwriting_metrics` | direct P&C book | gross_written_premium, claims_paid, recoveries, outstanding_reserve, claims_incurred, loss_ratio, policy_count, claim_count |
| `cession_metrics` | outward reinsurance | gross_premium, ceded_premium, average_ceded_share, ceded_policy_count |
| `submission_metrics` | inward reinsurance funnel | submission_count, bound_count, bind_ratio, requested_limit_total |
| `valuation_metrics` | published valuations (all regimes) | total_amount (per measure code), run_count |

Roadmap: earned premium (needs earning patterns), combined ratio (needs
expense allocation), group consolidation across currencies (needs FX policy —
deliberately absent until it can be honest).

## 3. Hard rules, learned live

These exist because Genie taught us they matter; they are now policy for
every metric view:

- **Label + code dimension pairs.** Every label dimension (e.g.
  `line_of_business` = 'Commercial Property') ships with a sibling
  `_code` dimension (COMMERCIAL_PROPERTY), and both descriptions say which is
  which. Twice, an LLM filtered a label column with a code and got an empty —
  and confidently wrong — answer. The fix belongs in the model, not the
  prompt.
- **Currency discipline.** Measures are in original currency; every metric
  view's description and every money measure's definition says "group by or
  filter on currency_code before summing". No silent cross-currency sums.
- **Measure-code constraint.** Where one view serves many measures
  (`valuation_metrics` spans BEL to CSM), definitions instruct constraining
  `valuation_measure_code` before aggregation.

## 4. LLM benchmarks are the regression tests of semantics

Each Genie space carries benchmark questions whose answers are stored as SQL
ground truths. They serve two jobs: they steer Genie, and they are **the
acceptance test of the semantic layer** — if the model, the metric views and
the instructions are right, the questions come back with reconciling numbers
(GWP by line ties to transactions; ceded premium ties to 30% of the ceded
book's GWP; Term Life BEL matches the valuation run's published result).
When a benchmark breaks after a model change, semantics regressed — treat it
like a failing test, because it is one.

## 5. Adopter guidance

Start with **five measures you argue about most** (typically GWP, incurred,
loss ratio, outstanding, one regime measure). Write their definitions with
the business owner — including the caveats — put them in metric-view specs,
and point one Genie space at them. The moment two departments get the same
number from the same question, the rest of the argument makes itself.
