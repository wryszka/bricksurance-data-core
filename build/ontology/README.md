# Bricksurance Data Core — Ontology Export

`bricksurance-data-core.ontology.json` is the **entire semantic model in one
platform-neutral file** (format `bricksurance-data-core/ontology-v1`,
v0.11.0): 83 entities, 76 code sets, 7 views, 13 metric views, 11 functions, 304 relationships.

## What is in it

| Key | What it holds |
|---|---|
| `domains` | The 21 business domains |
| `entities` | Tables: attributes with type, definition, data classification, keys, quality rules, ACORD/Lloyd's crosswalk |
| `code_sets` | Controlled vocabularies **with their allowed values** |
| `views` / `metric_views` | Semantic views and metrics — **each measure carries its exact SQL formula, plus owner and certification** |
| `functions` | Governed callable tools (name, typed inputs, return, body) |
| `relationships` | The full foreign-key graph, pre-derived |

Every attribute and measure has a business definition. This is a complete,
self-contained specification: a reader needs nothing else to understand or
re-implement the model.

## Two ways to use it

1. **Think about your own implementation** — read the JSON (or the companion
   `data_dictionary.md` and `metric_catalog.md`). It is deliberately
   platform-agnostic: entities, definitions, relationships and metric formulas,
   with no vendor specifics. Map it onto whatever platform you run.
2. **Stand it up on Databricks** — follow `INSTALL_DATABRICKS.md`. In short:
   drop this JSON into a fork, add a one-file binding (your catalog + schema
   naming), run the generator, deploy. ~30 minutes to a governed Unity Catalog
   with definitions, keys, tags, metric views and Genie context.

## Round-trip guarantee

`tools/import_ontology.py --input <this file> --target <dir>` regenerates the
full spec tree; export→import→export is verified byte-identical. Adopting the
model, or exchanging it between organisations, is this one file.
