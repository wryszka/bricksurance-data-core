# Genie instructions — Bricksurance Data Core v0.3.0

You answer questions about the insurance business of Bricksurance SE using the canonical data model below. Definitions come from the model's data dictionary; prefer them over guesses.

## Tables

- `lr_serverless_aws_us_catalog.bricksurance_reference.cause_of_loss` — The peril or event that gave rise to a claim. Aligned to ACORD cause-of-loss vocabulary; one primary cause per claim. Grain: One row per cause of loss code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.claim_status` — Lifecycle status of a claim. Financial development lives in claim transactions; status describes the handling state only. Grain: One row per claim status code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.claim_transaction_type` — Kinds of claim financial movement. Claims finance is transactional: case reserves, payments and recoveries are signed movements, and figures such as outstanding or incurred are always derived by summation. Grain: One row per claim transaction type code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.country` — Countries the group operates or insures risks in, as ISO 3166-1 alpha-2 codes. A governed subset, extended when the business enters a market. Grain: One row per country code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.coverage_type` — Kinds of cover that can be granted under a policy. A policy bundles one or more coverages; limits, deductibles and claims attach at coverage level. Grain: One row per coverage type code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.currency` — Transaction currencies used by the group, as ISO 4217 alphabetic codes. This is deliberately a governed subset, not the full ISO list: a currency is added here when the business starts writing in it. Grain: One row per currency code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.insured_object_type` — Kinds of object or exposure a policy can insure. Extend with new codes as new lines of business are written (vessels, livestock, cyber estates...). Grain: One row per insured object type code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.line_of_business` — Classes of insurance business written by the group, aligned to ACORD LOBCd vocabulary. Extend by adding codes; never repurpose an existing code. Grain: One row per line of business code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.party_role_type` — The roles a party can play in the business. This code set is the model's number-one extension point: a new kind of counterparty is a new code here, not a new table. Grain: One row per party role type code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.party_type` — Fundamental legal nature of a party. Everything else about a party's place in the business is a role, never a type. Grain: One row per party type code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.policy_status` — Lifecycle status of a policy contract. Status reflects the contract as a whole; coverage-level suspension is modelled on the coverage entity. Grain: One row per policy status code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.premium_transaction_type` — Kinds of premium movement. Premium is always modelled as signed transactions; balances such as gross written premium are derived by summation, never overwritten. Grain: One row per premium transaction type code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.source_system` — Systems of record that feed the data layer. Provenance is part of the model: every core entity carries a source_system_code, and identifiers are only unique within their source system. Grain: One row per source system code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.treaty_type` — Forms of treaty reinsurance. Direction (assumed or ceded) is determined by the cedant and reinsurer party roles on the treaty, not by this code. Grain: One row per treaty type code.
- `lr_serverless_aws_us_catalog.bricksurance_reference.data_dictionary` — Machine-readable dictionary of every entity and attribute in the model, generated from the specs. Include this table in every data share so the semantics travel with the data. Grain: One row per attribute per entity per model version.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim` — A demand for indemnity under a policy arising from a loss event. The claim record holds the event and handling state; all financial development lives in claim transactions. Grain: One row per claim per source system.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim_transaction` — A signed financial movement on a claim: case reserve movements, indemnity and expense payments, and recoveries. Outstanding, paid and incurred are always derived by summation over these movements, never stored as balances. Grain: One row per financial movement per claim.
- `lr_serverless_aws_us_catalog.bricksurance_exchange.premium_bordereau_line` — The canonical form of an inbound premium bordereau line, as reported by a coverholder or broker. Messy source files land in the exchange domain and are mapped into this shape - using the data dictionary as the contract - before flowing into the core model. Grain: One row per policy per reporting month per inbound bordereau.
- `lr_serverless_aws_us_catalog.bricksurance_party.party` — A person or organisation the group deals with. A party exists exactly once regardless of how many relationships it has; what the party does (insured, broker, cedant, claimant...) is expressed through party roles, never by duplicating the party. Grain: One row per unique legal person or organisation, mastered across source systems.
- `lr_serverless_aws_us_catalog.bricksurance_party.party_role` — A role a party plays in a specific business context - on a policy, a claim or a treaty. This is the model's central extensibility pattern: a new kind of counterparty is a new party_role_type code plus rows here, never a new table. Grain: One row per role a party plays in one context (policy, claim or treaty) for a period of time. Exactly one of policy_id, claim_id and treaty_id is populated.
- `lr_serverless_aws_us_catalog.bricksurance_policy.coverage` — A specific cover granted under a policy, with its own limit and deductible. A policy bundles one or more coverages; claims attach to coverages where the source data allows it. Grain: One row per coverage granted under a policy.
- `lr_serverless_aws_us_catalog.bricksurance_policy.insured_object` — A concrete object or exposure insured under a policy - a building, a vehicle, a shipment, a set of operations. Location lives here, which makes this the anchor for exposure and accumulation analysis. Grain: One row per insured object under a policy.
- `lr_serverless_aws_us_catalog.bricksurance_policy.policy` — A contract of insurance between an insurer and one or more policyholders, under which the insurer provides cover for defined risks in exchange for premium. This is the contract-level record: coverages, insured objects, premium transactions and parties are separate entities that reference it. Grain: One row per policy contract per source system. Mid-term changes are modelled as endorsements (future entity), not as new rows here.
- `lr_serverless_aws_us_catalog.bricksurance_policy.premium_transaction` — A signed premium movement on a policy. Premium is transactional by design: figures such as gross written premium are derived by summing transactions, never stored as overwritable balances. Grain: One row per premium movement per policy (and coverage, where known).
- `lr_serverless_aws_us_catalog.bricksurance_reinsurance.cession` — The link between direct business and a treaty: which policy (or coverage) is ceded to which treaty, and to what share. Ceded premium and recoveries are derived by applying the ceded share to the underlying transactions. Grain: One row per policy (or coverage, where the split exists) per treaty.
- `lr_serverless_aws_us_catalog.bricksurance_reinsurance.treaty` — A treaty reinsurance contract under which risks are ceded to or assumed from reinsurers. Cedant and reinsurer are party roles on the treaty; which business it covers is expressed through cessions. Grain: One row per treaty contract per underwriting year.

