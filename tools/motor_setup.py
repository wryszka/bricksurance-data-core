"""Motor chapter: create the two Genie agents, publish the metric view, reset before a room.

Usage:
  uv run --system-certs --with databricks-sdk --with fastapi --with pyyaml --with requests \
      python tools/motor_setup.py --create-spaces      # once; prints ids -> app.yaml / env
  ... python tools/motor_setup.py --publish           # metric view + governed agent from the approved rulebook
  ... python tools/motor_setup.py --acceptance        # ask the governed agent the benchmark questions

Set MOTOR_RAW_SPACE / MOTOR_GOVERNED_SPACE in the environment (or app.yaml) after --create-spaces.
Ownership note: whoever runs --publish owns semantics.motor_performance_metrics. The
deployed app republishes it on every rulebook approval, so the LAST publish before a
room must come from the app (POST /api/motor/reset or the Reset button), not from here.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="fevm-lr-serverless-aws-us")
    ap.add_argument("--create-spaces", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--acceptance", action="store_true")
    a = ap.parse_args()
    os.environ["DATABRICKS_CONFIG_PROFILE"] = a.profile
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
    from backend import motor, one_number as on  # shared with the app

    w = WorkspaceClient(profile=a.profile)
    if a.create_spaces:
        d = on.approved()
        for name, payload in (("raw", motor.raw_space_payload()), ("governed", motor.governed_space_payload(d))):
            payload["parent_path"] = "/Workspace/Shared/bricksurance-data-core"
            sid = w.api_client.do("POST", "/api/2.0/genie/spaces", body=payload)["space_id"]
            print(f"MOTOR_{name.upper()}_SPACE={sid}")
        return
    if a.publish:
        d = motor.publish()
        print(json.dumps({"published_version": d["version"], "headline": motor.headline()}, default=str, indent=1))
    if a.acceptance:
        if not motor.GOV_SPACE:
            sys.exit("set MOTOR_GOVERNED_SPACE first")
        seg = {s["code"]: s for s in motor.segments()}
        h = motor.headline()
        print(f"Truth: LR {h['q2']['loss_ratio']:.3%} -> {h['q3']['loss_ratio']:.3%}; "
              + "; ".join(f"{c} {s['q2']['loss_ratio']:.1%}->{s['q3']['loss_ratio']:.1%} share {s['share']:.0%}" for c, s in seg.items()))
        qs = [motor.QUESTION] + [f["question"] for f in motor.FOLLOW_UPS]
        for q in qs:
            r = on.ask_genie(motor.GOV_SPACE, q, timeout=120)
            text = " ".join(r["text"])[:600].replace("\n", " ")
            print(f"\nQ: {q}\n  {r['seconds']}s | rows {len(r['rows'])} | {text}")


if __name__ == "__main__":
    main()
