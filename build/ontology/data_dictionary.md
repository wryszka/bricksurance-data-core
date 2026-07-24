# Bricksurance Data Core — Data Dictionary

*Generated from model v0.9.0. Do not edit.*

## Account Type (`reference.account_type`)

The fundamental classification of a ledger account, which fixes its normal balance and where it lands in the financial statements.

**Grain:** One row per account type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| account_type_code | string | yes | Code value; referenced by account_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** account_type_code

## Appetite Effect (`reference.appetite_effect`)

What a matching appetite rule does to a risk. Appetite lives as data, not as code buried in a rating engine - so agents and humans read the same rules.

**Grain:** One row per appetite effect code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| appetite_effect_code | string | yes | Code value; referenced by appetite_effect_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** appetite_effect_code

## Asset Class (`reference.asset_class`)

Investment asset classes held to back liabilities and capital, aligned to Solvency II asset categories at a working level.

**Grain:** One row per asset class code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| asset_class_code | string | yes | Code value; referenced by asset_class_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** asset_class_code

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

## Business Event Type (`reference.business_event_type`)

Kinds of business event captured on the event stream - the near-real-time face of the model. Extend per domain as processes come online.

**Grain:** One row per business event type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| business_event_type_code | string | yes | Code value; referenced by business_event_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** business_event_type_code

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

## Commission Type (`reference.commission_type`)

Kinds of intermediary remuneration. Commission is transactional - signed movements, never overwritten balances - and disclosable by design.

**Grain:** One row per commission type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| commission_type_code | string | yes | Code value; referenced by commission_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** commission_type_code

## Complaint Category (`reference.complaint_category`)

Root category of a customer complaint, aligned to UK FCA complaints reporting groupings.

**Grain:** One row per complaint category code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| complaint_category_code | string | yes | Code value; referenced by complaint_category_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** complaint_category_code

## Complaint Status (`reference.complaint_status`)

Handling status of a complaint, through to ombudsman referral.

**Grain:** One row per complaint status code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| complaint_status_code | string | yes | Code value; referenced by complaint_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** complaint_status_code

## Consent Purpose (`reference.consent_purpose`)

Purposes a data subject can consent to, per the processing register.

**Grain:** One row per consent purpose code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| consent_purpose_code | string | yes | Code value; referenced by consent_purpose_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** consent_purpose_code

## Consent Status (`reference.consent_status`)

State of a consent record; withdrawal is an auditable event, not a deletion.

**Grain:** One row per consent status code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| consent_status_code | string | yes | Code value; referenced by consent_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** consent_status_code

## Contact Point Type (`reference.contact_point_type`)

Kinds of contact point held for a party.

**Grain:** One row per contact point type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| contact_point_type_code | string | yes | Code value; referenced by contact_point_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** contact_point_type_code

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

## CSM Movement Type (`reference.csm_movement_type`)

Steps in the IFRS 17 contractual service margin roll-forward. The closing CSM is the signed sum of these movements over the opening balance - a balance derived from movements, never overwritten.

**Grain:** One row per csm movement type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| csm_movement_type_code | string | yes | Code value; referenced by csm_movement_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** csm_movement_type_code

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

## Distribution Channel (`reference.distribution_channel`)

How business reaches the insurer. Machine channels are first-class: an agentic buyer is a channel, not an exception.

**Grain:** One row per distribution channel code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| distribution_channel_code | string | yes | Code value; referenced by distribution_channel_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** distribution_channel_code

## Document Type (`reference.document_type`)

Kinds of unstructured content the model governs. Documents carry extracted text so LLM tools can search and cite them under the same governance as structured data.

**Grain:** One row per document type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| document_type_code | string | yes | Code value; referenced by document_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** document_type_code

## Data Subject Request Status (`reference.dsr_status`)

Handling status of a data subject request against the statutory clock.

**Grain:** One row per data subject request status code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| dsr_status_code | string | yes | Code value; referenced by dsr_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** dsr_status_code

## Data Subject Request Type (`reference.dsr_type`)

GDPR data subject request kinds.

**Grain:** One row per data subject request type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| dsr_type_code | string | yes | Code value; referenced by dsr_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** dsr_type_code

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

## Expense Type (`reference.expense_type`)

Kinds of operating expense allocated to lines of business - the missing half of the combined ratio.

**Grain:** One row per expense type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| expense_type_code | string | yes | Code value; referenced by expense_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** expense_type_code

## Fraud Signal Type (`reference.fraud_signal_type`)

Kinds of fraud indicator on a claim. Signals inform investigation; they never auto-decide.

**Grain:** One row per fraud signal type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| fraud_signal_type_code | string | yes | Code value; referenced by fraud_signal_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** fraud_signal_type_code

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

## Investment Transaction Type (`reference.investment_transaction_type`)

Movements on investment holdings. Income and gains flow to the income statement; purchases and sales move the balance sheet.

**Grain:** One row per investment transaction type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| investment_transaction_type_code | string | yes | Code value; referenced by investment_transaction_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** investment_transaction_type_code

## Legal Entity Type (`reference.legal_entity_type`)

The role a legal entity plays in the group's reporting structure. The group holding consolidates its subsidiaries; each subsidiary reports solo.

**Grain:** One row per legal entity type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| legal_entity_type_code | string | yes | Code value; referenced by legal_entity_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** legal_entity_type_code

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

## IFRS 17 Measurement Model (`reference.measurement_model`)

The IFRS 17 measurement model applied to a group of contracts.

**Grain:** One row per ifrs 17 measurement model code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| measurement_model_code | string | yes | Code value; referenced by measurement_model_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** measurement_model_code

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

## Accounting Period Status (`reference.period_status`)

Lifecycle of an accounting period; postings are only allowed while OPEN.

**Grain:** One row per accounting period status code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| period_status_code | string | yes | Code value; referenced by period_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** period_status_code

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

## Product Status (`reference.product_status`)

Lifecycle status of an insurance product.

**Grain:** One row per product status code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| product_status_code | string | yes | Code value; referenced by product_status_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** product_status_code

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

## Receivable Transaction Type (`reference.receivable_transaction_type`)

Premium billing movements. Outstanding debt is the signed sum - invoices positive, cash negative - never a stored balance.

**Grain:** One row per receivable transaction type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| receivable_transaction_type_code | string | yes | Code value; referenced by receivable_transaction_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** receivable_transaction_type_code

## Reporting Level (`reference.reporting_level`)

Whether a figure is a single entity's own return (solo) or the consolidated group position. Solvency II and statutory accounts both require both.

**Grain:** One row per reporting level code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| reporting_level_code | string | yes | Code value; referenced by reporting_level_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** reporting_level_code

## Reporting Regime (`reference.reporting_regime`)

The reporting framework a figure is prepared under. One valuation or statement figure means different things under different regimes; the regime is never assumed.

**Grain:** One row per reporting regime code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| reporting_regime_code | string | yes | Code value; referenced by reporting_regime_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** reporting_regime_code

## Reserving Method (`reference.reserving_method`)

