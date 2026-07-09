# Getting Started — the 30-minute path

For a data engineer or architect who wants this running in their own
workspace, or an organisation adopting the ontology as their base.

## Prerequisites

- A Databricks workspace with Unity Catalog, a SQL warehouse, and a catalog
  you can create schemas in; the Databricks CLI authenticated (`databricks
  auth login`); `uv` (or plain Python 3.11+ with `pyyaml`/`databricks-sdk`).

## Path A — run the reference implementation (fork)

```bash
git clone https://github.com/wryszka/bricksurance-data-core && cd bricksurance-data-core

# 1. Point the binding at YOUR environment (the only file you must touch)
#    bindings/databricks.yaml: catalog, schema_pattern, tag_prefix
# 2. Compile the model
uv run --with pyyaml tools/generate.py
# 3. (Optional) generate the synthetic world — omit for structure-only
uv run --with pyyaml tools/world_engine.py --scale 1.0
# 4. Deploy and verify
uv run --with databricks-sdk tools/deploy_databricks.py --profile DEFAULT
uv run --with databricks-sdk,pyyaml tools/smoke_test.py --profile DEFAULT
# 5. Stand up the Genie spaces
uv run --with databricks-sdk,pyyaml tools/create_genie_space.py --space pnc
uv run --with databricks-sdk,pyyaml tools/create_genie_space.py --space reinsurance
uv run --with databricks-sdk,pyyaml tools/create_genie_space.py --space life
```

Then open a space and ask it something an actuary would ask. That moment is
the point of the whole exercise.

## Path B — adopt the ontology as YOUR model (import)

```bash
uv run --with pyyaml tools/import_ontology.py \
    --input build/ontology/bricksurance-data-core.ontology.json \
    --target /path/to/your-repo
cd /path/to/your-repo   # you now own a full model/ tree
# add bindings/ (copy ours, change catalog/prefix), copy tools/, generate, deploy
```

From here it is *your* ontology: rename the manifest, set your version, and
evolve it under the contract in [EVOLUTION.md](EVOLUTION.md). Keep the
crosswalk fields — they are what lets two adopters recognise each other's
data.

## Your first change (do this early, deliberately)

1. Add one optional attribute or one code value to a spec; bump the MINOR
   version.
2. `tools/generate.py`, then diff the ontology JSON — that diff is your
   change record.
3. `tools/plan_migration.py <old> <new>` — review the emitted script, apply
   it knowingly, keep the log row.
4. Re-run the smoke test and re-patch the Genie spaces.

You have now exercised the full governance loop once, on something harmless —
which is exactly how to learn it.

## Where to go next

- Moving real systems onto this: [ADOPTION_PATH.md](ADOPTION_PATH.md)
- Tag taxonomy to adopt or map: [TAGGING.md](TAGGING.md)
- Metric definitions and ownership: [METRICS.md](METRICS.md)
- What to demo to your own stakeholders: [DEMOS.md](DEMOS.md)