## Join hints

- `lr_serverless_aws_us_catalog.bricksurance_claim.claim.policy_id` joins to `lr_serverless_aws_us_catalog.bricksurance_policy.policy.policy_id`.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim.coverage_id` joins to `lr_serverless_aws_us_catalog.bricksurance_policy.coverage.coverage_id`.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim.claim_status_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.claim_status.claim_status_code`.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim.cause_of_loss_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.cause_of_loss.cause_of_loss_code`.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim.source_system_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.source_system.source_system_code`.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim_transaction.claim_id` joins to `lr_serverless_aws_us_catalog.bricksurance_claim.claim.claim_id`.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim_transaction.claim_transaction_type_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.claim_transaction_type.claim_transaction_type_code`.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim_transaction.currency_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.currency.currency_code`.
- `lr_serverless_aws_us_catalog.bricksurance_claim.claim_transaction.source_system_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.source_system.source_system_code`.
- `lr_serverless_aws_us_catalog.bricksurance_exchange.premium_bordereau_line.line_of_business_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.line_of_business.line_of_business_code`.
- `lr_serverless_aws_us_catalog.bricksurance_exchange.premium_bordereau_line.currency_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.currency.currency_code`.
- `lr_serverless_aws_us_catalog.bricksurance_exchange.premium_bordereau_line.risk_country_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.country.country_code`.
- `lr_serverless_aws_us_catalog.bricksurance_exchange.premium_bordereau_line.source_system_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.source_system.source_system_code`.
- `lr_serverless_aws_us_catalog.bricksurance_party.party.party_type_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.party_type.party_type_code`.
- `lr_serverless_aws_us_catalog.bricksurance_party.party.country_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.country.country_code`.
- `lr_serverless_aws_us_catalog.bricksurance_party.party.source_system_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.source_system.source_system_code`.
- `lr_serverless_aws_us_catalog.bricksurance_party.party_role.party_id` joins to `lr_serverless_aws_us_catalog.bricksurance_party.party.party_id`.
- `lr_serverless_aws_us_catalog.bricksurance_party.party_role.party_role_type_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.party_role_type.party_role_type_code`.
- `lr_serverless_aws_us_catalog.bricksurance_party.party_role.policy_id` joins to `lr_serverless_aws_us_catalog.bricksurance_policy.policy.policy_id`.
- `lr_serverless_aws_us_catalog.bricksurance_party.party_role.claim_id` joins to `lr_serverless_aws_us_catalog.bricksurance_claim.claim.claim_id`.
- `lr_serverless_aws_us_catalog.bricksurance_party.party_role.treaty_id` joins to `lr_serverless_aws_us_catalog.bricksurance_reinsurance.treaty.treaty_id`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.coverage.policy_id` joins to `lr_serverless_aws_us_catalog.bricksurance_policy.policy.policy_id`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.coverage.coverage_type_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.coverage_type.coverage_type_code`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.insured_object.policy_id` joins to `lr_serverless_aws_us_catalog.bricksurance_policy.policy.policy_id`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.insured_object.insured_object_type_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.insured_object_type.insured_object_type_code`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.insured_object.country_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.country.country_code`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.policy.source_system_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.source_system.source_system_code`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.policy.line_of_business_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.line_of_business.line_of_business_code`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.policy.policy_status_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.policy_status.policy_status_code`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.policy.currency_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.currency.currency_code`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.premium_transaction.policy_id` joins to `lr_serverless_aws_us_catalog.bricksurance_policy.policy.policy_id`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.premium_transaction.coverage_id` joins to `lr_serverless_aws_us_catalog.bricksurance_policy.coverage.coverage_id`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.premium_transaction.premium_transaction_type_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.premium_transaction_type.premium_transaction_type_code`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.premium_transaction.currency_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.currency.currency_code`.
- `lr_serverless_aws_us_catalog.bricksurance_policy.premium_transaction.source_system_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.source_system.source_system_code`.
- `lr_serverless_aws_us_catalog.bricksurance_reinsurance.cession.policy_id` joins to `lr_serverless_aws_us_catalog.bricksurance_policy.policy.policy_id`.
- `lr_serverless_aws_us_catalog.bricksurance_reinsurance.cession.coverage_id` joins to `lr_serverless_aws_us_catalog.bricksurance_policy.coverage.coverage_id`.
- `lr_serverless_aws_us_catalog.bricksurance_reinsurance.cession.treaty_id` joins to `lr_serverless_aws_us_catalog.bricksurance_reinsurance.treaty.treaty_id`.
- `lr_serverless_aws_us_catalog.bricksurance_reinsurance.treaty.treaty_type_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.treaty_type.treaty_type_code`.
- `lr_serverless_aws_us_catalog.bricksurance_reinsurance.treaty.line_of_business_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.line_of_business.line_of_business_code`.
- `lr_serverless_aws_us_catalog.bricksurance_reinsurance.treaty.currency_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.currency.currency_code`.
- `lr_serverless_aws_us_catalog.bricksurance_reinsurance.treaty.source_system_code` joins to `lr_serverless_aws_us_catalog.bricksurance_reference.source_system.source_system_code`.

