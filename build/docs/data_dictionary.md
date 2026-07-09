# Bricksurance Data Core — Data Dictionary

*Generated from model v0.4.0. Do not edit.*

## Assumption Status (`reference.assumption_status`)

Maker/checker lifecycle of an assumption set. Only one set per assumption type is APPROVED and in force at a time; superseded sets remain queryable for reproducibility.

**Grain:** One row per assumption status code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| assumption_status_code | string | yes | Code value; referenced by assumption_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** assumption_status_code

## Assumption Type (`reference.assumption_type`)

Kinds of actuarial assumption governed through the assumption-set maker/checker process.

**Grain:** One row per assumption type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| assumption_type_code | string | yes | Code value; referenced by assumption_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** assumption_type_code

## Cause of Loss (`reference.cause_of_loss`)

The peril or event that gave rise to a claim. Aligned to ACORD cause-of-loss vocabulary; one primary cause per claim.

**Grain:** One row per cause of loss code.

**Standards:** Acord: LossCauseCd; Lloyds Cdr: Cause of loss

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| cause_of_loss_code | string | yes | Code value; referenced by cause_of_loss_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** cause_of_loss_code

## Claim Status (`reference.claim_status`)

Lifecycle status of a claim. Financial development lives in claim transactions; status describes the handling state only.

**Grain:** One row per claim status code.

**Standards:** Acord: ClaimStatusCd

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| claim_status_code | string | yes | Code value; referenced by claim_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** claim_status_code

## Claim Transaction Type (`reference.claim_transaction_type`)

Kinds of claim financial movement. Claims finance is transactional: case reserves, payments and recoveries are signed movements, and figures such as outstanding or incurred are always derived by summation.

**Grain:** One row per claim transaction type code.

**Standards:** Acord: Claim payment / reserve patterns of the ACORD Information Model

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| claim_transaction_type_code | string | yes | Code value; referenced by claim_transaction_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** claim_transaction_type_code

## Country (`reference.country`)

Countries the group operates or insures risks in, as ISO 3166-1 alpha-2 codes. A governed subset, extended when the business enters a market.

**Grain:** One row per country code.

**Standards:** Acord: CountryCd (ISO 3166-1)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| country_code | string | yes | Code value; referenced by country_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** country_code

## Coverage Type (`reference.coverage_type`)

Kinds of cover that can be granted under a policy. A policy bundles one or more coverages; limits, deductibles and claims attach at coverage level.

**Grain:** One row per coverage type code.

**Standards:** Acord: CoverageCd

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| coverage_type_code | string | yes | Code value; referenced by coverage_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** coverage_type_code

## Currency (`reference.currency`)

Transaction currencies used by the group, as ISO 4217 alphabetic codes. This is deliberately a governed subset, not the full ISO list: a currency is added here when the business starts writing in it.

**Grain:** One row per currency code.

**Standards:** Acord: CurCd (ISO 4217); Lloyds Cdr: Settlement currency (ISO 4217)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| currency_code | string | yes | Code value; referenced by currency_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** currency_code

## Endorsement Type (`reference.endorsement_type`)

Kinds of mid-term change to a policy. The premium effect of an endorsement is always booked as premium transactions; the endorsement records the contractual change itself.

**Grain:** One row per endorsement type code.

**Standards:** Acord: PolicyChange / endorsement patterns

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| endorsement_type_code | string | yes | Code value; referenced by endorsement_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** endorsement_type_code

## Insured Object Type (`reference.insured_object_type`)

Kinds of object or exposure a policy can insure. Extend with new codes as new lines of business are written (vessels, livestock, cyber estates...).

**Grain:** One row per insured object type code.

**Standards:** Acord: InsuredObject / Risk patterns of the ACORD Information Model

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| insured_object_type_code | string | yes | Code value; referenced by insured_object_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** insured_object_type_code

## Line of Business (`reference.line_of_business`)

Classes of insurance business written by the group, aligned to ACORD LOBCd vocabulary. Extend by adding codes; never repurpose an existing code.

**Grain:** One row per line of business code.

**Standards:** Acord: LOBCd; Lloyds Cdr: Class of business

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| line_of_business_code | string | yes | Code value; referenced by line_of_business_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** line_of_business_code

## Loss Basis (`reference.loss_basis`)

Whether an event loss figure is modelled or reported. Day-one catastrophe numbers are modelled (event footprint against in-force exposure); cedant reports firm up over the following weeks — the basis keeps the two honest.

**Grain:** One row per loss basis code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| loss_basis_code | string | yes | Code value; referenced by loss_basis_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** loss_basis_code

## Party Role Type (`reference.party_role_type`)

