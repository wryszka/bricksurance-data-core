# Bricksurance Data Core - Metric Catalog

*Generated from model v0.11.0. Every measure is defined once here and physicalised as a Unity Catalog metric view; the formula is platform-neutral SQL.*

## Policy Lifecycle Metrics (`policy_lifecycle.lifecycle_metrics`)

Flow KPIs over the policy event spine - new business, renewals, lapses, cancellations and mid-term adjustments by line, period, channel and actor. Retention is chain-based (renewed over invited). Point-in-time policies-in-force is answered from vw_policy_current (status = IN_FORCE), not here. Query measures with MEASURE(name).

**Owner:** Head of Operations · **Certification:** draft · **Source:** `policy_lifecycle.policy_event`

**Dimensions:** policy_event_type_code, line_of_business_code, event_month, actor_type_code, event_source_system_code

| Measure | Definition | Formula |
|---|---|---|
| `event_count` | Total lifecycle events. | `COUNT(event_id)` |
| `new_business_count` | Policies bound (new business). | `COUNT(DISTINCT CASE WHEN policy_event_type_code = 'BOUND' THEN policy_id END)` |
| `renewal_invited_count` | Policies invited to renew. | `COUNT(DISTINCT CASE WHEN policy_event_type_code = 'RENEWAL_INVITED' THEN policy_id END)` |
| `renewed_count` | Policies renewed. | `COUNT(DISTINCT CASE WHEN policy_event_type_code = 'RENEWED' THEN policy_id END)` |
| `lapsed_count` | Policies lapsed at renewal. | `COUNT(DISTINCT CASE WHEN policy_event_type_code = 'LAPSED' THEN policy_id END)` |
| `cancelled_count` | Policies cancelled mid-term (any cause). | `COUNT(DISTINCT CASE WHEN policy_event_type_code IN ('CANCELLED_INSURED', 'CANCELLED_INSURER', 'CANCELLED_NONPAYMENT') THEN policy_id END)` |
| `mta_count` | Mid-term adjustments applied. | `COUNT(CASE WHEN policy_event_type_code = 'MTA_APPLIED' THEN event_id END)` |
| `retention_rate` | Renewed over invited - chain-based retention rate. | `COUNT(DISTINCT CASE WHEN policy_event_type_code = 'RENEWED' THEN policy_id END) / NULLIF(COUNT(DISTINCT CASE WHEN policy_event_type_code = 'RENEWAL_INVITED' THEN policy_id END), 0)` |

## Reserving Metrics (`reserving.reserving_metrics`)

Certified reserving KPIs over the loss-development triangle - cumulative paid and incurred by accident year, line of business and development lag - defined once so the reserving actuary, the finance close and Genie all read the same figures. Ultimate, IBNR and the chain-ladder / Bornhuetter-Ferguson projections are computed in the reserving notebook from these same movements and published to finance.valuation_result. Amounts are in original currency: always group by or filter on currency_code before summing. Query measures with MEASURE(name).

**Owner:** Chief Actuary · **Certification:** certified · **Source:** `reserving.loss_development`

**Dimensions:** accident_year, development_lag, line_of_business, line_of_business_code, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `paid_to_date` | Cumulative paid (indemnity plus expense, net of recoveries) for the selected accident years and development lags, in original currency. | `SUM(incremental_paid)` |
| `incurred_to_date` | Cumulative incurred (paid plus case reserves) for the selection, in original currency - the latest diagonal is the current best estimate before IBNR. | `SUM(incremental_incurred)` |
| `paid_ratio` | Paid over incurred - how far the selected cohort has run off. Low early, approaching 1.0 as an accident year matures. | `SUM(incremental_paid) / NULLIF(SUM(incremental_incurred), 0)` |
| `accident_year_count` | Number of distinct accident years in the selection. | `COUNT(DISTINCT accident_year)` |

## Accumulation Metrics (`semantics.accumulation_metrics`)

Catastrophe accumulation KPIs over event losses - gross loss, ceded recovery and net retained by event and peril. The exposure view reinsurance and capital teams work from, derived from the event-loss records rather than stored. Amounts are in original currency; group by or filter on currency_code before summing money. Query measures with MEASURE(name).

