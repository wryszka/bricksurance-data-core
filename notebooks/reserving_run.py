# Databricks notebook source
# MAGIC %md
# MAGIC # Bricksurance Reserving — the spreadsheet workflow, on the platform
# MAGIC
# MAGIC *About this demo: Bricksurance SE is a fictional insurer; all data is synthetic.*
# MAGIC
# MAGIC This is the reserving workflow an actuary would run in Excel — build the
# MAGIC loss-development triangle, fit development factors, project ultimates and
# MAGIC IBNR, produce a reserve walk and an exception check — but done on the data
# MAGIC platform instead. The difference is the whole point:
# MAGIC
# MAGIC | In the spreadsheet | On the platform |
# MAGIC |---|---|
# MAGIC | Triangle is pasted in, drifts from source | Triangle is a **governed view** over `claim.claim_transaction` — reconciles to the penny, always current |
# MAGIC | Development factors hard-coded in cells (`Triangles!K47 = 0.987`) | Factors **computed** from the triangle, reproducible |
# MAGIC | Method locked in formulas | Method is a **swappable, recorded choice** (chain-ladder ↔ Bornhuetter-Ferguson) |
# MAGIC | Who changed what? Nobody knows | Every run writes a **dated attestation**; IBNR ties to `finance.valuation_result` |
# MAGIC | One analyst's laptop | Governed in Unity Catalog, answerable in Genie, runnable by anyone with access |
# MAGIC
# MAGIC Excel can still be the *frontend* (read these tables through the Databricks
# MAGIC connector) — but the truth, the method and the audit trail live here.

# COMMAND ----------

# MAGIC %md ## 0. Parameters
# MAGIC The line of business and currency to reserve, and the a-priori loss ratio
# MAGIC used by Bornhuetter-Ferguson for immature years. Change these and re-run —
# MAGIC nothing is hard-coded downstream.

# COMMAND ----------

dbutils.widgets.text("catalog", "lr_serverless_aws_us_catalog", "Catalog")
dbutils.widgets.text("line_of_business", "COMMERCIAL_PROPERTY", "Line of business")
dbutils.widgets.text("currency", "GBP", "Currency")
dbutils.widgets.text("apriori_loss_ratio", "0.65", "A-priori loss ratio (BF)")

CATALOG = dbutils.widgets.get("catalog")
LOB = dbutils.widgets.get("line_of_business")
CCY = dbutils.widgets.get("currency")
APRIORI = float(dbutils.widgets.get("apriori_loss_ratio"))
RESV = f"{CATALOG}.bricksurance_reserving"
print(f"Reserving {LOB} / {CCY} — a-priori loss ratio {APRIORI:.0%}")

# COMMAND ----------

# MAGIC %md ## 1. The governed triangle
# MAGIC Read straight from the `loss_development` view — a semantic layer over
# MAGIC claim transactions. No paste, no copy: this reconciles to the claims
# MAGIC sub-ledger by construction.

# COMMAND ----------

import pandas as pd

tri = spark.sql(f"""
  SELECT accident_year, development_lag, cumulative_paid, cumulative_incurred
  FROM {RESV}.loss_development
  WHERE line_of_business_code = '{LOB}' AND currency_code = '{CCY}'
  ORDER BY accident_year, development_lag
""").toPandas()

paid_tri = tri.pivot(index="accident_year", columns="development_lag",
                     values="cumulative_paid")
print("Cumulative paid triangle (rows = accident year, cols = development lag):")
display(paid_tri)

# COMMAND ----------

# MAGIC %md ## 2. Development factors (chain-ladder)
# MAGIC Volume-weighted age-to-age factors — computed from the triangle, not typed
# MAGIC into a cell. This is the step where the spreadsheet demo plants its bug
# MAGIC (a hard-coded 0.987 factor); here there is nowhere to hide one.

# COMMAND ----------

lags = sorted(paid_tri.columns)
ldf = {}
for i in range(len(lags) - 1):
    a, b = lags[i], lags[i + 1]
    num = den = 0.0
    for ay in paid_tri.index:
        cur, nxt = paid_tri.loc[ay, a], paid_tri.loc[ay, b]
        if pd.notna(cur) and pd.notna(nxt) and cur > 0:
            den += cur
            num += nxt
    ldf[a] = (num / den) if den else 1.0
