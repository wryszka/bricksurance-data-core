#!/usr/bin/env python3
"""advance_period — the estate's first closed loop (WP5).

Rolls the book forward one renewal cycle: for every renewing policy it applies a
price walk, draws the renewal outcome from the retention response curve, and
produces the next cycle's renewal cases. A decision (the price walk) changes next
period's synthetic behaviour — retention responds to price, deterministically.

Determinism is the contract: given the same seed and the same decisions, running
this twice produces byte-identical output. That is what makes the loop safe to
demo and safe to reset.

This tool operates on the generated world model (the source of truth for the
synthetic estate). It reuses world_engine's curve and outcome draw so the loop is
consistent with the seeded world. The live-workspace form — appending RENEWED /
LAPSED events onto the hash-chained spine and re-materialising versions — is the
runtime job a workbench app wires to a button; it is intentionally not performed
here (the data-core layer stays declarative and rebuildable).

Usage:
    uv run --with pyyaml tools/advance_period.py [--walk 0.08] [--check-determinism]
"""
import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_world_engine():
    spec = importlib.util.spec_from_file_location("we", ROOT / "tools" / "world_engine.py")
    we = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(we)
    return we


def advance(we, default_walk):
    """Compute the next cycle's renewal cases from the current in-force book.

    default_walk is the pricing decision applied where a policy has no explicit
    renewal price yet. Outcomes are drawn from RETENTION_CURVE, deterministically.
    Returns a list of (policy_id, walk, band, outcome) tuples, sorted for stability.
    """
    w = we.build_world(1.0)
    prem = {pt["policy_id"]: float(pt.get("amount") or 0)
            for pt in w.t["premium_transaction"]
            if pt.get("premium_transaction_type_code") == "WRITTEN"}
    in_force = [p for p in w.t["policy"] if p["policy_status_code"] == "IN_FORCE"]
    out = []
    for p in sorted(in_force, key=lambda x: x["policy_id"]):
        pid = p["policy_id"]
        if not prem.get(pid):
            continue
        try:
            pnum = int(pid.split("_")[-1])
        except ValueError:
            pnum = 0
        walk = default_walk
        band = we._walk_band(walk)
        curve = we.RETENTION_CURVE.get(p["line_of_business_code"], we.RETENTION_CURVE["MOTOR"])
        prob = curve[band]
        u = ((pnum * 2654435761) % 1000) / 1000.0
        outcome = "RENEWED" if u < prob else ("LAPSED_PRICE" if walk >= 0.10 else "LAPSED_OTHER")
        out.append((pid, walk, band, outcome))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--walk", type=float, default=0.08,
                    help="Renewal price walk to apply this cycle (the decision).")
    ap.add_argument("--check-determinism", action="store_true",
                    help="Run twice and assert byte-identical output.")
    args = ap.parse_args()
    we = _load_world_engine()

    result = advance(we, args.walk)
    renewed = sum(1 for _, _, _, o in result if o == "RENEWED")
    lapsed = len(result) - renewed
    print(f"advance_period: walk={args.walk:.2%} over {len(result)} in-force policies "
          f"-> {renewed} renewed, {lapsed} lapsed "
          f"(retention {renewed / max(len(result),1):.1%})")

    if args.check_determinism:
        again = advance(we, args.walk)
        assert result == again, "NON-DETERMINISTIC: advance_period produced different output"
        print("determinism check: PASS (two runs byte-identical)")

    # show the price sensitivity: retention falls as the walk rises
    print("price sensitivity (retention by walk):")
    for wlk in (0.03, 0.08, 0.15, 0.25):
        r = advance(we, wlk)
        rr = sum(1 for _, _, _, o in r if o == "RENEWED") / max(len(r), 1)
        print(f"  walk {wlk:5.0%} -> retention {rr:5.1%}")


if __name__ == "__main__":
    main()
