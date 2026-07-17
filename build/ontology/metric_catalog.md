# Bricksurance Data Core - Metric Catalog

*Generated from model v0.8.0. Every measure is defined once here and physicalised as a Unity Catalog metric view; the formula is platform-neutral SQL.*

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

## Performance Metrics (`semantics.performance_metrics`)

The underwriting result: earned premium, incurred claims, expenses and the loss / expense / combined ratios - each defined once. Earning is straight-line daily; expenses are line-level, so combined ratio is meaningful per line and currency (not per underwriting year). Always constrain currency_code. Query measures with MEASURE(name).

**Owner:** Chief Financial Officer · **Certification:** certified · **Source:** `semantics.underwriting_performance`

**Dimensions:** line_of_business, line_of_business_code, currency_code

| Measure | Definition | Formula |
|---|---|---|
| `earned_premium` | Premium earned to date, straight-line daily basis. | `SUM(CASE WHEN component = 'EARNED' THEN amount ELSE 0 END)` |
| `claims_incurred` | Paid plus outstanding net of recoveries. | `SUM(CASE WHEN component = 'INCURRED' THEN amount ELSE 0 END)` |
| `expenses` | Operating, acquisition and claims-handling expenses allocated to the line. | `SUM(CASE WHEN component = 'EXPENSE' THEN amount ELSE 0 END)` |
| `loss_ratio_earned` | Claims incurred over earned premium. | `SUM(CASE WHEN component = 'INCURRED' THEN amount ELSE 0 END) / NULLIF(SUM(CASE WHEN component = 'EARNED' THEN amount ELSE 0 END), 0)` |
| `expense_ratio` | Expenses over earned premium. | `SUM(CASE WHEN component = 'EXPENSE' THEN amount ELSE 0 END) / NULLIF(SUM(CASE WHEN component = 'EARNED' THEN amount ELSE 0 END), 0)` |
| `combined_ratio` | Loss ratio plus expense ratio; below 1.0 is an underwriting profit. | `(SUM(CASE WHEN component = 'INCURRED' THEN amount ELSE 0 END) + SUM(CASE WHEN component = 'EXPENSE' THEN amount ELSE 0 END)) / NULLIF(SUM(CASE WHEN component = 'EARNED' THEN amount ELSE 0 END), 0)` |

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
| `loss_ratio` | Claims incurred divided by gross written premium. Meaningful within a single currency; not premium-earned-adjusted in this version. | `SUM(CASE WHEN transaction_kind = 'CLAIM' THEN amount ELSE 0 END) / NULLIF(SUM(CASE WHEN transaction_kind = 'PREMIUM' THEN amount ELSE 0 END), 0)` |
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