Actuarial methods for projecting ultimate losses from a development triangle. The method is a governed, attestable choice: swapping it produces a new reserve estimate row, never an overwrite, so bases are comparable and the sign-off records which method set the reserves.

**Grain:** One row per reserving method code.

**Standards:** Acord: n/a — actuarial method terminology

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| reserving_method_code | string | yes | Code value; referenced by reserving_method_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** reserving_method_code

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

## Financial Statement Type (`reference.statement_type`)

The primary financial statement a line belongs to.

**Grain:** One row per financial statement type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| statement_type_code | string | yes | Code value; referenced by statement_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** statement_type_code

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

## Tax Type (`reference.tax_type`)

Kinds of tax the group accounts for.

**Grain:** One row per tax type code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| tax_type_code | string | yes | Code value; referenced by tax_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** tax_type_code

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

## Underwriting Decision (`reference.underwriting_decision_type`)

Outcome of an underwriting decision. Every decision records who or what decided and against which appetite rule - human and machine decisions are audited identically.

**Grain:** One row per underwriting decision code.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| underwriting_decision_type_code | string | yes | Code value; referenced by underwriting_decision_type_code columns across the model. |  |  |  |
| label | string | yes | Short human-readable name for the code. |  |  |  |
| description | string | yes | Business definition of the code. |  |  |  |

**Primary key:** underwriting_decision_type_code

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
| entity_owner | string |  | Accountable business owner of the entity, as an org role. |  |  |  |
| entity_maturity | string |  | Certification maturity of the entity: draft or certified. |  |  |  |
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
| claim_status_code | string | yes | Current handling status of the claim. | internal | ClaimStatusCd |  |
| cause_of_loss_code | string | yes | Primary peril or event that gave rise to the claim. | internal | LossCauseCd | Cause of loss |
| loss_date | date | yes | Date the loss occurred. | internal | LossDt | Date of loss |
| reported_date | date | yes | Date the loss was first reported to the insurer. Must be on or after loss_date. | internal | ReportedDt |  |
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
| claim_transaction_type_code | string | yes | Kind of financial movement. | internal |  |  |
| amount | decimal(18,2) | yes | Signed amount in the transaction currency. Reserve increases positive, reserve releases negative; payments positive; recoveries negative from the insurer's cost perspective. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |
| transaction_date | date | yes | Date the movement was booked. | internal |  |  |
| source_system_code | string | yes | System of record the movement originates from. | internal |  |  |

**Primary key:** claim_transaction_id

## Fraud Signal (`claim.fraud_signal`)

A fraud indicator raised on a claim, with its score and provenance. Signals inform SIU referral decisions; a signal is never itself a decision.

**Grain:** One row per signal per claim.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| fraud_signal_id | string | yes | Identifier for the signal. | internal |  |  |
| claim_id | string | yes | Claim the signal concerns. | internal |  |  |
| fraud_signal_type_code | string | yes | Kind of indicator. | internal |  |  |
| score | integer | yes | Signal strength 0-100. | confidential |  |  |
| detected_at | timestamp | yes | When the signal was raised. | internal |  |  |
| detail | string |  | What was observed, in business language. | confidential |  |  |
| source_system_code | string | yes | Detecting system. | internal |  |  |

**Primary key:** fraud_signal_id

## Complaint (`conduct.complaint`)

A customer complaint, categorised per UK FCA reporting groupings and tracked through to ombudsman referral. The conduct domain is where fair treatment becomes measurable.

**Grain:** One row per complaint per source system.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| complaint_id | string | yes | Identifier for the complaint. | internal |  |  |
| complaint_reference | string | yes | Reference as issued to the complainant. | confidential |  |  |
| complainant_party_id | string | yes | The complaining party. | internal |  |  |
| policy_id | string |  | Policy concerned, where applicable. | internal |  |  |
| claim_id | string |  | Claim concerned, where applicable. | internal |  |  |
| complaint_category_code | string | yes | Root category. | internal |  |  |
| complaint_status_code | string | yes | Handling status. | internal |  |  |
| received_date | date | yes | Date received. | internal |  |  |
| closed_date | date |  | Date resolved or referred; empty while open. | internal |  |  |
| redress_amount | decimal(18,2) |  | Redress paid, where upheld, in the stated currency. | confidential |  |  |
| currency_code | string |  | Currency of any redress. | internal |  |  |
| source_system_code | string | yes | System of record. | internal |  |  |

**Primary key:** complaint_id
**Quality — closed_after_received:** `closed_date >= received_date` — A complaint cannot close before it is received.

## Document (`content.document`)

Governed unstructured content: policy wordings, schedules, claim evidence, survey reports, MRC slips. The extracted text is carried in the row so LLM tools search and cite documents under the same classification and lineage as structured data; binary originals live in a Volume referenced by path.

**Grain:** One row per document version.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| document_id | string | yes | Identifier for the document. | internal |  |  |
| document_type_code | string | yes | Kind of document. | internal |  |  |
| title | string | yes | Document title. | internal |  |  |
| product_id | string |  | Product context (wordings attach here). | internal |  |  |
| policy_id | string |  | Policy context (schedules attach here). | internal |  |  |
| claim_id | string |  | Claim context (evidence attaches here). | internal |  |  |
| submission_id | string |  | Submission context (slips attach here). | internal |  |  |
| extracted_text | string |  | Full extracted text, indexed for semantic search. | confidential |  |  |
| volume_path | string |  | Path to the binary original in a governed Volume, where one exists. | internal |  |  |
| created_date | date | yes | Date the document version was created. | internal |  |  |
| source_system_code | string | yes | System of record. | internal |  |  |

**Primary key:** document_id
**Quality — exactly_one_context:** `exactly one of product_id, policy_id, claim_id, submission_id is not null` — A document belongs to exactly one business context.

## Commission Transaction (`distribution.commission_transaction`)

A signed intermediary remuneration movement on a policy. Transactional like all money in this model; disclosable commission is a query, not a project.

**Grain:** One row per commission movement per policy per intermediary.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| commission_transaction_id | string | yes | Identifier for the movement. | internal |  |  |
| policy_id | string | yes | The policy the commission relates to. | internal |  |  |
| party_id | string | yes | The intermediary earning (or repaying) the commission. | internal |  |  |
| commission_type_code | string | yes | Kind of remuneration. | internal |  |  |
| rate | decimal(5,4) |  | Commission rate applied, as a fraction of premium. | confidential |  |  |
| amount | decimal(18,2) | yes | Signed amount in the transaction currency; clawbacks negative. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |
| transaction_date | date | yes | Date the movement was booked. | internal |  |  |
| source_system_code | string | yes | System of record. | internal |  |  |

**Primary key:** commission_transaction_id

## Business Event (`events.business_event`)

The event stream: business moments (quote requested, loss notified, payment made, complaint received) as append-only, timestamped records referencing the entity they concern. This is the near-real-time face of the model and the natural feed for monitoring agents.

