# Bricksurance Data Core

**An open, business-first semantic data model for insurance.**

Most insurers approach data governance from the technology end: pick a platform,
pick a catalog tool, pick a modelling tool — then argue about them for a year while
the business still can't agree what a *policy* is. This project inverts that. The
**business semantic layer comes first** and lives as plain, versioned, human-readable
specifications. The toolset is secondary: platform-specific artifacts (Databricks,
Snowflake, others) are **generated** from the same specs, so the model works in the
federated estates insurers actually have.

## What this is

- **A canonical insurance data model** — parties, policies, coverages, claims,
  reinsurance, exchange — aligned to **ACORD terminology** with a crosswalk to the
  **Lloyd's Core Data Record**, expressed as simple YAML specs in [`model/`](model/).
- **A generator** ([`tools/generate.py`](tools/generate.py)) that turns those specs
  into everything downstream: DDL with full column-level definitions, primary/foreign
  key relationships, governance tags, a machine-readable data dictionary, ERDs, and
  instructions for natural-language tools such as Databricks Genie.
- **Platform bindings** ([`bindings/`](bindings/)) that map the *logical* model onto
  each *physical* platform. The same Policy spec becomes a Unity Catalog table on
  Databricks and a commented table on Snowflake — the definitions never fork.
- **A data-exchange pattern** where the standard travels with the data: every share
  between parties (insurer ↔ reinsurer ↔ broker) includes a `data_dictionary` table
  generated from the same specs, so the receiver gets the semantics, not just rows.

## Design principles

1. **Business layer first.** The model is owned in business terms (function), not in
   any platform's DDL (toolset). If you can't read it without an engineer, it isn't
   governance.
2. **Model-as-code, single source of truth.** One spec generates the tables, the
   comments, the tags, the docs, the ERD and the LLM context. Catalog, documentation
   and semantic layer can never drift apart because they are the same file.
3. **Standards-aligned, not standards-imprisoned.** Names, definitions and code sets
   follow ACORD vocabulary and map to the Lloyd's CDR where relevant. We take the
   proven structural patterns (party–role, agreement, coverage, money provision),
   not the full model ocean.
4. **Federation is the normal case.** Group centre on one cloud, retail units on
   Databricks, an acquired specialty unit on Snowflake — that is a *supported
   topology*, not a migration problem. Exchange rides on open table formats and open sharing
   protocols, never bespoke middleware.
5. **Extend, never restart.** New lines of business, new domains, new parties are
   new spec files and new code-set rows. The party–role pattern and the generator
   make additions additive.

## Quickstart

```bash
# Generate all platform artifacts from the model specs
uv run --with pyyaml tools/generate.py

# Output lands in build/:
#   build/databricks/   DDL + tags + seeds for Unity Catalog
#   build/snowflake/    DDL + seeds for Snowflake
#   build/docs/         data dictionary (markdown) + ERD (mermaid)
#   build/genie/        instructions for Databricks Genie spaces
```

To target your own environment, edit the binding files in `bindings/` — for example
the Unity Catalog name and schema naming pattern. Nothing in `model/` needs to change.

## Repository layout

```
model/            The semantic model (the product). YAML specs: entities + code sets.
  model.yaml      Manifest: model version and domain definitions.
bindings/         Logical → physical mapping per platform.
tools/            The generator.
build/            Generated artifacts (committed for visibility — do not edit).
docs/DESIGN.md    Architecture, federated topology, exchange patterns, roadmap.
```

## Standards note

ACORD standards are licensed to ACORD members. This project **aligns to ACORD
terminology and cites ACORD element names** as a crosswalk; it does not reproduce or
redistribute the ACORD Information Model itself. The same applies to Lloyd's Core
Data Record references. If you are an ACORD member, the crosswalk columns in the
specs tell you exactly where to attach your licensed artifacts.

## About this demo

Bricksurance SE is a **fictional insurance group** used by Databricks field
engineering to demonstrate platform capabilities. All data produced by this project
is synthetic. The model, however, is designed to be genuinely reusable: fork it,
rename the binding, and use it to start your own governance story.

## License

[Apache 2.0](LICENSE)
