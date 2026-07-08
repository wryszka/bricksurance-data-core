# Bricksurance Data Core — Design

*Status: living document. Model version 0.1.0.*

## 1. Problem

The insurance data market is a mess. Every carrier is rebuilding the same policy /
claim / party model from scratch, in private, welded to whichever platform they
bought, and exchanging data with counterparties through bordereaux spreadsheets and
point-to-point middleware. Governance programmes start from the toolset ("which
catalog do we buy?") instead of the function ("what do we mean by *incurred*, and who
owns that definition?"). The result: no two units of the same group agree on terms,
and cross-company exchange loses all metadata at the boundary.

## 2. What we are building

A **canonical, open, business-first semantic model for insurance** with three
load-bearing ideas:

1. **Model-as-code.** Every entity and code set is a YAML spec: name, definition,
   grain, attributes with definitions, data classification, keys, relationships,
   quality rules, and standards crosswalk (ACORD + Lloyd's CDR). A generator emits
   all downstream artifacts from these specs.
2. **Platform bindings.** The logical model is platform-neutral. A binding maps
   logical domains to physical containers per platform. Toolset is an output of
   requirements, not the starting point.
3. **Semantics that travel.** Exchange between parties uses open sharing (Delta
   Sharing, open table formats), and every share carries a generated
   `data_dictionary` table — the receiving party gets definitions, classifications
   and standards references alongside the rows.

## 3. Architecture

### 3.1 Layers

```
┌────────────────────────────────────────────────────────────┐
│  model/  — YAML specs (entities, code sets, manifest)      │  ← governed by business
├────────────────────────────────────────────────────────────┤
│  tools/generate.py — the compiler                          │
├─────────────────────┬────────────────────┬─────────────────┤
│  build/databricks/  │  build/snowflake/  │  build/docs +   │  ← generated, never
│  DDL, PK/FK, tags,  │  DDL, comments,    │  build/genie    │    hand-edited
│  comments, seeds    │  seeds             │                 │
└─────────────────────┴────────────────────┴─────────────────┘
```

### 3.2 Domains → schemas

| Domain        | Contents                                                        |
|---------------|-----------------------------------------------------------------|
| `reference`   | Code sets (LOB, status, currency, cause of loss…) + the generated `data_dictionary` |
| `party`       | Persons, organisations, and the **roles** they play (insured, broker, cedant, reinsurer, claimant) |
| `policy`      | Policy contracts, coverages, insured objects, premium transactions |
| `claim`       | Claims, claim transactions (reserves, payments, recoveries)     |
| `reinsurance` | Treaties, cessions, recoveries                                  |
| `exchange`    | Canonical exchange objects (bordereau lines, submission messages) and inbound landing |
| `semantics`   | Metric views (GWP, NEP, incurred, loss ratio, combined ratio) — Databricks binding only |

**The party–role pattern is the number-one extensibility lever.** A party exists
once; every business relationship (insured, broker, cedant, claimant, coverholder…)
is a role row, not a new table. Adding a new kind of counterparty later costs one
code-set row.

### 3.3 Physical bindings

- **Databricks (primary demo):** workspace `fevm-lr-serverless-aws-us`, single fixed
  catalog `lr_serverless_aws_us_catalog` (cannot be renamed on this workspace), so
  domains map to schemas named `bricksurance_<domain>`. Adopters with their own
  metastore would typically use a dedicated `bricksurance` catalog with plain domain
  schemas — that is a one-line binding change, which is exactly the point.
- **Snowflake (federation example):** database `BRICKSURANCE`, schema per domain.
  Comments generated; PK/FK generated (informational in Snowflake, as they are in
  Unity Catalog).
- Other platforms (BigQuery for a group-centre topology) follow the same pattern:
  add a binding + a type map. The specs do not change.

### 3.4 Semantics on Databricks

The Databricks binding is the richest, because Unity Catalog can carry the whole
semantic layer natively:

- **Definitions** → table and column `COMMENT`s, generated from spec descriptions.
- **Relationships** → informational `PRIMARY KEY` / `FOREIGN KEY` constraints
  (Genie and BI tools use these for join inference).
- **Governance** → tags: `model`, `model_version`, `domain`, `acord_ref`,
  `maturity`, and per-column `data_classification` (public / internal /
  confidential / pii).
- **Metrics** → metric views in the `semantics` domain (phase 2).
- **Acceptance test** → a Genie space wired to the model. The working definition of
  "the semantic layer is done" is: *Genie answers actuarial questions correctly with
  no hand-holding.* The generator emits the Genie instruction text from the specs.

## 4. Federated topology

The reference scenario is deliberately heterogeneous — the shape most groups end
up with after a few acquisitions:

```
            Group centre (GCP / BigQuery)          ← group model, consolidated views
                 ▲ reads via open formats
   ┌─────────────┴──────────────┐
   │                            │
Retail units (Databricks)   Specialty unit (Snowflake)
bricksurance_* schemas      BRICKSURANCE database
   │                            ▲
   └── exchange ────────────────┘
       open table formats / Delta Sharing / federation
```

Interop mechanisms, in order of preference:

1. **Same model everywhere.** Each unit deploys its platform's generated binding.
   The *contract* between units is the spec version, not an interface document.
2. **Open table formats.** Unity Catalog tables exposed as Iceberg (UniForm /
   Iceberg REST catalog) are readable from Snowflake and BigQuery without copies.
3. **Delta Sharing.** Databricks-to-Databricks shares for insurer ↔ reinsurer
   (live, governed, revocable); the open sharing protocol for brokers and
   non-Databricks recipients.
4. **Lakehouse Federation** for read-back: Databricks querying the Snowflake unit's
   conformed tables during transition or for group reporting.

We do not overbuild this: the demo shows **one example of each** — a Snowflake trial
account acting as "Bricksurance Specialty" running the generated Snowflake DDL,
one cross-platform read, and one bordereau exchanged with full dictionary.

## 5. Data exchange — killing the bordereau

A bordereau today is an Excel file emailed monthly, schema unknown, definitions
absent. In this model an exchange is:

1. A **canonical exchange entity** (e.g. `premium_bordereau_line`) defined in
   `model/exchange/` like any other entity — with ACORD/CDR crosswalk.
2. Shared as a **table** (Delta Share or open format), not a file.
3. Accompanied by the **`data_dictionary` table** generated from the same specs —
   entity, attribute, definition, classification, standards references, model
   version. The receiver can validate the payload against the dictionary
   mechanically. Tags don't cross platform boundaries; the dictionary table does.
4. Inbound messy data (a coverholder's spreadsheet) lands in `exchange` and is
   mapped to canonical entities — the demo shows an LLM-assisted mapping using the
   dictionary as context, which is the "no middleware" punchline.

## 6. Spec format

See [`model/policy/policy.yaml`](../model/policy/policy.yaml) for the exemplar. Key
fields:

| Field | Purpose |
|---|---|
| `kind` | `entity` or `code_set` |
| `name` / `domain` / `title` | Identity and placement |
| `description` | The business definition — this becomes the table comment, the docs, and the LLM context |
| `grain` | One-sentence statement of what one row means (non-negotiable) |
| `standards` | Crosswalk: `acord`, `lloyds_cdr` (extensible to other standards) |
| `attributes[]` | `name`, `type` (logical: string/integer/decimal(p,s)/date/timestamp/boolean), `required`, `description`, `classification`, optional `code_set` reference, per-attribute `standards` |
| `keys` | `primary` (generated as PK constraint) and `natural` |
| `quality[]` | Named business rules (generated into docs now; DQ expectations later) |

An attribute with `code_set: x` automatically gets a foreign key to
`reference.x (x_code)`. Code sets carry their allowed values in the spec, and the
generator emits the seed rows — reference data is versioned with the model.

## 7. Roadmap

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Repo, spec format, generator, Policy exemplar + code sets, Databricks & Snowflake bindings | done |
| 1 | Full core P&C slice (party/party_role, coverage, insured object, premium & claim transactions, treaty & cession) deployed to Unity Catalog with synthetic data | done |
| 2 | Semantic layer proven: metric view, Genie space, acceptance test passed | done |
| 3 | Exchange: D2D Delta Share to `fevm-lr-dev-aws-us` (Bricksurance Re), bordereau ingest demo (messy file → canonical, dictionary-assisted) | |
| 4 | Federation example: Snowflake trial as the "Bricksurance Specialty" unit — generated DDL deployed, one cross-platform read, one cross-platform exchange | |
| 5 | Adoption proof: retrofit one existing Bricksurance demo as a consumer via views | |
| 6 | Extension proof: life domain (LifeCast) and full reinsurance domain added with zero rework to existing entities | |

## 8. Conventions

- Logical names: `snake_case`, singular entities (`policy`, not `policies`).
- Code columns: `<code_set>_code`; code values: `UPPER_SNAKE`, never overloaded —
  deprecate and add, don't repurpose.
- Every entity carries `source_system_code`: provenance is part of the model.
- Definitions are written for a business reader; if a definition needs the source
  system to make sense, it is not done.
- `build/` is generated output. Never hand-edit; change the spec and regenerate.
