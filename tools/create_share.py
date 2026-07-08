#!/usr/bin/env python3
"""Create the Bricksurance Re exchange share (Delta Sharing, Databricks-to-Databricks).

Shares the outbound cession bordereau together with the data dictionary and
the code sets it depends on — the standard travels with the data. Idempotent.

Usage:
    uv run --with databricks-sdk,pyyaml tools/create_share.py \
        --recipient-metastore-id aws:REGION:UUID [--profile DEFAULT]

On the recipient workspace, mount the share as a catalog:
    databricks providers list                    # find the provider name
    databricks api post /api/2.1/unity-catalog/catalogs --json \
      '{"name": "bricksurance_exchange", "provider_name": "<provider>", "share_name": "bricksurance_re_exchange"}'
"""

import argparse
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError

ROOT = Path(__file__).resolve().parents[1]
SHARE = "bricksurance_re_exchange"
RECIPIENT = "bricksurance-re"

# what travels: the bordereau, plus everything needed to understand it
OBJECTS = [
    ("exchange", "cession_bordereau_line", "VIEW"),
    ("reference", "data_dictionary", "TABLE"),
    ("reference", "line_of_business", "TABLE"),
    ("reference", "currency", "TABLE"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--recipient-metastore-id", required=True,
                    help="Recipient's global metastore id, e.g. aws:us-east-2:UUID")
    args = ap.parse_args()

    binding = yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())

    def fqn(domain, name):
        return f"{binding['catalog']}.{binding['schema_pattern'].format(domain=domain)}.{name}"

    w = WorkspaceClient(profile=args.profile)

    def do(method, path, body=None, ok_if=("already exists", "ALREADY_EXISTS")):
        try:
            return w.api_client.do(method, path, body=body)
        except DatabricksError as e:
            if any(s in str(e) for s in ok_if):
                print(f"  (exists) {path}")
                return None
            raise

    print(f"Share: {SHARE}")
    do("POST", "/api/2.1/unity-catalog/shares",
       {"name": SHARE,
        "comment": "Bricksurance SE -> Bricksurance Re: cession bordereau with its data dictionary. Generated demo data; Bricksurance is fictional."})

    updates = [{"action": "ADD",
                "data_object": {"name": fqn(d, n), "data_object_type": t}}
               for d, n, t in OBJECTS]
    do("PATCH", f"/api/2.1/unity-catalog/shares/{SHARE}", {"updates": updates},
       ok_if=("already exists in this share",))

    print(f"Recipient: {RECIPIENT} ({args.recipient_metastore_id})")
    do("POST", "/api/2.1/unity-catalog/recipients",
       {"name": RECIPIENT, "authentication_type": "DATABRICKS",
        "data_recipient_global_metastore_id": args.recipient_metastore_id,
        "comment": "Bricksurance Re AG (fictional) — the group reinsurer's metastore."})

    do("PATCH", f"/api/2.1/unity-catalog/shares/{SHARE}/permissions",
       {"changes": [{"principal": RECIPIENT, "add": ["SELECT"]}]})

    share = w.api_client.do("GET", f"/api/2.1/unity-catalog/shares/{SHARE}?include_shared_data=true")
    names = [o["name"] for o in share.get("objects", [])]
    print("Shared objects:")
    for n in names:
        print(f"  - {n}")


if __name__ == "__main__":
    main()