**Grain:** One row per business event occurrence; append-only.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| business_event_id | string | yes | Identifier for the event. | internal |  |  |
| business_event_type_code | string | yes | Kind of event. | internal |  |  |
| subject_entity | string | yes | Entity name of the subject (e.g. quote, claim). | internal |  |  |
| subject_id | string | yes | Identifier of the subject row. | internal |  |  |
| occurred_at | timestamp | yes | When the event occurred. | internal |  |  |
| channel_code | string |  | Channel the event arrived through, where relevant. | internal |  |  |
| payload | string |  | Event payload as JSON, schema per event type. | confidential |  |  |
| source_system_code | string | yes | Emitting system. | internal |  |  |

**Primary key:** business_event_id

## Premium Bordereau Line (inbound) (`exchange.premium_bordereau_line`)

The canonical form of an inbound premium bordereau line, as reported by a coverholder or broker. Messy source files land in the exchange domain and are mapped into this shape - using the data dictionary as the contract - before flowing into the core model.

**Grain:** One row per policy per reporting month per inbound bordereau.

**Standards:** Lloyds Cdr: Coverholder premium reporting attributes (indicative)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| bordereau_line_id | string | yes | Identifier for the bordereau line, assigned on ingestion. | internal |  |  |
| reporting_month | date | yes | First day of the calendar month the bordereau reports on. | internal |  |  |
| coverholder_name | string | yes | Name of the coverholder or broker submitting the bordereau. | confidential |  |  |
| policy_number | string | yes | Policy reference as reported by the coverholder; matched to the core model downstream. | confidential |  |  |
| insured_name | string |  | Name of the insured as reported. | pii |  |  |
| line_of_business_code | string | yes | Line of business, mapped from the coverholder's own class descriptions to the canonical code set. | internal |  |  |
| inception_date | date | yes | Cover inception as reported. | internal |  |  |
| expiry_date | date |  | Cover expiry as reported. | internal |  |  |
| currency_code | string | yes | Currency of the reported amounts. | internal |  |  |
| gross_premium | decimal(18,2) | yes | Gross written premium reported for the line. | confidential |  |  |
| commission_amount | decimal(18,2) |  | Coverholder commission reported for the line. | confidential |  |  |
| risk_country_code | string |  | Country of the risk location, where reported. | internal |  |  |
| risk_postcode | string |  | Postal code of the risk location, where reported. | confidential |  |  |
| source_system_code | string | yes | Provenance of the line; coverholder bordereaux use COVERHOLDER_BDX. | internal |  |  |

**Primary key:** bordereau_line_id

## Accounting Period (`finance.accounting_period`)

A financial reporting period for a legal entity, with its open/closed/locked status. Postings are only permitted into open periods; the close process moves periods to locked. The unit the finance calendar runs on.

**Grain:** One row per period per legal entity.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| accounting_period_id | string | yes | Identifier for the period. | internal |  |  |
| legal_entity_id | string | yes | The entity whose books this period governs. | internal |  |  |
| period_label | string | yes | Human label, e.g. 2026-Q2. | confidential |  |  |
| start_date | date | yes | First day of the period. | internal |  |  |
| end_date | date | yes | Last day of the period. | internal |  |  |
| period_status_code | string | yes | Open, closed or locked. | internal |  |  |

**Primary key:** accounting_period_id

## Chart of Account (`finance.chart_of_account`)

The chart of accounts: every ledger account with its type (which fixes its normal balance) and its parent, forming the account hierarchy that statements roll up. This is what turns classified postings into a real general ledger.

**Grain:** One row per ledger account.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| account_id | string | yes | Identifier for the account. | internal |  |  |
| account_number | string | yes | Ledger account number. | confidential |  |  |
| name | string | yes | Account name. | internal |  |  |
| account_type_code | string | yes | Asset, liability, equity, income or expense - fixes the normal balance. | internal |  |  |
| parent_account_id | string |  | Parent account for roll-up; empty at the top of the hierarchy. | internal |  |  |
| statement_type_code | string | yes | Which primary statement the account belongs to. | internal |  |  |

**Primary key:** account_id
**Natural key:** account_number

## Contract Group (IFRS 17) (`finance.contract_group`)

An IFRS 17 group of contracts - the unit of account for the standard: contracts of similar risk, managed together, issued within a year, split by onerous status. Carries the measurement model and links to the entity and line. The CSM roll-forward and the LRC/LIC split hang off this.

**Grain:** One row per group of contracts.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| contract_group_id | string | yes | Identifier for the group of contracts. | internal |  |  |
| legal_entity_id | string | yes | The carrier holding the group. | internal |  |  |
| line_of_business_code | string | yes | Line of business of the group. | internal |  |  |
| cohort_year | integer | yes | Annual cohort (issue year) - contracts more than a year apart cannot share a group. | internal |  |  |
| measurement_model_code | string | yes | IFRS 17 model applied (GMM, PAA, VFA). | internal |  |  |
| onerous | boolean | yes | Whether the group is onerous at initial recognition. | internal |  |  |
| currency_code | string | yes | Currency of the group's measurement. | internal |  |  |

**Primary key:** contract_group_id

## CSM Movement (IFRS 17) (`finance.csm_movement`)

A step in the contractual service margin roll-forward for a group of contracts in a period: opening, new business, interest accretion, experience adjustments and release to profit. The closing CSM is the signed sum over the opening - a balance derived from movements, never overwritten, and produced by an auditable valuation run.

**Grain:** One row per movement type per contract group per period.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| csm_movement_id | string | yes | Identifier for the movement. | internal |  |  |
| contract_group_id | string | yes | The group of contracts. | internal |  |  |
| valuation_run_id | string | yes | The run that produced this movement - the audit anchor. | internal |  |  |
| csm_movement_type_code | string | yes | Which step of the roll-forward this is. | internal |  |  |
| amount | decimal(18,2) | yes | Signed amount in the group currency; release is negative. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |

**Primary key:** csm_movement_id

## Expense Transaction (`finance.expense_transaction`)

An operating expense allocated to a line of business - the missing half of the combined ratio, transactional like all money in the model.

**Grain:** One row per expense allocation per line per period booking.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| expense_transaction_id | string | yes | Identifier for the expense movement. | internal |  |  |
| legal_entity_id | string |  | The entity the expense is booked in. | internal |  |  |
| expense_type_code | string | yes | Kind of expense. | internal |  |  |
| line_of_business_code | string | yes | Line the expense is allocated to. | internal |  |  |
| amount | decimal(18,2) | yes | Signed amount in the stated currency. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |
| transaction_date | date | yes | Booking date. | internal |  |  |
| source_system_code | string | yes | System of record. | internal |  |  |

**Primary key:** expense_transaction_id

## Financial Plan (`finance.financial_plan`)

A budgeted or forecast figure for a legal entity, line and measure in a period - the plan side of budget-versus-actual. FP&A cannot function without it; pairing it with the actuals metric views is the variance story.