**Owner:** Head of Reinsurance · **Certification:** draft · **Source:** `reinsurance.event_loss`

**Dimensions:** event_name, peril_code, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `event_count` | Number of catastrophe events with losses. | `COUNT(DISTINCT source.cat_event_id)` |
| `gross_loss_total` | Total gross loss across events, in original currency. | `SUM(gross_loss_amount)` |
| `ceded_recovery_total` | Total reinsurance recovery on those losses, in original currency. | `SUM(ceded_loss_amount)` |
| `net_retained_total` | Net retained loss after reinsurance recovery, in original currency. | `SUM(gross_loss_amount - ceded_loss_amount)` |

## Cession Metrics (`semantics.cession_metrics`)

Outward reinsurance KPIs over the cession bordereau: gross and ceded premium by treaty and period. Amounts are in original transaction currency; group by or filter on currency_code before summing money. Query measures with MEASURE(name).

**Owner:** Head of Reinsurance · **Certification:** certified · **Source:** `exchange.cession_bordereau_line`

**Dimensions:** treaty_reference, reporting_month, line_of_business, line_of_business_code, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `gross_premium` | Gross premium on the ceded policies, in original currency. | `SUM(gross_premium)` |
| `ceded_premium` | Premium ceded to reinsurers, in original currency. | `SUM(ceded_premium)` |
| `average_ceded_share` | Effective ceded share - ceded premium over gross premium. | `SUM(ceded_premium) / NULLIF(SUM(gross_premium), 0)` |
| `ceded_policy_count` | Number of distinct policies with ceded premium. | `COUNT(DISTINCT policy_number)` |

## Financial Position (`semantics.financial_position`)

Financial-statement line items assembled from the ledger via the statement mapping - the balance sheet and income statement in business language, by legal entity and regime. Query MEASURE(line_amount) grouped by statement and line; constrain currency_code and reporting_regime.

**Owner:** Financial Controller · **Certification:** certified · **Source:** `finance.journal_line`

**Dimensions:** statement_type, reporting_regime, line_label, legal_entity_id, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `line_amount` | The statement line value, sign-adjusted for presentation. | `SUM(amount * statement_line.sign)` |

## Investment Metrics (`semantics.investment_metrics`)

The asset side: market value, book cost, unrealised gain and investment income by asset class and legal entity. Query with MEASURE(); constrain currency_code.

**Owner:** Chief Investment Officer · **Certification:** draft · **Source:** `investment.investment_holding`

**Dimensions:** asset_class, asset_class_code, legal_entity_id, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `market_value` | Total market value of holdings. | `SUM(market_value)` |
| `book_cost` | Total acquisition cost of holdings. | `SUM(book_cost)` |
| `unrealised_gain` | Market value less book cost. | `SUM(market_value) - SUM(book_cost)` |
| `holding_count` | Number of holdings. | `COUNT(*)` |

## Model Governance Metrics (`semantics.model_governance_metrics`)

Governance KPIs over the model estate - how many models and versions exist, how many are champion versus challenger or retired, by type and purpose. The AI-governance readout the semantic layer can answer directly: which models decide, and are they under control. Query measures with MEASURE(name).

**Owner:** Head of Data Science · **Certification:** draft · **Source:** `model.model_version`

**Dimensions:** model_purpose_code, model_type_code, model_status_code, line_of_business_code

| Measure | Definition | Formula |
|---|---|---|
| `model_version_count` | Number of model versions. | `COUNT(DISTINCT model_version_id)` |
| `model_count` | Number of distinct model assets. | `COUNT(DISTINCT source.model_id)` |
| `champion_count` | Versions currently serving as champion. | `COUNT(DISTINCT CASE WHEN model_status_code = 'CHAMPION' THEN model_version_id END)` |
| `challenger_count` | Versions being evaluated as challengers. | `COUNT(DISTINCT CASE WHEN model_status_code = 'CHALLENGER' THEN model_version_id END)` |
| `retired_count` | Retired versions kept for lineage. | `COUNT(DISTINCT CASE WHEN model_status_code = 'RETIRED' THEN model_version_id END)` |

