## Vocabulary of Actuarial warehouse (motor) -> core concepts (source system ACT_DW)

The actuarial warehouse holds what neither operational system does: earned premium and vehicle-years by policy and accounting month (the earning engine output), the IBNR estimate by segment and accident quarter, and the reference dimensions the pricing team uses (segment, postcode region). Its vocabulary is the actuaries' own: 'pol ref', 'yyyymm', 'ep amt', 'veh years', 'acc qtr'.

- `earned_premium_monthly.pol_ref` means **premium_earning.policy_id**:  'Pol ref' is the policy system's contract reference.
- `earned_premium_monthly.ep_amt` means **premium_earning.earned_premium**: Premium earned in the month, GBP, daily pro-rata over the cover period.
- `earned_premium_monthly.yyyymm` means **premium_earning.accounting_month**: Accounting month as YYYYMM.
- `earned_premium_monthly.yyyymm` means **premium_earning.accident_quarter**: Calendar quarter of the accounting month, e.g. 2026Q3. Same labelling as the claims accident quarter so premium and claims line up.
- `earned_premium_monthly.veh_years` is the enterprise extension **vehicle_years**: Vehicle-years of exposure earned in the month (vehicles x days in force / 365). The denominator for claim frequency.
- `earned_premium_monthly.days_in_force` is the enterprise extension **days_in_force**: Days of cover in the month.
- `earned_premium_monthly.seg_cd` is the enterprise extension **motor_segment_code**: Bricksurance SE motor segment (PMU / PMO / CMV) as carried by the warehouse.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_earned_premium` presents `earned_premium_monthly` in core terms; prefer it over the raw table.
- `ibnr_estimate.ibnr_amt` means **valuation_result.amount**: The figure, in the stated currency. Sign follows the measure's own convention.
- `ibnr_estimate.acc_qtr` means **valuation_result.cohort**: Optional sub-division (e.g. an age-by-term band or underwriting-year cohort). The warehouse cohort is the accident quarter.
- `ibnr_estimate.seg_cd` is the enterprise extension **motor_segment_code**: Bricksurance SE motor segment.
- `ibnr_estimate.valuation_dt` is the enterprise extension **valuation_date**: Date the estimate was struck.
- `ibnr_estimate.method_cd` is the enterprise extension **reserving_method_code**: Reserving method (CHAIN_LADDER).
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_ibnr` presents `ibnr_estimate` in core terms; prefer it over the raw table.
- `segment_dim.seg_cd` is the enterprise extension **motor_segment_code**: PMU urban private motor, PMO other private motor, CMV commercial motor.
- `segment_dim.seg_desc` is the enterprise extension **motor_segment**: Segment label for people (use for filtering with labels).
- `segment_dim.lob_cd` is the enterprise extension **line_of_business_code**: Always MOTOR.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_segment` presents `segment_dim` in core terms; prefer it over the raw table.
- `postcode_region_dim.postcode_area` means **postcode_enrichment.postcode**: Postcode or postal-area key the attributes describe. Postcode AREA (letters only), not a full postcode.
- `postcode_region_dim.urbanity_code` means **postcode_enrichment.urbanity_code**: Settlement type of the postcode.
- `postcode_region_dim.region_name` means **postcode_enrichment.region_code**: Statistical region the postcode sits in. The warehouse carries the region name; the core attribute is a code. Kept as the name.
- Conformed view `lr_serverless_aws_us_catalog.bricksurance_semantics.vw_motor_postcode_region` presents `postcode_region_dim` in core terms; prefer it over the raw table.
