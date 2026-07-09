# Asset Inventory — what exists, what it's based on, which services carry it

The authoritative per-column inventory is generated (the `data_dictionary`
table and `build/ontology/*.ontology.json`); this page is the human map.

## 1. The model (the product)

| Asset | Count | Based on | Where |
|---|---|---|---|
| Entity specs | 24 | ACORD terminology + Lloyd's CDR crosswalk; party–role / transactional-money / typed-satellite / measure-code patterns | `model/<domain>/*.yaml` |
| Code sets (with governed values) | 23 | ACORD vocabularies, ISO 4217/3166 subsets | `model/reference/*.yaml` |
| Semantic views + metric views | 2 + 4 | The entities; metric definitions per [METRICS.md](METRICS.md) | `model/semantics/*.yaml`, `model/exchange/*.yaml` |
| Portable ontology (one JSON) | 1 | Everything above, exported + importable, round-trip verified | `build/ontology/` |

## 2. Deployed estate (demo workspace, catalog `lr_serverless_aws_us_catalog`)

| Asset | Databricks service | Notes |
|---|---|---|
| 48 tables across 9 `bricksurance_*` schemas | **Unity Catalog** (managed Delta) | Column definitions as comments; 86 informational PK/FK relationships |
| Governance tags on every table/column | **UC tags** | Taxonomy per [TAGGING.md](TAGGING.md), namespaced `bxc_` |
| `data_dictionary` + `schema_migration` | UC tables | Semantics that travel with shares; migration audit log |
| 4 metric views + 2 views | **UC metric views** | `MEASURE()` queries; the single definition point |
| 3 Genie spaces: [P&C Book](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17ade46ec18bc8da2cb30b55a26a6) · [Reinsurance & Exchange](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17b83371f1d56bba2404ad475e29d) · [Life & Valuations](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17b8339b41106b9f5784f0b2d04a4) | **AI/BI Genie** (+ **Genie One** as the unified front door) | Instructions, examples and SQL benchmarks generated from the model |
| [Data Core Console](https://data-core-console-7474659673789953.aws.databricksapps.com) | **Databricks Apps** (FastAPI + React) | Model browser · live metrics · exchange (LLM bordereau mapping) · network |
| Bordereau ingest | **Foundation Model API** (Claude) + SQL warehouse | Dictionary-as-contract mapping with validation before load |
| Share `bricksurance_re_exchange` (recipient `bricksurance-re`) | **Delta Sharing** (D2D) | Bordereau + dictionary + code sets; pending a metastore grant |
| Serverless SQL warehouse | **Databricks SQL** | Everything queries through it; scale-to-zero |
| ~700-row coherent world | `tools/world_engine.py` | Deterministic, `--scale` knob, sacred heroes invariant |

## 3. Tooling (all in `tools/`, all idempotent)

| Tool | Does |
|---|---|
| `generate.py` | Compiles specs → DDL (Databricks + Snowflake), tags, dictionary, docs, ERD, Genie context, ontology JSON |
| `world_engine.py` | The deterministic Bricksurance world, all domains, scale knob |
| `deploy_databricks.py` | Statement-by-statement deploy via the SQL execution API |
| `smoke_test.py` | 16 checks derived from the model, incl. cross-domain tie-outs |
| `create_genie_space.py` | Creates/updates the three specialized Genie spaces |
| `create_share.py` | The D2D exchange share (dictionary travels with the data) |
| `ingest_bordereau.py` | LLM mapping of messy inbound files against the dictionary |
| `import_ontology.py` | Adopt the whole model from one JSON file (round-trip verified) |
| `plan_migration.py` | Ontology diff → classified, reviewable migration plan (never auto-applies) |

## 4. Documents

[OVERVIEW.md](OVERVIEW.md) · [DESIGN.md](DESIGN.md) · [TAGGING.md](TAGGING.md) ·
[METRICS.md](METRICS.md) · [DEMOS.md](DEMOS.md) ·
[GETTING_STARTED.md](GETTING_STARTED.md) · [ADOPTION_PATH.md](ADOPTION_PATH.md) ·
[EVOLUTION.md](EVOLUTION.md) — all mirrored to Google Docs for review, and
linked from the relevant Console sections.
