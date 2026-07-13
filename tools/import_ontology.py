#!/usr/bin/env python3
"""Import an ontology JSON document back into model/ YAML specs.

This is how an adopter takes the model on: import the ontology, get a full
model/ tree they own, then generate their own platform artifacts with their
own bindings. Also proves the ontology round-trips: export -> import ->
export must be semantically identical.

Usage:
    # import into a directory (creates <target>/model/...)
    uv run --with pyyaml tools/import_ontology.py \
        --input build/ontology/bricksurance-data-core.ontology.json \
        --target /path/to/new/repo

    # verify round-trip against this repo's model/ (no writes outside /tmp)
    uv run --with pyyaml tools/import_ontology.py \
        --input build/ontology/bricksurance-data-core.ontology.json --verify
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

SUPPORTED_FORMAT = "bricksurance-data-core/ontology-v1"


def dump_yaml(spec, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(
        spec, sort_keys=False, allow_unicode=True, width=88,
        default_flow_style=False))


def import_ontology(doc, model_dir):
    manifest = {
        "model": doc["name"],
        "title": doc["title"],
        "version": doc["version"],
        "description": doc["description"],
        "domains": doc["domains"],
    }
    dump_yaml(manifest, model_dir / "model.yaml")
    for cs in doc.get("code_sets", []):
        dump_yaml(cs, model_dir / "reference" / f"{cs['name']}.yaml")
    for kind in ("entities", "views", "metric_views", "functions"):
        for spec in doc.get(kind, []):
            dump_yaml(spec, model_dir / spec["domain"] / f"{spec['name']}.yaml")


def load_specs(model_dir):
    """Parse a model tree back to comparable python objects."""
    manifest = yaml.safe_load((model_dir / "model.yaml").read_text())
    specs = {}
    for path in sorted(model_dir.rglob("*.yaml")):
        if path.name == "model.yaml":
            continue
        spec = yaml.safe_load(path.read_text())
        specs[(spec["kind"], spec["name"])] = spec
    return manifest, specs


def normalise(obj):
    """Whitespace-normalise every string (YAML folding differences are not
    semantic differences)."""
    if isinstance(obj, dict):
        return {k: normalise(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalise(v) for v in obj]
    if isinstance(obj, str):
        return " ".join(obj.split())
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--target", help="Directory to import into (creates <target>/model)")
    ap.add_argument("--verify", action="store_true",
                    help="Round-trip check against this repo's model/ instead of importing")
    args = ap.parse_args()

    doc = json.loads(Path(args.input).read_text())
    if doc.get("ontology_format") != SUPPORTED_FORMAT:
        sys.exit(f"Unsupported ontology_format: {doc.get('ontology_format')!r} "
                 f"(expected {SUPPORTED_FORMAT})")

    if args.verify:
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = Path(tmp) / "model"
            import_ontology(doc, model_dir)
            got_manifest, got = load_specs(model_dir)
            want_manifest, want = load_specs(ROOT / "model")
            failures = []
            if normalise(got_manifest) != normalise(want_manifest):
                failures.append("manifest differs")
            if set(got) != set(want):
                failures.append(f"spec sets differ: only-imported={sorted(set(got) - set(want))} "
                                f"only-source={sorted(set(want) - set(got))}")
            for key in sorted(set(got) & set(want)):
                if normalise(got[key]) != normalise(want[key]):
                    failures.append(f"{key[0]} {key[1]} differs")
            if failures:
                sys.exit("ROUND-TRIP FAILED:\n  " + "\n  ".join(failures))
            print(f"Round-trip OK: {len(got)} specs + manifest identical after "
                  f"export -> import -> parse (ontology v{doc['version']}).")
        return

    if not args.target:
        sys.exit("Provide --target (or --verify).")
    model_dir = Path(args.target) / "model"
    import_ontology(doc, model_dir)
    n = sum(1 for _ in model_dir.rglob("*.yaml"))
    print(f"Imported ontology v{doc['version']} -> {model_dir} ({n} spec files). "
          f"Next: add bindings/ and run tools/generate.py.")


if __name__ == "__main__":
    main()
