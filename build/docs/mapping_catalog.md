# Mapping catalog — Bricksurance Data Core v0.17.0

How each source system's vocabulary maps to the core (ACORD-aligned) concepts. One row per core attribute; one column per source system. Generated from `model/mappings/*.yaml`; this is the content a Unity Catalog Page per concept would carry.

- **ACT_DW** — Actuarial warehouse (motor) -> core concepts (schema `bricksurance_src_actuarial`, owner Chief Actuary, certified)
- **CLM_MOTOR** — Claims management (motor) -> core concepts (schema `bricksurance_src_claims`, owner Head of Motor Claims, certified)
- **HARBOUR_CC** — Harbour Mutual claim centre -> core concepts (schema `bricksurance_harbour_cc`, owner Harbour Mutual, Head of Claims, certified)
- **HARBOUR_PC** — Harbour Mutual policy centre -> core concepts (schema `bricksurance_harbour_pc`, owner Harbour Mutual, Head of Personal Lines, certified)
- **PAS_MOTOR** — Policy administration (motor book) -> core concepts (schema `bricksurance_src_pas`, owner Head of Motor Underwriting, certified)

## policy (policy)

| Core attribute | Definition | ACORD | ACT_DW | CLM_MOTOR | HARBOUR_CC | HARBOUR_PC | PAS_MOTOR |
|---|---|---|---|---|---|---|---|
| `policy_id` | Stable, source-agnostic identifier for the policy. A surrogate key owned by the data layer, not by any policy administration system. |  |  |  |  | `pc_policyperiod.PublicID` | `pol_master.contract_reference` - Surrogate key = source system plus contract reference. |
| `policy_number` | Policy number as issued to the policyholder. Unique within a source system, not globally - always interpret together with source_system_code. | PolicyNumber |  |  |  | `pc_policyperiod.PolicyNumber` - Harbour's system calls it PolicyNumber; the claim centre carries the same value. | `pol_master.contract_reference` - The policy system calls the policy number a 'contract reference'. |
| `line_of_business_code` | Line of business written under this policy. | LOBCd |  |  |  | `pc_policyperiod.ProductCode` - PersonalAuto and CommercialAuto are both Motor; the product code is kept as the segment extension. | `pol_master.product_cd` - All three product codes are Motor; the product code itself is kept as the motor_segment_code extension. |
| `policy_status_code` | Current lifecycle status of the policy. | PolicyStatusCd |  |  |  | `pc_policyperiod.Status` (Bound->IN_FORCE, Expired->EXPIRED) | `pol_master.contract_status` (LIVE->IN_FORCE, EXPIRED->EXPIRED) |
| `inception_date` | Date on which cover begins (inclusive). | EffectiveDt |  |  |  | `pc_policyperiod.PeriodStart` | `pol_master.cover_start_dt` |
| `expiry_date` | Date on which cover ends (inclusive). Must be on or after inception_date. | ExpirationDt |  |  |  | `pc_policyperiod.PeriodEnd` | `pol_master.cover_end_dt` - Cover end date is the last day of cover in the policy system; the core expiry_date is the same day. |
| `underwriting_year` | Year of account to which the policy is allocated; drives reinsurance cession and market reporting. |  |  |  |  | `pc_policyperiod.PeriodStart` | `pol_master.cover_start_dt` |
| `currency_code` | Original currency of the policy. Monetary amounts on child entities are expressed in this currency unless explicitly stated otherwise. | CurCd |  |  |  | constant 'GBP' | constant 'GBP' - The policy system is single-currency (GBP) and carries no currency column. |
| `source_system_code` | System of record this policy originates from. Provenance is part of the model, not an afterthought. |  |  |  |  | constant 'HARBOUR_PC' | `pol_master.source_sys` |

## coverage (policy)

| Core attribute | Definition | ACORD | ACT_DW | CLM_MOTOR | HARBOUR_CC | HARBOUR_PC | PAS_MOTOR |
|---|---|---|---|---|---|---|---|
| `coverage_id` | Identifier for the coverage. |  |  |  |  |  | `pol_cover.contract_reference` |
| `policy_id` | Policy the coverage is granted under. |  |  |  |  |  | `pol_cover.contract_reference` |
| `coverage_type_code` | Kind of cover granted. | CoverageCd |  |  |  |  | `pol_cover.cover_cd` (COMP->MOTOR_OWN_DAMAGE + MOTOR_TPL, TPFT->MOTOR_OWN_DAMAGE + MOTOR_TPL, TPO->MOTOR_TPL) - One source row becomes one or two coverage rows. |
| `limit_amount` | Maximum amount payable under this coverage, in the policy currency; empty where unlimited or not applicable. | Limit |  |  |  |  | `pol_cover.tpl_limit_amt` - Third-party liability limit; applies to the MOTOR_TPL row. |
| `deductible_amount` | Amount borne by the insured before this coverage responds, in the policy currency. | Deductible |  |  |  |  | `pol_cover.excess_amt` - The policy system says 'excess'; applies to the MOTOR_OWN_DAMAGE row. |
| `sum_insured_amount` | Declared value insured under this coverage, in the policy currency. |  |  |  |  |  | derived (None) - Not held by the policy system for motor; vehicle value is on the vehicle. |

