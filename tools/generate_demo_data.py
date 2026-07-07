#!/usr/bin/env python3
"""Generate deterministic synthetic demo data for the Bricksurance book.

Reads the model specs (for column order and validation) and emits
build/databricks/95_demo_data.sql as INSERT OVERWRITE statements, so reruns
are idempotent. Run AFTER tools/generate.py (which recreates build/).

The data tells one golden thread end to end: policy POL-2026-000001
(Aldgate Mills Ltd, commercial property, GBP) -> written premium -> fire
claim CLM-2026-000001 with reserves and payments -> 30% quota-share cession
to treaty TR-QS-PROP-2026 (Bricksurance SE -> Bricksurance Re AG), inside a
small surrounding book of ~60 policies across four lines of business.

All parties, names and numbers are synthetic. Usage:
    uv run --with pyyaml tools/generate_demo_data.py
"""

import random
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "databricks" / "95_demo_data.sql"
TODAY = date(2026, 7, 7)
rng = random.Random(20260707)


def load_entities():
    entities = {}
    for path in sorted((ROOT / "model").rglob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        if spec.get("kind") == "entity":
            entities[spec["name"]] = spec
    return entities


def load_binding():
    return yaml.safe_load((ROOT / "bindings" / "databricks.yaml").read_text())


def fqn(binding, domain, table):
    return f"{binding['catalog']}.{binding['schema_pattern'].format(domain=domain)}.{table}"


def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, date):
        return f"DATE '{v.isoformat()}'"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def insert(binding, entity, rows):
    cols = [a["name"] for a in entity["attributes"]]
    for r in rows:
        unknown = set(r) - set(cols)
        assert not unknown, f"{entity['name']}: unknown columns {unknown}"
    table = fqn(binding, entity["domain"], entity["name"])
    values = ",\n".join("  (" + ", ".join(lit(r.get(c)) for c in cols) + ")" for r in rows)
    return f"INSERT OVERWRITE {table} ({', '.join(cols)}) VALUES\n{values};"


# ---------------------------------------------------------------- reference world

ORGS = [
    ("Aldgate Mills Ltd", "GB"), ("Bluestone Retail Ltd", "GB"),
    ("Clyde Fabrication Ltd", "GB"), ("Rivelin Foods plc", "GB"),
    ("Northgate Logistics GmbH", "DE"), ("Hafen Industrie AG", "DE"),
    ("Vantera Pharma SE", "IE"), ("Cormorant Marine SA", "FR"),
    ("Helvetia Precision AG", "CH"), ("Beacon Point Hotels Inc", "US"),
]
PERSONS = [("Anna Novak", "GB"), ("James Whitfield", "GB"), ("Claire Dubois", "FR")]
BROKERS = [("Marlin & Rees Brokers LLP", "GB"), ("Atlas Cover Partners", "IE")]
GROUP = [("Bricksurance SE", "DE"), ("Bricksurance Re AG", "CH")]

CCY = {"GB": "GBP", "IE": "EUR", "DE": "EUR", "FR": "EUR", "CH": "CHF", "US": "USD"}
LOB_PLAN = ["COMMERCIAL_PROPERTY"] * 24 + ["MOTOR"] * 18 + ["GENERAL_LIABILITY"] * 12 + ["MARINE_CARGO"] * 6
BASE_PREMIUM = {"COMMERCIAL_PROPERTY": 85000, "MOTOR": 18000, "GENERAL_LIABILITY": 22000, "MARINE_CARGO": 30000}
OBJ_TYPE = {"COMMERCIAL_PROPERTY": "BUILDING", "MOTOR": "VEHICLE",
            "GENERAL_LIABILITY": "LIABILITY_EXPOSURE", "MARINE_CARGO": "CARGO_SHIPMENT"}
OBJ_DESC = {"COMMERCIAL_PROPERTY": ["Warehouse and distribution centre", "Office building", "Factory unit", "Retail premises"],
            "MOTOR": ["Fleet of delivery vans", "Company car fleet", "Mixed commercial fleet"],
            "GENERAL_LIABILITY": ["Business operations at head office", "Manufacturing operations", "Hospitality operations"],
            "MARINE_CARGO": ["Machinery consignments, EU routes", "Pharmaceutical consignments, transatlantic"]}