**Grain:** One row per plan version per entity per line per measure per period.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| financial_plan_id | string | yes | Identifier for the plan figure. | internal |  |  |
| legal_entity_id | string | yes | The entity the plan is for. | internal |  |  |
| plan_version | string | yes | Plan version, e.g. 2026 Budget v1. | internal |  |  |
| line_of_business_code | string |  | Line of business, where the plan is at line level. | internal |  |  |
| plan_measure | string | yes | What is planned, e.g. gross_written_premium or combined_ratio. | internal |  |  |
| period_label | string | yes | Period the figure applies to, e.g. 2026-Q3. | confidential |  |  |
| amount | decimal(18,2) | yes | Planned value in the stated currency (or a ratio, per plan_measure). | confidential |  |  |
| currency_code | string |  | Currency, for monetary plan measures. | internal |  |  |

**Primary key:** financial_plan_id

## FX Rate (`finance.fx_rate`)

A foreign-exchange rate to the group presentation currency at a date - what makes group consolidation across multi-currency subsidiaries a real number instead of a per-currency caveat.

**Grain:** One row per from-currency per rate date.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| fx_rate_id | string | yes | Identifier for the rate. | internal |  |  |
| from_currency_code | string | yes | Currency being translated. | internal |  |  |
| to_currency_code | string | yes | Presentation currency translated to. | internal |  |  |
| rate_date | date | yes | Date the rate applies. | confidential |  |  |
| rate | decimal(18,8) | yes | Units of to-currency per one unit of from-currency. | confidential |  |  |

**Primary key:** fx_rate_id
**Natural key:** from_currency_code, to_currency_code, rate_date

## Journal (`finance.journal`)

A journal entry header: a balanced set of debit and credit lines posted to one legal entity in one period. Every journal's lines sum to zero - that invariant is what makes this a real double-entry ledger rather than a pile of classified amounts.

**Grain:** One row per journal entry.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| journal_id | string | yes | Identifier for the journal. | internal |  |  |
| journal_reference | string | yes | Human reference for the journal. | internal |  |  |
| legal_entity_id | string | yes | The entity whose ledger this posts to. | internal |  |  |
| accounting_period_id | string | yes | The period the journal posts into; must be open at posting time. | internal |  |  |
| posting_date | date | yes | Ledger date of the entry. | internal |  |  |
| description | string |  | What the entry records. | confidential |  |  |
| source_system_code | string | yes | System that raised the journal. | internal |  |  |

**Primary key:** journal_id
**Quality — journal_balances:** `sum(journal_line.amount) per journal_id = 0` — Debits and credits within a journal must net to zero.

## Journal Line (`finance.journal_line`)

A single debit or credit line of a journal, posted to one ledger account and carrying a signed amount (debits positive, credits negative) plus its source operational transaction. Trial balance and financial statements are sums over these lines; the link to source rows makes the ledger reconcile to the sub-ledgers by construction.

**Grain:** One row per posting line.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| journal_line_id | string | yes | Identifier for the line. | internal |  |  |
| journal_id | string | yes | The journal this line belongs to. | internal |  |  |
| account_id | string | yes | The ledger account posted to. | internal |  |  |
| amount | decimal(18,2) | yes | Signed amount in the entity's functional currency: debits positive, credits negative. Lines within a journal sum to zero. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |
| source_entity | string |  | Entity name of the originating operational row (e.g. premium_transaction). | internal |  |  |
| source_id | string |  | Identifier of the originating operational row, for reconciliation. | internal |  |  |

**Primary key:** journal_line_id

## Receivable Transaction (`finance.receivable_transaction`)

Premium billing and collection movements on a policy. Written premium is earned exposure; this is the cash reality - outstanding and aged debt are signed sums over these rows.

**Grain:** One row per billing movement per policy.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| receivable_transaction_id | string | yes | Identifier for the movement. | internal |  |  |
| policy_id | string | yes | Policy billed. | internal |  |  |
| legal_entity_id | string |  | The entity carrying the receivable. | internal |  |  |
| receivable_transaction_type_code | string | yes | Kind of movement; invoices positive, receipts negative. | internal |  |  |
| amount | decimal(18,2) | yes | Signed amount in the stated currency. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |
| transaction_date | date | yes | Booking date. | internal |  |  |
| due_date | date |  | Payment due date, for invoices - the anchor for ageing. | internal |  |  |
| source_system_code | string | yes | System of record. | internal |  |  |

**Primary key:** receivable_transaction_id

## Statement Line (`finance.statement_line`)

The mapping from ledger accounts to financial-statement line items - how the chart of accounts becomes a balance sheet, income statement and cash flow. Different regimes present differently, so a line carries its regime; this is what lets the same ledger produce a Solvency II balance sheet and an IFRS/statutory one.

**Grain:** One row per statement line item per account per regime.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| statement_line_id | string | yes | Identifier for the mapping row. | internal |  |  |
| statement_type_code | string | yes | Which primary statement the line belongs to. | internal |  |  |
| reporting_regime_code | string | yes | Presentation regime this mapping is for. | internal |  |  |
| line_label | string | yes | The statement line item, e.g. 'Net earned premium' or 'Total assets'. | confidential |  |  |
| line_order | integer | yes | Presentation order within the statement. | internal |  |  |
| account_id | string | yes | The ledger account that rolls up into this line. | internal |  |  |
| sign | integer | yes | +1 or -1 applied to the account balance for presentation. | internal |  |  |

**Primary key:** statement_line_id

## Tax Transaction (`finance.tax_transaction`)

A tax movement for a legal entity - insurance premium tax, corporation tax, deferred tax. IPT in particular is a real line on every premium; this makes the tax position queryable rather than buried.

**Grain:** One row per tax movement per entity.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| tax_transaction_id | string | yes | Identifier for the movement. | internal |  |  |
| legal_entity_id | string | yes | The entity the tax relates to. | internal |  |  |
| tax_type_code | string | yes | Kind of tax. | internal |  |  |
| policy_id | string |  | Source policy, for premium tax. | internal |  |  |
| amount | decimal(18,2) | yes | Signed amount in the stated currency. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |
| transaction_date | date | yes | Booking date. | internal |  |  |
| source_system_code | string | yes | System of record. | internal |  |  |

**Primary key:** tax_transaction_id

## Valuation Result (`finance.valuation_result`)

A published valuation figure: one measure (BEL, technical provision, IBNR, SCR, CSM...) for one line of business and cohort, produced by exactly one auditable valuation run. One shape serves life and non-life, Solvency II and IFRS 17 - new regimes add measure codes, not tables.

**Grain:** One row per valuation run per line of business per measure per cohort.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| valuation_result_id | string | yes | Identifier for the result row. | internal |  |  |
| valuation_run_id | string | yes | The run that produced this figure. | internal |  |  |
| line_of_business_code | string | yes | Line of business the figure relates to. | internal |  |  |
| valuation_measure_code | string | yes | Which defined measure this figure is. | internal |  |  |
| cohort | string |  | Optional sub-division (e.g. an age-by-term band or underwriting-year cohort). | internal |  |  |
| amount | decimal(18,2) | yes | The figure, in the stated currency. Sign follows the measure's own convention. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |

**Primary key:** valuation_result_id

## Investment Holding (`investment.investment_holding`)

An investment asset held by a legal entity - the asset side of the balance sheet. Book cost and market value are carried here; income and revaluations are transactional. Without this domain there is no balance sheet and no asset-liability conversation.

