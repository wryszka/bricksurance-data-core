# Demo Cookbook

Ten runnable set pieces. Each shows one claim the project makes; together they
make the argument: **give LLM agents governed semantics and everything gets
better.** Every demo runs against the live estate; nothing is staged footage.

## 1. The LLM difference (the headline)
**Claim:** LLM value is a semantics problem, not a model problem.
**Do:** In the [P&C Genie space](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17ade46ec18bc8da2cb30b55a26a6), ask *"What is our gross written premium by line of business for underwriting year 2026 in GBP?"*
**Expect:** Genie picks the metric view, uses `MEASURE()`, and returns figures that reconcile to the transactions. Then show the same question in a room over bare, comment-less tables (any scratch schema) — hedging and guesswork. Same LLM; the semantics are the difference.

## 2. The golden thread
**Claim:** One world, every hop governed.
**Do:** Catalog Explorer: `policy` POL-2026-000001 → claim CLM-2026-000001 → cession → treaty TR-QS-PROP-2026 → submission SUB-2026-000001; show each table's definitions, tags and relationships along the way.
**Expect:** A quote-to-reinsurance thread where every column explains itself.

## 3. Derived, never stored
**Claim:** Balances you can audit.
**Do:** Ask the P&C space *"What is the outstanding reserve on claim CLM-2026-000001?"*
**Expect:** 270,000 — computed live as the sum of signed reserve movements (450k set, 180k released on payment). No stored balance anywhere to disagree with it.

## 4. Killing the bordereau
**Claim:** Exchange without middleware.
**Do:** In the [Console](https://data-core-console-7474659673789953.aws.databricksapps.com) Exchange tab: load the sample coverholder CSV (title rows, DD/MM dates, "Prop - Commercial"), click **Map with Claude**, review the mapping report and validation, then load.
**Expect:** The dictionary acted as the contract; every record validated against it before landing; the loaded total matches the file's own TOTAL row.

## 5. Semantics that travel
**Claim:** A share carries its meaning.
**Do:** Show the `bricksurance_re_exchange` share contents: the live cession bordereau **view** plus `data_dictionary` plus code sets; query it from the recipient workspace as Bricksurance Re.
**Expect:** The receiving analyst reads definitions, classifications and code meanings without a single email to the sender.

## 6. Adopt the ontology in five minutes
**Claim:** Starting is one file, not one programme.
**Do:** `import_ontology.py --input build/ontology/*.json --target /tmp/newco` → show the generated model tree → add a one-file binding → `generate.py`.
**Expect:** A second company owns the full model and its platform artifacts in minutes — the market-standard mechanism, live.

## 7. Change without fear
**Claim:** Evolution is governed, not heroic.
**Do:** Run `plan_migration.py` on the real v0.4.0 vs v0.5.0 exports from git history.
**Expect:** Six changes found, the column removal classified MAJOR with a `-- MANUAL` block, version-bump gate applied, reviewable script + migration log emitted. Nothing auto-applied.

## 8. The RED run
**Claim:** Governance that blocks, visibly.
**Do:** In the [Life & Valuations space](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17b8339b41106b9f5784f0b2d04a4), ask for the runs on 30 June 2026 and their verdicts; then ask *"Which assumption sets did the latest green valuation run use?"*
**Expect:** One RED run with **no published results** (the gate held); the GREEN run's full recipe — assumption sets, scenario set, model version — the reproducibility story in one answer.

## 9. Modelled vs reported, honestly
**Claim:** The model keeps day-one estimates and firming reality apart.
**Do:** Ask the [Reinsurance space](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17b83371f1d56bba2404ad475e29d): *"For Windstorm Ostara, compare modelled and reported gross losses on the treaty book."*
**Expect:** Modelled 12.4m (as of day 2) vs reported 10.9m (a month on) — as-of snapshots on an explicit basis, never overwritten.

## 10. Rebuild the world from zero
**Claim:** The whole estate is reproducible.
**Do:** `generate.py` → `world_engine.py` → `deploy_databricks.py` → `smoke_test.py`.
**Expect:** 16/16 checks including cross-domain tie-outs (published reserves == sum of claim transactions), on a freshly rebuilt estate. Add `--scale 10` to show the volume knob.

## 11. Bricksurance Re, locally (the share without the share)
**Claim:** The exchange story doesn't wait for infrastructure.
**Do:** `create_local_exchange.py` builds a `partner_re` schema holding exactly what the Delta Share would deliver — the live cession bordereau plus the dictionary and code sets. Query it as the receiving analyst.
**Expect:** 13 bordereau lines with their meaning readable locally ("Premium ceded to reinsurers..."). When the D2D grant lands, the recipient mounts the share instead — identical queries, zero rework.

## 12. Two insurers, one ontology (the market-standard punchline)
**Claim:** When both parties run the ontology, the mapping project disappears.
**Do:** `create_second_company.py` — Meridian Mutual adopts via ontology import (one JSON + a one-file binding), deploys its full estate (own schemas, own tag namespace, same catalog for now), then submits its canonical premium bordereau into ours: `INSERT INTO ... SELECT *`.
**Expect:** 6 lines, totals matching both sides, no mapping spec, no LLM needed — contrast demo 4, where the non-adopter's CSV required Claude against the dictionary. Moving Meridian to its own workspace later changes the binding, nothing else.

---
*Bricksurance is fictional; all data synthetic. Before customer sessions:
warehouse warm, share status checked (Console → Network), and never present a
real customer's estate shape — anonymize past recognition.*