## vehicle (policy)

| Core attribute | Definition | ACORD | ACT_DW | CLM_MOTOR | HARBOUR_CC | HARBOUR_PC | PAS_MOTOR |
|---|---|---|---|---|---|---|---|
| `vehicle_id` | Identifier for the vehicle record. |  |  |  |  | `pc_vehicle.PublicID` | `pol_vehicle.contract_reference` |
| `insured_object_id` | The insured object this vehicle detail belongs to (object type VEHICLE). |  |  |  |  | `pc_vehicle.PublicID` | `pol_vehicle.contract_reference` - One insured object per vehicle; the vehicle is its typed satellite. |
| `policy_id` | Policy the object is insured under. |  |  |  |  | `pc_vehicle.PolicyPeriodID` | `pol_vehicle.contract_reference` |
| `registration_number` | Vehicle registration mark. | VehIdentificationNumber / registration |  |  |  | `pc_vehicle.VIN` - Harbour keys vehicles by VIN, not registration mark; kept in the registration_number slot and said so. | `pol_vehicle.reg_mark` - The policy system says 'reg mark'. |
| `make` | Manufacturer. |  |  |  |  | `pc_vehicle.Make` | `pol_vehicle.make` |
| `model` | Model designation. |  |  |  |  | `pc_vehicle.Model` | `pol_vehicle.model` |
| `year_of_manufacture` | Year of manufacture. |  |  |  |  | `pc_vehicle.Year` | `pol_vehicle.year_of_manufacture` |
| `vehicle_group` | Insurance vehicle group used in rating, e.g. an ABI-style group. |  |  |  |  |  | `pol_vehicle.abi_group` - UK ABI insurance group 1-50; the core vehicle_group is the same scale. |

## premium_transaction (policy)

| Core attribute | Definition | ACORD | ACT_DW | CLM_MOTOR | HARBOUR_CC | HARBOUR_PC | PAS_MOTOR |
|---|---|---|---|---|---|---|---|
| `premium_transaction_id` | Identifier for the premium transaction. |  |  |  |  | `pc_policyperiod.PublicID` | `pol_premium_txn.txn_id` |
| `policy_id` | Policy the premium movement belongs to. |  |  |  |  | `pc_policyperiod.PublicID` | `pol_premium_txn.contract_reference` |
| `premium_transaction_type_code` | Kind of premium movement. |  |  |  |  | constant 'WRITTEN' | `pol_premium_txn.txn_type` (NEW_BUSINESS->WRITTEN) - The policy system distinguishes new business from renewals; both are WRITTEN premium in the core. |
| `amount` | Signed amount of the movement in the transaction currency: written and positive adjustments positive, returns negative. |  |  |  |  | `pc_policyperiod.TotalPremiumRPT` | `pol_premium_txn.txn_amt` |
| `currency_code` | Currency of the amount. |  |  |  |  | constant 'GBP' | constant 'GBP' |
| `transaction_date` | Date the movement was booked. |  |  |  |  | `pc_policyperiod.PeriodStart` | `pol_premium_txn.txn_dt` |
| `source_system_code` | System of record the movement originates from. |  |  |  |  | constant 'HARBOUR_PC' | `pol_premium_txn.txn_type` |
| `ipt_amount` | Insurance premium tax on the movement, in the transaction currency. |  |  |  |  |  | `pol_premium_txn.ipt_amt` |

## premium_earning (semantics)