**Grain:** One row per holding per legal entity.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| investment_holding_id | string | yes | Identifier for the holding. | internal |  |  |
| legal_entity_id | string | yes | The entity that owns the asset. | internal |  |  |
| asset_class_code | string | yes | Asset class of the holding. | internal |  |  |
| instrument_name | string | yes | Name or description of the instrument. | internal |  |  |
| isin | string |  | ISIN where the instrument is a listed security. | internal |  |  |
| book_cost | decimal(18,2) | yes | Acquisition cost in the entity's functional currency. | confidential |  |  |
| market_value | decimal(18,2) | yes | Current market value in the entity's functional currency. | confidential |  |  |
| currency_code | string | yes | Currency of the amounts. | internal |  |  |
| valuation_date | date | yes | Date the market value was struck. | internal |  |  |
| source_system_code | string | yes | System of record (typically an investment/custody system). | internal |  |  |

**Primary key:** investment_holding_id

## Investment Transaction (`investment.investment_transaction`)

A movement on an investment holding - purchase, sale, coupon, dividend or fair-value revaluation. Investment income and gains (the P&L line) and the movement in asset values (the balance sheet) are both derived from these.

**Grain:** One row per investment movement.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| investment_transaction_id | string | yes | Identifier for the movement. | internal |  |  |
| investment_holding_id | string | yes | The holding moved. | internal |  |  |
| investment_transaction_type_code | string | yes | Kind of movement. | internal |  |  |
| amount | decimal(18,2) | yes | Signed amount in the holding currency. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |
| transaction_date | date | yes | Date of the movement. | internal |  |  |
| source_system_code | string | yes | System of record. | internal |  |  |

**Primary key:** investment_transaction_id

## Assumption Set (`life.assumption_set`)

A versioned, governed set of actuarial assumptions (mortality, lapse, expense, economic). Sets move through a maker/checker lifecycle; valuation runs record exactly which approved set they used, which is what makes any past result reproducible.

**Grain:** One row per assumption set version per assumption type.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| assumption_set_id | string | yes | Identifier for the assumption set version. | internal |  |  |
| assumption_type_code | string | yes | Kind of assumption governed by this set. | internal |  |  |
| assumption_status_code | string | yes | Maker/checker lifecycle status. | internal |  |  |
| version | integer | yes | Monotonic version number within the assumption type. | internal |  |  |
| description | string |  | What changed in this version and why. | confidential |  |  |
| effective_from | date |  | First valuation date this set applies to, once approved. | internal |  |  |
| approved_by | string |  | Checker who approved or rejected the set. | internal |  |  |
| approved_at | timestamp |  | When the approval decision was made. | internal |  |  |
| source_system_code | string | yes | System of record the assumption set originates from. | internal |  |  |

**Primary key:** assumption_set_id

## Model Point (`life.model_point`)

A grouped model point for life valuation: policies compressed into cohorts (attained age by outstanding term) at a valuation date. Model points are derived from in-force life policies; the grouping is proven back to the policy count and sum assured it represents.

**Grain:** One row per cohort per line of business per valuation date.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| model_point_id | string | yes | Identifier for the model point. | internal |  |  |
| valuation_date | date | yes | Valuation date the model point file was cut at. | internal |  |  |
| line_of_business_code | string | yes | Life line of business the cohort belongs to. | internal |  |  |
| age_attained | integer | yes | Attained age of the cohort at the valuation date. | internal |  |  |
| outstanding_term_years | integer | yes | Remaining policy term of the cohort in whole years. | internal |  |  |
| policy_count | integer | yes | Number of in-force policies grouped into this model point. | internal |  |  |
| sum_assured | decimal(18,2) | yes | Total sum assured of the cohort, in the cohort currency. | confidential |  |  |
| annual_premium | decimal(18,2) |  | Total annualised premium of the cohort. | confidential |  |  |
| currency_code | string | yes | Currency of the monetary amounts. | internal |  |  |
| source_system_code | string | yes | System of record the model point file originates from. | internal |  |  |

**Primary key:** model_point_id
**Quality — grouping_proven:** `sum(policy_count) per valuation_date equals the in-force policy count it was cut from` — Model point grouping must reconcile exactly to the underlying book.

## Scenario Set (`life.scenario_set`)

A delivered economic scenario set (risk-free curves, equity paths) used by stochastic valuation. Registered with a lifecycle so exactly one set is active for production runs, and every run records which set it used.

**Grain:** One row per delivered scenario set.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| scenario_set_id | string | yes | Identifier for the scenario set. | internal |  |  |
| name | string | yes | Human-readable name of the set, including its calibration reference. | internal |  |  |
| scenario_status_code | string | yes | Lifecycle status; exactly one set is ACTIVE for production. | internal |  |  |
| scenario_count | integer |  | Number of stochastic paths in the set. | internal |  |  |
| calibration_date | date |  | Market date the set was calibrated to. | internal |  |  |
| source_system_code | string | yes | Provenance of the set (vendor delivery or internal generation). | internal |  |  |

**Primary key:** scenario_set_id

## Valuation Run (`life.valuation_run`)

One execution of a valuation process: which valuation date, which approved assumption sets (one per assumption type, via valuation_run_assumption), which scenario set, which model version, run by whom, with what quality verdict. The run is the unit of auditability - every published valuation result points back to exactly one run.

**Grain:** One row per valuation run execution.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| valuation_run_id | string | yes | Identifier for the run. | internal |  |  |
| legal_entity_id | string |  | The legal entity the run values. With reporting_level this is what distinguishes a subsidiary's solo run from the group consolidated run. | internal |  |  |
| reporting_level_code | string |  | Solo (this entity) or group (consolidated). | internal |  |  |
| reporting_regime_code | string |  | Regime the run is prepared under (Solvency II, IFRS 17...). | internal |  |  |
| valuation_date | date | yes | Valuation date the run values the book at. | internal |  |  |
| run_timestamp | timestamp | yes | When the run executed. | internal |  |  |
| scenario_set_id | string |  | Scenario set the run used, for stochastic runs. | internal |  |  |
| model_version | string |  | Version of the valuation model/engine used (e.g. a Unity Catalog model version). | internal |  |  |
| run_verdict_code | string | yes | Quality-gate verdict; RED runs never feed published results. | internal |  |  |
| run_by | string |  | Operator or service principal that executed the run. | internal |  |  |
| source_system_code | string | yes | System that executed the run. | internal |  |  |

**Primary key:** valuation_run_id

## Valuation Run Assumption (`life.valuation_run_assumption`)

Which assumption sets a valuation run used - one row per assumption set, typically one per assumption type (mortality, lapse, expense, economic). This junction is what makes any past result exactly reproducible: run plus sets plus scenario plus model version is the full recipe.

**Grain:** One row per assumption set used by a valuation run.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| valuation_run_id | string | yes | The valuation run. | internal |  |  |
| assumption_set_id | string | yes | An assumption set the run used. | internal |  |  |

**Primary key:** valuation_run_id, assumption_set_id

## Legal Entity (`org.legal_entity`)

