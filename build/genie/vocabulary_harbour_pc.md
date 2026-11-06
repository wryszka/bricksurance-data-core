## Vocabulary of Harbour Mutual policy centre -> core concepts (source system HARBOUR_PC)

A second insurer, Harbour Mutual, on a different policy system shape: policy periods with PublicID / PolicyNumber / PeriodStart / PeriodEnd / TotalPremiumRPT and product codes PersonalAuto / CommercialAuto. Mapped to the same core concepts as Bricksurance's motor book with one file. Harbour has no actuarial warehouse, so earned premium is derived in the conformed view on the core's daily pro-rata convention.

- `pc_policyperiod.PublicID` means **policy.policy_id**: Stable, source-agnostic identifier for the policy. A surrogate key owned by the data layer, not by any policy administration system.
- `pc_policyperiod.PolicyNumber` means **policy.policy_number**: Policy number as issued to the policyholder. Unique within a source system, not globally - always interpret together with source_system_code. Harbour's system calls it PolicyNumber; the claim centre carries the same value.
- `pc_policyperiod.ProductCode` means **policy.line_of_business_code**: Line of business written under this policy. PersonalAuto and CommercialAuto are both Motor; the product code is kept as the segment extension.
- `pc_policyperiod.Status` means **policy.policy_status_code**: Current lifecycle status of the policy.
- `pc_policyperiod.PeriodStart` means **policy.inception_date**: Date on which cover begins (inclusive).
- `pc_policyperiod.PeriodEnd` means **policy.expiry_date**: Date on which cover ends (inclusive). Must be on or after inception_date.
- `pc_policyperiod.PeriodStart` means **policy.underwriting_year**: Year of account to which the policy is allocated; drives reinsurance cession and market reporting.
- `pc_policyperiod.ProductCode` is the enterprise extension **motor_segment_code**: Harbour Mutual segment - HP personal auto, HC commercial auto. Harbour's own segmentation, not the standard's.
- `pc_policyperiod.TotalPremiumRPT` is the enterprise extension **annual_premium**: Total period premium in GBP as reported by the policy centre.
- `pc_policyperiod.PrimaryInsuredPostalCode` is the enterprise extension **risk_postcode**: Postcode area of the primary insured.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_policy` presents `pc_policyperiod` in core terms; prefer it over the raw table.
- `pc_policyperiod.PublicID` means **premium_transaction.premium_transaction_id**: Identifier for the premium transaction.
- `pc_policyperiod.PublicID` means **premium_transaction.policy_id**: Policy the premium movement belongs to.
- `pc_policyperiod.TotalPremiumRPT` means **premium_transaction.amount**: Signed amount of the movement in the transaction currency: written and positive adjustments positive, returns negative.
- `pc_policyperiod.PeriodStart` means **premium_transaction.transaction_date**: Date the movement was booked.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_premium_transaction` presents `pc_policyperiod` in core terms; prefer it over the raw table.
- `pc_policyperiod.PublicID` means **premium_earning.policy_id**: Stable, source-agnostic identifier for the policy.
- `pc_policyperiod.TotalPremiumRPT` means **premium_earning.earned_premium**: Premium earned in the month, GBP, daily pro-rata over the policy period.
- `pc_policyperiod.vehicle_years` is the enterprise extension **vehicle_years**: Policy-years of exposure in the month (one vehicle assumed per personal policy; commercial fleets count their vehicles via pc_vehicle).
- `pc_policyperiod.ProductCode` is the enterprise extension **motor_segment_code**: HP personal auto, HC commercial auto.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_earned_premium` presents `pc_policyperiod` in core terms; prefer it over the raw table.
- `pc_vehicle.PublicID` means **vehicle.vehicle_id**: Identifier for the vehicle record.
- `pc_vehicle.PublicID` means **vehicle.insured_object_id**: The insured object this vehicle detail belongs to (object type VEHICLE).
- `pc_vehicle.PolicyPeriodID` means **insured_object.policy_id**: Policy the object is insured under.
- `pc_vehicle.VIN` means **vehicle.registration_number**: Vehicle registration mark. Harbour keys vehicles by VIN, not registration mark; kept in the registration_number slot and said so.
- `pc_vehicle.Make` means **vehicle.make**: Manufacturer.
- `pc_vehicle.Model` means **vehicle.model**: Model designation.
- `pc_vehicle.Year` means **vehicle.year_of_manufacture**: Year of manufacture.
- `pc_vehicle.CostNew` is the enterprise extension **vehicle_value_amount**: Cost new in GBP as recorded by the policy centre.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_harbour_vehicle` presents `pc_vehicle` in core terms; prefer it over the raw table.