| Core attribute | Definition | ACORD | ACT_DW | CLM_MOTOR | HARBOUR_CC | HARBOUR_PC | PAS_MOTOR |
|---|---|---|---|---|---|---|---|
| `policy_id` | Stable, source-agnostic identifier for the policy (same surrogate as the policy system mapping). |  | `earned_premium_monthly.pol_ref` - 'Pol ref' is the policy system's contract reference. |  |  | `pc_policyperiod.PublicID` |  |
| `earned_premium` | Premium earned in the month, GBP, daily pro-rata over the cover period. |  | `earned_premium_monthly.ep_amt` |  |  | `pc_policyperiod.TotalPremiumRPT` |  |
| `accounting_month` | Accounting month as YYYYMM. |  | `earned_premium_monthly.yyyymm` |  |  | derived (derived) |  |
| `accident_quarter` | Calendar quarter of the accounting month, e.g. 2026Q3. Same labelling as the claims accident quarter so premium and claims line up. |  | `earned_premium_monthly.yyyymm` |  |  | derived (derived) |  |

## claim (claim)

| Core attribute | Definition | ACORD | ACT_DW | CLM_MOTOR | HARBOUR_CC | HARBOUR_PC | PAS_MOTOR |
|---|---|---|---|---|---|---|---|
| `claim_id` | Stable, source-agnostic identifier for the claim, owned by the data layer. |  |  | `clm_header.claim_ref` | `cc_claim.PublicID` |  |  |
| `claim_number` | Claim number as issued by the claims system. Unique within a source system - always interpret together with source_system_code. | ClaimNumber |  | `clm_header.claim_ref` | `cc_claim.ClaimNumber` |  |  |
| `policy_id` | Policy the claim is made under. |  |  | `clm_header.policy_no` - The claims system stores the policy system's contract reference as 'policy no'; this is the join to the policy. | `cc_claim.PolicyNumber` - The claim centre holds the PolicyNumber; the policy id is resolved through the policy centre. |  |  |
| `claim_status_code` | Current handling status of the claim. | ClaimStatusCd |  | `clm_header.claim_status` (OPEN->OPEN, SETTLED->CLOSED) - The claims team says 'settled'; the core says CLOSED. | `cc_claim.State` (open->OPEN, closed->CLOSED) |  |  |
| `cause_of_loss_code` | Primary peril or event that gave rise to the claim. | LossCauseCd |  | `clm_header.peril_cd` (AD->COLLISION, THEFT->THEFT, TPPD->LIABILITY_INCIDENT, TPBI->LIABILITY_INCIDENT, WINDSCREEN->GLASS, FIRE->FIRE) - AD (accidental damage) is a collision in the standard vocabulary; third party property damage and bodily injury are both liability incidents, so the finer peril code is kept as the peril_code extension. | `cc_claim.LossCause` (vehcollision->COLLISION, theft->THEFT, propertydamage->LIABILITY_INCIDENT, bodilyinjury->LIABILITY_INCIDENT, glassbreakage->GLASS, fire->FIRE) |  |  |
| `loss_date` | Date the loss occurred. | LossDt |  | `clm_header.loss_dt` | `cc_claim.LossDate` |  |  |
| `reported_date` | Date the loss was first reported to the insurer. Must be on or after loss_date. | ReportedDt |  | `clm_header.notified_dt` - The claims team says 'notified'. | `cc_claim.ReportedDate` |  |  |
| `handling_office` | Claims office or team handling the file. |  |  | `clm_header.handling_office` |  |  |  |
| `source_system_code` | System of record the claim originates from. |  |  | constant 'CLM_MOTOR' | constant 'HARBOUR_CC' |  |  |

## claim_transaction (claim)

| Core attribute | Definition | ACORD | ACT_DW | CLM_MOTOR | HARBOUR_CC | HARBOUR_PC | PAS_MOTOR |
|---|---|---|---|---|---|---|---|
| `claim_transaction_id` | Identifier for the claim transaction. |  |  | `clm_movement.movement_id` | `cc_transaction.PublicID` |  |  |
| `claim_id` | Claim the movement belongs to. |  |  | `clm_movement.claim_ref` | `cc_transaction.ClaimID` |  |  |
| `claim_transaction_type_code` | Kind of financial movement. |  |  | `clm_movement.movement_type` (PAID->INDEMNITY_PAYMENT, RESERVE->CASE_RESERVE_MOVEMENT, RECOVERY->RECOVERY, FEE->EXPENSE_PAYMENT) - FEE is allocated claims handling cost (ALAE); RECOVERY is negative in both systems. | `cc_transaction.TransactionType` (Payment->INDEMNITY_PAYMENT or EXPENSE_PAYMENT by CostType, Reserve->CASE_RESERVE_MOVEMENT, Recovery->RECOVERY) |  |  |
| `amount` | Signed amount in the transaction currency. Reserve increases positive, reserve releases negative; payments positive; recoveries negative from the insurer's cost perspective. |  |  | `clm_movement.amount` | `cc_transaction.Amount` |  |  |
| `currency_code` | Currency of the amount. |  |  | constant 'GBP' | constant 'GBP' |  |  |
| `transaction_date` | Date the movement was booked. |  |  | `clm_movement.movement_dt` | `cc_transaction.CreateTime` |  |  |
| `source_system_code` | System of record the movement originates from. |  |  | constant 'CLM_MOTOR' | constant 'HARBOUR_CC' |  |  |