The roles a party can play in the business. This code set is the model's number-one extension point: a new kind of counterparty is a new code here, not a new table.

**Grain:** One row per party role type code.

**Standards:** Acord: Party role patterns of the ACORD Information Model

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| party_role_type_code | string | yes | Code value; referenced by party_role_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** party_role_type_code

## Party Type (`reference.party_type`)

Fundamental legal nature of a party. Everything else about a party's place in the business is a role, never a type.

**Grain:** One row per party type code.

**Standards:** Acord: PartyTypeCd

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| party_type_code | string | yes | Code value; referenced by party_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** party_type_code

## Policy Status (`reference.policy_status`)

Lifecycle status of a policy contract. Status reflects the contract as a whole; coverage-level suspension is modelled on the coverage entity.

**Grain:** One row per policy status code.

**Standards:** Acord: PolicyStatusCd

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| policy_status_code | string | yes | Code value; referenced by policy_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** policy_status_code

## Premium Transaction Type (`reference.premium_transaction_type`)

Kinds of premium movement. Premium is always modelled as signed transactions; balances such as gross written premium are derived by summation, never overwritten.

**Grain:** One row per premium transaction type code.

**Standards:** Lloyds Cdr: Premium-related CDR attributes (indicative)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| premium_transaction_type_code | string | yes | Code value; referenced by premium_transaction_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** premium_transaction_type_code

## Quote Status (`reference.quote_status`)

Lifecycle status of a quotation. A quote that converts is linked to the resulting policy; premium only ever arises on the policy, never the quote.

**Grain:** One row per quote status code.

**Standards:** Acord: QuoteStatusCd

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| quote_status_code | string | yes | Code value; referenced by quote_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** quote_status_code

## Run Verdict (`reference.run_verdict`)

Quality-gate verdict of a processing or valuation run. RED runs never feed downstream consumption; the verdict is part of the auditable run record.

**Grain:** One row per run verdict code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| run_verdict_code | string | yes | Code value; referenced by run_verdict_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** run_verdict_code

## Scenario Set Status (`reference.scenario_status`)

Lifecycle of an economic scenario set. Exactly one set is ACTIVE for production valuations; others remain AVAILABLE for analysis.

**Grain:** One row per scenario set status code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| scenario_status_code | string | yes | Code value; referenced by scenario_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** scenario_status_code

## Source System (`reference.source_system`)

Systems of record that feed the data layer. Provenance is part of the model: every core entity carries a source_system_code, and identifiers are only unique within their source system.

**Grain:** One row per source system code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| source_system_code | string | yes | Code value; referenced by source_system_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** source_system_code

## Submission Status (`reference.submission_status`)

Lifecycle of a reinsurance submission from receipt to bind or decline.

**Grain:** One row per submission status code.

**Standards:** Acord: Placement / submission patterns (ACORD GRLC)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| submission_status_code | string | yes | Code value; referenced by submission_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** submission_status_code

## Treaty Type (`reference.treaty_type`)

Forms of treaty reinsurance. Direction (assumed or ceded) is determined by the cedant and reinsurer party roles on the treaty, not by this code.

**Grain:** One row per treaty type code.

**Standards:** Acord: Reinsurance agreement patterns (ACORD GRLC)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| treaty_type_code | string | yes | Code value; referenced by treaty_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** treaty_type_code

## Valuation Measure (`reference.valuation_measure`)

Financial measures produced by valuation processes across regimes. One code set serves life and non-life, Solvency II and IFRS 17: a measure is a defined quantity, and new regimes add codes, not tables.

**Grain:** One row per valuation measure code.

**Standards:** Lloyds Cdr: n/a — regime measures per Solvency II / IFRS 17 definitions

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| valuation_measure_code | string | yes | Code value; referenced by valuation_measure_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** valuation_measure_code

## Data Dictionary (`reference.data_dictionary`)

Machine-readable dictionary of every entity and attribute in the model, generated from the specs. Include this table in every data share so the semantics travel with the data.

**Grain:** One row per attribute per entity per model version.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| entity_name | string | yes | Entity (table) the attribute belongs to. |  |  |  |
| attribute_name | string | yes | Attribute (column) name. |  |  |  |
| data_type | string | yes | Logical, platform-neutral data type. |  |  |  |
| is_required | boolean | yes | Whether the attribute is mandatory. |  |  |  |
| definition | string | yes | Business definition of the attribute. |  |  |  |
| data_classification | string |  | Data classification: public, internal, confidential or pii. |  |  |  |
| acord_ref | string |  | ACORD vocabulary crosswalk reference. |  |  |  |
| lloyds_cdr_ref | string |  | Lloyd's Core Data Record crosswalk reference. |  |  |  |
| model_version | string | yes | Version of bricksurance-data-core this row was generated from. |  |  |  |