A legal entity in the group's structure and the reporting hierarchy that connects them. This is the spine of the whole system: policies, valuations, ledgers and statements all belong to a legal entity, and every entity rolls up to the group holding via parent_legal_entity_id. Solo reporting is one entity; group reporting is the consolidation up this tree.

**Grain:** One row per legal entity.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| legal_entity_id | string | yes | Identifier for the legal entity. | internal |  |  |
| name | string | yes | Registered name of the entity. | internal |  |  |
| legal_entity_type_code | string | yes | Role in the reporting structure (holding, insurance subsidiary...). | internal |  |  |
| parent_legal_entity_id | string |  | The consolidating parent; empty only for the top group holding. This self-reference is the consolidation tree. | internal |  |  |
| country_code | string | yes | Country of incorporation and primary supervision. | internal |  |  |
| functional_currency_code | string | yes | The entity's functional currency; group presentation currency is the holding's. | internal |  |  |
| lei | string |  | Legal Entity Identifier (ISO 17442), where registered. | internal |  |  |
| source_system_code | string | yes | System of record. | internal |  |  |

**Primary key:** legal_entity_id

## Consent (`party.consent`)

A data subject's consent for a processing purpose. Withdrawal is a state change with a timestamp, never a deletion - the consent history is itself evidence.

**Grain:** One row per party per purpose per consent grant.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| consent_id | string | yes | Identifier for the consent record. | internal |  |  |
| party_id | string | yes | The consenting data subject. | internal |  |  |
| consent_purpose_code | string | yes | Purpose consented to. | internal |  |  |
| consent_status_code | string | yes | Current state of the consent. | internal |  |  |
| granted_at | timestamp | yes | When consent was given. | internal |  |  |
| withdrawn_at | timestamp |  | When consent was withdrawn, where it was. | internal |  |  |
| channel_code | string |  | Channel the consent was captured through. | internal |  |  |

**Primary key:** consent_id

## Contact Point (`party.contact_point`)

A contact point for a party. PII is deliberately concentrated here and on party - the erasure design in PRIVACY.md redacts these anchors while transactional history keeps its surrogate keys.

**Grain:** One row per contact point per party.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| contact_point_id | string | yes | Identifier for the contact point. | internal |  |  |
| party_id | string | yes | The party contactable here. | internal |  |  |
| contact_point_type_code | string | yes | Kind of contact point. | internal |  |  |
| value | string | yes | The address, number or email itself. | pii |  |  |
| preferred | boolean | yes | Whether this is the party's preferred contact point of its kind. | internal |  |  |

**Primary key:** contact_point_id

## Data Subject Request (`party.data_subject_request`)

A GDPR data subject request (access, erasure, rectification, portability) tracked against the statutory clock. Erasure execution follows the design in PRIVACY.md.

**Grain:** One row per request received.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| data_subject_request_id | string | yes | Identifier for the request. | internal |  |  |
| party_id | string | yes | The requesting data subject. | internal |  |  |
| dsr_type_code | string | yes | Kind of request. | internal |  |  |
| dsr_status_code | string | yes | Handling status. | internal |  |  |
| received_date | date | yes | Date received; the statutory window starts here. | internal |  |  |
| completed_date | date |  | Date fulfilled or refused. | internal |  |  |
| notes | string |  | Handling notes, including refusal grounds where applicable. | confidential |  |  |

**Primary key:** data_subject_request_id
**Quality — completed_after_received:** `completed_date >= received_date` — A request cannot complete before it is received.

## Party (`party.party`)

A person or organisation the group deals with. A party exists exactly once regardless of how many relationships it has; what the party does (insured, broker, cedant, claimant...) is expressed through party roles, never by duplicating the party.

**Grain:** One row per unique legal person or organisation, mastered across source systems.

**Standards:** Acord: Party (ACORD Information Model)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| party_id | string | yes | Stable, source-agnostic identifier for the party, owned by the data layer. | internal |  |  |
| party_type_code | string | yes | Whether the party is a natural person or a legal entity. | internal |  |  |
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
| party_role_type_code | string | yes | Which role the party plays in the context. | internal |  |  |
| policy_id | string |  | Policy context of the role, when the role is played on a policy. | internal |  |  |
| claim_id | string |  | Claim context of the role, when the role is played on a claim. | internal |  |  |
| treaty_id | string |  | Treaty context of the role, when the role is played on a treaty. | internal |  |  |
| quote_id | string |  | Quote context of the role, when the role is played on a quotation. | internal |  |  |
| submission_id | string |  | Submission context of the role, when the role is played on a reinsurance submission. | internal |  |  |
| start_date | date | yes | Date from which the role applies (inclusive). | internal |  |  |
| end_date | date |  | Date on which the role ceased (inclusive); empty while the role is current. | internal |  |  |

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
| coverage_type_code | string | yes | Kind of cover granted. | internal | CoverageCd |  |
| limit_amount | decimal(18,2) |  | Maximum amount payable under this coverage, in the policy currency; empty where unlimited or not applicable. | confidential | Limit | Limit of liability |
| deductible_amount | decimal(18,2) |  | Amount borne by the insured before this coverage responds, in the policy currency. | confidential | Deductible | Deductible / excess |
| sum_insured_amount | decimal(18,2) |  | Declared value insured under this coverage, in the policy currency. | confidential |  |  |

**Primary key:** coverage_id

## Endorsement (`policy.endorsement`)

A mid-term change to a policy contract. The endorsement records the contractual change; any premium effect is booked as premium transactions referencing the same policy, never stored here.

**Grain:** One row per endorsement per policy.

**Standards:** Acord: PolicyChange / endorsement patterns

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| endorsement_id | string | yes | Identifier for the endorsement. | internal |  |  |
| policy_id | string | yes | Policy being endorsed. | internal |  |  |
| endorsement_type_code | string | yes | Kind of contractual change. | internal |  |  |
| effective_date | date | yes | Date the change takes effect (inclusive). | internal |  |  |
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
| insured_object_type_code | string | yes | Kind of object or exposure insured. | internal |  |  |
| description | string |  | Human-readable description of the object, as declared. | confidential |  |  |
| country_code | string | yes | Country where the object is located or the exposure arises. | internal |  |  |
| postcode | string |  | Postal code of the object's location, where applicable; drives geographic accumulation. | confidential |  | Risk location |
| latitude | decimal(9,6) |  | Latitude of the object's location, where geocoded. | confidential |  |  |
| longitude | decimal(9,6) |  | Longitude of the object's location, where geocoded. | confidential |  |  |

**Primary key:** insured_object_id

## Policy (`policy.policy`)

A contract of insurance between an insurer and one or more policyholders, under which the insurer provides cover for defined risks in exchange for premium. This is the contract-level record: coverages, insured objects, premium transactions and parties are separate entities that reference it.

**Grain:** One row per policy contract per source system. Mid-term changes are modelled as endorsements (future entity), not as new rows here.

