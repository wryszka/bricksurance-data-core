#!/usr/bin/env python3
"""Semantic search over the model's governed documents.

Creates (idempotently) a Vector Search endpoint and a delta-sync index over
content.document(extracted_text) — wordings, slips, evidence — so RAG-style
questions ("which wordings exclude flood?") run under the same governance as
structured queries. Ends with a live similarity query as the smoke check.

Usage:
    uv run --with databricks-sdk,pyyaml tools/create_vector_index.py \
        [--profile DEFAULT] [--query "flood exclusion"]
"""

import argparse
import time
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "bricksurance-vs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--query", default="which wording excludes flood damage?")
    args = ap.parse_args()

    binding = yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())
    src = f"{binding['catalog']}.{binding['schema_pattern'].format(domain='content')}.document"
    index_name = f"{binding['catalog']}.{binding['schema_pattern'].format(domain='content')}.document_index"

    w = WorkspaceClient(profile=args.profile)

    # source table must expose change data feed for delta-sync
    from smoke_test import run_sql
    from deploy_databricks import pick_warehouse
    wid = pick_warehouse(w).id
    run_sql(w, wid, f"ALTER TABLE {src} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

    try:
        w.api_client.do("POST", "/api/2.0/vector-search/endpoints",
                        body={"name": ENDPOINT, "endpoint_type": "STANDARD"})
        print(f"endpoint {ENDPOINT} creating...")
    except DatabricksError as e:
        if "already exists" not in str(e):
            raise
        print(f"endpoint {ENDPOINT} exists")
    for _ in range(60):
        ep = w.api_client.do("GET", f"/api/2.0/vector-search/endpoints/{ENDPOINT}")
        state = ep.get("endpoint_status", {}).get("state")
        if state == "ONLINE":
            break
        time.sleep(20)
    print(f"endpoint state: {state}")

    try:
        w.api_client.do("POST", "/api/2.0/vector-search/indexes", body={
            "name": index_name, "endpoint_name": ENDPOINT,
            "primary_key": "document_id", "index_type": "DELTA_SYNC",
            "delta_sync_index_spec": {
                "source_table": src, "pipeline_type": "TRIGGERED",
                "embedding_source_columns": [{
                    "name": "extracted_text",
                    "embedding_model_endpoint_name": "databricks-gte-large-en"}]}})
        print(f"index {index_name} creating...")
    except DatabricksError as e:
        if "already exists" not in str(e):
            raise
        print(f"index {index_name} exists")
        try:
            w.api_client.do("POST", f"/api/2.0/vector-search/indexes/{index_name}/sync")
            print("sync triggered")
        except DatabricksError as sync_err:
            if "not ready" not in str(sync_err):
                raise
            print("index not ready yet; initial sync runs automatically")

    st = {}
    for _ in range(90):
        idx = w.api_client.do("GET", f"/api/2.0/vector-search/indexes/{index_name}")
        st = idx.get("status", {})
        if st.get("ready"):
            break
        time.sleep(20)
    print(f"index ready: {st.get('ready')} ({st.get('indexed_row_count')} rows)")
    if not st.get("ready"):
        print(f"Index still provisioning ({st.get('detailed_state')}). "
              "Re-run this tool later; creation is idempotent.")
        return

    hits = w.api_client.do("POST", f"/api/2.0/vector-search/indexes/{index_name}/query", body={
        "columns": ["document_id", "title", "document_type_code"],
        "query_text": args.query, "num_results": 3})
    print(f"\nquery: {args.query!r}")
    for row in hits.get("result", {}).get("data_array", []):
        print("  hit:", row)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
