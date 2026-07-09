# Bricksurance Data Core — What it is, who it's for, what it resolves

## The point, in one paragraph

**The goal is to make insurance data and context available to LLM agents — and
to prove how much better everything gets when you do.** Genie answering
actuarial questions unaided, agents mapping a coverholder's messy bordereau
against a governed contract, a reinsurer's analyst querying a share whose
meaning travelled with it: none of that works on tables alone. It works on
*semantics* — definitions, relationships, code meanings, metric definitions —
captured once, governed by the business, and compiled onto the platform. This
project is that semantic layer, built as a working system rather than a
slideware target architecture. The by-product is deliberately bigger: an
**open, ACORD-aligned insurance ontology** anyone can learn from, add to, or
adopt as their base — with a live Databricks implementation and a working
demonstration of two entities exchanging data because they share the standard.

## What it is

- An **insurance ontology**: entities, definitions, grains, code sets,
  relationships and metric definitions for P&C (commercial + motor), life,
  reinsurance and finance — expressed as versioned, human-readable YAML specs
  and exported as one portable JSON document.
- A **compiler** that generates everything downstream from those specs:
  Unity Catalog DDL with column-level definitions, PK/FK relationships,
  governance tags, metric views, the machine-readable data dictionary, Genie
  space context, ERDs, docs — and Snowflake DDL from the same specs, because
  federated estates are the normal case.
- A **live implementation**: a coherent synthetic world across all domains,
  three specialized Genie spaces that pass actuarial acceptance tests, a
  Databricks App (the Data Core Console), an LLM-driven bordereau ingest, and
  a data-exchange pattern where the dictionary travels with every share.
- A **change discipline**: semver on the ontology, a migration planner that
  diffs versions and refuses silent breaking change, and a migration log.

## Who it is for

| Audience | What you get on day one |
|---|---|
| **CDO / head of data governance** (primary) | A concrete, working answer to "where do we even start with an insurance semantic layer" — a base to adopt, a structure to critique, a tagging and metrics strategy to compare against yours. The governance argument is embodied, not asserted: business definitions are the source files; the catalog cannot drift from the documentation because they are compiled from the same specs. |
| **Chief actuary / business data owners** | Your vocabulary, governed: one definition of *incurred*, *outstanding*, *BEL* — owned in business terms, enforced everywhere, queryable in plain English through Genie. Money is transactional (derived, never overwritten); valuation runs are reproducible recipes. |
| **Platform / data engineering** | A model-as-code reference implementation: spec format, generator, bindings, deploy/smoke/migration tooling — all open source, all runnable in ~30 minutes ([GETTING_STARTED.md](GETTING_STARTED.md)). |
| **The market** | A proposed starting point for a shared insurance ontology — ACORD-aligned terminology, Lloyd's CDR crosswalk, importable as one JSON file — so that two companies who adopt it can exchange data without middleware, mapping projects, or meaning lost at the boundary. |

## What it resolves

1. **"Our LLM pilots disappoint."** LLMs are only as good as the context they
   are given. The dictionary, relationships, code vocabularies and metric
   definitions here are exactly that context — and the difference is
   demonstrable ([DEMOS.md](DEMOS.md)): the same question against bare tables
   fails; against this layer it returns the reconciling number.
2. **"Every unit defines *incurred* differently."** Metric views define each
   measure once, with ownership and honest caveats ([METRICS.md](METRICS.md)).
3. **"Governance programmes start with tooling debates."** Here the business
   layer comes first and the toolset is generated from it — the argument your
   governance programme has been trying to win, working.
4. **"Exchange means bordereaux spreadsheets and mapping projects."** Shares
   carry their own data dictionary; inbound mess is mapped by an LLM against
   the dictionary as a contract, validated before a single row lands.
5. **"We'd have to boil the ocean."** The ontology imports in one file, the
   estate deploys in minutes, and the adoption path is deliberately
   incremental ([ADOPTION_PATH.md](ADOPTION_PATH.md)) — start with the
   dictionary and one domain, not a two-year re-platforming.

## What it is based on

ACORD terminology (cited as a crosswalk — the licensed models are not
reproduced), the Lloyd's Core Data Record for London-market attributes, and
proven structural patterns: party–role, agreement/coverage, transactional
money, typed satellites, measure codes across regulatory regimes. European /
UK-first in its examples (Solvency II, IFRS 17, GDPR-aware classifications),
portable everywhere.

## The picture

Four diagrams in [`docs/diagrams/`](diagrams/) (mermaid sources alongside):
the **estate map** (one company, workbenches and LLM agents around one core),
the **compile pipeline** (specs → generator → everything), the **exchange
flow** (killing the bordereau, both directions) and the **domain map** (the
ontology at a glance).

## Where everything lives

Repo: [github.com/wryszka/bricksurance-data-core](https://github.com/wryszka/bricksurance-data-core) ·
assets and services: [ASSETS.md](ASSETS.md) · demos: [DEMOS.md](DEMOS.md) ·
start here: [GETTING_STARTED.md](GETTING_STARTED.md) · moving off legacy:
[ADOPTION_PATH.md](ADOPTION_PATH.md) · tagging: [TAGGING.md](TAGGING.md) ·
metrics: [METRICS.md](METRICS.md) · change: [EVOLUTION.md](EVOLUTION.md) ·
architecture: [DESIGN.md](DESIGN.md).

*Bricksurance SE is a fictional insurance group; all data is synthetic. The
model is designed to be genuinely reusable.*