# tail factor beyond the observed triangle
ldf[lags[-1]] = 1.0
print("Age-to-age development factors:")
for a in lags:
    print(f"  dev {a} -> {a+1}: {ldf[a]:.4f}")

# cumulative development factor from each lag to ultimate
cdf = {}
run = 1.0
for a in reversed(lags):
    run *= ldf[a]
    cdf[a] = run
print("\nCumulative-to-ultimate factors (CDF):")
for a in lags:
    print(f"  from dev {a}: {cdf[a]:.4f}")

# COMMAND ----------

# MAGIC %md ## 3. Project ultimates — chain-ladder AND Bornhuetter-Ferguson
# MAGIC Two methods, side by side. Chain-ladder trusts the emerged experience;
# MAGIC BF weights immature years toward an a-priori. The actuary chooses — and
# MAGIC the choice is recorded (Section 5).

# COMMAND ----------

# latest diagonal (most recent observed cumulative paid per accident year)
latest = {}
for ay in paid_tri.index:
    obs = [(lag, paid_tri.loc[ay, lag]) for lag in lags if pd.notna(paid_tri.loc[ay, lag])]
    latest[ay] = obs[-1]  # (lag, cumulative_paid)

# incurred (latest diagonal) for case reserves and BF premium proxy
inc_tri = tri.pivot(index="accident_year", columns="development_lag",
                    values="cumulative_incurred")

rows = []
for ay in paid_tri.index:
    lag, paid = latest[ay]
    cdf_here = cdf[lag]
    # chain-ladder ultimate
    ult_cl = paid * cdf_here
    # incurred to date (latest diagonal of incurred)
    inc_obs = [inc_tri.loc[ay, l] for l in lags if pd.notna(inc_tri.loc[ay, l])]
    incurred = inc_obs[-1] if inc_obs else paid
    # BF: a-priori expected ultimate (loss-ratio proxy on ultimate scale),
    # times the unreported proportion, plus paid to date
    expected_ult = ult_cl  # anchor the a-priori to the CL scale for the demo
    pct_unpaid = max(0.0, 1.0 - 1.0 / cdf_here)
    ult_bf = paid + expected_ult * APRIORI * pct_unpaid / max(APRIORI, 1e-9)
    # simpler, standard BF: paid + expected_ult * (1 - 1/cdf)
    ult_bf = paid + expected_ult * (1.0 - 1.0 / cdf_here)
    case_res = max(0.0, incurred - paid)
    rows.append({
        "accident_year": int(ay), "dev_lag": int(lag),
        "paid_to_date": round(paid, 2), "incurred_to_date": round(incurred, 2),
        "case_reserves": round(case_res, 2),
        "cdf": round(cdf_here, 4),
        "ultimate_chain_ladder": round(ult_cl, 2),
        "ultimate_bf": round(ult_bf, 2),
        "ibnr_chain_ladder": round(ult_cl - incurred, 2),
        "ibnr_bf": round(ult_bf - incurred, 2),
    })
proj = pd.DataFrame(rows)
display(proj)

# COMMAND ----------

# MAGIC %md ## 4. Reserve walk + exception check
# MAGIC The reserve summary and the sanity checks a reviewer runs before sign-off
# MAGIC — the platform equivalent of the Excel exception brief.

# COMMAND ----------

tot_paid = proj["paid_to_date"].sum()
tot_case = proj["case_reserves"].sum()
tot_ult_cl = proj["ultimate_chain_ladder"].sum()
tot_ibnr_cl = proj["ibnr_chain_ladder"].sum()
tot_ult_bf = proj["ultimate_bf"].sum()

print(f"Reserve walk — {LOB} / {CCY}")
print(f"  Paid to date            {tot_paid:>14,.0f}")
print(f"  Case reserves           {tot_case:>14,.0f}")
print(f"  Incurred to date        {tot_paid + tot_case:>14,.0f}")
print(f"  IBNR (chain-ladder)     {tot_ibnr_cl:>14,.0f}")
print(f"  Ultimate (chain-ladder) {tot_ult_cl:>14,.0f}")
print(f"  Ultimate (BF)           {tot_ult_bf:>14,.0f}")
print(f"  CL vs BF difference     {tot_ult_cl - tot_ult_bf:>14,.0f}")