## valuation_result (finance)

| Core attribute | Definition | ACORD | ACT_DW | CLM_MOTOR | HARBOUR_CC | HARBOUR_PC | PAS_MOTOR |
|---|---|---|---|---|---|---|---|
| `amount` | The figure, in the stated currency. Sign follows the measure's own convention. |  | `ibnr_estimate.ibnr_amt` |  |  |  |  |
| `valuation_measure_code` | Which defined measure this figure is. |  | constant 'IBNR' |  |  |  |  |
| `line_of_business_code` | Line of business the figure relates to. |  | constant 'MOTOR' |  |  |  |  |
| `cohort` | Optional sub-division (e.g. an age-by-term band or underwriting-year cohort). |  | `ibnr_estimate.acc_qtr` - The warehouse cohort is the accident quarter. |  |  |  |  |
| `currency_code` | Currency of the amount. |  | constant 'GBP' |  |  |  |  |

## postcode_enrichment (enrichment)

| Core attribute | Definition | ACORD | ACT_DW | CLM_MOTOR | HARBOUR_CC | HARBOUR_PC | PAS_MOTOR |
|---|---|---|---|---|---|---|---|
| `postcode` | Postcode or postal-area key the attributes describe. |  | `postcode_region_dim.postcode_area` - Postcode AREA (letters only), not a full postcode. |  |  |  |  |
| `urbanity_code` | Settlement type of the postcode. |  | `postcode_region_dim.urbanity_code` |  |  |  |  |
| `region_code` | Statistical region the postcode sits in. |  | `postcode_region_dim.region_name` - The warehouse carries the region name; the core attribute is a code. Kept as the name. |  |  |  |  |
| `country_code` | Country the postcode belongs to. |  | constant 'GB' |  |  |  |  |

## Enterprise extensions (preserved, not forced into the standard)