**Primary key:** entity_name, attribute_name, model_version

## Claim (`claim.claim`)

A demand for indemnity under a policy arising from a loss event. The claim record holds the event and handling state; all financial development lives in claim transactions.

**Grain:** One row per claim per source system.

**Standards:** Acord: Claim (ACORD Information Model); Lloyds Cdr: Claim-level attributes (indicative)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| claim_id | string | yes | Stable, source-agnostic identifier for the claim, owned by the data layer. | internal |  |  |
| policy_id | string | yes | Policy the claim is made under. | internal |  |  |
| coverage_id | string |  | Coverage the claim attaches to, where the source provides it. | internal |  |  |
| claim_number | string | yes | Claim number as issued by the claims system. Unique within a source system - always interpret together with source_system_code. | confidential | ClaimNumber | Claim reference |
| claim_status_code | string | yes | Current handling status of the claim. |  | ClaimStatusCd |  |
| cause_of_loss_code | string | yes | Primary peril or event that gave rise to the claim. |  | LossCauseCd | Cause of loss |
| loss_date | date | yes | Date the loss occurred. |  | LossDt | Date of loss |
| reported_date | date | yes | Date the loss was first reported to the insurer. Must be on or after loss_date. |  | ReportedDt |  |
| description | string |  | Free-text description of the loss circumstances. | confidential |  |  |
| source_system_code | string | yes | System of record the claim originates from. | internal |  |  |

**Primary key:** claim_id
**Natural key:** source_system_code, claim_number
**Quality — reported_after_loss:** `reported_date >= loss_date` — A loss cannot be reported before it happens.

## Claim Transaction (`claim.claim_transaction`)

A signed financial movement on a claim: case reserve movements, indemnity and expense payments, and recoveries. Outstanding, paid and incurred are always derived by summation over these movements, never stored as balances.

**Grain:** One row per financial movement per claim.

**Standards:** Acord: Claim payment / reserve patterns of the ACORD Information Model

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| claim_transaction_id | string | yes | Identifier for the claim transaction. | internal |  |  |
| claim_id | string | yes | Claim the movement belongs to. | internal |  |  |
| claim_transaction_type_code | string | yes | Kind of financial movement. |  |  |  |
| amount | decimal(18,2) | yes | Signed amount in the transaction currency. Reserve increases positive, reserve releases negative; payments positive; recoveries negative from the insurer's cost perspective. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. |  |  |  |
| transaction_date | date | yes | Date the movement was booked. |  |  |  |
| source_system_code | string | yes | System of record the movement originates from. | internal |  |  |

**Primary key:** claim_transaction_id

## Premium Bordereau Line (inbound) (`exchange.premium_bordereau_line`)

The canonical form of an inbound premium bordereau line, as reported by a coverholder or broker. Messy source files land in the exchange domain and are mapped into this shape - using the data dictionary as the contract - before flowing into the core model.

**Grain:** One row per policy per reporting month per inbound bordereau.

**Standards:** Lloyds Cdr: Coverholder premium reporting attributes (indicative)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| bordereau_line_id | string | yes | Identifier for the bordereau line, assigned on ingestion. | internal |  |  |
| reporting_month | date | yes | First day of the calendar month the bordereau reports on. |  |  |  |
| coverholder_name | string | yes | Name of the coverholder or broker submitting the bordereau. | confidential |  |  |
| policy_number | string | yes | Policy reference as reported by the coverholder; matched to the core model downstream. | confidential |  |  |
| insured_name | string |  | Name of the insured as reported. | pii |  |  |
| line_of_business_code | string | yes | Line of business, mapped from the coverholder's own class descriptions to the canonical code set. |  |  |  |
| inception_date | date | yes | Cover inception as reported. |  |  |  |
| expiry_date | date |  | Cover expiry as reported. |  |  |  |
| currency_code | string | yes | Currency of the reported amounts. |  |  |  |
| gross_premium | decimal(18,2) | yes | Gross written premium reported for the line. | confidential |  |  |
| commission_amount | decimal(18,2) |  | Coverholder commission reported for the line. | confidential |  |  |
| risk_country_code | string |  | Country of the risk location, where reported. |  |  |  |
| risk_postcode | string |  | Postal code of the risk location, where reported. | confidential |  |  |
| source_system_code | string | yes | Provenance of the line; coverholder bordereaux use COVERHOLDER_BDX. | internal |  |  |

**Primary key:** bordereau_line_id

## Valuation Result (`finance.valuation_result`)

