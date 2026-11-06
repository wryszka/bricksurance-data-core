## Vocabulary of Claims management (motor) -> core concepts (source system CLM_MOTOR)

The motor claims system extract in the claims team's vocabulary: a 'claim ref' on a 'policy no', a 'peril code' (AD, THEFT, TPPD, TPBI, WINDSCREEN, FIRE), and 'movements' typed PAID / RESERVE / RECOVERY / FEE with a 'head of damage'. Mapped to the core Claim and Claim Transaction concepts. Two conventions differ and are translated, not hidden: the claims system books payments without releasing the reserve (the core releases reserve on payment), and recoveries are negative movements in both.

- `clm_header.claim_ref` means **claim.claim_id**: Stable, source-agnostic identifier for the claim, owned by the data layer.
- `clm_header.claim_ref` means **claim.claim_number**: Claim number as issued by the claims system. Unique within a source system - always interpret together with source_system_code.
- `clm_header.policy_no` means **claim.policy_id**: Policy the claim is made under. The claims system stores the policy system's contract reference as 'policy no'; this is the join to the policy.
- `clm_header.claim_status` means **claim.claim_status_code**: Current handling status of the claim. The claims team says 'settled'; the core says CLOSED.
- `clm_header.peril_cd` means **claim.cause_of_loss_code**: Primary peril or event that gave rise to the claim. AD (accidental damage) is a collision in the standard vocabulary; third party property damage and bodily injury are both liability incidents, so the finer peril code is kept as the peril_code extension.
- `clm_header.loss_dt` means **claim.loss_date**: Date the loss occurred.
- `clm_header.notified_dt` means **claim.reported_date**: Date the loss was first reported to the insurer. Must be on or after loss_date. The claims team says 'notified'.
- `clm_header.handling_office` means **claim.handling_office**: Claims office or team handling the file.
- `clm_header.peril_cd` is the enterprise extension **peril_code**: Claims-system peril: AD accidental damage, THEFT, TPPD third party property damage, TPBI third party bodily injury, WINDSCREEN, FIRE. Finer than the standard cause of loss; this is the code to use for peril questions.
- `clm_header.fault_ind` is the enterprise extension **fault_indicator**: Y at fault, N non-fault, SPLIT shared liability.
- `clm_header.loss_postcode_area` is the enterprise extension **loss_postcode_area**: Postcode area where the loss occurred; joins to the actuarial postcode region dimension.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_claim` presents `clm_header` in core terms; prefer it over the raw table.
- `clm_movement.movement_id` means **claim_transaction.claim_transaction_id**: Identifier for the claim transaction.
- `clm_movement.claim_ref` means **claim_transaction.claim_id**: Claim the movement belongs to.
- `clm_movement.movement_type` means **claim_transaction.claim_transaction_type_code**: Kind of financial movement. FEE is allocated claims handling cost (ALAE); RECOVERY is negative in both systems.
- `clm_movement.amount` means **claim_transaction.amount**: Signed amount in the transaction currency. Reserve increases positive, reserve releases negative; payments positive; recoveries negative from the insurer's cost perspective.
- `clm_movement.movement_dt` means **claim_transaction.transaction_date**: Date the movement was booked.
- `clm_movement.head_of_damage` is the enterprise extension **head_of_damage_code**: Claims-system head of damage: VEHICLE_REPAIR, THEFT_TOTAL_LOSS, TP_PROPERTY, BODILY_INJURY, GLASS, FIRE_TOTAL_LOSS. The level at which repair-cost and injury questions are answered.
- `clm_movement.head_of_damage` is the enterprise extension **claim_feature_type_code**: Head of damage rolled up to the core claim feature type (OWN_DAMAGE, THIRD_PARTY_PROPERTY, THIRD_PARTY_INJURY).
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_claim_transaction` presents `clm_movement` in core terms; prefer it over the raw table.
