#!/usr/bin/env python3
"""The action layer, live: an LLM agent using the model's governed tools.

Loads every `kind: function` spec from the model, presents them to Claude
(Foundation Model API) as tools, and runs a tool-use loop — each call executed
as `SELECT function(args)` on the warehouse. The ontology declares what agents
may do; this script is just the loop.

Usage:
    uv run --with databricks-sdk,pyyaml tools/agent_demo.py \
        [--ask "..."] [--profile DEFAULT] [--endpoint databricks-claude-sonnet-5]
"""

import argparse
import json
import sys
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy_databricks import pick_warehouse  # noqa: E402
from smoke_test import run_sql  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
JSON_TYPE = {"string": "string", "integer": "integer", "boolean": "boolean",
             "date": "string", "timestamp": "string"}

DEFAULT_ASK = (
    "You are speaking to Bricksurance's underwriting service. I am Athena "
    "Procurement Agent v2, acting for Kestrel Foods Group. We need commercial "
    "property cover in Great Britain for a warehouse with a sum insured of "
    "GBP 8,000,000. Is this within your appetite, and what would the "
    "indicative premium be on your standard product (CP-STD)? Separately, "
    "please confirm the current outstanding reserve and status on claim "
    "CLM-2026-000001, and what 'outstanding_reserve' means in your model.")


def load_functions():
    fns = {}
    for path in sorted((ROOT / "model").rglob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        if spec.get("kind") == "function":
            fns[spec["name"]] = spec
    return fns


def to_tool(fn):
    props, required = {}, []
    for p in fn["inputs"]:
        t = str(p["type"]).lower()
        props[p["name"]] = {
            "type": "number" if t.startswith("decimal") else JSON_TYPE.get(t, "string"),
            "description": p["description"]}
        required.append(p["name"])
    return {"type": "function",
            "function": {"name": fn["name"],
                         "description": f"{fn['description']} Returns: {fn['returns']['description']}",
                         "parameters": {"type": "object", "properties": props,
                                        "required": required}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask", default=DEFAULT_ASK)
    ap.add_argument("--profile", default="DEFAULT")
    ap.add_argument("--warehouse-id")
    ap.add_argument("--endpoint", default="databricks-claude-sonnet-5")
    args = ap.parse_args()

    binding = yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())

    def fqn(domain, name):
        return f"{binding['catalog']}.{binding['schema_pattern'].format(domain=domain)}.{name}"

    w = WorkspaceClient(profile=args.profile)
    wid = args.warehouse_id or pick_warehouse(w).id
    fns = load_functions()
    tools = [to_tool(f) for f in fns.values()]
    print(f"Governed tools from the model: {', '.join(fns)}\n")

    messages = [
        {"role": "system", "content":
            "You are the Bricksurance underwriting and service agent. Answer using "
            "ONLY the governed tools; never invent figures. State appetite effects, "
            "premiums and reserves exactly as the tools return them. Be concise and "
            "businesslike; you are talking to another machine agent."},
        {"role": "user", "content": args.ask}]

    for _ in range(6):
        resp = w.api_client.do(
            "POST", f"/serving-endpoints/{args.endpoint}/invocations",
            body={"messages": messages, "tools": tools, "max_tokens": 2000})
        msg = resp["choices"][0]["message"]
        calls = msg.get("tool_calls") or []
        content = msg.get("content")
        if isinstance(content, list):
            content = "".join(b.get("text", "") for b in content if b.get("type") == "text")
        messages.append({"role": "assistant", "content": content or "",
                         "tool_calls": calls if calls else None})
        if not calls:
            print(f"\n=== AGENT RESPONSE ===\n{content}")
            return
        for call in calls:
            name = call["function"]["name"]
            fn_args = json.loads(call["function"]["arguments"] or "{}")
            spec = fns[name]
            lits = []
            for p in spec["inputs"]:
                v = fn_args.get(p["name"])
                if v is None:
                    lits.append("NULL")
                elif str(p["type"]).lower().startswith("decimal"):
                    lits.append(str(float(v)))
                else:
                    lits.append("'" + str(v).replace("'", "''") + "'")
            sql = f"SELECT {fqn(spec['domain'], name)}({', '.join(lits)})"
            rows = run_sql(w, wid, sql)
            result = str(rows[0][0]) if rows and rows[0] else "NULL"
            print(f"tool  {name}({fn_args}) -> {result}")
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": result})
    sys.exit("Agent did not converge within the tool-call budget.")


if __name__ == "__main__":
    main()