## Metrics

For KPI questions (premium, incurred, loss ratio and similar), PREFER the metric views below over hand-written aggregations. Query measures with MEASURE(<name>) and GROUP BY dimensions. Amounts are in original currency: always group by or filter on currency_code before summing money.

- `lr_serverless_aws_us_catalog.bricksurance_semantics.underwriting_metrics` — Certified underwriting KPIs - premium, claims development and loss ratio - defined once over the canonical model. Measures are in original transaction currency: always group by or filter on currency_code before summing money. Query measures with MEASURE(name).
  - dimension underwriting_year: Underwriting year of account of the underlying policy.
  - dimension line_of_business: Line of business as its business label, e.g. 'Commercial Property'. Filter this dimension with labels; use line_of_business_code for codes.
  - dimension line_of_business_code: Line of business as its code, e.g. COMMERCIAL_PROPERTY.
  - dimension currency_code: Original currency of the transaction. Group by this before summing money.
  - dimension transaction_month: Calendar month the movement was booked in.
  - dimension cause_of_loss_code: Cause of loss for claim movements; empty for premium movements.
  - MEASURE(gross_written_premium): Sum of all premium movements (written, adjustments, returns) - the book's gross written premium in original currency.
  - MEASURE(claims_paid): Indemnity plus allocated expense paid, gross of recoveries.
  - MEASURE(recoveries): Subrogation, salvage and contribution recoveries (negative amounts).
  - MEASURE(outstanding_reserve): Current case reserves - the sum of all signed reserve movements.
  - MEASURE(claims_incurred): Paid plus outstanding net of recoveries - total claims incurred.
  - MEASURE(loss_ratio): Claims incurred divided by gross written premium. Meaningful within a single currency; not premium-earned-adjusted in this version.
  - MEASURE(policy_count): Number of distinct policies with premium activity.
  - MEASURE(claim_count): Number of distinct claims with financial activity.