A published valuation figure: one measure (BEL, technical provision, IBNR, SCR, CSM...) for one line of business and cohort, produced by exactly one auditable valuation run. One shape serves life and non-life, Solvency II and IFRS 17 - new regimes add measure codes, not tables.

**Grain:** One row per valuation run per line of business per measure per cohort.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| valuation_result_id | string | yes | Identifier for the result row. | internal |  |  |
| valuation_run_id | string | yes | The run that produced this figure. | internal |  |  |
| line_of_business_code | string | yes | Line of business the figure relates to. |  |  |  |
| valuation_measure_code | string | yes | Which defined measure this figure is. |  |  |  |
| cohort | string |  | Optional sub-division (e.g. an age-by-term band or underwriting-year cohort). |  |  |  |
| amount | decimal(18,2) | yes | The figure, in the stated currency. Sign follows the measure's own convention. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. |  |  |  |

**Primary key:** valuation_result_id

## Assumption Set (`life.assumption_set`)

A versioned, governed set of actuarial assumptions (mortality, lapse, expense, economic). Sets move through a maker/checker lifecycle; valuation runs record exactly which approved set they used, which is what makes any past result reproducible.

**Grain:** One row per assumption set version per assumption type.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| assumption_set_id | string | yes | Identifier for the assumption set version. | internal |  |  |
| assumption_type_code | string | yes | Kind of assumption governed by this set. |  |  |  |
| assumption_status_code | string | yes | Maker/checker lifecycle status. |  |  |  |
| version | integer | yes | Monotonic version number within the assumption type. |  |  |  |
| description | string |  | What changed in this version and why. |  |  |  |
| effective_from | date |  | First valuation date this set applies to, once approved. |  |  |  |
| approved_by | string |  | Checker who approved or rejected the set. | internal |  |  |
| approved_at | timestamp |  | When the approval decision was made. |  |  |  |
| source_system_code | string | yes | System of record the assumption set originates from. | internal |  |  |

**Primary key:** assumption_set_id

## Model Point (`life.model_point`)

A grouped model point for life valuation: policies compressed into cohorts (attained age by outstanding term) at a valuation date. Model points are derived from in-force life policies; the grouping is proven back to the policy count and sum assured it represents.

**Grain:** One row per cohort per line of business per valuation date.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| model_point_id | string | yes | Identifier for the model point. | internal |  |  |
| valuation_date | date | yes | Valuation date the model point file was cut at. |  |  |  |
| line_of_business_code | string | yes | Life line of business the cohort belongs to. |  |  |  |
| age_attained | integer | yes | Attained age of the cohort at the valuation date. |  |  |  |
| outstanding_term_years | integer | yes | Remaining policy term of the cohort in whole years. |  |  |  |
| policy_count | integer | yes | Number of in-force policies grouped into this model point. |  |  |  |
| sum_assured | decimal(18,2) | yes | Total sum assured of the cohort, in the cohort currency. | confidential |  |  |
| annual_premium | decimal(18,2) |  | Total annualised premium of the cohort. | confidential |  |  |
| currency_code | string | yes | Currency of the monetary amounts. |  |  |  |
| source_system_code | string | yes | System of record the model point file originates from. | internal |  |  |

**Primary key:** model_point_id
**Quality — grouping_proven:** `sum(policy_count) per valuation_date equals the in-force policy count it was cut from` — Model point grouping must reconcile exactly to the underlying book.

## Scenario Set (`life.scenario_set`)

A delivered economic scenario set (risk-free curves, equity paths) used by stochastic valuation. Registered with a lifecycle so exactly one set is active for production runs, and every run records which set it used.

**Grain:** One row per delivered scenario set.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| scenario_set_id | string | yes | Identifier for the scenario set. | internal |  |  |
| name | string | yes | Human-readable name of the set, including its calibration reference. |  |  |  |
| scenario_status_code | string | yes | Lifecycle status; exactly one set is ACTIVE for production. |  |  |  |
| scenario_count | integer |  | Number of stochastic paths in the set. |  |  |  |
| calibration_date | date |  | Market date the set was calibrated to. |  |  |  |
| source_system_code | string | yes | Provenance of the set (vendor delivery or internal generation). | internal |  |  |

**Primary key:** scenario_set_id

## Valuation Run (`life.valuation_run`)

One execution of a valuation process: which valuation date, which approved assumption set, which scenario set, which model version, run by whom, with what quality verdict. The run is the unit of auditability - every published valuation result points back to exactly one run.

