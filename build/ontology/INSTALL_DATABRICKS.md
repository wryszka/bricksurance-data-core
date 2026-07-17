# Installing the Semantic Layer on Databricks

How to take the ontology export and stand it up as a governed Unity Catalog
semantic layer — tables with definitions, keys, governance tags, metric views
and Genie context — in about 30 minutes. Nothing here is bespoke to
Bricksurance; swap the binding and it is your model on your workspace.

## What you are installing

From one platform-neutral file (`build/ontology/*.ontology.json`) the generator
produces, per platform:

- **Unity Catalog DDL** — every entity as a table with column-level `COMMENT`
  definitions, informational `PRIMARY KEY` / `FOREIGN KEY` constraints, and
  reference-data seeds.
- **Governance tags** — model/version/domain/maturity and per-column
  `data_classification`, namespaced so they never clash with your tag policies.
- **Metric views** — `CREATE VIEW ... WITH METRICS` for every metric; the
  measure formulas come straight from the spec.
- **The data dictionary table** — the model describing itself, in-catalog.
- **Genie space context** — instructions, vocabulary and benchmarks.

## Prerequisites

- A Databricks workspace with **Unity Catalog**, a **SQL warehouse**, and a
  catalog you can create schemas in.
- The **Databricks CLI** authenticated: `databricks auth login --profile <name>`.
- `uv` (or Python 3.11+ with `pyyaml` and `databricks-sdk`).

## Step 1 — Get the model

Either clone the repo, or import the ontology into a fresh tree you own:

```bash
uv run --with pyyaml tools/import_ontology.py \
  --input build/ontology/bricksurance-data-core.ontology.json \
  --target /path/to/your-repo
```

## Step 2 — Point the binding at your environment (the only file you edit)

`bindings/databricks.yaml` maps the logical model onto your physical platform:

```yaml
platform: databricks
catalog: your_catalog              # your Unity Catalog
schema_pattern: "bricksurance_{domain}"   # or "{domain}", or your own convention
tag_prefix: "bxc_"                 # namespace for governance tag keys
```

Nothing in `model/` changes. The catalog, the schema naming, and the tag
namespace are the whole of what makes it "yours".

## Step 3 — Compile

```bash
uv run --with pyyaml tools/generate.py
```

Writes `build/databricks/` (numbered SQL you can read before running):
`00_schemas.sql`, `10_reference.sql` (code sets + dictionary + seeds),
`20_*` (entities), `30_*`/`35_*` (views + metric views), `40_*` (functions),
`90_relationships.sql` (all PK/FK).

## Step 4 — Deploy

```bash
uv run --with databricks-sdk tools/deploy_databricks.py --profile <name>
```

Runs the SQL statement-by-statement through the SQL Execution API, idempotent
(`CREATE ... IF NOT EXISTS`, `INSERT OVERWRITE` seeds). To run it by hand
instead, execute the numbered files in order in a SQL editor.

**With synthetic data** (optional, for a demo or a shape check):

```bash
uv run --with pyyaml tools/world_engine.py --scale 1.0   # run BEFORE deploy
uv run --with databricks-sdk tools/deploy_databricks.py --profile <name>
```

> Order matters: `generate.py` rebuilds `build/`, so always generate **before**
> world_engine, and deploy after both.

## Step 5 — Verify

```bash
uv run --with databricks-sdk,pyyaml tools/smoke_test.py --profile <name>
```

Structural + tie-out checks, all derived from the model (table counts, the
FK graph, the ledger balancing, cross-domain reconciliations).

## Step 6 — Stand up Genie (the payoff)

```bash
uv run --with databricks-sdk,pyyaml tools/create_genie_space.py --space pnc --profile <name>
# spaces: pnc reinsurance life distribution customer finance capital governance
```

Each space is created from the model with generated instructions, examples and
SQL-verified benchmarks. Genie One surfaces the certified spaces together.

## What you end up with

A Unity Catalog where **every table and column explains itself**, relationships
are declared (so Genie and BI infer joins), **metrics are defined once** and
queried with `MEASURE()`, PII is tagged for masking, and the catalog *is* the
documentation. From here: attach your own data by conforming it to these tables
(see `docs/ADOPTION_PATH.md`), and evolve the model under the versioned change
process (`docs/EVOLUTION.md`).

## Other platforms

`build/snowflake/` is generated from the same specs (tables + comments +
keys). New platforms are a binding plus a type map; the model does not change.
That portability is the point — you install on Databricks today and the
semantic contract still travels to whatever else your group runs.