## Performance Metrics (`semantics.performance_metrics`)

The underwriting result: earned premium, incurred claims, expenses and the loss / expense / combined ratios - each defined once. Earning is straight-line daily; expenses are line-level, so combined ratio is meaningful per line and currency (not per underwriting year). Always constrain currency_code. Query measures with MEASURE(name).

**Owner:** Chief Financial Officer · **Certification:** certified · **Source:** `semantics.underwriting_performance`

**Dimensions:** line_of_business, line_of_business_code, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `earned_premium` | Premium earned to date, straight-line daily basis. | `SUM(CASE WHEN component = 'EARNED' THEN amount ELSE 0 END)` |
| `claims_incurred` | Paid plus outstanding net of recoveries. | `SUM(CASE WHEN component = 'INCURRED' THEN amount ELSE 0 END)` |
| `expenses` | Operating, acquisition and claims-handling expenses allocated to the line. | `SUM(CASE WHEN component = 'EXPENSE' THEN amount ELSE 0 END)` |
| `loss_ratio` | The loss ratio: claims incurred over EARNED premium. This is the canonical, reporting-basis definition. (underwriting_metrics.loss_ratio_written is the quick written-basis view.) Meaningful within a single currency. | `SUM(CASE WHEN component = 'INCURRED' THEN amount ELSE 0 END) / NULLIF(SUM(CASE WHEN component = 'EARNED' THEN amount ELSE 0 END), 0)` |
| `expense_ratio` | Expenses over earned premium. | `SUM(CASE WHEN component = 'EXPENSE' THEN amount ELSE 0 END) / NULLIF(SUM(CASE WHEN component = 'EARNED' THEN amount ELSE 0 END), 0)` |
| `combined_ratio` | Loss ratio plus expense ratio; below 1.0 is an underwriting profit. | `(SUM(CASE WHEN component = 'INCURRED' THEN amount ELSE 0 END) + SUM(CASE WHEN component = 'EXPENSE' THEN amount ELSE 0 END)) / NULLIF(SUM(CASE WHEN component = 'EARNED' THEN amount ELSE 0 END), 0)` |

## Pricing Metrics (`semantics.pricing_metrics`)

Quote and conversion KPIs over the quote book - volumes, conversion and rated versus quoted premium by line and period. The pricing and demand view of the funnel. Amounts are in original quote currency; group by or filter on currency_code before summing money. Query measures with MEASURE(name).

**Owner:** Chief Pricing Actuary · **Certification:** draft · **Source:** `policy.quote`

**Dimensions:** quote_month, line_of_business, line_of_business_code, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `quote_count` | Number of quotes produced. | `COUNT(DISTINCT quote_id)` |
| `converted_count` | Quotes that converted to a policy. | `COUNT(DISTINCT CASE WHEN conversion_flag THEN quote_id END)` |
| `conversion_rate` | Converted quotes over all quotes - the headline conversion rate. | `COUNT(DISTINCT CASE WHEN conversion_flag THEN quote_id END) / NULLIF(COUNT(DISTINCT quote_id), 0)` |
| `quoted_premium_total` | Total gross premium quoted, in original currency. | `SUM(quoted_gross_premium)` |
| `rated_premium_total` | Total technical rated premium, in original currency. | `SUM(rated_gross_premium)` |

## Submission Metrics (`semantics.submission_metrics`)

Reinsurance submission funnel KPIs: volumes and requested capacity by status, form and year. Amounts are in original submission currency; group by or filter on currency_code before summing money. Query measures with MEASURE(name).

**Owner:** Head of Reinsurance · **Certification:** draft · **Source:** `reinsurance.submission`

**Dimensions:** underwriting_year, submission_status, treaty_type_code, line_of_business, line_of_business_code, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `submission_count` | Number of submissions. | `COUNT(DISTINCT submission_id)` |
| `bound_count` | Submissions bound into treaties. | `COUNT(DISTINCT CASE WHEN submission_status_code = 'BOUND' THEN submission_id END)` |
| `bind_ratio` | Bound submissions over all submissions. | `COUNT(DISTINCT CASE WHEN submission_status_code = 'BOUND' THEN submission_id END) / NULLIF(COUNT(DISTINCT submission_id), 0)` |
| `requested_limit_total` | Total limit requested, in original currency. | `SUM(requested_limit)` |

