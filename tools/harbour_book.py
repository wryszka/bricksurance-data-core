"""Harbour Mutual: a second insurer's motor extract, in a different system shape.

Proves the mapping mechanism is reusable: Harbour's policy-centre / claim-centre
style tables (PublicID, PolicyNumber, PeriodStart, LossCause, TransactionType...)
are mapped to the same core concepts by two mapping files, and the same executive
question is answered the same way. No targets to hit here - just a plausible
book (loss ratio drifting up Q2 -> Q3 2026) at small scale.

Usage:
  uv run --system-certs --with numpy --with pandas --with pyarrow python tools/harbour_book.py [--out data/harbour]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261107
rng = np.random.default_rng(SEED)
VALUATION = np.datetime64("2026-10-31")
CAUSES = ["vehcollision", "theft", "propertydamage", "bodilyinjury", "glassbreakage", "fire"]
MIX = {"PersonalAuto": [0.47, 0.11, 0.20, 0.09, 0.11, 0.02], "CommercialAuto": [0.40, 0.08, 0.27, 0.13, 0.10, 0.02]}
SEV = {"vehcollision": (2_600, 0.55), "theft": (7_500, 0.6), "propertydamage": (2_700, 0.7),
       "bodilyinjury": (21_000, 1.2), "glassbreakage": (380, 0.3), "fire": (11_000, 0.5)}
FREQ = {"PersonalAuto": 0.12, "CommercialAuto": 0.22}
POSTCODES = ["BS", "BA", "EX", "PL", "TA", "GL", "SN", "SP", "DT", "TR", "CF", "NP"]


def lognormal(mean, sigma, n):
    return rng.lognormal(np.log(mean) - sigma ** 2 / 2, sigma, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/harbour")
    a = ap.parse_args()
    out = Path(a.out)

    # policy periods: 3,200 personal + 800 commercial, annual, inceptions over 18 months
    n_p, n_c = 3_200, 800
    product = np.array(["PersonalAuto"] * n_p + ["CommercialAuto"] * n_c)
    n = len(product)
    start = np.datetime64("2025-04-02") + rng.integers(0, 547, n).astype("timedelta64[D]")
    end = start + np.timedelta64(365, "D")
    prem = np.where(product == "PersonalAuto", lognormal(640, 0.35, n), lognormal(2_400, 0.4, n) * rng.integers(1, 6, n))
    prem = np.where(start >= np.datetime64("2026-07-01"), prem * 1.04, prem).round(2)
    pol = pd.DataFrame({
        "PublicID": [f"pc:{100000 + i}" for i in range(n)],
        "PolicyNumber": [f"HM{7000000 + i}" for i in range(n)],
        "ProductCode": product, "PeriodStart": start, "PeriodEnd": end - np.timedelta64(1, "D"),
        "TotalPremiumRPT": prem, "PrimaryInsuredPostalCode": rng.choice(POSTCODES, n),
        "Status": np.where(end > VALUATION, "Bound", "Expired"), "BaseState": "GB"})
    veh_n = np.where(product == "PersonalAuto", 1, rng.integers(1, 6, n))
    veh = pd.DataFrame({
        "PublicID": [f"pcv:{200000 + i}" for i in range(int(veh_n.sum()))],
        "PolicyPeriodID": np.repeat(pol.PublicID.to_numpy(), veh_n),
        "VIN": ["".join(rng.choice(list("ABCDEFGHJKLMNPRSTUVWXYZ0123456789"), 17)) for _ in range(int(veh_n.sum()))],
        "Make": rng.choice(["Ford", "Vauxhall", "VW", "Toyota", "Mercedes", "Nissan"], int(veh_n.sum())),
        "Model": rng.choice(["Focus", "Corsa", "Golf", "Yaris", "Sprinter", "Transit"], int(veh_n.sum())),
        "Year": rng.integers(2012, 2026, int(veh_n.sum())),
        "CostNew": lognormal(22_000, 0.5, int(veh_n.sum())).round(0)})

    # claims in Q2/Q3 2026 for policies in force
    claims = []
    for q, (qs, qe) in {"Q2": (np.datetime64("2026-04-01"), np.datetime64("2026-07-01")),
                        "Q3": (np.datetime64("2026-07-01"), np.datetime64("2026-10-01"))}.items():
        for prod in ("PersonalAuto", "CommercialAuto"):
            m = (product == prod) & (start < qe) & (end > qs)
            idx = np.flatnonzero(m)
            vy = (veh_n[idx] * 0.25).sum()
            k = int(round(FREQ[prod] * vy * (1.08 if q == "Q3" else 1.0)))
            pick = rng.choice(idx, k, p=veh_n[idx] / veh_n[idx].sum())
            cause = rng.choice(CAUSES, k, p=MIX[prod])
            lo, hi = np.maximum(start[pick], qs), np.minimum(end[pick], qe)
            loss = lo + (rng.random(k) * np.clip((hi - lo).astype(int), 1, None)).astype(int).astype("timedelta64[D]")
            sev = np.array([lognormal(*SEV[c], 1)[0] for c in cause]) * (1.07 if q == "Q3" else 1.0)
            claims.append(pd.DataFrame({"pidx": pick, "LossCause": cause, "LossDate": loss, "gross": sev.round(2), "q": q}))
    c = pd.concat(claims, ignore_index=True)
    c["PublicID"] = [f"cc:{300000 + i}" for i in range(len(c))]
    c["ClaimNumber"] = [f"HMC{900000 + i}" for i in range(len(c))]
    c["PolicyNumber"] = pol.PolicyNumber.to_numpy()[c.pidx]
    c["ReportedDate"] = np.minimum(c.LossDate.to_numpy() + rng.integers(0, 25, len(c)).astype("timedelta64[D]"), VALUATION)
    paid_frac = np.where(c.LossCause == "bodilyinjury", 0.2, 0.8) * np.where(c.q == "Q3", 0.75, 1.0)
    c["paid"] = (c.gross * np.clip(paid_frac * rng.uniform(0.85, 1.1, len(c)), 0, 1)).round(2)
    c["recovery"] = np.where((c.LossCause == "theft") & (rng.random(len(c)) < 0.3), (c.gross * 0.15).round(2), 0.0)
    claim = pd.DataFrame({"PublicID": c.PublicID, "ClaimNumber": c.ClaimNumber, "PolicyNumber": c.PolicyNumber,
                          "LossDate": c.LossDate, "ReportedDate": c.ReportedDate, "LossCause": c.LossCause,
                          "State": np.where(c.paid < c.gross, "open", "closed"),
                          "LossLocationPostalCode": pol.PrimaryInsuredPostalCode.to_numpy()[c.pidx]})
    rows = []
    for _, r in c.iterrows():
        rows.append((r.PublicID, "Reserve", "claimcost", round(r.gross * rng.uniform(0.9, 1.2), 2), r.ReportedDate))
        if r.paid > 0:
            rows.append((r.PublicID, "Payment", "claimcost", r.paid, min(r.ReportedDate + np.timedelta64(int(rng.integers(5, 70)), "D"), VALUATION)))
        rows.append((r.PublicID, "Reserve", "claimcost", round(r.gross - rows[-1][3] if r.paid == 0 else r.gross - sum(x[3] for x in rows if x[0] == r.PublicID and x[1] == "Reserve"), 2),
                     min(r.ReportedDate + np.timedelta64(30, "D"), VALUATION)))
        if r.recovery > 0:
            rows.append((r.PublicID, "Recovery", "claimcost", -r.recovery, min(r.ReportedDate + np.timedelta64(90, "D"), VALUATION)))
        if r.LossCause == "bodilyinjury":
            rows.append((r.PublicID, "Payment", "expense", round(r.gross * 0.05, 2), min(r.ReportedDate + np.timedelta64(40, "D"), VALUATION)))
    tx = pd.DataFrame(rows, columns=["ClaimID", "TransactionType", "CostType", "Amount", "CreateTime"])
    tx.insert(0, "PublicID", [f"cct:{400000 + i}" for i in range(len(tx))])

    for name, df in {"harbour_pc/pc_policyperiod": pol, "harbour_pc/pc_vehicle": veh,
                     "harbour_cc/cc_claim": claim, "harbour_cc/cc_transaction": tx}.items():
        p = out / f"{name}.parquet"
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(p, index=False)
        print(f"  {name:28s} {len(df):>7,d} rows")
    # rough check
    g = c.assign(net=c.gross - c.recovery).groupby(["q"]).net.sum()
    print("net incurred by quarter (GBP m):", (g / 1e6).round(2).to_dict())


if __name__ == "__main__":
    main()
