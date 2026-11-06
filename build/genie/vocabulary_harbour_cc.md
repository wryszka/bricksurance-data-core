## Vocabulary of Harbour Mutual claim centre -> core concepts (source system HARBOUR_CC)

Harbour Mutual's claim centre: claims with PublicID / ClaimNumber / PolicyNumber / LossCause (vehcollision, theft, propertydamage, bodilyinjury, glassbreakage, fire) and transactions typed Payment / Reserve / Recovery with a CostType of claimcost or expense. Mapped to the same core Claim and Claim Transaction concepts as the Bricksurance motor claims system, so the same metric and the same questions work.

- `cc_claim.PublicID` means **claim.claim_id**: Stable, source-agnostic identifier for the claim, owned by the data layer.
- `cc_claim.ClaimNumber` means **claim.claim_number**: Claim number as issued by the claims system. Unique within a source system - always interpret together with source_system_code.
- `cc_claim.PolicyNumber` means **claim.policy_id**: Policy the claim is made under. The claim centre holds the PolicyNumber; the policy id is resolved through the policy centre.
- `cc_claim.State` means **claim.claim_status_code**: Current handling status of the claim.
- `cc_claim.LossCause` means **claim.cause_of_loss_code**: Primary peril or event that gave rise to the claim.
- `cc_claim.LossDate` means **claim.loss_date**: Date the loss occurred.
- `cc_claim.ReportedDate` means **claim.reported_date**: Date the loss was first reported to the insurer. Must be on or after loss_date.
- `cc_claim.LossCause` is the enterprise extension **peril_code**: Harbour's loss cause translated to the shared peril vocabulary (AD, THEFT, TPPD, TPBI, WINDSCREEN, FIRE) so cross-insurer peril questions line up.
- `cc_claim.LossLocationPostalCode` is the enterprise extension **loss_postcode_area**: Postcode area where the loss occurred.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_claim` presents `cc_claim` in core terms; prefer it over the raw table.
- `cc_transaction.PublicID` means **claim_transaction.claim_transaction_id**: Identifier for the claim transaction.
- `cc_transaction.ClaimID` means **claim_transaction.claim_id**: Claim the movement belongs to.
- `cc_transaction.TransactionType` means **claim_transaction.claim_transaction_type_code**: Kind of financial movement.
- `cc_transaction.Amount` means **claim_transaction.amount**: Signed amount in the transaction currency. Reserve increases positive, reserve releases negative; payments positive; recoveries negative from the insurer's cost perspective.
- `cc_transaction.CreateTime` means **claim_transaction.transaction_date**: Date the movement was booked.
- `cc_transaction.CostType` is the enterprise extension **head_of_damage_code**: Harbour does not record head of damage; CostType (claimcost / expense) is carried in its place.
- `cc_transaction.claim_feature_type_code` is the enterprise extension **claim_feature_type_code**: Not available from Harbour's claim centre at transaction level; defaulted to OWN_DAMAGE and said so.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_claim_transaction` presents `cc_transaction` in core terms; prefer it over the raw table.