**Standards:** Acord: Policy (ACORD Information Model, P&C); Lloyds Cdr: Contract-level attributes of the Lloyd's Core Data Record (indicative)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| policy_id | string | yes | Stable, source-agnostic identifier for the policy. A surrogate key owned by the data layer, not by any policy administration system. | internal |  |  |
| policy_number | string | yes | Policy number as issued to the policyholder. Unique within a source system, not globally - always interpret together with source_system_code. | confidential | PolicyNumber | Contract reference |
| legal_entity_id | string |  | The carrier that wrote the policy - which subsidiary owns it. The anchor for solo-vs-group reporting of the underwriting book. | internal |  |  |
| source_system_code | string | yes | System of record this policy originates from. Provenance is part of the model, not an afterthought. | internal |  |  |
| line_of_business_code | string | yes | Line of business written under this policy. | internal | LOBCd | Class of business |
| policy_status_code | string | yes | Current lifecycle status of the policy. | internal | PolicyStatusCd |  |
| inception_date | date | yes | Date on which cover begins (inclusive). | internal | EffectiveDt | Inception date |
| expiry_date | date | yes | Date on which cover ends (inclusive). Must be on or after inception_date. | internal | ExpirationDt | Expiry date |
| underwriting_year | integer | yes | Year of account to which the policy is allocated; drives reinsurance cession and market reporting. | internal |  | Year of account |
| currency_code | string | yes | Original currency of the policy. Monetary amounts on child entities are expressed in this currency unless explicitly stated otherwise. | internal | CurCd | Settlement currency |
| renews_policy_id | string |  | The expiring policy this one renews, closing the retention chain; empty for new business. | internal |  |  |

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
| premium_transaction_type_code | string | yes | Kind of premium movement. | internal |  |  |
| amount | decimal(18,2) | yes | Signed amount of the movement in the transaction currency: written and positive adjustments positive, returns negative. | confidential |  |  |
| currency_code | string | yes | Currency of the amount. | internal |  |  |
| transaction_date | date | yes | Date the movement was booked. | internal |  |  |
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
| line_of_business_code | string | yes | Line of business quoted. | internal |  |  |
| quote_status_code | string | yes | Lifecycle status of the quote. | internal |  |  |
| quote_date | date | yes | Date the quotation was produced. | internal |  |  |
| requested_inception_date | date |  | Cover start date requested by the prospect. | internal |  |  |
| quoted_gross_premium | decimal(18,2) |  | Gross premium quoted, in the quote currency; empty while the quote is open. | confidential |  |  |
| currency_code | string | yes | Currency of the quoted premium. | internal |  |  |
| source_system_code | string | yes | System of record the quote originates from. | internal |  |  |
| product_id | string |  | The product quoted, where the product catalog applies. | internal |  |  |
| distribution_channel_code | string |  | Channel the quote was requested through. | internal |  |  |

**Primary key:** quote_id
**Natural key:** source_system_code, quote_number

## Underwriting Decision (`policy.underwriting_decision`)

A recorded underwriting decision on a quote: the outcome, who or what decided (human underwriter or named agent), and the appetite rule applied. Machine decisions are audited to exactly the same standard as human ones - that is the condition for letting agents underwrite at all.

**Grain:** One row per decision per quote.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| underwriting_decision_id | string | yes | Identifier for the decision. | internal |  |  |
| quote_id | string | yes | The quote decided on. | internal |  |  |
| underwriting_decision_type_code | string | yes | The outcome. | internal |  |  |
| appetite_rule_id | string |  | The appetite rule the decision applied, where rule-driven. | internal |  |  |
| decided_by | string | yes | The human underwriter or named agent/system that decided. | internal |  |  |
| decided_by_agent | boolean | yes | True when the decision was taken autonomously by software. | internal |  |  |
| decided_at | timestamp | yes | When the decision was taken. | internal |  |  |
| rationale | string |  | Free-text rationale, human- or agent-written. | confidential |  |  |

**Primary key:** underwriting_decision_id

## Vehicle (`policy.vehicle`)

Motor-specific detail for an insured object of type VEHICLE. This is the model's typed-satellite pattern: the generic insured_object stays lean, and object types that need depth get a satellite entity - vessels, buildings surveys or cyber estates would follow the same shape.

**Grain:** One row per vehicle per insured object.

**Standards:** Acord: Vehicle (ACORD Information Model, personal/commercial auto)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| vehicle_id | string | yes | Identifier for the vehicle record. | internal |  |  |
| insured_object_id | string | yes | The insured object this vehicle detail belongs to (object type VEHICLE). | internal |  |  |
| registration_number | string |  | Vehicle registration mark. | pii | VehIdentificationNumber / registration |  |
| make | string |  | Manufacturer. | internal |  |  |
| model | string |  | Model designation. | internal |  |  |
| year_of_manufacture | integer |  | Year of manufacture. | internal |  |  |

**Primary key:** vehicle_id

## Appetite Rule (`product.appetite_rule`)

An underwriting appetite statement as data: for a product (or a whole line), a bounded condition and its effect - within appetite, refer, or out of appetite. Humans read the same rules agents execute, and every underwriting decision cites the rule it applied.

**Grain:** One row per active appetite rule.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| appetite_rule_id | string | yes | Identifier for the rule. | internal |  |  |
| product_id | string |  | Product the rule scopes to; empty when the rule applies to the whole line. | internal |  |  |
| line_of_business_code | string | yes | Line of business the rule applies to. | internal |  |  |
| rule_order | integer | yes | Evaluation order; first matching terminal effect wins. | internal |  |  |
| description | string | yes | The rule in business language - what it checks and why it exists. | confidential |  |  |
| max_sum_insured | decimal(18,2) |  | Upper sum-insured bound for the effect to apply, in the product currency. | confidential |  |  |
| country_code | string |  | Country the rule scopes to, where geographic. | internal |  |  |
| appetite_effect_code | string | yes | What happens when the rule matches. | internal |  |  |
| effective_from | date | yes | First date the rule applies. | internal |  |  |
| effective_to | date |  | Last date the rule applies; empty while current. | internal |  |  |

**Primary key:** appetite_rule_id

## Product (`product.product`)

A machine-readable insurance product: what is offered, under which line of business, at which base rate. Products are what quotes are requested against - by humans, aggregators or buyer agents alike - and what wordings, questions and appetite rules attach to.

**Grain:** One row per product version offered.

**Standards:** Acord: Product / program patterns

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| product_id | string | yes | Identifier for the product. | internal |  |  |
| product_code | string | yes | Marketing/product code, unique within the source system. | internal |  |  |
| name | string | yes | Product name as marketed. | internal |  |  |
| line_of_business_code | string | yes | Line of business the product is written under. | internal |  |  |
| product_status_code | string | yes | Lifecycle status. | internal |  |  |
| base_rate | decimal(10,6) |  | Indicative base rate per unit of sum insured, used for indicative quotes only. | confidential |  |  |
| currency_code | string | yes | Default currency of the product. | internal |  |  |
| source_system_code | string | yes | System of record. | internal |  |  |

**Primary key:** product_id
**Natural key:** source_system_code, product_code

## Product Coverage (`product.product_coverage`)

A coverage the product offers, with its default limits. Policy coverages are instances of these offers.