| Source system | Extension | Source column | Definition |
|---|---|---|---|
| ACT_DW | `vehicle_years` | `earned_premium_monthly.veh_years` | Vehicle-years of exposure earned in the month (vehicles x days in force / 365). The denominator for claim frequency. |
| ACT_DW | `days_in_force` | `earned_premium_monthly.days_in_force` | Days of cover in the month. |
| ACT_DW | `motor_segment_code` | `earned_premium_monthly.seg_cd` | Bricksurance SE motor segment (PMU / PMO / CMV) as carried by the warehouse. |
| ACT_DW | `motor_segment_code` | `ibnr_estimate.seg_cd` | Bricksurance SE motor segment. |
| ACT_DW | `valuation_date` | `ibnr_estimate.valuation_dt` | Date the estimate was struck. |
| ACT_DW | `reserving_method_code` | `ibnr_estimate.method_cd` | Reserving method (CHAIN_LADDER). |
| ACT_DW | `motor_segment_code` | `segment_dim.seg_cd` | PMU urban private motor, PMO other private motor, CMV commercial motor. |
| ACT_DW | `motor_segment` | `segment_dim.seg_desc` | Segment label for people (use for filtering with labels). |
| ACT_DW | `line_of_business_code` | `segment_dim.lob_cd` | Always MOTOR. |
| CLM_MOTOR | `peril_code` | `clm_header.peril_cd` | Claims-system peril: AD accidental damage, THEFT, TPPD third party property damage, TPBI third party bodily injury, WINDSCREEN, FIRE. Finer than the standard cause of loss; this is the code to use for peril questions. |
| CLM_MOTOR | `fault_indicator` | `clm_header.fault_ind` | Y at fault, N non-fault, SPLIT shared liability. |
| CLM_MOTOR | `loss_postcode_area` | `clm_header.loss_postcode_area` | Postcode area where the loss occurred; joins to the actuarial postcode region dimension. |
| CLM_MOTOR | `head_of_damage_code` | `clm_movement.head_of_damage` | Claims-system head of damage: VEHICLE_REPAIR, THEFT_TOTAL_LOSS, TP_PROPERTY, BODILY_INJURY, GLASS, FIRE_TOTAL_LOSS. The level at which repair-cost and injury questions are answered. |
| CLM_MOTOR | `claim_feature_type_code` | `clm_movement.head_of_damage` | Head of damage rolled up to the core claim feature type (OWN_DAMAGE, THIRD_PARTY_PROPERTY, THIRD_PARTY_INJURY). |
| HARBOUR_CC | `peril_code` | `cc_claim.LossCause` | Harbour's loss cause translated to the shared peril vocabulary (AD, THEFT, TPPD, TPBI, WINDSCREEN, FIRE) so cross-insurer peril questions line up. |
| HARBOUR_CC | `loss_postcode_area` | `cc_claim.LossLocationPostalCode` | Postcode area where the loss occurred. |
| HARBOUR_CC | `head_of_damage_code` | `cc_transaction.CostType` | Harbour does not record head of damage; CostType (claimcost / expense) is carried in its place. |
| HARBOUR_CC | `claim_feature_type_code` | `cc_transaction.` | Not available from Harbour's claim centre at transaction level; defaulted to OWN_DAMAGE and said so. |
| HARBOUR_PC | `motor_segment_code` | `pc_policyperiod.ProductCode` | Harbour Mutual segment - HP personal auto, HC commercial auto. Harbour's own segmentation, not the standard's. |
| HARBOUR_PC | `annual_premium` | `pc_policyperiod.TotalPremiumRPT` | Total period premium in GBP as reported by the policy centre. |
| HARBOUR_PC | `risk_postcode` | `pc_policyperiod.PrimaryInsuredPostalCode` | Postcode area of the primary insured. |
| HARBOUR_PC | `vehicle_years` | `pc_policyperiod.` | Policy-years of exposure in the month (one vehicle assumed per personal policy; commercial fleets count their vehicles via pc_vehicle). |
| HARBOUR_PC | `motor_segment_code` | `pc_policyperiod.ProductCode` | HP personal auto, HC commercial auto. |
| HARBOUR_PC | `vehicle_value_amount` | `pc_vehicle.CostNew` | Cost new in GBP as recorded by the policy centre. |
| PAS_MOTOR | `motor_segment_code` | `pol_master.product_cd` | Bricksurance SE motor segment: PMU urban private motor, PMO other private motor, CMV commercial motor. Insurer-specific; the standard has no segment concept, so it is kept beside the standard columns, not forced into them. |
| PAS_MOTOR | `use_class_code` | `pol_master.use_class` | Declared use of the vehicle(s): SDP social domestic and pleasure, SDP_COMMUTE including commuting, BUSINESS; commercial uses DELIVERY, HAULAGE, TRADES, FLEET_CAR, TAXI. |
| PAS_MOTOR | `vehicle_count` | `pol_master.veh_count` | Number of vehicles on the contract (fleets carry several). |
| PAS_MOTOR | `risk_postcode` | `pol_master.risk_postcode` | Postcode area and district where the vehicle(s) are kept overnight. |
| PAS_MOTOR | `annual_premium` | `pol_master.annual_prem_amt` | Annual contract premium excluding insurance premium tax, in GBP. |
| PAS_MOTOR | `vehicle_value_amount` | `pol_vehicle.vehicle_value_amt` | Declared vehicle value in GBP at inception. |
| PAS_MOTOR | `cover_code` | `pol_cover.cover_cd` | Policy-system cover code kept for reference: COMP comprehensive, TPFT third party fire and theft, TPO third party only. |

## Conformed views

- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_earned_premium` — ACT_DW in core terms (premium_earning)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_ibnr` — ACT_DW in core terms (valuation_result)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_segment` — ACT_DW in core terms (extension)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_postcode_region` — ACT_DW in core terms (postcode_enrichment)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_claim` — CLM_MOTOR in core terms (claim)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_claim_transaction` — CLM_MOTOR in core terms (claim_transaction)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_claim` — HARBOUR_CC in core terms (claim)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_claim_transaction` — HARBOUR_CC in core terms (claim_transaction)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_policy` — HARBOUR_PC in core terms (policy)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_premium_transaction` — HARBOUR_PC in core terms (premium_transaction)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_earned_premium` — HARBOUR_PC in core terms (premium_earning)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_vehicle` — HARBOUR_PC in core terms (vehicle)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_policy` — PAS_MOTOR in core terms (policy)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_vehicle` — PAS_MOTOR in core terms (vehicle)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_coverage` — PAS_MOTOR in core terms (coverage)
- `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_premium_transaction` — PAS_MOTOR in core terms (premium_transaction)