## Trial Balance (`semantics.trial_balance`)

The trial balance: net movement by ledger account, entity and period, from the journal lines. Because every journal balances, the total across all accounts nets to zero - the controller's first check. Query with MEASURE(net_movement); always constrain currency_code.

**Owner:** Financial Controller · **Certification:** certified · **Source:** `finance.journal_line`

**Dimensions:** account_number, account_name, account_type, statement_type, legal_entity_id, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `net_movement` | Net signed movement (debits positive, credits negative). Summed across all accounts this is zero - the balancing check. | `SUM(amount)` |
| `total_debits` | Sum of debit lines. | `SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END)` |
| `total_credits` | Sum of credit lines. | `SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END)` |

## Underwriting Metrics (`semantics.underwriting_metrics`)

Certified underwriting KPIs - premium, claims development and loss ratio - defined once over the canonical model. Measures are in original transaction currency: always group by or filter on currency_code before summing money. Query measures with MEASURE(name).

**Owner:** Chief Underwriting Officer · **Certification:** certified · **Source:** `semantics.financial_transaction`

**Dimensions:** underwriting_year, line_of_business, line_of_business_code, currency_code, transaction_month, cause_of_loss_code

| Measure | Definition | Formula |
|---|---|---|
| `gross_written_premium` | Sum of all premium movements (written, adjustments, returns) - the book's gross written premium in original currency. | `SUM(CASE WHEN transaction_kind = 'PREMIUM' THEN amount ELSE 0 END)` |
| `claims_paid` | Indemnity plus allocated expense paid, gross of recoveries. | `SUM(CASE WHEN transaction_type_code IN ('INDEMNITY_PAYMENT', 'EXPENSE_PAYMENT') THEN amount ELSE 0 END)` |
| `recoveries` | Subrogation, salvage and contribution recoveries (negative amounts). | `SUM(CASE WHEN transaction_type_code = 'RECOVERY' THEN amount ELSE 0 END)` |
| `outstanding_reserve` | Current case reserves - the sum of all signed reserve movements. | `SUM(CASE WHEN transaction_type_code = 'CASE_RESERVE_MOVEMENT' THEN amount ELSE 0 END)` |
| `claims_incurred` | Paid plus outstanding net of recoveries - total claims incurred. | `SUM(CASE WHEN transaction_kind = 'CLAIM' THEN amount ELSE 0 END)` |
| `loss_ratio_written` | Written-basis loss ratio: claims incurred over gross WRITTEN premium - the quick operational view, before premium is earned. The canonical, earned-basis loss ratio is performance_metrics.loss_ratio. Meaningful within a single currency and only over a cohort (underwriting year or the whole book) - never by calendar month, where premium and claims are out of phase. | `SUM(CASE WHEN transaction_kind = 'CLAIM' THEN amount ELSE 0 END) / NULLIF(SUM(CASE WHEN transaction_kind = 'PREMIUM' THEN amount ELSE 0 END), 0)` |
| `policy_count` | Number of distinct policies with premium activity. | `COUNT(DISTINCT CASE WHEN transaction_kind = 'PREMIUM' THEN policy_id END)` |
| `claim_count` | Number of distinct claims with financial activity. | `COUNT(DISTINCT claim_id)` |

## Valuation Metrics (`semantics.valuation_metrics`)

Published valuation figures (BEL, technical provisions, SCR, CSM...) by run, measure and line of business - one semantic surface across life and non-life, Solvency II and IFRS 17. Amounts are in original currency; group by or filter on currency_code and valuation_measure_code before summing. Query measures with MEASURE(name).

**Owner:** Chief Actuary · **Certification:** certified · **Source:** `finance.valuation_result`

**Dimensions:** valuation_date, valuation_measure_code, line_of_business, line_of_business_code, cohort, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `total_amount` | Sum of the figures - only meaningful within one measure and one currency. | `SUM(amount)` |
| `run_count` | Number of distinct producing runs represented. | `COUNT(DISTINCT valuation_run_id)` |
