"""Motor experience book: three source systems, one deterministic world.

Generates the synthetic motor book behind the context demo
"Why has our motor loss ratio deteriorated this quarter?" (specs/SPEC_MOTOR_CONTEXT_DEMO.md).

Three source-shaped extracts, each with its own vocabulary:
  src_pas        policy administration   pol_master, pol_vehicle, pol_cover, pol_premium_txn
  src_claims     claims management       clm_header, clm_movement
  src_actuarial  actuarial warehouse     earned_premium_monthly, ibnr_estimate, segment_dim,
                                         postcode_region_dim

Targets (GBP m, reproduced to the penny; incurred = paid + outstanding + IBNR - recoveries):
  segment              Q2 EP  Q2 inc   Q3 EP  Q3 inc
  Urban private (PMU)   35.00  25.20   37.00  31.82
  Other private (PMO)   40.00  22.00   42.00  23.94
  Commercial (CMV)      25.00  16.80   26.00  19.84

How exactness is achieved: earned premium is hit by two premium multipliers per
segment (pre-July inceptions, Q3 inceptions) and a one-penny residual fix; claims
are scaled per segment-quarter, then IBNR is set to target - sum(net claims), so
IBNR absorbs the rounding. Everything is seeded; rerunning gives identical files.

Usage:
  uv run --native-tls --with numpy --with pandas --with pyarrow python tools/motor_book.py [--out data/motor]
Outputs parquet files under --out (not committed) and prints the verification table.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261106
VALUATION = np.datetime64("2026-10-31")
MONTHS = pd.period_range("2026-04", "2026-09", freq="M")
Q = {"2026Q2": (np.datetime64("2026-04-01"), np.datetime64("2026-07-01")),
     "2026Q3": (np.datetime64("2026-07-01"), np.datetime64("2026-10-01"))}

# ------------------------------------------------------------------ targets (£)
TARGET_EP = {("PMU", "2026Q2"): 35_000_000, ("PMU", "2026Q3"): 37_000_000,
             ("PMO", "2026Q2"): 40_000_000, ("PMO", "2026Q3"): 42_000_000,
             ("CMV", "2026Q2"): 25_000_000, ("CMV", "2026Q3"): 26_000_000}
TARGET_INC = {("PMU", "2026Q2"): 25_200_000, ("PMU", "2026Q3"): 31_820_000,
              ("PMO", "2026Q2"): 22_000_000, ("PMO", "2026Q3"): 23_940_000,
              ("CMV", "2026Q2"): 16_800_000, ("CMV", "2026Q3"): 19_840_000}
# intended IBNR share of incurred (recent quarter is less developed; BI-heavy book higher)
IBNR_SHARE = {("PMU", "2026Q2"): 0.03, ("PMU", "2026Q3"): 0.07,
              ("PMO", "2026Q2"): 0.03, ("PMO", "2026Q3"): 0.05,
              ("CMV", "2026Q2"): 0.06, ("CMV", "2026Q3"): 0.10}

SEGMENTS = {
    # code: (label, policies, base annual premium per vehicle, vehicles per policy range)
    "PMU": ("Urban private motor", 222_000, 950.0, (1, 1)),
    "PMO": ("Other private motor", 334_000, 720.0, (1, 1)),
    "CMV": ("Commercial motor", 11_500, 2_900.0, (1, 8)),
}
RATE_CHANGE_Q3 = 0.05            # Q3 new business priced 5% above the pre-July book
Q3_INCEPTION_BOOST = 1.6         # oversample Q3 inceptions, then subsample to hit RATE_CHANGE_Q3
# segment severity level (urban repair/theft costs run higher; vans cheaper per claim)
SEG_SEV = {"PMU": 0.85, "PMO": 0.65, "CMV": 0.95}
# how the Q3 excess over "Q2 cost levels" is carried, by segment (shares sum to 1)
Q3_DRIVERS = {"PMU": {"THEFT": 0.50, "AD": 0.38, "OTHER": 0.12},
              "PMO": {"AD": 0.70, "OTHER": 0.30},
              "CMV": {"LARGE_BI": 0.65, "AD": 0.15, "OTHER": 0.20}}

# postcode areas -> (region, urbanity). Synthetic allocation, UK-shaped.
METRO = {"Greater London": (["E", "N", "SE", "SW", "W", "NW", "EC", "WC", "IG", "RM", "CR", "BR"], "URBAN_MAJOR"),
         "West Midlands": (["B", "WV", "CV", "DY", "WS"], "URBAN_MAJOR"),
         "Greater Manchester": (["M", "OL", "BL", "SK", "WN"], "URBAN_MAJOR")}
OTHER_URBAN = {"West Yorkshire": (["LS", "BD", "HD", "WF"], "URBAN"),
               "Merseyside": (["L", "WA", "CH"], "URBAN"),
               "Tyne and Wear": (["NE", "SR"], "URBAN"),
               "Glasgow": (["G", "PA", "ML"], "URBAN"),
               "Bristol": (["BS", "BA"], "URBAN"),
               "Sheffield": (["S", "DN"], "URBAN")}
SHIRES = {"South West": (["EX", "TQ", "PL", "TA", "DT"], "RURAL"),
          "East of England": (["NR", "IP", "CB", "CO", "PE"], "SUBURBAN"),
          "South East": (["RG", "GU", "SO", "PO", "BN", "ME", "TN"], "SUBURBAN"),
          "East Midlands": (["NG", "LE", "DE", "LN"], "SUBURBAN"),
          "Yorkshire and Humber": (["YO", "HU", "HG"], "RURAL"),
          "North West": (["LA", "PR", "FY", "CA"], "RURAL"),
          "Wales": (["CF", "SA", "LL", "NP"], "RURAL"),
          "Scotland": (["EH", "AB", "DD", "KY", "IV"], "RURAL")}

PERILS = ["AD", "THEFT", "TPPD", "TPBI", "WINDSCREEN", "FIRE"]
HEAD = {"AD": "VEHICLE_REPAIR", "THEFT": "THEFT_TOTAL_LOSS", "TPPD": "TP_PROPERTY",
        "TPBI": "BODILY_INJURY", "WINDSCREEN": "GLASS", "FIRE": "FIRE_TOTAL_LOSS"}
# peril mix by segment, Q2 then Q3 (urban theft share rises in Q3)
MIX = {"PMU": {"2026Q2": [0.46, 0.14, 0.20, 0.09, 0.09, 0.02], "2026Q3": [0.44, 0.18, 0.19, 0.09, 0.08, 0.02]},
       "PMO": {"2026Q2": [0.48, 0.07, 0.22, 0.10, 0.11, 0.02], "2026Q3": [0.48, 0.07, 0.22, 0.10, 0.11, 0.02]},
       "CMV": {"2026Q2": [0.40, 0.08, 0.26, 0.14, 0.10, 0.02], "2026Q3": [0.40, 0.08, 0.26, 0.14, 0.10, 0.02]}}
# claim frequency per vehicle-year by segment and quarter
FREQ = {"PMU": {"2026Q2": 0.135, "2026Q3": 0.143},
        "PMO": {"2026Q2": 0.110, "2026Q3": 0.110},
        "CMV": {"2026Q2": 0.240, "2026Q3": 0.240}}
# gross severity: lognormal mean (GBP) and sigma, by peril; multipliers below
SEV = {"AD": (3_100, 0.55), "THEFT": (9_500, 0.60), "TPPD": (2_900, 0.70),
       "TPBI": (24_000, 1.20), "WINDSCREEN": (420, 0.30), "FIRE": (13_000, 0.50)}
REPAIR_INFLATION_Q3 = 1.0        # structural pre-uplifts off: Q3 excess is allocated by Q3_DRIVERS
THEFT_SEV_Q3_PMU = 1.0
CMV_LARGE_BI = {"2026Q2": [900_000.0, 550_000.0],
                "2026Q3": [900_000.0, 650_000.0, 500_000.0, 450_000.0]}  # raw, before levels
# share of claims paid by the valuation date, by peril (rest is outstanding reserve)
PAID_FRAC = {"AD": (0.88, 0.70), "THEFT": (0.80, 0.55), "TPPD": (0.75, 0.50),
             "TPBI": (0.22, 0.10), "WINDSCREEN": (0.98, 0.90), "FIRE": (0.70, 0.45)}  # (Q2, Q3)
RECOVERY = {"THEFT": (0.30, 0.18), "AD": (0.10, 0.22), "TPPD": (0.05, 0.30)}  # (p(any), share)
FEE_SHARE = {"TPBI": 0.06, "TPPD": 0.02}  # allocated claims-handling fees (ALAE), not in v1 incurred

rng = np.random.default_rng(SEED)


def lognormal(mean, sigma, n):
    mu = np.log(mean) - sigma ** 2 / 2
    return rng.lognormal(mu, sigma, n)


def area_table():
    rows = []
    for groups in (METRO, OTHER_URBAN, SHIRES):
        for region, (areas, urb) in groups.items():
            for a in areas:
                rows.append((a, region, urb))
    return pd.DataFrame(rows, columns=["postcode_area", "region", "urbanity_code"])


def build_policies(areas):
    frames = []
    for seg, (label, n, base_prem, (vmin, vmax)) in SEGMENTS.items():
        # inceptions uniform over 18 months (2025-04-02 .. 2026-09-30), Q3-2026 oversampled;
        # solve_multipliers() later thins Q3 so new business lands RATE_CHANGE_Q3 above the book
        days = rng.integers(0, 547, n)
        q3 = days >= 455  # 2026-07-01 onwards
        extra = rng.integers(455, 547, int(q3.sum() * (Q3_INCEPTION_BOOST - 1)))
        days = np.concatenate([days, extra])
        n = len(days)
        inception = np.datetime64("2025-04-02") + days.astype("timedelta64[D]")
        if seg == "PMU":
            pool = areas[areas.urbanity_code == "URBAN_MAJOR"].postcode_area.to_numpy()
            pool2 = areas[areas.urbanity_code == "URBAN"].postcode_area.to_numpy()
            area = np.where(rng.random(n) < 0.72, rng.choice(pool, n), rng.choice(pool2, n))
        elif seg == "PMO":
            pool = areas[areas.urbanity_code.isin(["SUBURBAN", "RURAL"])].postcode_area.to_numpy()
            pool2 = areas[areas.urbanity_code == "URBAN"].postcode_area.to_numpy()
            area = np.where(rng.random(n) < 0.85, rng.choice(pool, n), rng.choice(pool2, n))
        else:
            area = rng.choice(areas.postcode_area.to_numpy(), n)
        n_veh = rng.integers(vmin, vmax + 1, n) if vmax > vmin else np.ones(n, dtype=int)
        prem_per_veh = lognormal(base_prem, 0.35, n)
        cover = rng.choice(["COMP", "TPFT", "TPO"], n, p=[0.86, 0.11, 0.03])
        if seg == "CMV":
            use = rng.choice(["DELIVERY", "HAULAGE", "TRADES", "FLEET_CAR", "TAXI"], n, p=[0.30, 0.15, 0.30, 0.17, 0.08])
        else:
            use = rng.choice(["SDP", "SDP_COMMUTE", "BUSINESS"], n, p=[0.45, 0.45, 0.10])
        frames.append(pd.DataFrame({
            "product_cd": seg, "inception": inception, "postcode_area": area,
            "n_veh": n_veh, "prem_per_veh": prem_per_veh, "cover_cd": cover, "use_class": use}))
    p = pd.concat(frames, ignore_index=True)
    p["expiry"] = p.inception + np.timedelta64(365, "D")
    p["policy_idx"] = np.arange(len(p))
    p["contract_reference"] = ["MC%08d" % (10_000_000 + i) for i in p.policy_idx]
    p["is_q3_new"] = p.inception >= np.datetime64("2026-07-01")
    return p


def earned_days(p):
    """days in force per policy per month, shape (n, len(MONTHS))."""
    inc = p.inception.to_numpy().astype("datetime64[D]")
    exp = p.expiry.to_numpy().astype("datetime64[D]")
    starts = np.array([m.start_time.to_datetime64() for m in MONTHS]).astype("datetime64[D]")
    ends = np.array([(m + 1).start_time.to_datetime64() for m in MONTHS]).astype("datetime64[D]")
    lo = np.maximum(inc[:, None], starts[None, :])
    hi = np.minimum(exp[:, None], ends[None, :])
    return np.clip((hi - lo).astype(int), 0, None)


def solve_multipliers(p, days):
    """Thin Q3 inceptions so new business prices RATE_CHANGE_Q3 above the book, then set two
    premium multipliers per segment so quarterly earned hits the targets exactly.
    Returns (p, days, mult) with Q3 policies subsampled."""
    annual = (p.prem_per_veh * p.n_veh).to_numpy()
    raw = annual[:, None] * days / 365.0
    q2 = raw[:, :3].sum(axis=1)
    q3 = raw[:, 3:].sum(axis=1)
    keep = np.ones(len(p), dtype=bool)
    for seg in SEGMENTS:
        m = (p.product_cd == seg).to_numpy()
        old, new = m & ~p.is_q3_new.to_numpy(), m & p.is_q3_new.to_numpy()
        a, b, c = q2[old].sum(), q3[old].sum(), q3[new].sum()
        m_old = TARGET_EP[(seg, "2026Q2")] / a
        c_needed = (TARGET_EP[(seg, "2026Q3")] - m_old * b) / (m_old * (1 + RATE_CHANGE_Q3))
        frac = c_needed / c
        if frac > 1:
            raise SystemExit(f"{seg}: raise Q3_INCEPTION_BOOST (need {frac:.2f}x more Q3 inceptions)")
        idx = np.flatnonzero(new)
        drop = rng.choice(idx, int(round(len(idx) * (1 - frac))), replace=False)
        keep[drop] = False
    p = p[keep].reset_index(drop=True)
    p["policy_idx"] = np.arange(len(p))
    p["contract_reference"] = ["MC%08d" % (10_000_000 + i) for i in p.policy_idx]
    days = days[keep]
    annual, q2, q3 = annual[keep], q2[keep], q3[keep]
    mult = np.ones(len(p))
    for seg in SEGMENTS:
        m = (p.product_cd == seg).to_numpy()
        old, new = m & ~p.is_q3_new.to_numpy(), m & p.is_q3_new.to_numpy()
        a, b, c = q2[old].sum(), q3[old].sum(), q3[new].sum()
        m_old = TARGET_EP[(seg, "2026Q2")] / a
        m_new = (TARGET_EP[(seg, "2026Q3")] - m_old * b) / c
        mult[old], mult[new] = m_old, m_new
        print(f"  {seg}: {m.sum():7,d} policies ({new.sum():6,d} incepting Q3); premium level {m_old:.3f}, "
              f"Q3 new business {m_new:.3f} (rate change {100 * (m_new / m_old - 1):+.1f}%)")
    return p, days, mult


def build_earned(p, days, mult):
    annual = np.round((p.prem_per_veh * p.n_veh).to_numpy() * mult, 2)
    p["annual_prem_amt"] = annual
    ep = np.round(annual[:, None] * days / 365.0, 2)
    n_veh = p.n_veh.to_numpy()
    veh_years = np.round(n_veh[:, None] * days / 365.0, 6)
    keep = days > 0
    idx, mi = np.nonzero(keep)
    e = pd.DataFrame({
        "pol_ref": p.contract_reference.to_numpy()[idx],
        "seg_cd": p.product_cd.to_numpy()[idx],
        "yyyymm": np.array([int(m.strftime("%Y%m")) for m in MONTHS])[mi],
        "acc_qtr": np.where(mi < 3, "2026Q2", "2026Q3"),
        "days_in_force": days[idx, mi],
        "ep_amt": ep[idx, mi],
        "veh_years": veh_years[idx, mi],
    })
    # penny fix: push the rounding residual onto the biggest row of each segment-quarter
    for (seg, q), target in TARGET_EP.items():
        m = (e.seg_cd == seg) & (e.acc_qtr == q)
        resid = round(target - e.loc[m, "ep_amt"].sum(), 2)
        if resid:
            i = e.loc[m, "ep_amt"].idxmax()
            e.loc[i, "ep_amt"] = round(e.loc[i, "ep_amt"] + resid, 2)
    return e


def build_claims(p, e, areas):
    exposure = e.groupby(["pol_ref", "acc_qtr"], as_index=False).agg(vy=("veh_years", "sum"))
    exposure = exposure.merge(p[["contract_reference", "product_cd", "postcode_area", "inception", "expiry"]],
                              left_on="pol_ref", right_on="contract_reference")
    exposure = exposure.merge(areas, on="postcode_area")
    claims = []
    for seg in SEGMENTS:
        for q, (qs, qe) in Q.items():
            ex = exposure[(exposure.product_cd == seg) & (exposure.acc_qtr == q)]
            vy = ex.vy.sum()
            n = int(round(FREQ[seg][q] * vy))
            w = ex.vy.to_numpy()
            # urban theft wave Q3: metro areas carry more weight for THEFT claims
            peril = rng.choice(PERILS, n, p=MIX[seg][q])
            metro = ex.region.isin(METRO.keys()).to_numpy()
            w_theft = w * np.where(metro, 1.7 if (seg == "PMU" and q == "2026Q3") else 1.15, 1.0)
            pick = np.empty(n, dtype=int)
            is_theft = peril == "THEFT"
            pick[~is_theft] = rng.choice(len(ex), (~is_theft).sum(), p=w / w.sum())
            pick[is_theft] = rng.choice(len(ex), is_theft.sum(), p=w_theft / w_theft.sum())
            row = ex.iloc[pick]
            lo = np.maximum(row.inception.to_numpy().astype("datetime64[D]"), qs)
            hi = np.minimum(row.expiry.to_numpy().astype("datetime64[D]"), qe)
            span = np.clip((hi - lo).astype(int), 1, None)
            loss = lo + (rng.random(n) * span).astype(int).astype("timedelta64[D]")
            sev = np.array([lognormal(*SEV[pr], 1)[0] for pr in peril]) if n < 50 else np.zeros(n)
            if n >= 50:
                for pr in PERILS:
                    m = peril == pr
                    sev[m] = lognormal(*SEV[pr], m.sum())
            if q == "2026Q3":
                sev = np.where(peril == "AD", sev * REPAIR_INFLATION_Q3, sev)
                if seg == "PMU":
                    sev = np.where(peril == "THEFT", sev * THEFT_SEV_Q3_PMU, sev)
            # TP bodily injury cannot exist on TPO? it can (TPO covers TP). Own-damage perils need COMP/TPFT:
            if seg == "CMV":
                big = CMV_LARGE_BI[q]
                bi_idx = np.flatnonzero(peril == "TPBI")[: len(big)]
                sev[bi_idx] = big
            claims.append(pd.DataFrame({
                "policy_no": row.pol_ref.to_numpy(), "seg_cd": seg, "acc_qtr": q,
                "region": row.region.to_numpy(), "postcode_area": row.postcode_area.to_numpy(),
                "loss_dt": loss, "peril_cd": peril, "gross": sev}))
    c = pd.concat(claims, ignore_index=True)
    c["notified_dt"] = c.loss_dt + rng.integers(0, 21, len(c)).astype("timedelta64[D]")
    c.loc[c.peril_cd == "TPBI", "notified_dt"] += rng.integers(0, 40, (c.peril_cd == "TPBI").sum()).astype("timedelta64[D]")
    c["notified_dt"] = np.minimum(c.notified_dt.to_numpy(), VALUATION)
    # recoveries (salvage / subrogation) as a share of gross
    c["recovery"] = 0.0
    for pr, (p_any, share) in RECOVERY.items():
        m = (c.peril_cd == pr) & (rng.random(len(c)) < p_any)
        c.loc[m, "recovery"] = c.loc[m, "gross"] * share * rng.uniform(0.6, 1.2, m.sum())
    # Calibration. Q2: one segment level k2 so net incurred = target - intended IBNR.
    # Q3: the SAME k2 (Q2 cost levels), then the excess still needed is carried by the named
    # drivers (Q3_DRIVERS), so the deterioration IS the evidence, mechanically.
    c["gross"] *= c.seg_cd.map(SEG_SEV)
    c["recovery"] *= c.seg_cd.map(SEG_SEV)
    for seg in SEGMENTS:
        m2 = (c.seg_cd == seg) & (c.acc_qtr == "2026Q2")
        want2 = TARGET_INC[(seg, "2026Q2")] * (1 - IBNR_SHARE[(seg, "2026Q2")])
        k2 = want2 / (c.loc[m2, "gross"] - c.loc[m2, "recovery"]).sum()
        m3 = (c.seg_cd == seg) & (c.acc_qtr == "2026Q3")
        c.loc[m2 | m3, ["gross", "recovery"]] *= k2
        want3 = TARGET_INC[(seg, "2026Q3")] * (1 - IBNR_SHARE[(seg, "2026Q3")])
        gap = want3 - (c.loc[m3, "gross"] - c.loc[m3, "recovery"]).sum()
        groups = {"THEFT": m3 & (c.peril_cd == "THEFT"), "AD": m3 & (c.peril_cd == "AD"),
                  "LARGE_BI": c.index.isin(c.loc[m3 & (c.peril_cd == "TPBI"), "gross"].nlargest(len(CMV_LARGE_BI["2026Q3"])).index)}
        groups["OTHER"] = m3 & ~(groups["THEFT"] | groups["AD"] | groups["LARGE_BI"])
        print(f"  {seg}: Q2 {m2.sum():6d} claims, level k2 {k2:.3f}; Q3 {m3.sum():6d} claims, "
              f"excess over Q2 cost levels {gap / 1e6:+.2f}m carried by:")
        for g, share in Q3_DRIVERS[seg].items():
            gm = groups[g]
            base = (c.loc[gm, "gross"] - c.loc[gm, "recovery"]).sum()
            f = 1 + gap * share / base
            c.loc[gm, ["gross", "recovery"]] *= f
            print(f"      {g:9s} x{f:.3f} ({gm.sum()} claims)")
    c["gross"] = c.gross.round(2)
    c["recovery"] = c.recovery.round(2)
    # paid share by valuation date
    pf = np.array([PAID_FRAC[pr][0 if q == "2026Q2" else 1] for pr, q in zip(c.peril_cd, c.acc_qtr)])
    pf = np.clip(pf * rng.uniform(0.85, 1.1, len(c)), 0, 1)
    # claims notified at the valuation date are entirely outstanding
    pf = np.where(c.notified_dt.to_numpy() >= VALUATION - np.timedelta64(7, "D"), 0.0, pf)
    c["paid"] = (c.gross * pf).round(2)
    c["outstanding"] = (c.gross - c.paid).round(2)
    c["fee"] = 0.0
    for pr, s in FEE_SHARE.items():
        m = c.peril_cd == pr
        c.loc[m, "fee"] = (c.loc[m, "gross"] * s).round(2)
    c["head_of_damage"] = c.peril_cd.map(HEAD)
    c["claim_ref"] = ["CL%09d" % (260_000_000 + i) for i in range(len(c))]
    c["large_loss_flag"] = c.gross >= 500_000
    return c


def build_movements(c):
    """Claims-system movements: RESERVE (signed change in outstanding), PAID (+), RECOVERY (-), FEE (+)."""
    rows = []
    n = len(c)
    init_est = (c.gross * rng.uniform(0.85, 1.30, n)).round(2)
    # 1. initial reserve at notification
    rows.append(pd.DataFrame({"claim_ref": c.claim_ref, "movement_dt": c.notified_dt,
                              "movement_type": "RESERVE", "head_of_damage": c.head_of_damage,
                              "amount": init_est, "seq": 1}))
    # 2. payments: one or two PAID movements for paid > 0
    has_paid = c.paid > 0
    split = rng.random(n) < 0.35
    first = np.where(split, (c.paid * rng.uniform(0.3, 0.7, n)).round(2), c.paid)
    second = (c.paid - first).round(2)
    gap1 = rng.integers(5, 60, n).astype("timedelta64[D]")
    gap2 = gap1 + rng.integers(10, 70, n).astype("timedelta64[D]")
    d1 = np.minimum(c.notified_dt.to_numpy() + gap1, VALUATION)
    d2 = np.minimum(c.notified_dt.to_numpy() + gap2, VALUATION)
    rows.append(pd.DataFrame({"claim_ref": c.claim_ref[has_paid], "movement_dt": d1[has_paid],
                              "movement_type": "PAID", "head_of_damage": c.head_of_damage[has_paid],
                              "amount": first[has_paid], "seq": 2}))
    m2 = has_paid & split & (second > 0)
    rows.append(pd.DataFrame({"claim_ref": c.claim_ref[m2], "movement_dt": d2[m2],
                              "movement_type": "PAID", "head_of_damage": c.head_of_damage[m2],
                              "amount": second[m2], "seq": 3}))
    # 3. reserve adjustment so that outstanding at valuation = gross - paid
    #    outstanding = init_est + adj - paid  =>  adj = gross - init_est
    adj = (c.gross - init_est).round(2)
    d3 = np.minimum(np.maximum(d2, c.notified_dt.to_numpy() + np.timedelta64(14, "D")), VALUATION)
    nz = adj != 0
    rows.append(pd.DataFrame({"claim_ref": c.claim_ref[nz], "movement_dt": d3[nz],
                              "movement_type": "RESERVE", "head_of_damage": c.head_of_damage[nz],
                              "amount": adj[nz], "seq": 4}))
    # 4. recoveries (negative = cash in) and fees
    rc = c.recovery > 0
    rows.append(pd.DataFrame({"claim_ref": c.claim_ref[rc], "movement_dt": np.minimum(d2[rc] + np.timedelta64(20, "D"), VALUATION),
                              "movement_type": "RECOVERY", "head_of_damage": c.head_of_damage[rc],
                              "amount": -c.recovery[rc], "seq": 5}))
    fe = c.fee > 0
    rows.append(pd.DataFrame({"claim_ref": c.claim_ref[fe], "movement_dt": d1[fe],
                              "movement_type": "FEE", "head_of_damage": c.head_of_damage[fe],
                              "amount": c.fee[fe], "seq": 6}))
    mv = pd.concat(rows, ignore_index=True).sort_values(["claim_ref", "seq", "movement_dt"]).reset_index(drop=True)
    mv["movement_id"] = np.arange(1, len(mv) + 1)
    return mv[["movement_id", "claim_ref", "movement_dt", "movement_type", "head_of_damage", "amount"]]


def build_ibnr(c):
    rows = []
    for (seg, q), target in TARGET_INC.items():
        m = (c.seg_cd == seg) & (c.acc_qtr == q)
        net = round((c.loc[m, "paid"] + c.loc[m, "outstanding"] - c.loc[m, "recovery"]).sum(), 2)
        ibnr = round(target - net, 2)
        rows.append((seg, q, ibnr, str(VALUATION), "CHAIN_LADDER", "Actuarial reserving, Q3 2026 close"))
    return pd.DataFrame(rows, columns=["seg_cd", "acc_qtr", "ibnr_amt", "valuation_dt", "method_cd", "note"])


MAKES = {"PMU": [("Ford", "Fiesta"), ("Vauxhall", "Corsa"), ("VW", "Golf"), ("BMW", "1 Series"), ("Toyota", "Yaris"),
                 ("Mercedes", "A-Class"), ("Audi", "A3"), ("Range Rover", "Evoque"), ("Kia", "Sportage"), ("Tesla", "Model 3")],
         "PMO": [("Ford", "Focus"), ("Vauxhall", "Astra"), ("VW", "Polo"), ("Nissan", "Qashqai"), ("Skoda", "Octavia"),
                 ("Hyundai", "Tucson"), ("Honda", "Civic"), ("Peugeot", "3008"), ("Mini", "Hatch"), ("Volvo", "XC40")],
         "CMV": [("Ford", "Transit"), ("Mercedes", "Sprinter"), ("VW", "Transporter"), ("Vauxhall", "Vivaro"),
                 ("Citroen", "Berlingo"), ("DAF", "LF"), ("Scania", "P-series"), ("Toyota", "Proace"), ("Iveco", "Daily"), ("Ford", "Ranger")]}


def build_vehicles(p):
    reps = p.n_veh.to_numpy()
    seg = np.repeat(p.product_cd.to_numpy(), reps)
    ref = np.repeat(p.contract_reference.to_numpy(), reps)
    n = len(seg)
    make = np.empty(n, dtype=object)
    model = np.empty(n, dtype=object)
    for s, lst in MAKES.items():
        m = seg == s
        k = rng.integers(0, len(lst), m.sum())
        make[m] = np.array([x[0] for x in lst], dtype=object)[k]
        model[m] = np.array([x[1] for x in lst], dtype=object)[k]
    year = rng.integers(2012, 2026, n)
    grp = np.where(seg == "CMV", rng.integers(20, 51, n), rng.integers(1, 51, n))
    value = np.round(np.where(seg == "CMV", lognormal(28_000, 0.5, n), lognormal(14_000, 0.6, n)) * (1 - (2026 - year) * 0.04), 0)
    letters = np.array(list("ABCDEFGHKLMNOPRSTUVWXY"))
    l1 = rng.choice(letters, (n, 2))
    l2 = rng.choice(letters, (n, 3))
    yr = rng.integers(10, 76, n)
    reg = np.char.add(np.char.add(np.char.add(l1[:, 0], l1[:, 1]), np.char.zfill(yr.astype(str), 2) + " "),
                      np.char.add(np.char.add(l2[:, 0], l2[:, 1]), l2[:, 2]))
    v = pd.DataFrame({"contract_reference": ref, "vehicle_seq": 1, "reg_mark": reg,
                      "make": make, "model": model, "year_of_manufacture": year, "abi_group": grp, "vehicle_value_amt": value})
    v["vehicle_seq"] = v.groupby("contract_reference").cumcount() + 1
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/motor")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    areas = area_table()
    print("Policies")
    p = build_policies(areas)
    days = earned_days(p)
    p, days, mult = solve_multipliers(p, days)
    e = build_earned(p, days, mult)
    print("Claims")
    c = build_claims(p, e, areas)
    mv = build_movements(c)
    ibnr = build_ibnr(c)
    v = build_vehicles(p)

    # ---------------- source-system tables -----------------
    pol_master = pd.DataFrame({
        "contract_reference": p.contract_reference, "product_cd": p.product_cd,
        "cover_start_dt": p.inception, "cover_end_dt": p.expiry - np.timedelta64(1, "D"),
        "annual_prem_amt": p.annual_prem_amt, "risk_postcode": p.postcode_area + " " + rng.integers(1, 30, len(p)).astype(str),
        "use_class": p.use_class, "veh_count": p.n_veh, "contract_status": np.where(p.expiry > VALUATION, "LIVE", "EXPIRED"),
        "source_sys": "PAS_MOTOR"})
    pol_cover = pd.DataFrame({"contract_reference": p.contract_reference, "cover_cd": p.cover_cd,
                              "excess_amt": rng.choice([250, 350, 500, 750, 1000], len(p)),
                              "tpl_limit_amt": np.where(p.product_cd == "CMV", 5_000_000, 20_000_000)})
    pol_premium_txn = pd.DataFrame({"txn_id": np.arange(1, len(p) + 1), "contract_reference": p.contract_reference,
                                    "txn_type": "NEW_BUSINESS", "txn_dt": p.inception,
                                    "txn_amt": p.annual_prem_amt, "ipt_amt": (p.annual_prem_amt * 0.12).round(2)})
    clm_header = pd.DataFrame({"claim_ref": c.claim_ref, "policy_no": c.policy_no, "loss_dt": c.loss_dt,
                               "notified_dt": c.notified_dt, "peril_cd": c.peril_cd,
                               "claim_status": np.where(c.outstanding > 0, "OPEN", "SETTLED"),
                               "loss_postcode_area": c.postcode_area, "handling_office": rng.choice(["Leeds", "Glasgow", "Bristol"], len(c)),
                               "fault_ind": rng.choice(["Y", "N", "SPLIT"], len(c), p=[0.6, 0.3, 0.1])})
    earned = e.rename(columns={})[["pol_ref", "seg_cd", "yyyymm", "ep_amt", "veh_years", "days_in_force"]]
    segment_dim = pd.DataFrame([(s, SEGMENTS[s][0], "MOTOR") for s in SEGMENTS], columns=["seg_cd", "seg_desc", "lob_cd"])
    areas_out = areas.rename(columns={"region": "region_name"})

    tables = {"src_pas/pol_master": pol_master, "src_pas/pol_vehicle": v, "src_pas/pol_cover": pol_cover,
              "src_pas/pol_premium_txn": pol_premium_txn,
              "src_claims/clm_header": clm_header, "src_claims/clm_movement": mv,
              "src_actuarial/earned_premium_monthly": earned, "src_actuarial/ibnr_estimate": ibnr,
              "src_actuarial/segment_dim": segment_dim, "src_actuarial/postcode_region_dim": areas_out}
    for name, df in tables.items():
        path = out / f"{name}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)
        print(f"  {name:40s} {len(df):>9,d} rows  {path.stat().st_size / 1e6:6.1f} MB")

    # ---------------- verification ---------------------------
    print("\nVerification (GBP m)")
    ep = e.groupby(["seg_cd", "acc_qtr"]).ep_amt.sum()
    net = (c.assign(net=c.paid + c.outstanding - c.recovery).groupby(["seg_cd", "acc_qtr"]).net.sum())
    inc = net + ibnr.set_index(["seg_cd", "acc_qtr"]).ibnr_amt
    tbl = pd.DataFrame({"earned": ep, "incurred": inc, "ibnr": ibnr.set_index(["seg_cd", "acc_qtr"]).ibnr_amt})
    tbl["lr"] = tbl.incurred / tbl.earned
    tbl["ibnr_share"] = tbl.ibnr / tbl.incurred
    print(tbl.assign(earned=tbl.earned / 1e6, incurred=tbl.incurred / 1e6, ibnr=tbl.ibnr / 1e6).round(4).to_string())
    tot = tbl.groupby(level=1)[["earned", "incurred"]].sum()
    print((tot / 1e6).assign(lr=tot.incurred / tot.earned).round(4).to_string())
    exact = all(abs(ep[k] - TARGET_EP[k]) < 0.005 for k in TARGET_EP) and all(abs(inc[k] - TARGET_INC[k]) < 0.005 for k in TARGET_INC)
    print("EXACT to the penny:", exact)
    # contribution at constant Q3 EP
    print("\nContribution to deterioration (Q3 EP held, Q2 LR applied)")
    contrib = {}
    for seg in SEGMENTS:
        lr2 = inc[(seg, "2026Q2")] / ep[(seg, "2026Q2")]
        contrib[seg] = inc[(seg, "2026Q3")] - lr2 * ep[(seg, "2026Q3")]
    s = sum(contrib.values())
    for seg, x in contrib.items():
        print(f"  {seg}: {x / 1e6:6.2f}m  {100 * x / s:5.1f}%")
    # evidence
    print("\nEvidence")
    vy = e.groupby(["seg_cd", "acc_qtr"]).veh_years.sum()
    th = c[c.peril_cd == "THEFT"].groupby(["seg_cd", "acc_qtr"]).agg(n=("gross", "size"), sev=("gross", "mean"))
    th["freq_per_100vy"] = 100 * th.n / vy
    print("theft frequency per 100 vehicle-years and mean severity:\n", th.round(2).to_string())
    ad = c[c.peril_cd == "AD"].groupby(["seg_cd", "acc_qtr"]).gross.mean()
    print("vehicle repair mean cost:\n", ad.round(0).to_string())
    big = c[(c.seg_cd == "CMV") & (c.peril_cd == "TPBI")].groupby("acc_qtr").agg(n=("gross", "size"), large=("large_loss_flag", "sum"), large_amt=("gross", lambda x: x[x >= 500_000].sum()))
    print("commercial bodily injury:\n", big.to_string())
    metro = c[(c.seg_cd == "PMU") & (c.peril_cd == "THEFT")].assign(metro=lambda d: d.region.isin(METRO)).groupby(["acc_qtr", "metro"]).gross.agg(["size", "sum"])
    print("urban theft by metro vs other:\n", metro.to_string())
    freq = c.groupby(["seg_cd", "acc_qtr"]).size() / vy * 100
    sev = c.groupby(["seg_cd", "acc_qtr"]).gross.mean()
    print("all-peril frequency per 100 vy / mean severity:\n", pd.DataFrame({"freq": freq, "sev": sev}).round(2).to_string())


if __name__ == "__main__":
    main()
