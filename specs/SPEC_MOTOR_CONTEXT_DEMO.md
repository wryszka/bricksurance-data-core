# SPEC — "Why has our motor loss ratio deteriorated?" (ACORD base + enterprise mapping + Genie Ontology)

> Status: PLAN agreed 2026-11-06 (decisions recorded in §0). Second chapter of the
> context demo in the Data Core Console, beside One Number.
> Audience: insurance executives, architects and actuaries; also the Genie Code /
> Genie Ontology team (Belgrade) follow-up. Bricksurance SE is fictional; all data
> is synthetic.

## 0. Decisions taken (2026-11-06)

| Question | Decision |
|---|---|
| Scale of the motor book (£100m earned per quarter vs a £3m core book) | **Separate motor experience book at spec scale.** Own source schemas, mapped to the core concepts. Not posted to the ledger, reserving triangle or IFRS 17; said plainly on screen. Core heroes untouched. |
| Where it lives | **Second chapter in the Data Core Console** (route `#/motor`), reusing One Number's rulebook, maker/checker, dual Genie spaces and cached answers. |
| Track order | Answer first (clear-track rule), ontology as "how it got there". Spec's 8 stages are all present, reordered. |
| Native surfaces | **Workspace admin only.** Modeled layer = comments, tags, certification tags, metric views, Genie Agent instructions, dashboards. Pages and Domains need account-level previews: shown as roadmap, with the mapping catalog as the Page-ready content. Genie One API: enable the workspace preview if it is offered. |
| Audience | General reusable insurer demo first; shaped so the Belgrade follow-up can use it (two layers, inferred-snippet evidence, Genie One path). No fixed date. |

## 1. The one picture (what sits where)

```
  A. INDUSTRY BASE (open, ours)        B. ENTERPRISE SEMANTICS (the insurer's)      C. INFERRED (native, automatic)
  bricksurance-data-core YAML   --->   mapping specs: source column -> concept  ---> Genie Ontology snippets harvested
  ACORD-aligned concepts:              + insurer definitions (rulebook, segments)     from dashboards, saved queries,
  Policy, Coverage, Insured Object,    materialised as UC comments, tags,              metric views, Genie Agents.
  Party, Claim, Claim Transaction,     certification, conformed views, metric          Ranked by authority, permission-
  Premium Transaction                  view, Genie Agent instructions                  gated, cited in answers.
                                       (= Databricks' "modeled layer")                 Cannot be authored or exported.
                                                   |
                                                   v
                                   CONSUMPTION: Genie Agent (curated space, API we already use)
                                                Genie One (workspace-wide, ontology-grounded, API preview)
                                                Genie Code / agents (same ontology)
```

Reading of the Databricks docs as of 2026-11-06 (not memory):
- Genie Ontology = two layers. "Unity Catalog semantics (modeled context)" = metric views,
  domains, Pages, certification. "Inferred context" = snippets Genie extracts from metric
  views, dashboards, SQL queries (incl. dbt runs since 22 Oct 2026) and Genie Agents, scored
  by authority (source, usage, freshness), gated by UC permissions, shown as citation icons.
  Public Preview; enabled by default since 6 Aug 2026; snippets to all customers since 13 Aug.
- No public API to list, edit, approve or promote inferred snippets. Internal roadmap decks
  describe promoting inferred terms into the glossary and owner approval workflows: roadmap,
  not product. We say so.
- Pages (Beta, account-level preview, need a domain). Genie One prioritises a Page over
  inferred context and cites it. Created in the UI or bulk-imported with Genie Code. No REST
  API documented. Domains have a Beta REST API (`POST /api/2.0/domains`, needs MANAGE DISCOVER).
- Certification = governed tag `system.certification_status` set by SQL on tables, views,
  functions, dashboards, Genie Agents. Metric views are not in the documented list (test it).
- Genie One API (preview, workspace admin enables): `POST /api/2.0/genie/one/responses`, SSE,
  answers carry citation annotations. Genie Agents API: what One Number already uses.