**Grain:** One row per valuation run execution.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| valuation_run_id | string | yes | Identifier for the run. | internal |  |  |
| valuation_date | date | yes | Valuation date the run values the book at. |  |  |  |
| run_timestamp | timestamp | yes | When the run executed. |  |  |  |
| assumption_set_id | string |  | Approved assumption set the run used. | internal |  |  |
| scenario_set_id | string |  | Scenario set the run used, for stochastic runs. | internal |  |  |
| model_version | string |  | Version of the valuation model/engine used (e.g. a Unity Catalog model version). |  |  |  |
| run_verdict_code | string | yes | Quality-gate verdict; RED runs never feed published results. |  |  |  |
| run_by | string |  | Operator or service principal that executed the run. | internal |  |  |
| source_system_code | string | yes | System that executed the run. | internal |  |  |

**Primary key:** valuation_run_id

## Party (`party.party`)

A person or organisation the group deals with. A party exists exactly once regardless of how many relationships it has; what the party does (insured, broker, cedant, claimant...) is expressed through party roles, never by duplicating the party.

**Grain:** One row per unique legal person or organisation, mastered across source systems.

**Standards:** Acord: Party (ACORD Information Model)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| party_id | string | yes | Stable, source-agnostic identifier for the party, owned by the data layer. | internal |  |  |
| party_type_code | string | yes | Whether the party is a natural person or a legal entity. |  |  |  |
| name | string | yes | Full legal name of the party. | pii | CommercialName / PersonName |  |
| country_code | string | yes | Country of residence or registration. | pii | CountryCd |  |
| source_system_code | string | yes | System of record this party was mastered from. | internal |  |  |

**Primary key:** party_id

## Party Role (`party.party_role`)

A role a party plays in a specific business context - on a policy, a claim or a treaty. This is the model's central extensibility pattern: a new kind of counterparty is a new party_role_type code plus rows here, never a new table.

**Grain:** One row per role a party plays in one context (policy, claim, treaty, quote or submission) for a period of time. Exactly one of policy_id, claim_id, treaty_id, quote_id and submission_id is populated.

**Standards:** Acord: PartyRole patterns of the ACORD Information Model

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| party_role_id | string | yes | Identifier for this role assignment. | internal |  |  |
| party_id | string | yes | The party playing the role. | internal |  |  |
| party_role_type_code | string | yes | Which role the party plays in the context. |  |  |  |
| policy_id | string |  | Policy context of the role, when the role is played on a policy. | internal |  |  |
| claim_id | string |  | Claim context of the role, when the role is played on a claim. | internal |  |  |
| treaty_id | string |  | Treaty context of the role, when the role is played on a treaty. | internal |  |  |
| quote_id | string |  | Quote context of the role, when the role is played on a quotation. | internal |  |  |
| submission_id | string |  | Submission context of the role, when the role is played on a reinsurance submission. | internal |  |  |
| start_date | date | yes | Date from which the role applies (inclusive). |  |  |  |
| end_date | date |  | Date on which the role ceased (inclusive); empty while the role is current. |  |  |  |

**Primary key:** party_role_id
**Quality — exactly_one_context:** `exactly one of policy_id, claim_id, treaty_id, quote_id, submission_id is not null` — A role is always played in exactly one business context.

## Coverage (`policy.coverage`)

A specific cover granted under a policy, with its own limit and deductible. A policy bundles one or more coverages; claims attach to coverages where the source data allows it.

**Grain:** One row per coverage granted under a policy.

**Standards:** Acord: Coverage (ACORD Information Model)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| coverage_id | string | yes | Identifier for the coverage. | internal |  |  |
| policy_id | string | yes | Policy the coverage is granted under. | internal |  |  |
| coverage_type_code | string | yes | Kind of cover granted. |  | CoverageCd |  |
| limit_amount | decimal(18,2) |  | Maximum amount payable under this coverage, in the policy currency; empty where unlimited or not applicable. |  | Limit | Limit of liability |
| deductible_amount | decimal(18,2) |  | Amount borne by the insured before this coverage responds, in the policy currency. |  | Deductible | Deductible / excess |
| sum_insured_amount | decimal(18,2) |  | Declared value insured under this coverage, in the policy currency. |  |  |  |

**Primary key:** coverage_id

## Endorsement (`policy.endorsement`)

A mid-term change to a policy contract. The endorsement records the contractual change; any premium effect is booked as premium transactions referencing the same policy, never stored here.

**Grain:** One row per endorsement per policy.

**Standards:** Acord: PolicyChange / endorsement patterns

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| endorsement_id | string | yes | Identifier for the endorsement. | internal |  |  |
| policy_id | string | yes | Policy being endorsed. | internal |  |  |
| endorsement_type_code | string | yes | Kind of contractual change. |  |  |  |
| effective_date | date | yes | Date the change takes effect (inclusive). |  |  |  |
| description | string |  | Free-text description of the change as recorded. | confidential |  |  |
| source_system_code | string | yes | System of record the endorsement originates from. | internal |  |  |