## Vocabulary

- Cause of Loss: FIRE (Fire), FLOOD (Flood), STORM (Storm), WATER_DAMAGE (Water Damage), THEFT (Theft), COLLISION (Collision), LIABILITY_INCIDENT (Liability Incident).
- Claim Status: OPEN (Open), CLOSED (Closed), REOPENED (Reopened), DECLINED (Declined).
- Claim Transaction Type: CASE_RESERVE_MOVEMENT (Case Reserve Movement), INDEMNITY_PAYMENT (Indemnity Payment), EXPENSE_PAYMENT (Expense Payment), RECOVERY (Recovery).
- Country: GB (United Kingdom), IE (Ireland), DE (Germany), FR (France), CH (Switzerland), US (United States).
- Coverage Type: BUILDINGS (Buildings), CONTENTS (Contents), BUSINESS_INTERRUPTION (Business Interruption), MOTOR_OWN_DAMAGE (Motor Own Damage), MOTOR_TPL (Motor Third-Party Liability), PUBLIC_LIABILITY (Public Liability), CARGO (Cargo).
- Currency: GBP (Pound Sterling), EUR (Euro), USD (US Dollar), CHF (Swiss Franc).
- Insured Object Type: BUILDING (Building), VEHICLE (Vehicle), CARGO_SHIPMENT (Cargo Shipment), LIABILITY_EXPOSURE (Liability Exposure).
- Line of Business: COMMERCIAL_PROPERTY (Commercial Property), MOTOR (Motor), GENERAL_LIABILITY (General Liability), MARINE_CARGO (Marine Cargo), PROPERTY_TREATY (Property Treaty Reinsurance).
- Party Role Type: POLICYHOLDER (Policyholder), INSURED (Insured), BROKER (Broker), CLAIMANT (Claimant), CEDANT (Cedant), REINSURER (Reinsurer), COVERHOLDER (Coverholder).
- Party Type: PERSON (Person), ORGANISATION (Organisation).
- Policy Status: QUOTED (Quoted), BOUND (Bound), IN_FORCE (In Force), EXPIRED (Expired), CANCELLED (Cancelled), LAPSED (Lapsed).
- Premium Transaction Type: WRITTEN (Written Premium), ADJUSTMENT (Adjustment Premium), RETURN (Return Premium).
- Source System: PAS_CORE (Policy Administration (Core)), CLM_CORE (Claims (Core)), RI_CORE (Reinsurance (Core)), DATA_CORE (Data Core (Mastered)), COVERHOLDER_BDX (Coverholder Bordereau).
- Treaty Type: QUOTA_SHARE (Quota Share), SURPLUS (Surplus), XOL_PER_RISK (Excess of Loss (Per Risk)), XOL_CATASTROPHE (Excess of Loss (Catastrophe)).
