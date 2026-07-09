# Model Evolution — how the ontology changes safely

Change is part of the model's life. This document defines the rules and the
process; the tooling that automates it is a roadmap item (§4) and the process
below works manually today.

## 1. Versioning contract

The ontology version (`model/model.yaml` → every tag, dictionary row and
ontology export) follows semver, judged **from a consumer's point of view**:

| Bump | Meaning | Examples |
|---|---|---|
| **PATCH** | Meaning unchanged | Better definitions, added crosswalk refs, doc fixes |
| **MINOR** | Additive — existing consumers keep working | New entity, new optional attribute, new code value, new metric view, new domain |
| **MAJOR** | Breaking — consumers must adapt | Rename/drop of entity/attribute/code, type change, optional→required, changed grain or measure meaning |

Rules that keep most change MINOR:
- **Never repurpose a code value** — deprecate and add.
- **New attributes arrive optional**; they can be hardened to required in a
  later MAJOR once backfilled.
- **Grain is sacred**: if the meaning of a row changes, that is a new entity,
  not an edit.

## 2. The change process

1. Edit the specs in `model/`; bump the version in `model/model.yaml`.
2. `tools/generate.py` — regenerates DDL, dictionary, docs, Genie context and
   the ontology JSON. The diff of `build/ontology/*.ontology.json` between two
   commits **is** the change record.
3. **Migrate the physical schema** (see §3) — `deploy_databricks.py` alone
   only creates what is missing; it never alters existing tables.
4. Reseed / re-run the World Engine where data shape changed.
5. `tools/smoke_test.py` — expectations derive from the model, so structure
   drift fails loudly.
6. Update Genie spaces (`create_genie_space.py`) so instructions carry the new
   version.

## 3. Physical migration rules (today, manual)

| Change | Migration |
|---|---|
| New entity / code set / view | None — deploy creates it |
| New optional attribute | `ALTER TABLE ... ADD COLUMN ... COMMENT ...` (or drop+recreate if the table is regenerable demo data) |
| New code value | Seed rerun (INSERT OVERWRITE covers it) |
| Changed definition/comment | `ALTER TABLE ... ALTER COLUMN ... COMMENT` (deploy re-runs comments only on create — rerun the COMMENT statements) |
| Rename / retype / drop (MAJOR) | Hand-written migration: new column + backfill + view alias for the old name during a deprecation window |

The demo estate may use **drop + redeploy + reseed** for regenerable tables —
an adopter with real data must not, which is exactly why the tooling below
matters.

## 4. What the tooling will do (roadmap: phase 6.5)

`tools/plan_migration.py <old.ontology.json> <new.ontology.json>`:

1. **Diff the two ontology documents** (they are complete and deterministic,
   so the diff is exact): entities/attributes/code values added, removed,
   retyped, re-required; definition-only changes separated out.
2. **Classify** each change PATCH/MINOR/MAJOR and fail if the version bump
   doesn't match the classification.
3. **Emit a migration script** per binding: `ADD COLUMN`, `COMMENT` updates,
   code-set reseeds — and explicit `-- MANUAL:` blocks for every breaking
   change (backfills and renames are never auto-applied).
4. **Record the application** in a `reference.schema_migration` log table
   (from-version, to-version, applied-at, applied-by, script hash), so any
   environment can state exactly which model version its physical schema is
   at — the deployment-side twin of the data dictionary's `model_version`.

## 5. Worked example (v0.4.0 → v0.5.0)

v0.4.0 shipped `valuation_run.assumption_set_id` (one set per run). A run in
fact uses one set **per assumption type**, so v0.5.0 removes that column and
adds the `valuation_run_assumption` junction. Classification: **MAJOR in
principle** (column drop). Because every affected table was empty, the demo
migration was drop + redeploy; the tooling in §4 would have emitted the same
conclusion with a `-- MANUAL` block, and the migration log would show
0.4.0 → 0.5.0 applied.