**Primary key:** endorsement_id

## Insured Object (`policy.insured_object`)

A concrete object or exposure insured under a policy - a building, a vehicle, a shipment, a set of operations. Location lives here, which makes this the anchor for exposure and accumulation analysis.

**Grain:** One row per insured object under a policy.

**Standards:** Acord: InsuredObject / Risk (ACORD Information Model)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| insured_object_id | string | yes | Identifier for the insured object. | internal |  |  |
| policy_id | string | yes | Policy the object is insured under. | internal |  |  |
| insured_object_type_code | string | yes | Kind of object or exposure insured. |  |  |  |
| description | string |  | Human-readable description of the object, as declared. | confidential |  |  |
| country_code | string | yes | Country where the object is located or the exposure arises. |  |  |  |
| postcode | string |  | Postal code of the object's location, where applicable; drives geographic accumulation. | confidential |  | Risk location |

**Primary key:** insured_object_id

## Policy (`policy.policy`)

A contract of insurance between an insurer and one or more policyholders, under which the insurer provides cover for defined risks in exchange for premium. This is the contract-level record: coverages, insured objects, premium transactions and parties are separate entities that reference it.

**Grain:** One row per policy contract per source system. Mid-term changes are modelled as endorsements (future entity), not as new rows here.

**Standards:** Acord: Policy (ACORD Information Model, P&C); Lloyds Cdr: Contract-level attributes of the Lloyd's Core Data Record (indicative)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| policy_id | string | yes | Stable, source-agnostic identifier for the policy. A surrogate key owned by the data layer, not by any policy administration system. | internal |  |  |
| policy_number | string | yes | Policy number as issued to the policyholder. Unique within a source system, not globally - always interpret together with source_system_code. | confidential | PolicyNumber | Contract reference |
| source_system_code | string | yes | System of record this policy originates from. Provenance is part of the model, not an afterthought. | internal |  |  |
| line_of_business_code | string | yes | Line of business written under this policy. |  | LOBCd | Class of business |
| policy_status_code | string | yes | Current lifecycle status of the policy. |  | PolicyStatusCd |  |
| inception_date | date | yes | Date on which cover begins (inclusive). |  | EffectiveDt | Inception date |
| expiry_date | date | yes | Date on which cover ends (inclusive). Must be on or after inception_date. |  | ExpirationDt | Expiry date |
| underwriting_year | integer | yes | Year of account to which the policy is allocated; drives reinsurance cession and market reporting. |  |  | Year of account |
| currency_code | string | yes | Original currency of the policy. Monetary amounts on child entities are expressed in this currency unless explicitly stated otherwise. |  | CurCd | Settlement currency |

**Primary key:** policy_id
**Natural key:** source_system_code, policy_number
**Quality — cover_period_valid:** `expiry_date >= inception_date` — Cover cannot end before it begins.

## Premium Transaction (`policy.premium_transaction`)

A signed premium movement on a policy. Premium is transactional by design: figures such as gross written premium are derived by summing transactions, never stored as overwritable balances.

**Grain:** One row per premium movement per policy (and coverage, where known).

**Standards:** Acord: Premium / MoneyProvision patterns of the ACORD Information Model; Lloyds Cdr: Premium attributes (indicative)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| premium_transaction_id | string | yes | Identifier for the premium transaction. | internal |  |  |
| policy_id | string | yes | Policy the premium movement belongs to. | internal |  |  |
| coverage_id | string |  | Coverage the movement is allocated to, where the source provides that split. | internal |  |  |
| premium_transaction_type_code | string | yes | Kind of premium movement. |  |  |  |
| amount | decimal(18,2) | yes | Signed amount of the movement in the transaction currency: written and positive adjustments positive, returns negative. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. |  |  |  |
| transaction_date | date | yes | Date the movement was booked. |  |  |  |
| source_system_code | string | yes | System of record the movement originates from. | internal |  |  |

**Primary key:** premium_transaction_id

## Quote (`policy.quote`)

A quotation for insurance cover. Quotes live upstream of policies: a converted quote links to the policy issued from it, closing the quote-to-policy thread that pricing and underwriting processes work in. Premium only ever arises on the policy.

**Grain:** One row per quotation per source system.