**Grain:** One row per coverage type offered by a product.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| product_coverage_id | string | yes | Identifier for the offered coverage. | internal |  |  |
| product_id | string | yes | The offering product. | internal |  |  |
| coverage_type_code | string | yes | Kind of cover offered. | internal |  |  |
| default_limit_amount | decimal(18,2) |  | Default limit offered, in the product currency. | confidential |  |  |
| default_deductible_amount | decimal(18,2) |  | Default deductible, in the product currency. | confidential |  |  |
| optional | boolean | yes | Whether the coverage is optional (true) or core to the product (false). | internal |  |  |

**Primary key:** product_coverage_id

## Underwriting Question (`product.underwriting_question`)

A question the product asks at quotation. The question set is data, so any channel - a form, an aggregator API or a buyer agent - can discover what the product needs to know and answer it programmatically.

**Grain:** One row per question per product.

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| underwriting_question_id | string | yes | Identifier for the question. | internal |  |  |
| product_id | string | yes | The product asking the question. | internal |  |  |
| question_order | integer | yes | Presentation order. | internal |  |  |
| question_text | string | yes | The question as asked. | internal |  |  |
| answer_type | string | yes | Expected answer type - boolean, number, text or a code. | internal |  |  |
| required | boolean | yes | Whether an answer is mandatory to quote. | internal |  |  |

**Primary key:** underwriting_question_id

## Catastrophe Event (`reinsurance.cat_event`)

A named catastrophe event (windstorm, flood...) that losses accumulate against, across the direct book and the treaty portfolio. Event losses - modelled on day one, reported as cedant figures firm up - reference this event.

**Grain:** One row per catastrophe event.

**Standards:** Acord: Catastrophe / event patterns

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| cat_event_id | string | yes | Identifier for the event. | internal |  |  |
| event_name | string | yes | Market name of the event (e.g. a named windstorm). | internal |  |  |
| cause_of_loss_code | string | yes | Primary peril of the event. | internal |  |  |
| event_date | date | yes | Date of the event (first landfall or onset). | internal |  |  |
| country_code | string |  | Primary country affected, where a single country applies. | internal |  |  |
| industry_loss_estimate | decimal(18,2) |  | Market-wide insured loss estimate, in the stated currency. | internal |  |  |
| currency_code | string |  | Currency of the industry loss estimate. | internal |  |  |
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
| loss_basis_code | string | yes | Whether the figure is modelled or reported. | internal |  |  |
| gross_loss_amount | decimal(18,2) | yes | Gross loss to the contract, in the stated currency. | confidential |  |  |
| ceded_loss_amount | decimal(18,2) |  | Portion ceded onward under outward protections, where computed. | confidential |  |  |
| currency_code | string | yes | Currency of the amounts. | internal |  |  |
| as_of_date | date | yes | Snapshot date of the figure. | internal |  |  |

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
| submission_status_code | string | yes | Lifecycle status from receipt to bind or decline. | internal |  |  |
| treaty_type_code | string | yes | Form of treaty requested. | internal |  |  |
| line_of_business_code | string | yes | Class of business the cover is requested for. | internal |  |  |
| underwriting_year | integer | yes | Underwriting year the cover would attach to. | internal |  |  |
| requested_limit | decimal(18,2) |  | Limit requested, in the submission currency. | confidential |  |  |
| requested_attachment | decimal(18,2) |  | Attachment point requested, for non-proportional forms. | confidential |  |  |
| currency_code | string | yes | Currency of the requested terms. | internal |  |  |
| received_date | date | yes | Date the submission was received. | internal |  |  |
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
| treaty_type_code | string | yes | Form of the treaty. | internal |  |  |
| line_of_business_code | string | yes | Class of business the treaty covers. | internal |  |  |
| underwriting_year | integer | yes | Underwriting year of account of the treaty. | internal |  | Year of account |
| inception_date | date | yes | Date treaty cover begins (inclusive). | internal |  |  |
| expiry_date | date | yes | Date treaty cover ends (inclusive). Must be on or after inception_date. | internal |  |  |
| cession_rate | decimal(5,4) |  | Contractual ceded share for proportional treaties, as a fraction between 0 and 1; empty for non-proportional forms. | confidential |  |  |
| currency_code | string | yes | Currency of the treaty. | internal |  |  |
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
| layer_number | integer | yes | Position of the layer in the programme, 1 = lowest attachment. | internal |  |  |
| limit_amount | decimal(18,2) | yes | Limit of the layer, in the treaty currency. | confidential |  |  |
| attachment_amount | decimal(18,2) |  | Attachment point of the layer; empty for proportional forms. | confidential |  |  |
| reinstatement_count | integer |  | Number of reinstatements available, where applicable. | internal |  |  |
| reinstatement_premium_rate | decimal(5,4) |  | Reinstatement premium as a fraction of the layer premium. | confidential |  |  |

**Primary key:** treaty_layer_id

## Reserve Estimate (`reserving.reserve_estimate`)

A published reserving result: the projected ultimate loss, paid-to-date, case reserves, IBNR and total outstanding for one accident year and line of business, produced by one reserving method (chain-ladder, Bornhuetter-Ferguson) on one dated triangle. The estimate is the actuary's signed output; the method used is a governed, attestable choice, and the IBNR ties back to finance.valuation_result. Swapping method produces a new row, never an overwrite - so every basis and its result is auditable side by side.

**Grain:** One row per accident year per line of business per method per valuation date.

**Standards:** Acord: Reserve / loss-development patterns (indicative)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| reserve_estimate_id | string | yes | Identifier for the reserve estimate row. | internal |  |  |
| valuation_date | date | yes | The as-at date of the triangle this estimate was produced from. | internal |  |  |
| accident_year | integer | yes | Accident year the estimate is for. | internal |  |  |
| line_of_business_code | string | yes | Line of business the estimate is for. | internal |  |  |
| reserving_method_code | string | yes | The actuarial method used to project the ultimate. | internal |  |  |
| currency_code | string | yes | Currency of the amounts. | internal |  |  |
| paid_to_date | decimal(18,2) | yes | Cumulative paid on the latest diagonal for this accident year. | confidential |  |  |
| case_reserves | decimal(18,2) | yes | Current case reserves (incurred minus paid) on the latest diagonal. | confidential |  |  |
| ultimate_loss | decimal(18,2) | yes | The projected ultimate loss under the chosen method. | confidential |  |  |
| ibnr | decimal(18,2) | yes | Incurred but not reported - ultimate loss minus incurred to date. Ties to the IBNR figure published in finance.valuation_result. | confidential |  |  |
| outstanding | decimal(18,2) | yes | Total outstanding - ultimate loss minus paid to date (case reserves plus IBNR). | confidential |  |  |
| source_system_code | string | yes | The reserving engine that produced the estimate. | internal |  |  |

**Primary key:** reserve_estimate_id
**Quality — ibnr_reconciles:** `abs((paid_to_date + case_reserves + ibnr) - ultimate_loss) < 1.0` — Paid plus case reserves plus IBNR must reconcile to the projected ultimate.
**Quality — ultimate_covers_paid:** `ultimate_loss >= paid_to_date` — A projected ultimate cannot be below what has already been paid.