POSTCODES = {"GB": ["M3 5EN", "LS1 4AP", "B4 7DA", "G2 1AL", "BS1 6QF"],
             "DE": ["20457", "60311", "80331"], "IE": ["D02 X285"],
             "FR": ["13002", "75008"], "CH": ["8005"], "US": ["33131", "94105"]}
COL_BY_LOB = {"COMMERCIAL_PROPERTY": ["FIRE", "FLOOD", "STORM", "WATER_DAMAGE"],
              "MOTOR": ["COLLISION", "COLLISION", "THEFT"],
              "GENERAL_LIABILITY": ["LIABILITY_INCIDENT"],
              "MARINE_CARGO": ["THEFT", "WATER_DAMAGE"]}


def build_world():
    parties, roles = [], []
    pid = {}
    for i, (name, country) in enumerate(GROUP + BROKERS + ORGS + PERSONS):
        party_type = "PERSON" if (name, country) in PERSONS else "ORGANISATION"
        key = f"pty_{i + 1:04d}"
        pid[name] = key
        parties.append({"party_id": key, "party_type_code": party_type, "name": name,
                        "country_code": country, "source_system_code": "DATA_CORE"})

    policies, coverages, objects, premiums = [], [], [], []
    claims, claim_txs, cessions = [], [], []
    role_n, cov_n, obj_n, prm_n, ctx_n = [0], [0], [0], [0], [0]

    def add_role(role_type, party, start, policy_id=None, claim_id=None, treaty_id=None):
        role_n[0] += 1
        roles.append({"party_role_id": f"prl_{role_n[0]:04d}", "party_id": pid[party],
                      "party_role_type_code": role_type, "policy_id": policy_id,
                      "claim_id": claim_id, "treaty_id": treaty_id,
                      "start_date": start, "end_date": None})

    uwy_plan = [2024, 2025, 2026] * 20
    lobs = LOB_PLAN[:]
    rng.shuffle(lobs)
    lobs[0] = "COMMERCIAL_PROPERTY"  # the hero is always commercial property

    for i in range(60):
        n = i + 1
        hero = i == 0
        uwy = 2026 if hero else uwy_plan[i]
        lob = lobs[i]
        org, country = ORGS[0] if hero else ORGS[i % len(ORGS)]
        ccy = CCY[country]
        inception = date(2026, 1, 1) if hero else date(uwy, rng.randint(1, 12), rng.randint(1, 28))
        expiry = inception + timedelta(days=364)
        cancelled = (not hero) and uwy == 2025 and n % 17 == 0
        if cancelled:
            status = "CANCELLED"
        elif expiry < TODAY:
            status = "EXPIRED"
        elif inception > TODAY:
            status = "BOUND"
        else:
            status = "IN_FORCE"
        policy_id = f"pol_{n:04d}"
        policies.append({"policy_id": policy_id, "policy_number": f"POL-{uwy}-{n:06d}",
                         "source_system_code": "PAS_CORE", "line_of_business_code": lob,
                         "policy_status_code": status, "inception_date": inception,
                         "expiry_date": expiry, "underwriting_year": uwy, "currency_code": ccy})

        add_role("POLICYHOLDER", org, inception, policy_id=policy_id)
        add_role("INSURED", org, inception, policy_id=policy_id)
        if n % 2 == 0:
            add_role("BROKER", BROKERS[(n // 2) % 2][0], inception, policy_id=policy_id)

        def add_cov(ctype, limit, ded, sum_insured):
            cov_n[0] += 1
            cid = f"cov_{cov_n[0]:04d}"
            coverages.append({"coverage_id": cid, "policy_id": policy_id,
                              "coverage_type_code": ctype, "limit_amount": limit,
                              "deductible_amount": ded, "sum_insured_amount": sum_insured})
            return cid

        if lob == "COMMERCIAL_PROPERTY":
            first_cov = add_cov("BUILDINGS", 8000000 if hero else rng.randrange(4, 16) * 1000000, 25000,
                                6500000 if hero else None)
            add_cov("CONTENTS", rng.randrange(1, 4) * 1000000, 10000, None)
            if hero or rng.random() < 0.6:
                add_cov("BUSINESS_INTERRUPTION", rng.randrange(2, 6) * 1000000, 50000, None)
        elif lob == "MOTOR":
            first_cov = add_cov("MOTOR_OWN_DAMAGE", None, 1000, 250000)
            add_cov("MOTOR_TPL", 5000000, None, None)
        elif lob == "GENERAL_LIABILITY":
            first_cov = add_cov("PUBLIC_LIABILITY", 5000000, 5000, None)
        else:
            first_cov = add_cov("CARGO", 2000000, 10000, None)

        obj_n[0] += 1
        objects.append({"insured_object_id": f"obj_{obj_n[0]:04d}", "policy_id": policy_id,
                        "insured_object_type_code": OBJ_TYPE[lob],
                        "description": OBJ_DESC[lob][0] if hero else rng.choice(OBJ_DESC[lob]),
                        "country_code": country,
                        "postcode": "M3 5EN" if hero else (rng.choice(POSTCODES[country]) if lob == "COMMERCIAL_PROPERTY" else None)})

        written = 120000.00 if hero else round(BASE_PREMIUM[lob] * rng.uniform(0.7, 1.3), 2)

        def add_prm(ptype, amount, when):
            prm_n[0] += 1
            premiums.append({"premium_transaction_id": f"prm_{prm_n[0]:04d}", "policy_id": policy_id,
                             "coverage_id": None, "premium_transaction_type_code": ptype,
                             "amount": amount, "currency_code": ccy, "transaction_date": when,
                             "source_system_code": "PAS_CORE"})

        add_prm("WRITTEN", written, inception)
        if not hero and not cancelled and n % 7 == 0:
            add_prm("ADJUSTMENT", round(written * rng.uniform(0.04, 0.10), 2),
                    inception + timedelta(days=rng.randint(90, 240)))
        if cancelled:
            add_prm("RETURN", round(-written * 0.4, 2), inception + timedelta(days=rng.randint(120, 300)))

        # claims: the hero fire, plus a spread across the older book
        makes_claim = hero or (status in ("EXPIRED", "IN_FORCE") and n % 3 == 1 and len(claims) < 18)
        if makes_claim:
            c = len(claims) + 1
            claim_id = f"clm_{c:04d}"
            if hero:
                cause, loss = "FIRE", date(2026, 3, 14)
            else:
                cause = rng.choice(COL_BY_LOB[lob])
                last_loss = min(expiry, TODAY - timedelta(days=30))
                span = max((last_loss - inception).days, 1)
                loss = inception + timedelta(days=rng.randrange(span))
            reported = date(2026, 3, 16) if hero else loss + timedelta(days=rng.randint(2, 21))
            if hero:
                cstatus = "OPEN"
            elif c % 9 == 0:
                cstatus = "DECLINED"
            elif uwy == 2024:
                cstatus = "REOPENED" if c % 8 == 0 else "CLOSED"
            else:
                cstatus = rng.choice(["OPEN", "CLOSED"])
            claims.append({"claim_id": claim_id, "policy_id": policy_id, "coverage_id": first_cov,
                           "claim_number": f"CLM-{loss.year}-{c:06d}", "claim_status_code": cstatus,
                           "cause_of_loss_code": cause, "loss_date": loss, "reported_date": reported,
                           "description": "Fire in the main warehouse; sprinkler activation and smoke damage across two floors." if hero else None,
                           "source_system_code": "CLM_CORE"})
            add_role("CLAIMANT", PERSONS[c % 3][0] if (lob == "MOTOR" and c % 2 == 0) else org,
                     reported, claim_id=claim_id)

            def add_ctx(ttype, amount, when):
                ctx_n[0] += 1
                claim_txs.append({"claim_transaction_id": f"ctx_{ctx_n[0]:04d}", "claim_id": claim_id,
                                  "claim_transaction_type_code": ttype, "amount": amount,
                                  "currency_code": ccy, "transaction_date": when,
                                  "source_system_code": "CLM_CORE"})

            reserve = 450000.00 if hero else round(written * rng.uniform(0.5, 3.0), 2)
            add_ctx("CASE_RESERVE_MOVEMENT", reserve, reported + timedelta(days=3))
            if hero:
                add_ctx("INDEMNITY_PAYMENT", 180000.00, date(2026, 5, 20))
                add_ctx("EXPENSE_PAYMENT", 12000.00, date(2026, 4, 28))
                add_ctx("CASE_RESERVE_MOVEMENT", -180000.00, date(2026, 5, 20))
            elif cstatus == "DECLINED":
                add_ctx("CASE_RESERVE_MOVEMENT", -reserve, reported + timedelta(days=45))
            elif cstatus in ("CLOSED", "REOPENED"):
                paid = round(reserve * rng.uniform(0.55, 0.95), 2)
                pay_day = reported + timedelta(days=rng.randint(60, 200))
                add_ctx("INDEMNITY_PAYMENT", paid, pay_day)
                add_ctx("EXPENSE_PAYMENT", round(reserve * rng.uniform(0.03, 0.08), 2), pay_day)
                add_ctx("CASE_RESERVE_MOVEMENT", -reserve + (0 if cstatus == "REOPENED" else 0), pay_day)
                if cstatus == "REOPENED":
                    add_ctx("CASE_RESERVE_MOVEMENT", round(reserve * 0.4, 2), pay_day + timedelta(days=90))
                if c % 5 == 0:
                    add_ctx("RECOVERY", round(-paid * rng.uniform(0.10, 0.20), 2), pay_day + timedelta(days=60))
            else:  # OPEN
                if rng.random() < 0.5:
                    add_ctx("EXPENSE_PAYMENT", round(reserve * 0.04, 2), reported + timedelta(days=30))

    treaty = [{"treaty_id": "trt_0001", "treaty_reference": "TR-QS-PROP-2026",
               "treaty_type_code": "QUOTA_SHARE", "line_of_business_code": "COMMERCIAL_PROPERTY",
               "underwriting_year": 2026, "inception_date": date(2026, 1, 1),
               "expiry_date": date(2026, 12, 31), "cession_rate": 0.3000,
               "currency_code": "GBP", "source_system_code": "RI_CORE"}]
    add_role("CEDANT", "Bricksurance SE", date(2026, 1, 1), treaty_id="trt_0001")
    add_role("REINSURER", "Bricksurance Re AG", date(2026, 1, 1), treaty_id="trt_0001")

    ces = 0
    for p in policies:
        if p["line_of_business_code"] == "COMMERCIAL_PROPERTY" and p["underwriting_year"] == 2026:
            ces += 1
            cessions.append({"cession_id": f"ces_{ces:04d}", "policy_id": p["policy_id"],
                             "coverage_id": None, "treaty_id": "trt_0001", "ceded_share": 0.3000})

    return {"party": parties, "party_role": roles, "policy": policies, "coverage": coverages,
            "insured_object": objects, "premium_transaction": premiums, "claim": claims,
            "claim_transaction": claim_txs, "treaty": treaty, "cession": cessions}


def main():
    entities = load_entities()
    binding = load_binding()
    world = build_world()
    # parents before children, so the file can also run on enforcing platforms
    order = ["party", "policy", "coverage", "insured_object", "premium_transaction",
             "claim", "claim_transaction", "treaty", "cession", "party_role"]
    header = ("-- Generated by tools/generate_demo_data.py — deterministic synthetic demo data.\n"
              "-- Bricksurance SE is fictional; every party, policy and amount here is synthetic.\n\n")
    stmts = [insert(binding, entities[name], world[name]) for name in order]
    OUT.write_text(header + "\n\n".join(stmts) + "\n")
    counts = ", ".join(f"{k}={len(v)}" for k, v in world.items())
    print(f"Wrote {OUT.relative_to(ROOT)} ({counts})")


if __name__ == "__main__":
    main()