**Standards:** Acord: Quote / PolicyQuoteInqRq patterns

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| quote_id | string | yes | Stable, source-agnostic identifier for the quote, owned by the data layer. | internal |  |  |
| quote_number | string | yes | Quote reference as issued; unique within a source system. | confidential |  |  |
| policy_id | string |  | Policy issued from this quote; populated only when the quote converted. | internal |  |  |
| line_of_business_code | string | yes | Line of business quoted. |  |  |  |
| quote_status_code | string | yes | Lifecycle status of the quote. |  |  |  |
| quote_date | date | yes | Date the quotation was produced. |  |  |  |
| requested_inception_date | date |  | Cover start date requested by the prospect. |  |  |  |
| quoted_gross_premium | decimal(18,2) |  | Gross premium quoted, in the quote currency; empty while the quote is open. | confidential |  |  |
| currency_code | string | yes | Currency of the quoted premium. |  |  |  |
| source_system_code | string | yes | System of record the quote originates from. | internal |  |  |

**Primary key:** quote_id
**Natural key:** source_system_code, quote_number

## Vehicle (`policy.vehicle`)

Motor-specific detail for an insured object of type VEHICLE. This is the model's typed-satellite pattern: the generic insured_object stays lean, and object types that need depth get a satellite entity - vessels, buildings surveys or cyber estates would follow the same shape.

**Grain:** One row per vehicle per insured object.

**Standards:** Acord: Vehicle (ACORD Information Model, personal/commercial auto)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| vehicle_id | string | yes | Identifier for the vehicle record. | internal |  |  |
| insured_object_id | string | yes | The insured object this vehicle detail belongs to (object type VEHICLE). | internal |  |  |
| registration_number | string |  | Vehicle registration mark. | pii | VehIdentificationNumber / registration |  |
| make | string |  | Manufacturer. |  |  |  |
| model | string |  | Model designation. |  |  |  |
| year_of_manufacture | integer |  | Year of manufacture. |  |  |  |

**Primary key:** vehicle_id

## Catastrophe Event (`reinsurance.cat_event`)

A named catastrophe event (windstorm, flood...) that losses accumulate against, across the direct book and the treaty portfolio. Event losses - modelled on day one, reported as cedant figures firm up - reference this event.

**Grain:** One row per catastrophe event.

**Standards:** Acord: Catastrophe / event patterns

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| cat_event_id | string | yes | Identifier for the event. | internal |  |  |
| event_name | string | yes | Market name of the event (e.g. a named windstorm). |  |  |  |
| cause_of_loss_code | string | yes | Primary peril of the event. |  |  |  |
| event_date | date | yes | Date of the event (first landfall or onset). |  |  |  |
| country_code | string |  | Primary country affected, where a single country applies. |  |  |  |
| industry_loss_estimate | decimal(18,2) |  | Market-wide insured loss estimate, in the stated currency. |  |  |  |
| currency_code | string |  | Currency of the industry loss estimate. |  |  |  |
| source_system_code | string | yes | System of record the event was registered in. | internal |  |  |

**Primary key:** cat_event_id

## Cession (`reinsurance.cession`)

The link between direct business and a treaty: which policy (or coverage) is ceded to which treaty, and to what share. Ceded premium and recoveries are derived by applying the ceded share to the underlying transactions.

**Grain:** One row per policy (or coverage, where the split exists) per treaty.

**Standards:** Acord: Cession patterns (ACORD GRLC)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| cession_id | string | yes | Identifier for the cession. | internal |  |  |
| policy_id | string | yes | Policy being ceded. | internal |  |  |
| coverage_id | string |  | Coverage being ceded, where cession applies at coverage level. | internal |  |  |
| treaty_id | string | yes | Treaty the business is ceded to. | internal |  |  |
| ceded_share | decimal(5,4) | yes | Share of the risk ceded under this cession, as a fraction between 0 and 1. | confidential |  |  |

**Primary key:** cession_id

## Event Loss (`reinsurance.event_loss`)

A loss figure attributed to a catastrophe event - against a treaty (assumed book) or a policy (direct book). The loss basis keeps modelled day-one estimates and firming cedant reports honestly apart; figures are point-in- time as-of snapshots, never overwritten.

**Grain:** One row per event per treaty-or-policy per basis per as-of date.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| event_loss_id | string | yes | Identifier for the loss row. | internal |  |  |
| cat_event_id | string | yes | The catastrophe event the loss belongs to. | internal |  |  |
| treaty_id | string |  | Treaty the loss attaches to, for the assumed book. | internal |  |  |
| policy_id | string |  | Policy the loss attaches to, for the direct book. | internal |  |  |
| loss_basis_code | string | yes | Whether the figure is modelled or reported. |  |  |  |
| gross_loss_amount | decimal(18,2) | yes | Gross loss to the contract, in the stated currency. | confidential |  |  |
| ceded_loss_amount | decimal(18,2) |  | Portion ceded onward under outward protections, where computed. | confidential |  |  |
| currency_code | string | yes | Currency of the amounts. |  |  |  |
| as_of_date | date | yes | Snapshot date of the figure. |  |  |  |

