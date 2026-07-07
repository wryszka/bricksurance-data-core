# Bricksurance Data Core — Data Dictionary

*Generated from model v0.1.0. Do not edit.*

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

## Policy (`policy.policy`)

A contract of insurance between an insurer and one or more policyholders, under which the insurer provides cover for defined risks in exchange for premium. This is the contract-level record: coverages, insured objects, premium transactions and parties are separate entities that reference it.

**Grain:** One row per policy contract per source system. Mid-term changes are modelled as endorsements (future entity), not as new rows here.

**Standards:** Acord: Policy (ACORD Information Model, P&C); Lloyds Cdr: Contract-level attributes of the Lloyd's Core Data Record (indicative)

| Attribute | Type | Required | Definition | Classification | ACORD | Lloyd's CDR |
|---|---|---|---|---|---|---|
| policy_id | string | yes | Stable, source-agnostic identifier for the policy. A surrogate key owned by the data layer, not by any policy administration system. | internal |  |  |
| policy_number | string | yes | Policy number as issued to the policyholder. Unique within a source system, not globally - always interpret together with source_system_code. | confidential | PolicyNumber | Contract reference |
| source_system_code | string | yes | Code of the policy administration system this record originates from. Provenance is part of the model, not an afterthought. | internal |  |  |
| line_of_business_code | string | yes | Line of business written under this policy. |  | LOBCd | Class of business |
| policy_status_code | string | yes | Current lifecycle status of the policy. |  | PolicyStatusCd |  |
| inception_date | date | yes | Date on which cover begins (inclusive). |  | EffectiveDt | Inception date |
| expiry_date | date | yes | Date on which cover ends (inclusive). Must be on or after inception_date. |  | ExpirationDt | Expiry date |
| underwriting_year | integer | yes | Year of account to which the policy is allocated; drives reinsurance cession and market reporting. |  |  | Year of account |
| currency_code | string | yes | Original currency of the policy. Monetary amounts on child entities are expressed in this currency unless explicitly stated otherwise. |  | CurCd | Settlement currency |

**Primary key:** policy_id
**Natural key:** source_system_code, policy_number
**Quality — cover_period_valid:** `expiry_date >= inception_date` — Cover cannot end before it begins.