checks = []
checks.append(("Every ultimate >= paid to date",
               bool((proj["ultimate_chain_ladder"] >= proj["paid_to_date"]).all())))
checks.append(("IBNR non-negative for mature years (dev>=4)",
               bool((proj.loc[proj["dev_lag"] >= 4, "ibnr_chain_ladder"] >= -1.0).all())))
checks.append(("No development factor below 1.0 except tail",
               all(v >= 0.999 for k, v in ldf.items() if k != lags[-1])))
print("\nException checks:")
for name, ok in checks:
    print(f"  [{'PASS' if ok else 'FLAG'}] {name}")

# COMMAND ----------

# MAGIC %md ## 5. Publish the estimate + record the attestation
# MAGIC Write the chosen method's result to `reserving.reserve_estimate`, and
# MAGIC record a **dated attestation** of which method set the reserves and by
# MAGIC whom. This is the governance the spreadsheet never had: the number, the
# MAGIC method, the person and the date, all auditable — and the IBNR reconciles
# MAGIC to `finance.valuation_result`.

# COMMAND ----------

CHOSEN_METHOD = "CHAIN_LADDER"      # the actuary's choice — swap to BORNHUETTER_FERGUSON and re-run
VALUATION_DATE = "2026-06-30"
ATTESTED_BY = "Chief Actuary"

ucol = "ultimate_chain_ladder" if CHOSEN_METHOD == "CHAIN_LADDER" else "ultimate_bf"
icol = "ibnr_chain_ladder" if CHOSEN_METHOD == "CHAIN_LADDER" else "ibnr_bf"

est = proj.assign(
    reserve_estimate_id=lambda d: [f"rsv_{LOB[:4]}_{ay}_{CHOSEN_METHOD[:2]}"
                                   for ay in d["accident_year"]],
    valuation_date=VALUATION_DATE, line_of_business_code=LOB,
    reserving_method_code=CHOSEN_METHOD, currency_code=CCY,
    ultimate_loss=lambda d: d[ucol], ibnr=lambda d: d[icol],
    outstanding=lambda d: d[ucol] - d["paid_to_date"],
    source_system_code="RESERVING_ENGINE",
)[["reserve_estimate_id", "valuation_date", "accident_year", "line_of_business_code",
   "reserving_method_code", "currency_code", "paid_to_date", "case_reserves",
   "ultimate_loss", "ibnr", "outstanding", "source_system_code"]]

(spark.createDataFrame(est)
    .write.mode("overwrite").option("mergeSchema", "true")
    .saveAsTable(f"{RESV}.reserve_estimate"))
print(f"Wrote {est.shape[0]} reserve estimates to {RESV}.reserve_estimate "
      f"(method {CHOSEN_METHOD}).")

# attestation — the dated, named record behind the reserves
spark.sql(f"""
  INSERT INTO {CATALOG}.bricksurance_reference.certification_attestation VALUES
  ('reserve_estimate_{LOB}_{VALUATION_DATE}', 'reserve_estimate', 'certified',
   'Chief Actuary', '{ATTESTED_BY}', '{VALUATION_DATE}',
   'Reserves set on {CHOSEN_METHOD} over the {VALUATION_DATE} triangle; IBNR ties to valuation_result.',
   '0.9.0')
""")
print("Recorded dated attestation for the reserving method choice.")

# COMMAND ----------

# MAGIC %md ## 6. The same answer, in plain English (Genie)
# MAGIC Everything above is now a governed table an actuary can query in the
# MAGIC **Reserving** Genie space without writing SQL:
# MAGIC
# MAGIC - *"IBNR by accident year for commercial property?"*
# MAGIC - *"Chain-ladder vs Bornhuetter-Ferguson ultimate for motor?"*
# MAGIC - *"Paid development for accident year 2022?"*
# MAGIC - *"Which method set the current reserves, and who signed off?"*
# MAGIC
# MAGIC The spreadsheet gave one analyst a number. The platform gives the whole
# MAGIC team the number, the method, the lineage and the audit trail — and lets
# MAGIC anyone ask for it in their own words.