**Primary key:** event_loss_id
**Quality — exactly_one_book:** `exactly one of treaty_id, policy_id is not null` — A loss row belongs to either the assumed or the direct book, never both.

## Submission (`reinsurance.submission`)

A reinsurance submission: a cedant's (or broker's) request for treaty cover, from receipt through triage, pricing and decision. A bound submission links to the treaty it produced. Cedant and broker are party roles on the submission.

**Grain:** One row per submission per source system.

**Standards:** Acord: Placement / submission patterns (ACORD GRLC)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| submission_id | string | yes | Stable identifier for the submission, owned by the data layer. | internal |  |  |
| submission_reference | string | yes | Submission reference as received; unique within a source system. | confidential |  |  |
| treaty_id | string |  | Treaty bound from this submission; populated only when BOUND. | internal |  |  |
| submission_status_code | string | yes | Lifecycle status from receipt to bind or decline. |  |  |  |
| treaty_type_code | string | yes | Form of treaty requested. |  |  |  |
| line_of_business_code | string | yes | Class of business the cover is requested for. |  |  |  |
| underwriting_year | integer | yes | Underwriting year the cover would attach to. |  |  |  |
| requested_limit | decimal(18,2) |  | Limit requested, in the submission currency. | confidential |  |  |
| requested_attachment | decimal(18,2) |  | Attachment point requested, for non-proportional forms. | confidential |  |  |
| currency_code | string | yes | Currency of the requested terms. |  |  |  |
| received_date | date | yes | Date the submission was received. |  |  |  |
| source_system_code | string | yes | System of record the submission originates from. | internal |  |  |

**Primary key:** submission_id
**Natural key:** source_system_code, submission_reference

## Treaty (`reinsurance.treaty`)

A treaty reinsurance contract under which risks are ceded to or assumed from reinsurers. Cedant and reinsurer are party roles on the treaty; which business it covers is expressed through cessions.

**Grain:** One row per treaty contract per underwriting year.

**Standards:** Acord: Reinsurance agreement patterns (ACORD GRLC)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| treaty_id | string | yes | Stable identifier for the treaty, owned by the data layer. | internal |  |  |
| treaty_reference | string | yes | Treaty reference as agreed between the parties. | confidential |  |  |
| treaty_type_code | string | yes | Form of the treaty. |  |  |  |
| line_of_business_code | string | yes | Class of business the treaty covers. |  |  |  |
| underwriting_year | integer | yes | Underwriting year of account of the treaty. |  |  | Year of account |
| inception_date | date | yes | Date treaty cover begins (inclusive). |  |  |  |
| expiry_date | date | yes | Date treaty cover ends (inclusive). Must be on or after inception_date. |  |  |  |
| cession_rate | decimal(5,4) |  | Contractual ceded share for proportional treaties, as a fraction between 0 and 1; empty for non-proportional forms. | confidential |  |  |
| currency_code | string | yes | Currency of the treaty. |  |  |  |
| source_system_code | string | yes | System of record the treaty originates from. | internal |  |  |

**Primary key:** treaty_id
**Quality — cover_period_valid:** `expiry_date >= inception_date` — Treaty cover cannot end before it begins.

## Treaty Layer (`reinsurance.treaty_layer`)

A layer of a treaty programme: limit and attachment for non-proportional forms, with reinstatement terms where they apply. Proportional treaties typically have a single layer carrying the ceded share economics on the treaty itself.

**Grain:** One row per layer per treaty.

**Standards:** Acord: Layer / section patterns (ACORD GRLC)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| treaty_layer_id | string | yes | Identifier for the layer. | internal |  |  |
| treaty_id | string | yes | Treaty the layer belongs to. | internal |  |  |
| layer_number | integer | yes | Position of the layer in the programme, 1 = lowest attachment. |  |  |  |
| limit_amount | decimal(18,2) | yes | Limit of the layer, in the treaty currency. | confidential |  |  |
| attachment_amount | decimal(18,2) |  | Attachment point of the layer; empty for proportional forms. | confidential |  |  |
| reinstatement_count | integer |  | Number of reinstatements available, where applicable. |  |  |  |
| reinstatement_premium_rate | decimal(5,4) |  | Reinstatement premium as a fraction of the layer premium. | confidential |  |  |

**Primary key:** treaty_layer_id