- RDF/OWL import is not native. OntoBricks (Labs) does OWL/R2RML; Ontos (Labs) does RDF
  semantic models. We do not claim it.

The sentence that ties A, B and C together, already in the Belgrade proposal:
**"What Genie infers stays native; what a steward certifies becomes portable."**

## 2. What is reused (no rebuild)

| Spec stage | Existing asset | How it is used |
|---|---|---|
| ACORD reference ontology | model-as-code (100 entities, ACORD/Lloyd's CDR crosswalk), ontology JSON, Atlas model browser | The concepts the mapping targets. Six on screen: Policy, Coverage, Insured Object (Risk), Party, Claim, Premium. |
| Competing definitions | One Number rulebook `semantics.loss_ratio_definition`, `measure_expr()` compiles booleans to SQL, maker/checker, republish to metric view + Genie instructions | Same rulebook, same code. Motor adds the "claims operations ratio" (paid / written) as the popular legacy pattern. |
| Genie pattern | `one_number.py` ask/cache/explain, raw vs governed spaces, verified saved answers | Copied pattern, new spaces. |
| Second insurer | Meridian Mutual via ontology import (demo 12) | Kept as the "full adopter" rung; a mapping-based insurer is added as the middle rung. |
| Discovery seeding | 3 Lakeview dashboards over certified metric views; Genie Ontology explainer doc | Add motor dashboards and the legacy claims-ops query as snippet sources. |
| Console | Data Core Console app, One Number view (beats, Explain, Explore, Asker) | New view `MotorView.tsx` with the same components. |

## 3. What is new

### 3.1 Motor experience book (three source systems, three vocabularies)

Schemas (binding pattern `bricksurance_{domain}`; these are source extracts, not model domains):

| Schema | System | Tables | Vocabulary |
|---|---|---|---|
| `bricksurance_src_pas` | Policy administration | `pol_master`, `pol_vehicle`, `pol_cover`, `pol_premium_txn` | `contract_reference`, `cover_start_dt`, `product_cd` (PMU / PMO / CMV), `annual_prem_amt`, `risk_postcode`, `use_class` |
| `bricksurance_src_claims` | Claims management | `clm_header`, `clm_movement` | `claim_ref`, `policy_no`, `loss_dt`, `peril_cd` (THEFT, AD, TPBI, TPPD, FIRE, WINDSCREEN), `head_of_damage`, `movement_type` (PAID, RESERVE, RECOVERY, FEE) |
| `bricksurance_src_actuarial` | Actuarial warehouse | `earned_premium_monthly`, `ibnr_estimate`, `segment_dim`, `postcode_region_dim` | `pol_ref`, `yyyymm`, `ep_amt`, `veh_years`, `seg_cd`, `acc_qtr` |

Size (deterministic, seed 20261106): about 400k policies, 400k vehicles, 30k claims over Q2+Q3 2026
(plus Q1 2026 as context), about 100k movements, 2.4m earned-premium rows (policy × month,
Apr–Sep 2026). Generated locally with numpy, written as parquet, uploaded to a UC Volume,
loaded with `CREATE OR REPLACE TABLE ... AS SELECT * FROM read_files(...)`. Not committed
(regenerate on demand).

Valuation date 31 Oct 2026. Accident-quarter basis.

**Targets (must reproduce to the penny through SQL):**

| Segment | Q2 EP | Q2 incurred | Q3 EP | Q3 incurred | LR Q2 | LR Q3 |
|---|---:|---:|---:|---:|---:|---:|
| Urban private motor (PMU) | 35.00 | 25.20 | 37.00 | 31.82 | 72.0% | 86.0% |
| Other private motor (PMO) | 40.00 | 22.00 | 42.00 | 23.94 | 55.0% | 57.0% |
| Commercial motor (CMV) | 25.00 | 16.80 | 26.00 | 19.84 | 67.2% | 76.3% |
| Total | 100.00 | 64.00 | 105.00 | 75.60 | 64.0% | 72.0% |

Incurred = paid + outstanding case reserves + IBNR − recoveries (the One Number v1 rule,
earned basis). Contribution method: hold Q3 earned premium, compare actual Q3 claims with
Q2 loss ratio × Q3 EP: urban +5.18m (62%), commercial +2.37m (28%), other +0.84m (10%).

**Evidence the data must carry (spec §"Required supporting analysis"):**
- Urban theft: frequency per vehicle-year up (Q2→Q3) and theft severity up (total-loss values).
- Vehicle repair: `head_of_damage = VEHICLE_REPAIR` average cost up across all segments, strongest urban.
- Commercial bodily injury: a handful of large TPBI claims (> £500k) in Q3 vs one in Q2; the
  large-loss share of the commercial deterioration is computable.
- Geography: urban deterioration concentrated in three metro regions (Greater London,
  West Midlands, Greater Manchester) via `postcode_region_dim` (synthetic postcode areas).
- Coverage: own damage vs third-party injury vs third-party property vs theft.
- Follow-ups that must work from data, not narrative: "which areas", "frequency or
  severity", "how much is large losses".

### 3.2 Mapping spec kind (the reusable mechanism)

New `kind: mapping` in `model/mappings/*.yaml`, loaded by `generate.py` like other kinds:

```yaml
kind: mapping
name: pas_motor
title: Policy administration (motor) -> core concepts
source_system: PAS_MOTOR          # code in reference.source_system
schema: src_pas                   # bound via schema_pattern
tables:
  - source: pol_master
    concept: policy.policy          # core entity
    grain: one row per contract
    columns:
      - source: contract_reference
        attribute: policy_number
        note: "'contract reference' is what the policy system calls the policy number"
      - source: product_cd
        attribute: line_of_business_code
        value_map: {PMU: MOTOR, PMO: MOTOR, CMV: MOTOR}
extensions:                        # insurer-specific, preserved not forced into ACORD
  - name: motor_segment
    source: pol_master.product_cd
    definition: "Bricksurance SE motor segment: PMU urban private, PMO other private, CMV commercial"
```

Generator outputs from a mapping:
1. `build/databricks/50_mappings.sql`: conformed views `semantics.vw_motor_policy`,
   `vw_motor_vehicle`, `vw_motor_coverage`, `vw_motor_claim`, `vw_motor_claim_transaction`,
   `vw_motor_earned_premium` whose column comments are the core attribute definitions;
   `COMMENT ON COLUMN` and `bxc_concept` tags on the source tables ("maps to Policy.policy_number").
2. `build/docs/mapping_catalog.md`: the crosswalk table, one row per concept, one column per
   system (ACORD term | PAS term | Claims term | Actuarial term | definition). This is the
   Page-ready content for when Pages are available.
3. A "Vocabulary by source system" section in `genie_instructions.md`, and a `mappings`
   section in the ontology JSON (round-trip preserved).

Second insurer: `model/mappings/harbour_*.yaml` over a small Guidewire-shaped sample
(`harbour_src_*`, ~2k policies, ~200 claims, fictional "Harbour Mutual"). Same generator,
same conformed views and metric view, same question answered. Proof = the mapping file is
the only thing that changed.

### 3.3 Unity Catalog semantics

- `semantics.motor_loss_ratio_components` view (policy × quarter × segment × region: earned,
  written, paid, case outstanding, IBNR, recoveries, fees, claim count, vehicle-years).
- `semantics.motor_performance_metrics` metric view, **published from the APPROVED rulebook
  version** (same `publish()` path as One Number, owned by the app SP). Dimensions: quarter,
  segment, region, urbanity, peril, head of damage, coverage, vehicle group, large-loss flag.
  Measures: earned_premium, written_premium, incurred_claims, paid_claims, loss_ratio
  (approved), claim_count, vehicle_years, frequency, severity, plus
  `claims_operations_ratio` (paid / written) explicitly described as "the legacy weekly
  claims-ops number, not the approved loss ratio".
- Certification tags on conformed views and the metric view (test whether metric views
  accept the tag; fall back to the components view).
- Rulebook: motor adds nothing structural. The "claims operations ratio" is recorded as a
  LEGACY row so the governance beat can show where it came from.

### 3.4 Genie

- `motor-raw` Genie Agent: the 10 source tables, no instructions.
- `motor-governed` Genie Agent: metric view + conformed views + rulebook; instructions
  generated from the mapping specs and the approved definition; benchmark questions with
  SQL answers (acceptance test = definition of done).
- Genie One: the third arm. If the workspace preview can be enabled, the app calls the Genie
  One API and shows the citation annotations; otherwise screenshots from the UI. Reported
  honestly either way.
- Snippet seeding: Lakeview dashboard "Motor performance (certified)" over the metric view;
  a saved query + small dashboard "Claims ops weekly ratio" computing paid / written on the
  raw claims schema (the popular pattern). Then observe what Genie One cites. Genie Ontology
  builds on its own schedule; the demo never promises an instant panel.

### 3.5 Console chapter `#/motor` (beats)

1. **The question.** CUO's question; the three systems side by side with their three
   vocabularies for the same five concepts (the problem is meaning, not data).
2. **Ask with no context.** Raw agent, three live attempts, plain-English "what it counted".
3. **The answer.** Governed agent gives the spec's answer; the number tiles, segment table and
   contribution bridge are computed live from the metric view and must match.
4. **Drill down.** Three live follow-ups (areas, frequency vs severity, large losses) with
   the evidence charts.
5. **Two numbers, two questions.** Approved loss ratio vs claims-ops ratio side by side; the
   rulebook row for each; where each came from; what Genie Ontology inferred, if anything.
6. **How it got there.** The three-layer picture; the crosswalk table; "Harbour Mutual
   mapped in one file"; Genie One citations; the honest native/custom/simulated table.

Every beat: Explain ("what am I seeing / why it matters"), Explore for depth, "About this
demo" disclaimer, no product names on the main track.

## 4. Native vs custom vs simulated (say it on screen)

| Capability | Nature |
|---|---|
| Metric views, comments, tags, certification tags, FK constraints, Genie Agents + API, Lakeview dashboards | Native Databricks |
| Genie Ontology inferred snippets and citations | Native, automatic; we seed sources and observe, we do not author |
| Genie One API | Native, preview; used if enabled |
| Pages, Domains | Native but account-level previews we cannot enable here; shown as roadmap with ready content |
| Model-as-code, mapping spec kind, generator, rulebook with maker/checker, republish-on-approval | Custom (this repo, open source) |
| Motor experience book | Synthetic, deterministic, labelled; not in the ledger |

## 5. Work plan

| # | Step | Depends on workspace auth? |
|---|---|---|
| 1 | `tools/motor_book.py`: deterministic generator reproducing §3.1 to the penny; local checks | No |
| 2 | `kind: mapping` in generator + three PAS/claims/actuarial mapping specs; outputs of §3.2 | No |
| 3 | Load: volume upload, CTAS, source comments/tags, conformed views, components view, metric view, certification | Yes |
| 4 | Genie: raw + governed agents, benchmarks, acceptance script; Genie One preview check | Yes |
| 5 | Dashboards + legacy claims-ops query for snippet seeding; observe citations | Yes |
| 6 | Console chapter `#/motor` (backend `motor.py` sharing One Number code, `MotorView.tsx`), deploy | Yes |
| 7 | Harbour Mutual second-insurer mapping + sample | Partly |
| 8 | Presenter script `docs/MOTOR_CONTEXT_DEMO.md` + Google Doc mirror; DEMOS.md, GENIE_CATALOG, Console Documents panel, hub tile run doc; persona review | No |

Open item: serverless CLI profile `fevm-lr-serverless-aws-us` token expired; steps 3–6 wait
for `databricks auth login`.
