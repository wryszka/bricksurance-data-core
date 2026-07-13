#!/usr/bin/env python3
"""Plan a schema migration between two ontology versions. NEVER applies anything.

Diffs two ontology JSON exports (they are complete and deterministic, so the
diff is exact), classifies every change PATCH / MINOR / MAJOR per
docs/EVOLUTION.md, checks the version bump matches the classification, and
emits a reviewable migration script: automatic statements for additive change,
`-- MANUAL:` blocks for anything breaking. The script also maintains a
`schema_migration` log table so every environment can state which model
version its physical schema is at.

Pre-1.0 rule (semver convention): while the major version is 0, breaking
changes require only a MINOR bump; from 1.0.0 they require MAJOR.

Usage:
    uv run --with pyyaml tools/plan_migration.py OLD.ontology.json NEW.ontology.json \
        [--binding bindings/databricks.yaml] [--out build/migrations]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate  # noqa: E402  (entity_ddl, entity_fk_ddl, view_ddl, metric_view_ddl, fqn, esc, sql_type, code_set_as_entity)

ROOT = Path(__file__).resolve().parents[1]
LEVELS = {"PATCH": 0, "MINOR": 1, "MAJOR": 2}


def index(doc):
    return {kind: {s["name"]: s for s in doc.get(kind, [])}
            for kind in ("entities", "code_sets", "views", "metric_views", "functions")}


def attr_map(entity):
    return {a["name"]: a for a in entity.get("attributes", [])}


class Plan:
    def __init__(self):
        self.changes = []          # dicts: level, note, sql (list) | manual (str)

    def add(self, level, note, sql=None, manual=None):
        self.changes.append({"level": level, "note": note,
                             "sql": sql or [], "manual": manual})

    @property
    def required_level(self):
        return max((c["level"] for c in self.changes), key=LEVELS.get, default=None)


def diff_entities(plan, binding, manifest, old, new, new_entity_index):
    for name in sorted(set(new) - set(old)):
        plan.add("MINOR", f"new entity {name}",
                 sql=[generate.entity_ddl(binding, manifest, new[name])]
                     + generate.entity_fk_ddl(binding, new[name], new_entity_index))
    for name in sorted(set(old) - set(new)):
        plan.add("MAJOR", f"entity {name} removed",
                 manual=f"DROP TABLE {generate.fqn(binding, old[name]['domain'], name)} "
                        f"after consumers are migrated and data is archived.")
    for name in sorted(set(old) & set(new)):
        o, n = old[name], new[name]
        table = generate.fqn(binding, n["domain"], name)
        oa, na = attr_map(o), attr_map(n)
        for col in sorted(set(na) - set(oa)):
            a = na[col]
            sql = [f"ALTER TABLE {table} ADD COLUMN {col} "
                   f"{generate.sql_type(binding['platform'], a.get('type', 'string'))} "
                   f"COMMENT '{generate.esc(a['description'])}';"]
            if a.get("required"):
                plan.add("MAJOR", f"{name}.{col} added as REQUIRED", sql=sql,
                         manual=f"Backfill {table}.{col}, then SET NOT NULL. "
                                "New required attributes should normally arrive optional first.")
            else:
                plan.add("MINOR", f"{name}.{col} added", sql=sql)
        for col in sorted(set(oa) - set(na)):
            plan.add("MAJOR", f"{name}.{col} removed",
                     manual=f"Deprecate {table}.{col} (view alias during a deprecation "
                            f"window), migrate consumers, then DROP COLUMN.")
        for col in sorted(set(oa) & set(na)):
            a_old, a_new = oa[col], na[col]
            if a_old.get("type", "string") != a_new.get("type", "string"):
                plan.add("MAJOR", f"{name}.{col} type {a_old.get('type')} -> {a_new.get('type')}",
                         manual=f"Add a new column with the new type, backfill, swap via view alias.")
            if bool(a_old.get("required")) != bool(a_new.get("required")):
                if a_new.get("required"):
                    plan.add("MAJOR", f"{name}.{col} became required",
                             manual=f"Backfill NULLs in {table}.{col}, then "
                                    f"ALTER COLUMN {col} SET NOT NULL.")
                else:
                    plan.add("MINOR", f"{name}.{col} became optional",
                             sql=[f"ALTER TABLE {table} ALTER COLUMN {col} DROP NOT NULL;"])
            if (a_old.get("code_set"), a_old.get("references")) != \
               (a_new.get("code_set"), a_new.get("references")):
                plan.add("MAJOR", f"{name}.{col} relationship retargeted",
                         manual=f"Review FK fk_{name}_{col}: drop and re-add against the new "
                                f"target after validating the data.")
            if " ".join(str(a_old["description"]).split()) != " ".join(str(a_new["description"]).split()):
                plan.add("PATCH", f"{name}.{col} definition updated",
                         sql=[f"ALTER TABLE {table} ALTER COLUMN {col} "
                              f"COMMENT '{generate.esc(a_new['description'])}';"])
        if " ".join(str(o.get("grain", ""))).split() != " ".join(str(n.get("grain", ""))).split() \
                and str(o.get("grain")) != str(n.get("grain")):
            plan.add("MAJOR", f"{name} grain changed",
                     manual="Grain is sacred: a changed row meaning is a new entity. "
                            "Review whether this is wording only; if so re-classify PATCH.")
        elif " ".join(str(o["description"]).split()) != " ".join(str(n["description"]).split()):
            plan.add("PATCH", f"{name} description updated",
                     sql=[f"COMMENT ON TABLE {table} IS "
                          f"'{generate.esc(n['description'])} Grain: {generate.esc(n['grain'])}';"])


def diff_code_sets(plan, binding, manifest, old, new, new_entity_index):
    for name in sorted(set(new) - set(old)):
        cs_entity = generate.code_set_as_entity(new[name])
        plan.add("MINOR", f"new code set {name}",
                 sql=[generate.entity_ddl(binding, manifest, cs_entity),
                      generate.code_set_seed(binding, new[name])])
    for name in sorted(set(old) - set(new)):
        plan.add("MAJOR", f"code set {name} removed",
                 manual=f"Code sets are referenced by FKs — deprecate, never drop hot.")
    for name in sorted(set(old) & set(new)):
        o_codes = {c["code"]: c for c in old[name]["codes"]}
        n_codes = {c["code"]: c for c in new[name]["codes"]}
        if set(n_codes) - set(o_codes):
            plan.add("MINOR", f"code set {name}: codes added {sorted(set(n_codes) - set(o_codes))}",
                     sql=[generate.code_set_seed(binding, new[name])])
        if set(o_codes) - set(n_codes):
            plan.add("MAJOR", f"code set {name}: codes removed {sorted(set(o_codes) - set(n_codes))}",
                     manual="Codes are never removed while referenced — deprecate in the "
                            "description and stop issuing; remove only after data migration.")
        elif any(o_codes[c] != n_codes[c] for c in set(o_codes) & set(n_codes)):
            plan.add("PATCH", f"code set {name}: labels/definitions updated",
                     sql=[generate.code_set_seed(binding, new[name])])


def diff_semantics(plan, binding, old, new, kind, ddl):
    for name in sorted(set(new) - set(old)):
        plan.add("MINOR", f"new {kind} {name}", sql=[ddl(binding, new[name])])
    for name in sorted(set(old) - set(new)):
        plan.add("MAJOR", f"{kind} {name} removed",
                 manual=f"DROP VIEW {generate.fqn(binding, old[name]['domain'], name)} "
                        "after consumers are migrated.")
    for name in sorted(set(old) & set(new)):
        if old[name] != new[name]:
            plan.add("MINOR", f"{kind} {name} redefined (views are stateless)",
                     sql=[ddl(binding, new[name])])


def required_bump(old_version, new_version, level):
    o = [int(x) for x in old_version.split(".")]
    n = [int(x) for x in new_version.split(".")]
    if level is None:
        return o == n or n > o, "no changes"
    pre_1 = o[0] == 0
    if level == "MAJOR" and not pre_1:
        return n[0] > o[0], "MAJOR (X.0.0)"
    if level == "MAJOR" and pre_1:
        return n[:2] > o[:2], "MINOR (pre-1.0 rule: 0.X may break on minor)"
    if level == "MINOR":
        return n[:2] > o[:2], "MINOR (x.Y.0)"
    return n > o, "PATCH (x.y.Z)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--binding", default=str(ROOT / "bindings" / "databricks.yaml"))
    ap.add_argument("--out", default=str(ROOT / "build" / "migrations"))
    args = ap.parse_args()

    old_doc = json.loads(Path(args.old).read_text())
    new_doc = json.loads(Path(args.new).read_text())
    binding = yaml.safe_load(Path(args.binding).read_text())
    manifest = {"model": new_doc["name"], "title": new_doc["title"],
                "version": new_doc["version"], "description": new_doc["description"],
                "domains": new_doc["domains"]}

    o_idx, n_idx = index(old_doc), index(new_doc)
    new_entity_index = {e["name"]: e for e in new_doc["entities"]}
    new_entity_index.update({cs["name"]: generate.code_set_as_entity(cs)
                             for cs in new_doc["code_sets"]})

    plan = Plan()
    for d in [d["name"] for d in new_doc["domains"]] :
        if d not in [x["name"] for x in old_doc["domains"]]:
            container = binding.get("catalog") or binding.get("database")
            plan.add("MINOR", f"new domain {d}",
                     sql=[f"CREATE SCHEMA IF NOT EXISTS {container}."
                          f"{binding['schema_pattern'].format(domain=d)};"])
    diff_entities(plan, binding, manifest, o_idx["entities"], n_idx["entities"], new_entity_index)
    diff_code_sets(plan, binding, manifest, o_idx["code_sets"], n_idx["code_sets"], new_entity_index)
    diff_semantics(plan, binding, o_idx["views"], n_idx["views"], "view", generate.view_ddl)
    diff_semantics(plan, binding, o_idx["metric_views"], n_idx["metric_views"],
                   "metric view", generate.metric_view_ddl)
    diff_semantics(plan, binding, o_idx["functions"], n_idx["functions"],
                   "function", generate.function_ddl)

    level = plan.required_level
    ok, needed = required_bump(old_doc["version"], new_doc["version"], level)
    print(f"{old_doc['version']} -> {new_doc['version']}: {len(plan.changes)} changes, "
          f"classification {level or 'NONE'} (bump needed: {needed})")
    for c in plan.changes:
        print(f"  [{c['level']}] {c['note']}" + ("  ** MANUAL **" if c["manual"] else ""))

    if not plan.changes:
        print("Nothing to migrate.")
        return
    if not ok:
        sys.exit(f"VERSION BUMP INSUFFICIENT: changes require a {needed} bump.")

    # emit the reviewable script — never applied by this tool
    container = binding.get("catalog") or binding.get("database")
    log_table = generate.fqn(binding, "reference", "schema_migration")
    lines = [f"-- Migration plan {old_doc['version']} -> {new_doc['version']} "
             f"({binding['platform']}). REVIEW BEFORE APPLYING — never auto-applied.",
             f"-- Generated by tools/plan_migration.py; classification {level}.", "",
             f"CREATE TABLE IF NOT EXISTS {log_table} (",
             "  from_version STRING NOT NULL COMMENT 'Model version the schema was at',",
             "  to_version STRING NOT NULL COMMENT 'Model version after this migration',",
             "  classification STRING NOT NULL COMMENT 'PATCH, MINOR or MAJOR',",
             "  script_hash STRING NOT NULL COMMENT 'sha256 of the applied script',",
             "  applied_at TIMESTAMP NOT NULL COMMENT 'When the migration was applied',",
             "  applied_by STRING COMMENT 'Who applied it'",
             ") COMMENT 'Applied model migrations - the physical twin of the data "
             "dictionary''s model_version.';", ""]
    for c in plan.changes:
        lines.append(f"-- [{c['level']}] {c['note']}")
        if c["manual"]:
            lines.append(f"-- MANUAL: {c['manual']}")
        lines.extend(c["sql"])
        lines.append("")
    body = "\n".join(lines)
    digest = hashlib.sha256(body.encode()).hexdigest()
    lines += [f"INSERT INTO {log_table} VALUES ("
              f"'{old_doc['version']}', '{new_doc['version']}', '{level}', "
              f"'{digest}', current_timestamp(), current_user());", ""]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{old_doc['version']}__{new_doc['version']}.{binding['platform']}.sql"
    path.write_text("\n".join(lines))
    print(f"\nMigration script written to {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    print("Review it, apply it deliberately, and keep the log row it inserts.")


if __name__ == "__main__":
    main()
