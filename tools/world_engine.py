#!/usr/bin/env python3
"""The Bricksurance World Engine.

Generates ONE deterministic, coherent synthetic world across every domain of
the model — P&C (commercial + motor), life, reinsurance, finance — and emits
it as build/databricks/95_demo_data.sql (INSERT OVERWRITE, so reruns are
idempotent). Run AFTER tools/generate.py.

Coherence is the point: quotes convert into the policies that carry the
claims that are ceded to the treaties that were bound from submissions; the
finance domain's published case-reserve totals tie out to the sum of claim
transactions; life valuation runs reference the approved assumption sets and
the active scenario set. Change the world, and every surface changes together.

Scale: --scale multiplies book volumes (policies, quotes, cohort sizes).
Semantics never change with scale; the SACRED HEROES exist at every scale:
  - POL-2026-000001 (Aldgate Mills Ltd) -> fire claim CLM-2026-000001
    (450k reserved, 180k paid, 270k outstanding derived)
    -> 30% ceded to TR-QS-PROP-2026 -> quote QUO-2026-000001 it converted from
  - SUB-2026-000001 (BOUND) -> TR-QS-PROP-2026

Usage:
    uv run --with pyyaml tools/world_engine.py [--scale 1.0]
"""

import argparse
import random
from datetime import date, datetime, timedelta
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
    if isinstance(v, datetime):
        return f"TIMESTAMP '{v.strftime('%Y-%m-%d %H:%M:%S')}'"
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


# ---------------------------------------------------------------- fixed cast

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
CEDANTS = [("Meridian Mutual Insurance", "GB"), ("Nordlicht Versicherung AG", "DE")]

CCY = {"GB": "GBP", "IE": "EUR", "DE": "EUR", "FR": "EUR", "CH": "CHF", "US": "USD"}
LOB_MIX = [("COMMERCIAL_PROPERTY", 0.4), ("MOTOR", 0.3),
           ("GENERAL_LIABILITY", 0.2), ("MARINE_CARGO", 0.1)]
BASE_PREMIUM = {"COMMERCIAL_PROPERTY": 85000, "MOTOR": 18000,
                "GENERAL_LIABILITY": 22000, "MARINE_CARGO": 30000}
OBJ_TYPE = {"COMMERCIAL_PROPERTY": "BUILDING", "MOTOR": "VEHICLE",
            "GENERAL_LIABILITY": "LIABILITY_EXPOSURE", "MARINE_CARGO": "CARGO_SHIPMENT"}
OBJ_DESC = {"COMMERCIAL_PROPERTY": ["Warehouse and distribution centre", "Office building",
                                    "Factory unit", "Retail premises"],
            "MOTOR": ["Fleet of delivery vans", "Company car fleet", "Mixed commercial fleet"],
            "GENERAL_LIABILITY": ["Business operations at head office",
                                  "Manufacturing operations", "Hospitality operations"],
            "MARINE_CARGO": ["Machinery consignments, EU routes",
                             "Pharmaceutical consignments, transatlantic"]}
POSTCODES = {"GB": ["M3 5EN", "LS1 4AP", "B4 7DA", "G2 1AL", "BS1 6QF"],
             "DE": ["20457", "60311", "80331"], "IE": ["D02 X285"],
             "FR": ["13002", "75008"], "CH": ["8005"], "US": ["33131", "94105"]}
COL_BY_LOB = {"COMMERCIAL_PROPERTY": ["FIRE", "FLOOD", "STORM", "WATER_DAMAGE"],
              "MOTOR": ["COLLISION", "COLLISION", "THEFT"],
              "GENERAL_LIABILITY": ["LIABILITY_INCIDENT"],
              "MARINE_CARGO": ["THEFT", "WATER_DAMAGE"]}
VEHICLES = [("Ford", "Transit"), ("VW", "Crafter"), ("Mercedes-Benz", "Sprinter"),
            ("Toyota", "Hilux"), ("Iveco", "Daily")]


class World:
    def __init__(self, scale):
        self.scale = scale
        self.t = {}          # table -> rows
        self.counters = {}
        for name in ("party", "party_role", "policy", "quote", "endorsement", "coverage",
                     "insured_object", "vehicle", "premium_transaction", "claim",
                     "claim_transaction", "treaty", "treaty_layer", "submission", "cession",
                     "cat_event", "event_loss", "model_point", "assumption_set",
                     "scenario_set", "valuation_run", "valuation_run_assumption",
                     "valuation_result", "product", "product_coverage",
                     "underwriting_question", "appetite_rule", "underwriting_decision",
                     "commission_transaction", "complaint", "document", "business_event",
                     "contact_point", "consent", "data_subject_request", "fraud_signal",
                     "expense_transaction", "receivable_transaction",
                     "legal_entity", "chart_of_account", "accounting_period", "statement_line",
                     "journal", "journal_line", "investment_holding", "investment_transaction",
                     "tax_transaction", "financial_plan", "fx_rate",
                     "contract_group", "csm_movement"):
            self.t[name] = []

    def n(self, base):
        return max(1, round(base * self.scale))

    def nid(self, prefix):
        self.counters[prefix] = self.counters.get(prefix, 0) + 1
        return f"{prefix}_{self.counters[prefix]:04d}"

    def add(self, table, **row):
        self.t[table].append(row)
        return row


def build_world(scale):
    w = World(scale)
    pid = {}

    for name, country in GROUP + BROKERS + CEDANTS + ORGS + PERSONS:
        party_type = "PERSON" if (name, country) in PERSONS else "ORGANISATION"
        key = w.nid("pty")
        pid[name] = key
        w.add("party", party_id=key, party_type_code=party_type, name=name,
              country_code=country, source_system_code="DATA_CORE")

    def add_role(role_type, party, start, **ctx):
        w.add("party_role", party_role_id=w.nid("prl"), party_id=pid[party],
              party_role_type_code=role_type, start_date=start, end_date=None, **ctx)

    def add_event(etype, subject_entity, subject_id, when, channel=None, payload=None):
        w.add("business_event", business_event_id=w.nid("evt"),
              business_event_type_code=etype, subject_entity=subject_entity,
              subject_id=subject_id, occurred_at=when, channel_code=channel,
              payload=payload, source_system_code="PAS_CORE")

    # ------------------------------------------------------ machine agent party
    AGENT_NAME = "Athena Procurement Agent v2 (for Kestrel Foods Group)"
    key = w.nid("pty")
    pid[AGENT_NAME] = key
    w.add("party", party_id=key, party_type_code="MACHINE_AGENT", name=AGENT_NAME,
          country_code="GB", source_system_code="DATA_CORE")

    # ------------------------------------------------------ legal-entity structure
    # Group holding consolidates three regulated subsidiaries. Presentation
    # currency (group) is EUR; subsidiaries have their own functional currency.
    w.add("legal_entity", legal_entity_id="le_group", name="Bricksurance Group NV",
          legal_entity_type_code="GROUP_HOLDING", parent_legal_entity_id=None,
          country_code="DE", functional_currency_code="EUR",
          lei="5299000BRICKGROUP0001", source_system_code="DATA_CORE")
    ENTITIES = [
        ("le_se", "Bricksurance SE", "INSURANCE_SUBSIDIARY", "DE", "EUR", "5299000BRICKSE00001"),
        ("le_re", "Bricksurance Re AG", "REINSURANCE_SUBSIDIARY", "CH", "CHF", "5299000BRICKRE00001"),
        ("le_life", "Bricksurance Life Ltd", "INSURANCE_SUBSIDIARY", "GB", "GBP", "5299000BRICKLIFE001"),
    ]
    for leid, nm, typ, ctry, ccy, lei in ENTITIES:
        w.add("legal_entity", legal_entity_id=leid, name=nm, legal_entity_type_code=typ,
              parent_legal_entity_id="le_group", country_code=ctry,
              functional_currency_code=ccy, lei=lei, source_system_code="DATA_CORE")
    # the direct P&C book is written by Bricksurance SE
    CARRIER = "le_se"

    # ------------------------------------------------------ product catalog
    PRODUCTS = [
        ("CP-STD", "Commercial Property Standard", "COMMERCIAL_PROPERTY", 0.014,
         ["BUILDINGS", "CONTENTS", "BUSINESS_INTERRUPTION"],
         "flood in coastal postcode districts", 10000000, 25000000),
        ("MF-STD", "Motor Fleet", "MOTOR", 0.031,
         ["MOTOR_OWN_DAMAGE", "MOTOR_TPL"],
         "use for racing, pace-making or speed testing", 2000000, None),
        ("SME-LIA", "SME Combined Liability", "GENERAL_LIABILITY", 0.0044,
         ["PUBLIC_LIABILITY"], "asbestos-related injury or damage", 5000000, None),
        ("MC-STD", "Marine Cargo", "MARINE_CARGO", 0.015,
         ["CARGO"], "war, strikes and confiscation except as endorsed", 2000000, None),
    ]
    product_by_lob, appetite_within = {}, {}
    for code, name, lob, rate, covs, exclusion, within_max, refer_max in PRODUCTS:
        p = w.add("product", product_id=w.nid("prd"), product_code=code, name=name,
                  line_of_business_code=lob, product_status_code="ACTIVE",
                  base_rate=rate, currency_code="GBP", source_system_code="PAS_CORE")
        product_by_lob[lob] = p
        for i, cov in enumerate(covs):
            w.add("product_coverage", product_coverage_id=w.nid("pcv"),
                  product_id=p["product_id"], coverage_type_code=cov,
                  default_limit_amount=5000000.00, default_deductible_amount=10000.00,
                  optional=i > 0)
        for i, (q, a_type) in enumerate([
                ("What is the total sum insured requested?", "number"),
                ("Any claims in the last five years?", "boolean"),
                ("Country and postcode of the main risk location?", "text")]):
            w.add("underwriting_question", underwriting_question_id=w.nid("uwq"),
                  product_id=p["product_id"], question_order=i + 1,
                  question_text=q, answer_type=a_type, required=i < 2)
        r1 = w.add("appetite_rule", appetite_rule_id=w.nid("apr"),
                   product_id=p["product_id"], line_of_business_code=lob, rule_order=10,
                   description=f"{name}: risks up to the automatic authority limit are within appetite.",
                   max_sum_insured=float(within_max), country_code="GB",
                   appetite_effect_code="WITHIN_APPETITE",
                   effective_from=date(2026, 1, 1), effective_to=None)
        appetite_within[lob] = r1
        if refer_max:
            w.add("appetite_rule", appetite_rule_id=w.nid("apr"),
                  product_id=p["product_id"], line_of_business_code=lob, rule_order=20,
                  description=f"{name}: between authority limit and line capacity requires underwriter review.",
                  max_sum_insured=float(refer_max), country_code=None,
                  appetite_effect_code="REFER",
                  effective_from=date(2026, 1, 1), effective_to=None)
        w.add("appetite_rule", appetite_rule_id=w.nid("apr"),
              product_id=p["product_id"], line_of_business_code=lob, rule_order=30,
              description=f"{name}: above line capacity, or outside written geographies, is out of appetite.",
              max_sum_insured=None, country_code=None,
              appetite_effect_code="OUT_OF_APPETITE",
              effective_from=date(2026, 1, 1), effective_to=None)
        w.add("document", document_id=w.nid("doc"), document_type_code="POLICY_WORDING",
              title=f"{name} — Policy Wording v1", product_id=p["product_id"],
              policy_id=None, claim_id=None, submission_id=None,
              extracted_text=(
                  f"{name} POLICY WORDING. Section A - Insuring clause: the insurer agrees to "
                  f"indemnify the insured for {', '.join(c.replace('_', ' ').lower() for c in covs)} "
                  f"as specified in the schedule, subject to the limits and deductibles stated. "
                  f"Section B - Exclusions: this policy does not cover loss arising from {exclusion}; "
                  f"nor liability assumed under contract beyond that implied by law; nor loss caused "
                  f"by wilful misconduct of the insured. Section C - Conditions: claims must be "
                  f"notified without undue delay; the insured must take reasonable precautions; "
                  f"cover is subject to the sanctions limitation clause. Section D - Claims: "
                  f"first notification through any channel including the digital FNOL service; "
                  f"the insurer may appoint a loss adjuster above the delegated settlement limit."),
              volume_path=None, created_date=date(2026, 1, 1), source_system_code="PAS_CORE")

    POSTCODE_GEO = {"M3 5EN": (53.4839, -2.2521), "LS1 4AP": (53.7975, -1.5528),
                    "B4 7DA": (52.4841, -1.8935), "G2 1AL": (55.8621, -4.2542),
                    "BS1 6QF": (51.4500, -2.5967)}
    last_policy_by_key = {}

    # ---------------------------------------------------------- P&C book
    n_policies = w.n(60)
    lobs = []
    for lob, share in LOB_MIX:
        lobs += [lob] * round(n_policies * share)
    lobs = (lobs + ["COMMERCIAL_PROPERTY"] * n_policies)[:n_policies]
    rng.shuffle(lobs)
    lobs[0] = "COMMERCIAL_PROPERTY"          # the hero
    uwy_plan = [2024, 2025, 2026] * n_policies

    for i in range(n_policies):
        num = i + 1
        hero = i == 0
        uwy = 2026 if hero else uwy_plan[i]
        lob = lobs[i]
        org, country = ORGS[0] if hero else ORGS[i % len(ORGS)]
        ccy = CCY[country]
        inception = date(2026, 1, 1) if hero else date(uwy, rng.randint(1, 12), rng.randint(1, 28))
        expiry = inception + timedelta(days=364)
        cancelled = (not hero) and uwy == 2025 and num % 17 == 0
        if cancelled:
            status = "CANCELLED"
        elif expiry < TODAY:
            status = "EXPIRED"
        elif inception > TODAY:
            status = "BOUND"
        else:
            status = "IN_FORCE"
        policy_id = w.nid("pol")
        policy_number = f"POL-{uwy}-{num:06d}"
        prev = last_policy_by_key.get((org, lob))
        renews = prev["policy_id"] if prev and prev["underwriting_year"] == uwy - 1 else None
        policy_row = w.add("policy", policy_id=policy_id, policy_number=policy_number,
                           source_system_code="PAS_CORE", line_of_business_code=lob,
                           policy_status_code=status, inception_date=inception,
                           expiry_date=expiry, underwriting_year=uwy, currency_code=ccy,
                           renews_policy_id=renews, legal_entity_id=CARRIER)
        last_policy_by_key[(org, lob)] = policy_row

        written = 120000.00 if hero else round(BASE_PREMIUM[lob] * rng.uniform(0.7, 1.3), 2)
        has_broker = num % 2 == 0
        channel = "BROKER" if has_broker else "DIRECT"

        # every policy converted from exactly one quote, with a recorded decision
        quote = w.add("quote", quote_id=w.nid("quo"), quote_number=f"QUO-{uwy}-{num:06d}",
                      policy_id=policy_id, line_of_business_code=lob,
                      quote_status_code="CONVERTED",
                      quote_date=inception - timedelta(days=14 if hero else rng.randint(14, 45)),
                      requested_inception_date=inception, quoted_gross_premium=written,
                      currency_code=ccy, source_system_code="PAS_CORE",
                      product_id=product_by_lob[lob]["product_id"],
                      distribution_channel_code=channel)
        by_agent = (not hero) and num % 3 == 0
        w.add("underwriting_decision", underwriting_decision_id=w.nid("uwd"),
              quote_id=quote["quote_id"], underwriting_decision_type_code="ACCEPT",
              appetite_rule_id=appetite_within[lob]["appetite_rule_id"],
              decided_by="bricksurance-uw-agent v1" if by_agent else "U. Marsh (senior underwriter)",
              decided_by_agent=by_agent,
              decided_at=datetime.combine(quote["quote_date"], datetime.min.time()).replace(hour=10),
              rationale="Within appetite and automatic authority." if by_agent else None)
        add_event("QUOTE_REQUESTED", "quote", quote["quote_id"],
                  datetime.combine(quote["quote_date"], datetime.min.time()).replace(hour=9),
                  channel=channel)
        add_event("POLICY_BOUND", "policy", policy_id,
                  datetime.combine(inception, datetime.min.time()).replace(hour=12),
                  channel=channel)

        add_role("POLICYHOLDER", org, inception, policy_id=policy_id)
        add_role("INSURED", org, inception, policy_id=policy_id)
        if has_broker:
            broker_name = BROKERS[(num // 2) % 2][0]
            add_role("BROKER", broker_name, inception, policy_id=policy_id)
            rate = 0.175
            w.add("commission_transaction", commission_transaction_id=w.nid("cmt"),
                  policy_id=policy_id, party_id=pid[broker_name],
                  commission_type_code="RENEWAL" if renews else "NEW_BUSINESS",
                  rate=rate, amount=round(written * rate, 2), currency_code=ccy,
                  transaction_date=inception, source_system_code="PAS_CORE")
            if cancelled:
                w.add("commission_transaction", commission_transaction_id=w.nid("cmt"),
                      policy_id=policy_id, party_id=pid[broker_name],
                      commission_type_code="CLAWBACK", rate=rate,
                      amount=round(-written * rate * 0.4, 2), currency_code=ccy,
                      transaction_date=inception + timedelta(days=150),
                      source_system_code="PAS_CORE")

        def add_cov(ctype, limit, ded, sum_insured):
            row = w.add("coverage", coverage_id=w.nid("cov"), policy_id=policy_id,
                        coverage_type_code=ctype, limit_amount=limit,
                        deductible_amount=ded, sum_insured_amount=sum_insured)
            return row["coverage_id"]

        if lob == "COMMERCIAL_PROPERTY":
            first_cov = add_cov("BUILDINGS", 8000000 if hero else rng.randrange(4, 16) * 1000000,
                                25000, 6500000 if hero else None)
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

        pc = "M3 5EN" if hero else (rng.choice(POSTCODES[country])
                                    if lob == "COMMERCIAL_PROPERTY" else None)
        geo = POSTCODE_GEO.get(pc, (None, None))
        obj = w.add("insured_object", insured_object_id=w.nid("obj"), policy_id=policy_id,
                    insured_object_type_code=OBJ_TYPE[lob],
                    description=OBJ_DESC[lob][0] if hero else rng.choice(OBJ_DESC[lob]),
                    country_code=country, postcode=pc,
                    latitude=geo[0], longitude=geo[1])
        if lob == "MOTOR":
            make, model = rng.choice(VEHICLES)
            w.add("vehicle", vehicle_id=w.nid("veh"),
                  insured_object_id=obj["insured_object_id"],
                  registration_number=f"B{chr(65 + num % 26)}{num % 100:02d} "
                                      f"{chr(65 + (num * 7) % 26)}{chr(65 + (num * 3) % 26)}"
                                      f"{chr(65 + (num * 5) % 26)}",
                  make=make, model=model, year_of_manufacture=uwy - rng.randint(0, 6))

        def add_prm(ptype, amount, when):
            w.add("premium_transaction", premium_transaction_id=w.nid("prm"),
                  policy_id=policy_id, coverage_id=None, premium_transaction_type_code=ptype,
                  amount=amount, currency_code=ccy, transaction_date=when,
                  source_system_code="PAS_CORE")

        add_prm("WRITTEN", written, inception)
        if not hero and not cancelled and num % 7 == 0:
            when = inception + timedelta(days=rng.randint(90, 240))
            add_prm("ADJUSTMENT", round(written * rng.uniform(0.04, 0.10), 2), when)
            w.add("endorsement", endorsement_id=w.nid("end"), policy_id=policy_id,
                  endorsement_type_code="SUM_INSURED_CHANGE" if num % 14 == 0 else "MID_TERM_ADJUSTMENT",
                  effective_date=when, description="Declared values revised mid-term.",
                  source_system_code="PAS_CORE")
        if cancelled:
            when = inception + timedelta(days=rng.randint(120, 300))
            add_prm("RETURN", round(-written * 0.4, 2), when)
            w.add("endorsement", endorsement_id=w.nid("end"), policy_id=policy_id,
                  endorsement_type_code="CANCELLATION", effective_date=when,
                  description="Policy cancelled at the policyholder's request.",
                  source_system_code="PAS_CORE")

        # claims across the book, capped
        makes_claim = hero or (status in ("EXPIRED", "IN_FORCE") and num % 3 == 1
                               and len(w.t["claim"]) < w.n(18))
        if makes_claim:
            c = len(w.t["claim"]) + 1
            claim_id = w.nid("clm")
            if hero:
                cause, loss = "FIRE", date(2026, 3, 14)
            else:
                cause = rng.choice(COL_BY_LOB[lob])
                last_loss = min(expiry, TODAY - timedelta(days=30))
                loss = inception + timedelta(days=rng.randrange(max((last_loss - inception).days, 1)))
            reported = date(2026, 3, 16) if hero else loss + timedelta(days=rng.randint(2, 21))
            if hero:
                cstatus = "OPEN"
            elif c % 9 == 0:
                cstatus = "DECLINED"
            elif uwy == 2024:
                cstatus = "REOPENED" if c % 8 == 0 else "CLOSED"
            else:
                cstatus = rng.choice(["OPEN", "CLOSED"])
            w.add("claim", claim_id=claim_id, policy_id=policy_id, coverage_id=first_cov,
                  claim_number=f"CLM-{loss.year}-{c:06d}", claim_status_code=cstatus,
                  cause_of_loss_code=cause, loss_date=loss, reported_date=reported,
                  description=("Fire in the main warehouse; sprinkler activation and smoke "
                               "damage across two floors.") if hero else None,
                  source_system_code="CLM_CORE")
            add_role("CLAIMANT",
                     PERSONS[c % 3][0] if (lob == "MOTOR" and c % 2 == 0) else org,
                     reported, claim_id=claim_id)
            add_event("FNOL", "claim", claim_id,
                      datetime.combine(reported, datetime.min.time()).replace(hour=8),
                      channel="DIRECT")

            def add_ctx(ttype, amount, when):
                w.add("claim_transaction", claim_transaction_id=w.nid("ctx"), claim_id=claim_id,
                      claim_transaction_type_code=ttype, amount=amount, currency_code=ccy,
                      transaction_date=when, source_system_code="CLM_CORE")
                if ttype == "INDEMNITY_PAYMENT":
                    add_event("CLAIM_PAYMENT", "claim", claim_id,
                              datetime.combine(when, datetime.min.time()).replace(hour=15),
                              payload=f'{{"amount": {amount}, "currency": "{ccy}"}}')

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
                add_ctx("CASE_RESERVE_MOVEMENT", -reserve, pay_day)
                if cstatus == "REOPENED":
                    add_ctx("CASE_RESERVE_MOVEMENT", round(reserve * 0.4, 2),
                            pay_day + timedelta(days=90))
                if c % 5 == 0:
                    add_ctx("RECOVERY", round(-paid * rng.uniform(0.10, 0.20), 2),
                            pay_day + timedelta(days=60))
            else:
                if rng.random() < 0.5:
                    add_ctx("EXPENSE_PAYMENT", round(reserve * 0.04, 2),
                            reported + timedelta(days=30))

    # the rest of the quote funnel: quotes that never became policies
    lost = ["OFFERED", "REJECTED_BY_CUSTOMER", "EXPIRED", "DECLINED_BY_INSURER", "OPEN"]
    lost_channels = ["AGGREGATOR", "BROKER", "DIRECT", "AGGREGATOR", "DIRECT"]
    for k in range(w.n(25)):
        lob = rng.choice([l for l, _ in LOB_MIX])
        org, country = ORGS[(k * 3) % len(ORGS)]
        status = lost[k % len(lost)]
        q = w.add("quote", quote_id=w.nid("quo"), quote_number=f"QUO-2026-{200 + k:06d}",
                  policy_id=None, line_of_business_code=lob, quote_status_code=status,
                  quote_date=date(2026, 1, 5) + timedelta(days=rng.randint(0, 150)),
                  requested_inception_date=None,
                  quoted_gross_premium=None if status == "OPEN"
                  else round(BASE_PREMIUM[lob] * rng.uniform(0.7, 1.3), 2),
                  currency_code=CCY[country], source_system_code="PAS_CORE",
                  product_id=product_by_lob[lob]["product_id"],
                  distribution_channel_code=lost_channels[k % len(lost_channels)])
        add_event("QUOTE_REQUESTED", "quote", q["quote_id"],
                  datetime.combine(q["quote_date"], datetime.min.time()).replace(hour=11),
                  channel=q["distribution_channel_code"])
        if status == "DECLINED_BY_INSURER":
            w.add("underwriting_decision", underwriting_decision_id=w.nid("uwd"),
                  quote_id=q["quote_id"], underwriting_decision_type_code="DECLINE",
                  appetite_rule_id=None, decided_by="U. Marsh (senior underwriter)",
                  decided_by_agent=False,
                  decided_at=datetime.combine(q["quote_date"], datetime.min.time()).replace(hour=16),
                  rationale="Outside appetite for the declared trade and claims history.")

    # the agentic buyer: a MACHINE_AGENT party quoting machine-to-machine
    agent_cases = [("QUO-2026-000901", "COMMERCIAL_PROPERTY", 8000000.00, "OFFERED",
                    "ACCEPT", "Within appetite; automatic authority; indicative premium returned."),
                   ("QUO-2026-000902", "COMMERCIAL_PROPERTY", 30000000.00, "DECLINED_BY_INSURER",
                    "DECLINE", "Requested sum insured exceeds line capacity - out of appetite."),
                   ("QUO-2026-000903", "COMMERCIAL_PROPERTY", 18000000.00, "OPEN",
                    "REFER", "Between automatic authority and line capacity - referred to a human underwriter.")]
    for qnum, lob, si, qstatus, decision, why in agent_cases:
        q = w.add("quote", quote_id=w.nid("quo"), quote_number=qnum, policy_id=None,
                  line_of_business_code=lob, quote_status_code=qstatus,
                  quote_date=date(2026, 6, 24), requested_inception_date=date(2026, 8, 1),
                  quoted_gross_premium=round(si * 0.014, 2) if decision == "ACCEPT" else None,
                  currency_code="GBP", source_system_code="PAS_CORE",
                  product_id=product_by_lob[lob]["product_id"],
                  distribution_channel_code="MACHINE_AGENT")
        add_role("BUYER_AGENT", AGENT_NAME, q["quote_date"], quote_id=q["quote_id"])
        w.add("underwriting_decision", underwriting_decision_id=w.nid("uwd"),
              quote_id=q["quote_id"], underwriting_decision_type_code=decision,
              appetite_rule_id=appetite_within[lob]["appetite_rule_id"] if decision == "ACCEPT" else None,
              decided_by="bricksurance-uw-agent v1", decided_by_agent=True,
              decided_at=datetime(2026, 6, 24, 9, 42), rationale=why)
        add_event("QUOTE_REQUESTED", "quote", q["quote_id"],
                  datetime(2026, 6, 24, 9, 41), channel="MACHINE_AGENT",
                  payload=f'{{"sum_insured": {si}, "requested_by": "{AGENT_NAME}"}}')

    # ------------------------------------------------ reserving development
    # A credible claim-development history for reserving: enough claims across
    # accident years 2019-2026, each developing over time (reserve set at
    # report, payments stepping down the reserve across development lags), so
    # paid/incurred triangles actually develop. Every movement is an ordinary
    # claim_transaction - the reserving triangle is a pure semantic layer over
    # these, reconciling by construction, and the ledger auto-posts them.
    #
    # Reserving lines and their expected ultimate severity + development speed.
    # dev_pattern = cumulative-paid fraction by development year (year 0..5);
    # slower-developing lines (liability) pay out over more years than property.
    RSV_LINES = {
        "COMMERCIAL_PROPERTY": (95000, [0.35, 0.70, 0.88, 0.96, 1.00, 1.00]),
        "GENERAL_LIABILITY":   (60000, [0.10, 0.30, 0.55, 0.75, 0.90, 1.00]),
        "MOTOR":               (14000, [0.55, 0.85, 0.95, 0.99, 1.00, 1.00]),
        "MARINE_CARGO":        (40000, [0.45, 0.80, 0.93, 0.99, 1.00, 1.00]),
    }
    RSV_CARRIER = CARRIER
    rsv_org, rsv_country = ORGS[0]
    # ~n_dev claims per accident year 2019..2026; older years are fully/near
    # developed, recent years still developing - exactly what a triangle shows.
    for ay in range(2019, 2027):
        n_ay = w.n(14)
        for k in range(n_ay):
            lob = list(RSV_LINES)[(ay + k) % len(RSV_LINES)]
            sev, pattern = RSV_LINES[lob]
            ccy = "GBP"
            # a light historical policy so the claim has a real parent
            hpid = w.nid("pol")
            hnum = f"POL-{ay}-{900000 + k:06d}"
            inc = date(ay, 1 + (k % 12), 1 + (k % 28))
            w.add("policy", policy_id=hpid, policy_number=hnum,
                  source_system_code="PAS_CORE", line_of_business_code=lob,
                  policy_status_code="EXPIRED", inception_date=inc,
                  expiry_date=inc + timedelta(days=364), underwriting_year=ay,
                  currency_code=ccy, renews_policy_id=None, legal_entity_id=RSV_CARRIER)
            add_role("POLICYHOLDER", rsv_org, inc, policy_id=hpid)
            # the claim: loss in the accident year, reported with a short lag
            ult = round(sev * rng.uniform(0.5, 2.2), 2)          # ultimate incurred
            # written premium sized so the historical book runs at a realistic
            # loss ratio (~55-70%): premium = ultimate / target LR. Without this
            # the reserving claims would dwarf earned premium and blow up the
            # combined ratio. Booked once at inception, as real written premium.
            target_lr = rng.uniform(0.55, 0.70)
            w.add("premium_transaction", premium_transaction_id=w.nid("prm"),
                  policy_id=hpid, coverage_id=None,
                  premium_transaction_type_code="WRITTEN",
                  amount=round(ult / target_lr, 2), currency_code=ccy,
                  transaction_date=inc, source_system_code="PAS_CORE")
            loss = date(ay, 1 + ((k * 7) % 12), 1 + ((k * 5) % 28))
            reported = loss + timedelta(days=rng.randint(5, 60))
            years_dev = 2026 - ay
            fully = years_dev >= 5 or (k % 6 != 0)   # most claims closed by now
            cstatus = "CLOSED" if (fully and years_dev >= 1) else "OPEN"
            c = len(w.t["claim"]) + 1
            claim_id = w.nid("clm")
            w.add("claim", claim_id=claim_id, policy_id=hpid, coverage_id=None,
                  claim_number=f"CLM-{ay}-{c:06d}", claim_status_code=cstatus,
                  cause_of_loss_code=rng.choice(COL_BY_LOB[lob]),
                  loss_date=loss, reported_date=reported, description=None,
                  source_system_code="CLM_CORE")

            def rctx(ttype, amount, when):
                w.add("claim_transaction", claim_transaction_id=w.nid("ctx"),
                      claim_id=claim_id, claim_transaction_type_code=ttype,
                      amount=round(amount, 2), currency_code=ccy,
                      transaction_date=when, source_system_code="CLM_CORE")

            # initial case reserve at the ultimate estimate, at report date
            rctx("CASE_RESERVE_MOVEMENT", ult, reported)
            # pay down across development years per the pattern, up to 'now'
            prev_cum = 0.0
            for dy, cum_frac in enumerate(pattern):
                pay_date = date(min(ay + dy, 2026),
                                ((loss.month - 1 + (dy * 2)) % 12) + 1, 15)
                if pay_date > TODAY:
                    break
                cum_paid = ult * cum_frac
                step = cum_paid - prev_cum
                if step <= 0:
                    continue
                indem = round(step * 0.92, 2)
                expense = round(step * 0.08, 2)
                rctx("INDEMNITY_PAYMENT", indem, pay_date)
                rctx("EXPENSE_PAYMENT", expense, pay_date)
                # release reserve by the indemnity paid this step
                rctx("CASE_RESERVE_MOVEMENT", -indem, pay_date)
                prev_cum = cum_paid
                # occasional subrogation recovery on property/motor
                if lob in ("COMMERCIAL_PROPERTY", "MOTOR") and dy == 1 and k % 5 == 0:
                    rctx("RECOVERY", -round(indem * 0.12, 2),
                         pay_date + timedelta(days=45))
            # if fully developed and closed, release any residual reserve
            if cstatus == "CLOSED":
                paid_indem = sum(t["amount"] for t in w.t["claim_transaction"]
                                 if t["claim_id"] == claim_id
                                 and t["claim_transaction_type_code"] == "INDEMNITY_PAYMENT")
                residual = ult - paid_indem
                if residual > 0.01:
                    last_pay = date(min(ay + len(pattern) - 1, 2026), 12, 1)
                    rctx("CASE_RESERVE_MOVEMENT", -round(residual, 2),
                         min(last_pay, TODAY))

    # ---------------------------------------------------------- reinsurance
    qs = w.add("treaty", treaty_id=w.nid("trt"), treaty_reference="TR-QS-PROP-2026",
               treaty_type_code="QUOTA_SHARE", line_of_business_code="COMMERCIAL_PROPERTY",
               underwriting_year=2026, inception_date=date(2026, 1, 1),
               expiry_date=date(2026, 12, 31), cession_rate=0.3000,
               currency_code="GBP", source_system_code="RI_CORE")
    xl = w.add("treaty", treaty_id=w.nid("trt"), treaty_reference="TR-XL-PROP-2026",
               treaty_type_code="XOL_CATASTROPHE", line_of_business_code="COMMERCIAL_PROPERTY",
               underwriting_year=2026, inception_date=date(2026, 1, 1),
               expiry_date=date(2026, 12, 31), cession_rate=None,
               currency_code="GBP", source_system_code="RI_CORE")
    for treaty in (qs, xl):
        add_role("CEDANT", "Bricksurance SE", date(2026, 1, 1), treaty_id=treaty["treaty_id"])
        add_role("REINSURER", "Bricksurance Re AG", date(2026, 1, 1), treaty_id=treaty["treaty_id"])
    w.add("treaty_layer", treaty_layer_id=w.nid("lay"), treaty_id=qs["treaty_id"],
          layer_number=1, limit_amount=25000000.00, attachment_amount=None,
          reinstatement_count=None, reinstatement_premium_rate=None)
    w.add("treaty_layer", treaty_layer_id=w.nid("lay"), treaty_id=xl["treaty_id"],
          layer_number=1, limit_amount=10000000.00, attachment_amount=5000000.00,
          reinstatement_count=1, reinstatement_premium_rate=1.0000)
    w.add("treaty_layer", treaty_layer_id=w.nid("lay"), treaty_id=xl["treaty_id"],
          layer_number=2, limit_amount=20000000.00, attachment_amount=15000000.00,
          reinstatement_count=1, reinstatement_premium_rate=1.0000)

    # bound submissions behind the two treaties (the hero thread), plus a funnel
    for ref_num, treaty in ((1, qs), (2, xl)):
        sub = w.add("submission", submission_id=w.nid("sub"),
                    submission_reference=f"SUB-2026-{ref_num:06d}",
                    treaty_id=treaty["treaty_id"], submission_status_code="BOUND",
                    treaty_type_code=treaty["treaty_type_code"],
                    line_of_business_code="COMMERCIAL_PROPERTY", underwriting_year=2026,
                    requested_limit=25000000.00 if treaty is qs else 30000000.00,
                    requested_attachment=None if treaty is qs else 5000000.00,
                    currency_code="GBP", received_date=date(2025, 11, 15),
                    source_system_code="RI_CORE")
        add_role("CEDANT", "Bricksurance SE", sub["received_date"],
                 submission_id=sub["submission_id"])
    funnel = ["RECEIVED", "IN_REVIEW", "QUOTED", "QUOTED", "DECLINED", "WITHDRAWN", "IN_REVIEW"]
    for k in range(w.n(7)):
        status = funnel[k % len(funnel)]
        cedant = CEDANTS[k % 2][0]
        sub = w.add("submission", submission_id=w.nid("sub"),
                    submission_reference=f"SUB-2026-{100 + k:06d}", treaty_id=None,
                    submission_status_code=status,
                    treaty_type_code=rng.choice(["QUOTA_SHARE", "SURPLUS", "XOL_PER_RISK",
                                                 "XOL_CATASTROPHE"]),
                    line_of_business_code=rng.choice(["COMMERCIAL_PROPERTY", "MOTOR",
                                                      "GENERAL_LIABILITY"]),
                    underwriting_year=2026,
                    requested_limit=rng.randrange(5, 40) * 1000000.0,
                    requested_attachment=None, currency_code=rng.choice(["GBP", "EUR"]),
                    received_date=date(2025, 11, 1) + timedelta(days=rng.randint(0, 90)),
                    source_system_code="RI_CORE")
        add_role("CEDANT", cedant, sub["received_date"], submission_id=sub["submission_id"])

    for p in w.t["policy"]:
        if p["line_of_business_code"] == "COMMERCIAL_PROPERTY" and p["underwriting_year"] == 2026:
            w.add("cession", cession_id=w.nid("ces"), policy_id=p["policy_id"],
                  coverage_id=None, treaty_id=qs["treaty_id"], ceded_share=0.3000)

    # Windstorm Ostara: modelled day one, reported a month later
    evt = w.add("cat_event", cat_event_id=w.nid("cev"), event_name="Windstorm Ostara",
                cause_of_loss_code="STORM", event_date=date(2026, 2, 18), country_code="GB",
                industry_loss_estimate=850000000.00, currency_code="GBP",
                source_system_code="RI_CORE")
    hit = [p for p in w.t["policy"]
           if p["line_of_business_code"] == "COMMERCIAL_PROPERTY"
           and p["currency_code"] == "GBP"
           and p["inception_date"] <= evt["event_date"] <= p["expiry_date"]][:w.n(5)]
    for p in hit:
        modelled = round(rng.uniform(200000, 900000), 2)
        w.add("event_loss", event_loss_id=w.nid("evl"), cat_event_id=evt["cat_event_id"],
              treaty_id=None, policy_id=p["policy_id"], loss_basis_code="MODELLED",
              gross_loss_amount=modelled, ceded_loss_amount=round(modelled * 0.3, 2),
              currency_code="GBP", as_of_date=date(2026, 2, 20))
        w.add("event_loss", event_loss_id=w.nid("evl"), cat_event_id=evt["cat_event_id"],
              treaty_id=None, policy_id=p["policy_id"], loss_basis_code="REPORTED",
              gross_loss_amount=round(modelled * rng.uniform(0.75, 1.15), 2),
              ceded_loss_amount=None, currency_code="GBP", as_of_date=date(2026, 3, 20))
    for basis, as_of, gross, ceded in (("MODELLED", date(2026, 2, 20), 12400000.00, 7400000.00),
                                       ("REPORTED", date(2026, 3, 20), 10900000.00, 5900000.00)):
        w.add("event_loss", event_loss_id=w.nid("evl"), cat_event_id=evt["cat_event_id"],
              treaty_id=xl["treaty_id"], policy_id=None, loss_basis_code=basis,
              gross_loss_amount=gross, ceded_loss_amount=ceded,
              currency_code="GBP", as_of_date=as_of)

    # ---------------------------------------------------------- conduct & content
    ph_by_policy = {r["policy_id"]: r["party_id"] for r in w.t["party_role"]
                    if r["party_role_type_code"] == "POLICYHOLDER" and r.get("policy_id")}
    complaint_plan = [("CLAIMS_HANDLING", "UPHELD", 1200.00), ("CLAIMS_HANDLING", "NOT_UPHELD", None),
                      ("CLAIMS_HANDLING", "REFERRED_FOS", None), ("ADMIN_AND_SERVICE", "UPHELD", 150.00),
                      ("CLAIMS_HANDLING", "OPEN", None), ("SALES_AND_ADVICE", "NOT_UPHELD", None)]
    claim_rows = [c for c in w.t["claim"] if c["claim_status_code"] in ("DECLINED", "CLOSED", "REOPENED")]
    for i, (cat, cstatus, redress) in enumerate(complaint_plan):
        if i >= len(claim_rows):
            break
        cl = claim_rows[i]
        received = cl["reported_date"] + timedelta(days=30)
        w.add("complaint", complaint_id=w.nid("cpl"), complaint_reference=f"CMP-2026-{i + 1:06d}",
              complainant_party_id=ph_by_policy[cl["policy_id"]],
              policy_id=None, claim_id=cl["claim_id"],
              complaint_category_code=cat, complaint_status_code=cstatus,
              received_date=received,
              closed_date=None if cstatus == "OPEN" else received + timedelta(days=42),
              redress_amount=redress, currency_code="GBP" if redress else None,
              source_system_code="CLM_CORE")
        add_event("COMPLAINT_RECEIVED", "complaint", f"cpl_{i + 1:04d}",
                  datetime.combine(received, datetime.min.time()).replace(hour=14))
    # one pricing complaint on a renewal, policy context only
    renewed = next(p for p in w.t["policy"] if p.get("renews_policy_id"))
    w.add("complaint", complaint_id=w.nid("cpl"), complaint_reference="CMP-2026-000099",
          complainant_party_id=ph_by_policy[renewed["policy_id"]],
          policy_id=renewed["policy_id"], claim_id=None,
          complaint_category_code="PRICING_AND_RENEWAL", complaint_status_code="NOT_UPHELD",
          received_date=renewed["inception_date"] + timedelta(days=5),
          closed_date=renewed["inception_date"] + timedelta(days=30),
          redress_amount=None, currency_code=None, source_system_code="PAS_CORE")

    hero_claim = next(c for c in w.t["claim"] if c["claim_number"] == "CLM-2026-000001")
    w.add("document", document_id=w.nid("doc"), document_type_code="CLAIM_EVIDENCE",
          title="Fire investigation summary — CLM-2026-000001",
          product_id=None, policy_id=None, claim_id=hero_claim["claim_id"], submission_id=None,
          extracted_text=("FIRE INVESTIGATION SUMMARY. Site: warehouse and distribution centre, "
                          "Manchester M3 5EN. Origin: electrical fault in first-floor conveyor "
                          "control cabinet. Sprinkler activation contained spread; smoke damage "
                          "across two floors of racked stock. No indicators of deliberate ignition. "
                          "Recommended reserve basis: reinstatement of control systems, stock "
                          "write-off on floors one and two, business interruption per schedule."),
          volume_path=None, created_date=date(2026, 3, 25), source_system_code="CLM_CORE")
    xl_sub = next(s for s in w.t["submission"] if s["submission_reference"] == "SUB-2026-000002")
    w.add("document", document_id=w.nid("doc"), document_type_code="MRC_SLIP",
          title="MRC slip — property catastrophe XoL 2026",
          product_id=None, policy_id=None, claim_id=None, submission_id=xl_sub["submission_id"],
          extracted_text=("MARKET REFORM CONTRACT. Type: Property Catastrophe Excess of Loss. "
                          "Reinsured: Bricksurance SE. Period: 12 months at 1 January 2026. "
                          "Layer 1: GBP 10,000,000 excess of GBP 5,000,000 each and every loss "
                          "occurrence; one reinstatement at 100% additional premium. Layer 2: "
                          "GBP 20,000,000 excess of GBP 15,000,000; one reinstatement. Territorial "
                          "scope: United Kingdom. Exclusions: war, cyber as per LMA5564, "
                          "contingent business interruption without named suppliers."),
          volume_path=None, created_date=date(2025, 11, 15), source_system_code="RI_CORE")
    add_event("BORDEREAU_RECEIVED", "premium_bordereau_line", "atlas_2026_06",
              datetime(2026, 7, 2, 8, 30), channel="COVERHOLDER",
              payload='{"coverholder": "Atlas Cover Partners", "period": "2026-06"}')

    # ------------------------------------------- customer detail & privacy
    for name, country in ORGS + PERSONS + BROKERS:
        slug = name.lower().replace(" ", ".").replace("&", "and").replace("(", "").replace(")", "")
        w.add("contact_point", contact_point_id=w.nid("cpt"), party_id=pid[name],
              contact_point_type_code="EMAIL", value=f"contact@{slug[:24]}.example",
              preferred=True)
    for i, (name, _) in enumerate(PERSONS):
        w.add("contact_point", contact_point_id=w.nid("cpt"), party_id=pid[name],
              contact_point_type_code="PHONE", value=f"+44 7700 900{100 + i}",
              preferred=False)
        for purpose, status, withdrawn in (("MARKETING", "GRANTED" if i != 1 else "WITHDRAWN",
                                            datetime(2026, 5, 12, 10, 0) if i == 1 else None),
                                           ("PROFILING", "GRANTED", None)):
            w.add("consent", consent_id=w.nid("cns"), party_id=pid[name],
                  consent_purpose_code=purpose, consent_status_code=status,
                  granted_at=datetime(2026, 1, 15, 9, 0), withdrawn_at=withdrawn,
                  channel_code="DIRECT")
    for name, dtype, dstatus, completed, notes in (
            ("Anna Novak", "ACCESS", "COMPLETED", date(2026, 4, 20),
             "Access pack issued from the dictionary-driven PII inventory."),
            ("James Whitfield", "ERASURE", "REFUSED", date(2026, 6, 10),
             "Refused: open claim and regulatory retention obligations; "
             "erasure to be executed per PRIVACY.md at retention expiry."),
            ("Claire Dubois", "PORTABILITY", "IN_PROGRESS", None, None)):
        w.add("data_subject_request", data_subject_request_id=w.nid("dsr"),
              party_id=pid[name], dsr_type_code=dtype, dsr_status_code=dstatus,
              received_date=date(2026, 3, 25), completed_date=completed, notes=notes)

    # ------------------------------------------- fraud signals
    for cl in w.t["claim"]:
        lag = (cl["reported_date"] - cl["loss_date"]).days
        if cl["claim_status_code"] == "DECLINED":
            w.add("fraud_signal", fraud_signal_id=w.nid("frs"), claim_id=cl["claim_id"],
                  fraud_signal_type_code="NETWORK_LINK", score=78,
                  detected_at=datetime.combine(cl["reported_date"], datetime.min.time()).replace(hour=17),
                  detail="Claimant address linked to two previously repudiated claims.",
                  source_system_code="CLM_CORE")
        elif lag > 14:
            w.add("fraud_signal", fraud_signal_id=w.nid("frs"), claim_id=cl["claim_id"],
                  fraud_signal_type_code="LATE_REPORTING", score=min(90, 30 + lag * 2),
                  detected_at=datetime.combine(cl["reported_date"], datetime.min.time()).replace(hour=17),
                  detail=f"Loss reported {lag} days after occurrence.",
                  source_system_code="CLM_CORE")

    # ------------------------------------------- billing & finance bridge
    unpaid = 0
    for pt in [x for x in w.t["premium_transaction"]
               if x["premium_transaction_type_code"] == "WRITTEN"]:
        inv_date = pt["transaction_date"]
        w.add("receivable_transaction", receivable_transaction_id=w.nid("rcv"),
              policy_id=pt["policy_id"], receivable_transaction_type_code="INVOICE",
              amount=pt["amount"], currency_code=pt["currency_code"],
              transaction_date=inv_date, due_date=inv_date + timedelta(days=30),
              source_system_code="PAS_CORE")
        unpaid += 1
        if unpaid % 12 == 0 and inv_date > date(2026, 3, 1):
            continue                      # aged debt: invoice never settled
        w.add("receivable_transaction", receivable_transaction_id=w.nid("rcv"),
              policy_id=pt["policy_id"], receivable_transaction_type_code="CASH_RECEIPT",
              amount=round(-pt["amount"], 2), currency_code=pt["currency_code"],
              transaction_date=inv_date + timedelta(days=rng.randint(10, 45)),
              due_date=None, source_system_code="PAS_CORE")

    # line-level expenses sized off written premium (drives the combined ratio)
    policy_lob_ccy = {p["policy_id"]: (p["line_of_business_code"], p["currency_code"])
                      for p in w.t["policy"]}
    written_lob = {}
    for pt in w.t["premium_transaction"]:
        key = policy_lob_ccy[pt["policy_id"]]
        written_lob[key] = round(written_lob.get(key, 0) + pt["amount"], 2)
    for (lob, ccy), written in sorted(written_lob.items()):
        for etype, factor, when in (("OPERATING", 0.11, date(2026, 3, 31)),
                                    ("OPERATING", 0.11, date(2026, 6, 30)),
                                    ("ACQUISITION", 0.05, date(2026, 6, 30)),
                                    ("CLAIMS_HANDLING", 0.04, date(2026, 6, 30))):
            w.add("expense_transaction", expense_transaction_id=w.nid("exp"),
                  expense_type_code=etype, line_of_business_code=lob,
                  amount=round(written * factor, 2), currency_code=ccy,
                  transaction_date=when, source_system_code="PAS_CORE")

    # ---------------------------------------------------------- chart of accounts
    # (number, name, type, statement, parent) - a working insurer CoA
    COA = [
        ("1000", "Cash and bank", "ASSET", "BALANCE_SHEET", None),
        ("1100", "Investments", "ASSET", "BALANCE_SHEET", None),
        ("1200", "Premium receivable", "ASSET", "BALANCE_SHEET", None),
        ("1300", "Deferred acquisition costs", "ASSET", "BALANCE_SHEET", None),
        ("2000", "Claims reserves", "LIABILITY", "BALANCE_SHEET", None),
        ("2100", "Unearned premium reserve", "LIABILITY", "BALANCE_SHEET", None),
        ("2200", "Commission payable", "LIABILITY", "BALANCE_SHEET", None),
        ("2300", "Tax payable", "LIABILITY", "BALANCE_SHEET", None),
        ("3000", "Retained earnings", "EQUITY", "BALANCE_SHEET", None),
        ("4000", "Gross written premium", "INCOME", "INCOME_STATEMENT", None),
        ("4100", "Investment income", "INCOME", "INCOME_STATEMENT", None),
        ("5000", "Claims incurred", "EXPENSE", "INCOME_STATEMENT", None),
        ("5100", "Commission expense", "EXPENSE", "INCOME_STATEMENT", None),
        ("5200", "Operating expenses", "EXPENSE", "INCOME_STATEMENT", None),
        ("5300", "Insurance premium tax", "EXPENSE", "INCOME_STATEMENT", None),
    ]
    acct_id = {}
    for num, nm, typ, stmt, parent in COA:
        aid = w.nid("acc")
        acct_id[num] = aid
        w.add("chart_of_account", account_id=aid, account_number=num, name=nm,
              account_type_code=typ, parent_account_id=None, statement_type_code=stmt)

    # accounting periods for the carrier (Q1, Q2 2026)
    period_id = {}
    for lbl, s, e, st in (("2026-Q1", date(2026, 1, 1), date(2026, 3, 31), "LOCKED"),
                          ("2026-Q2", date(2026, 4, 1), date(2026, 6, 30), "OPEN")):
        pid_ = w.nid("per")
        period_id[lbl] = pid_
        w.add("accounting_period", accounting_period_id=pid_, legal_entity_id=CARRIER,
              period_label=lbl, start_date=s, end_date=e, period_status_code=st)

    def period_for(d):
        return period_id["2026-Q1"] if d <= date(2026, 3, 31) else period_id["2026-Q2"]

    # statement-line mapping (Solvency II presentation, one account -> one line)
    STMT_MAP = [
        ("BALANCE_SHEET", "Investments", "1100", 1, 3),
        ("BALANCE_SHEET", "Cash and equivalents", "1000", 1, 4),
        ("BALANCE_SHEET", "Premium receivable", "1200", 1, 5),
        ("BALANCE_SHEET", "Deferred acquisition costs", "1300", 1, 6),
        ("BALANCE_SHEET", "Technical provisions", "2000", -1, 10),
        ("BALANCE_SHEET", "Unearned premium reserve", "2100", -1, 11),
        ("BALANCE_SHEET", "Payables", "2200", -1, 12),
        ("BALANCE_SHEET", "Tax payable", "2300", -1, 13),
        ("INCOME_STATEMENT", "Gross written premium", "4000", -1, 1),
        ("INCOME_STATEMENT", "Investment income", "4100", -1, 2),
        ("INCOME_STATEMENT", "Claims incurred", "5000", 1, 3),
        ("INCOME_STATEMENT", "Commission expense", "5100", 1, 4),
        ("INCOME_STATEMENT", "Operating expenses", "5200", 1, 5),
        ("INCOME_STATEMENT", "Insurance premium tax", "5300", 1, 6),
    ]
    for stmt, label, num, sign, order in STMT_MAP:
        w.add("statement_line", statement_line_id=w.nid("stl"), statement_type_code=stmt,
              reporting_regime_code="SOLVENCY_II", line_label=label, line_order=order,
              account_id=acct_id[num], sign=sign)

    # double-entry journals derived from operational money. Convention:
    # debit positive, credit negative; every journal's two lines net to zero.
    def journal(ref, when, desc, debit_acct, credit_acct, amount, ccy,
                src_entity=None, src_id=None):
        jid = w.nid("jnl")
        w.add("journal", journal_id=jid, journal_reference=ref,
              legal_entity_id=CARRIER, accounting_period_id=period_for(when),
              posting_date=when, description=desc, source_system_code="PAS_CORE")
        w.add("journal_line", journal_line_id=w.nid("jll"), journal_id=jid,
              account_id=acct_id[debit_acct], amount=amount, currency_code=ccy,
              source_entity=src_entity, source_id=src_id)
        w.add("journal_line", journal_line_id=w.nid("jll"), journal_id=jid,
              account_id=acct_id[credit_acct], amount=round(-amount, 2), currency_code=ccy,
              source_entity=src_entity, source_id=src_id)

    # premium written: Dr receivable, Cr premium income
    for pt in w.t["premium_transaction"]:
        journal("PREM", pt["transaction_date"], "Premium written",
                "1200", "4000", pt["amount"], pt["currency_code"],
                "premium_transaction", pt["premium_transaction_id"])
    # claim movements: reserve -> Dr claims incurred / Cr reserves; payment -> Dr incurred / Cr cash
    for ct in w.t["claim_transaction"]:
        credit = "2000" if ct["claim_transaction_type_code"] == "CASE_RESERVE_MOVEMENT" else "1000"
        journal("CLM", ct["transaction_date"], "Claim movement",
                "5000", credit, ct["amount"], ct["currency_code"],
                "claim_transaction", ct["claim_transaction_id"])
    # commission: Dr commission expense, Cr payable
    for cm in w.t["commission_transaction"]:
        journal("COMM", cm["transaction_date"], "Commission",
                "5100", "2200", cm["amount"], cm["currency_code"],
                "commission_transaction", cm["commission_transaction_id"])
    # expenses: Dr operating expense, Cr cash
    for ex in w.t["expense_transaction"]:
        journal("EXP", ex["transaction_date"], "Operating expense",
                "5200", "1000", ex["amount"], ex["currency_code"],
                "expense_transaction", ex["expense_transaction_id"])

    # ---------------------------------------------------------- investments
    INVEST = [("GOVERNMENT_BOND", "UK Gilt 1.5% 2031", "GB00BMBL1D50", 42000000, 40950000),
              ("GOVERNMENT_BOND", "Bund 0.5% 2030", "DE0001102481", 28000000, 27600000),
              ("CORPORATE_BOND", "Investment-grade credit fund", None, 31000000, 31620000),
              ("EQUITY", "European equity portfolio", None, 18000000, 20430000),
              ("PROPERTY", "Commercial property fund", None, 12000000, 12180000),
              ("CASH_AND_DEPOSITS", "Money-market deposits", None, 15000000, 15000000)]
    for ac, nm, isin, cost, mv in INVEST:
        h = w.add("investment_holding", investment_holding_id=w.nid("inv"),
                  legal_entity_id=CARRIER, asset_class_code=ac, instrument_name=nm,
                  isin=isin, book_cost=float(cost), market_value=float(mv),
                  currency_code="EUR", valuation_date=date(2026, 6, 30),
                  source_system_code="RI_CORE")
        # income + revaluation as transactions
        if ac in ("GOVERNMENT_BOND", "CORPORATE_BOND"):
            inc = round(cost * 0.011, 2)
            w.add("investment_transaction", investment_transaction_id=w.nid("ivt"),
                  investment_holding_id=h["investment_holding_id"],
                  investment_transaction_type_code="COUPON", amount=inc,
                  currency_code="EUR", transaction_date=date(2026, 6, 30),
                  source_system_code="RI_CORE")
            journal("INV", date(2026, 6, 30), "Investment income",
                    "1000", "4100", inc, "EUR", "investment_holding", h["investment_holding_id"])
        if mv != cost:
            w.add("investment_transaction", investment_transaction_id=w.nid("ivt"),
                  investment_holding_id=h["investment_holding_id"],
                  investment_transaction_type_code="FAIR_VALUE_MOVEMENT",
                  amount=round(mv - cost, 2), currency_code="EUR",
                  transaction_date=date(2026, 6, 30), source_system_code="RI_CORE")

    # tax: IPT on GB premium (12%)
    for pt in [x for x in w.t["premium_transaction"]
               if x["premium_transaction_type_code"] == "WRITTEN"
               and policy_lob_ccy.get(x["policy_id"], (None, "X"))[1] == "GBP"]:
        ipt = round(pt["amount"] * 0.12, 2)
        w.add("tax_transaction", tax_transaction_id=w.nid("tax"), legal_entity_id=CARRIER,
              tax_type_code="IPT", policy_id=pt["policy_id"], amount=ipt,
              currency_code="GBP", transaction_date=pt["transaction_date"],
              source_system_code="PAS_CORE")
        journal("IPT", pt["transaction_date"], "Insurance premium tax",
                "5300", "2300", ipt, "GBP", "tax_transaction", pt["policy_id"])

    # financial plan: 2026 budget vs the actuals metric views
    for lob, gwp_plan, cor_plan in (("COMMERCIAL_PROPERTY", 1350000, 0.95),
                                    ("MOTOR", 420000, 1.02),
                                    ("GENERAL_LIABILITY", 260000, 0.88),
                                    ("MARINE_CARGO", 180000, 0.91)):
        for measure, amount, ccyp in (("gross_written_premium", gwp_plan, "GBP"),
                                      ("combined_ratio", cor_plan, None)):
            w.add("financial_plan", financial_plan_id=w.nid("pln"), legal_entity_id=CARRIER,
                  plan_version="2026 Budget v1", line_of_business_code=lob,
                  plan_measure=measure, period_label="2026-FY", amount=float(amount),
                  currency_code=ccyp)

    # FX rates to the group presentation currency (EUR)
    for frm, rate in (("EUR", 1.0), ("GBP", 1.1750), ("CHF", 1.0420), ("USD", 0.9180)):
        w.add("fx_rate", fx_rate_id=w.nid("fx"), from_currency_code=frm,
              to_currency_code="EUR", rate_date=date(2026, 6, 30), rate=rate)

    # ---------------------------------------------------------- life & finance
    def add_assumption(atype, version, status, effective, approved):
        return w.add("assumption_set", assumption_set_id=w.nid("asm"),
                     assumption_type_code=atype, assumption_status_code=status,
                     version=version,
                     description=f"{atype.title()} basis v{version}.",
                     effective_from=effective,
                     approved_by="Chief Actuary (checker)" if approved else None,
                     approved_at=datetime(2026, 6, 28, 14, 30) if approved and status == "APPROVED"
                     else (datetime(2026, 1, 10, 9, 0) if approved else None),
                     source_system_code="LIFE_CORE")

    mort_v1 = add_assumption("MORTALITY", 1, "SUPERSEDED", date(2026, 1, 1), True)
    mort_v2 = add_assumption("MORTALITY", 2, "APPROVED", date(2026, 6, 30), True)
    add_assumption("MORTALITY", 3, "REJECTED", None, True)
    lapse_v1 = add_assumption("LAPSE", 1, "APPROVED", date(2026, 1, 1), True)
    exp_v1 = add_assumption("EXPENSE", 1, "APPROVED", date(2026, 1, 1), True)
    econ_v1 = add_assumption("ECONOMIC", 1, "APPROVED", date(2026, 1, 1), True)

    scn_q1 = w.add("scenario_set", scenario_set_id=w.nid("scn"),
                   name="EIOPA RFR 2026-03 + HW1F 1,000 paths",
                   scenario_status_code="SUPERSEDED", scenario_count=1000,
                   calibration_date=date(2026, 3, 31), source_system_code="LIFE_CORE")
    scn_q2 = w.add("scenario_set", scenario_set_id=w.nid("scn"),
                   name="EIOPA RFR 2026-06 + HW1F 1,000 paths",
                   scenario_status_code="ACTIVE", scenario_count=1000,
                   calibration_date=date(2026, 6, 30), source_system_code="LIFE_CORE")
    w.add("scenario_set", scenario_set_id=w.nid("scn"),
          name="Vendor ESG 2026-06 delivery", scenario_status_code="AVAILABLE",
          scenario_count=1000, calibration_date=date(2026, 6, 30),
          source_system_code="LIFE_CORE")

    MP_PLAN = [("TERM_LIFE", [30, 35, 40, 45, 50, 55], [5, 10, 15, 20], 120000, 220),
               ("CREDIT_LIFE", [30, 40, 50], [1, 3, 5], 15000, 340),
               ("GROUP_PROTECTION", [35, 45], [1], 250000, 900)]
    for val_date in (date(2026, 3, 31), date(2026, 6, 30)):
        for lob, ages, terms, avg_sa, base_count in MP_PLAN:
            for age in ages:
                for term in terms:
                    count = w.n(round(base_count * rng.uniform(0.7, 1.3)))
                    w.add("model_point", model_point_id=w.nid("mpt"),
                          valuation_date=val_date, line_of_business_code=lob,
                          age_attained=age, outstanding_term_years=term,
                          policy_count=count,
                          sum_assured=round(count * avg_sa * rng.uniform(0.9, 1.1), 2),
                          annual_premium=round(count * avg_sa * 0.011 * rng.uniform(0.9, 1.1), 2),
                          currency_code="GBP", source_system_code="LIFE_CORE")

    def add_run(val_date, ts, verdict, scenario, source, model_version, sets=(),
                legal_entity=None, level=None, regime=None):
        run = w.add("valuation_run", valuation_run_id=w.nid("run"), valuation_date=val_date,
                    run_timestamp=ts, scenario_set_id=scenario, model_version=model_version,
                    run_verdict_code=verdict, run_by="svc-valuation",
                    source_system_code=source, legal_entity_id=legal_entity,
                    reporting_level_code=level, reporting_regime_code=regime)
        for s in sets:
            w.add("valuation_run_assumption", valuation_run_id=run["valuation_run_id"],
                  assumption_set_id=s["assumption_set_id"])
        return run

    run_q1 = add_run(date(2026, 3, 31), datetime(2026, 4, 2, 3, 10), "GREEN",
                     scn_q1["scenario_set_id"], "LIFE_CORE", "engine v2.0",
                     (mort_v1, lapse_v1, exp_v1, econ_v1),
                     legal_entity="le_life", level="SOLO", regime="SOLVENCY_II")
    add_run(date(2026, 6, 30), datetime(2026, 7, 1, 22, 40), "RED",
            scn_q2["scenario_set_id"], "LIFE_CORE", "engine v2.1",
            (mort_v2, lapse_v1, exp_v1, econ_v1),
            legal_entity="le_life", level="SOLO", regime="SOLVENCY_II")  # gate blocked; no results
    run_q2 = add_run(date(2026, 6, 30), datetime(2026, 7, 2, 3, 5), "GREEN",
                     scn_q2["scenario_set_id"], "LIFE_CORE", "engine v2.1",
                     (mort_v2, lapse_v1, exp_v1, econ_v1),
                     legal_entity="le_life", level="SOLO", regime="SOLVENCY_II")
    run_pnc = add_run(date(2026, 6, 30), datetime(2026, 7, 3, 6, 15), "GREEN",
                      None, "CLM_CORE", "chain-ladder v1",
                      legal_entity="le_se", level="SOLO", regime="SOLVENCY_II")
    # the GROUP consolidated Solvency II run - what a group CRO reports
    run_group = add_run(date(2026, 6, 30), datetime(2026, 7, 4, 8, 0), "GREEN",
                        None, "DATA_CORE", "consolidation v1",
                        legal_entity="le_group", level="GROUP", regime="SOLVENCY_II")

    BEL = {(run_q1["valuation_run_id"], "TERM_LIFE"): -23150000.00,
           (run_q1["valuation_run_id"], "CREDIT_LIFE"): 3180000.00,
           (run_q1["valuation_run_id"], "GROUP_PROTECTION"): 10940000.00,
           (run_q2["valuation_run_id"], "TERM_LIFE"): -24370000.00,
           (run_q2["valuation_run_id"], "CREDIT_LIFE"): 3210000.00,
           (run_q2["valuation_run_id"], "GROUP_PROTECTION"): 11420000.00}

    def add_result(run, lob, measure, amount, ccy="GBP"):
        w.add("valuation_result", valuation_result_id=w.nid("vrs"),
              valuation_run_id=run["valuation_run_id"], line_of_business_code=lob,
              valuation_measure_code=measure, cohort=None, amount=amount, currency_code=ccy)

    for (run_id, lob), bel in BEL.items():
        run = run_q1 if run_id == run_q1["valuation_run_id"] else run_q2
        rm = round(abs(bel) * 0.04, 2)
        add_result(run, lob, "BEL", bel)
        add_result(run, lob, "RISK_MARGIN", rm)
        add_result(run, lob, "TECHNICAL_PROVISION", round(bel + rm, 2))

    # P&C case reserves: published figures DERIVED from the world's own claims
    outstanding = {}
    lob_by_policy = {p["policy_id"]: p["line_of_business_code"] for p in w.t["policy"]}
    policy_by_claim = {c["claim_id"]: c["policy_id"] for c in w.t["claim"]}
    for tx in w.t["claim_transaction"]:
        if tx["claim_transaction_type_code"] == "CASE_RESERVE_MOVEMENT":
            key = (lob_by_policy[policy_by_claim[tx["claim_id"]]], tx["currency_code"])
            outstanding[key] = round(outstanding.get(key, 0) + tx["amount"], 2)
    for (lob, ccy), amount in sorted(outstanding.items()):
        add_result(run_pnc, lob, "CASE_RESERVE_TOTAL", amount, ccy)
        add_result(run_pnc, lob, "IBNR", round(amount * 0.4, 2), ccy)

    # Solvency II capital - solo (SE) and consolidated (group). The group is
    # NOT the sum of solos: diversification benefit reduces group SCR.
    def add_capital(run, scr, own_funds, mcr, ccy):
        add_result(run, "COMMERCIAL_PROPERTY", "SCR", scr, ccy)      # line is nominal at capital level
        add_result(run, "COMMERCIAL_PROPERTY", "MCR", mcr, ccy)
        add_result(run, "COMMERCIAL_PROPERTY", "OWN_FUNDS", own_funds, ccy)
        add_result(run, "COMMERCIAL_PROPERTY", "ELIGIBLE_OWN_FUNDS_T1", round(own_funds * 0.92, 2), ccy)
        add_result(run, "COMMERCIAL_PROPERTY", "SCR_COVERAGE_RATIO",
                   round(own_funds / scr, 4), ccy)
    add_capital(run_pnc, 210000000.00, 388500000.00, 94500000.00, "EUR")   # SE solo
    add_capital(run_group, 402000000.00, 690000000.00, 181000000.00, "EUR")  # group, diversified

    # IFRS 17: contract groups + CSM roll-forward (life term book, GMM)
    for cohort in (2025, 2026):
        cg = w.add("contract_group", contract_group_id=w.nid("cg"),
                   legal_entity_id="le_life", line_of_business_code="TERM_LIFE",
                   cohort_year=cohort, measurement_model_code="GMM",
                   onerous=False, currency_code="GBP")
        opening = 8400000.00 if cohort == 2025 else 0.00
        movements = [("OPENING", opening),
                     ("NEW_BUSINESS", 0.00 if cohort == 2025 else 6200000.00),
                     ("INTEREST_ACCRETION", round((opening or 6200000.00) * 0.021, 2)),
                     ("EXPERIENCE_ADJUSTMENT", 180000.00 if cohort == 2025 else -90000.00),
                     ("RELEASE", -740000.00 if cohort == 2025 else -310000.00)]
        for mtype, amt in movements:
            w.add("csm_movement", csm_movement_id=w.nid("csm"),
                  contract_group_id=cg["contract_group_id"],
                  valuation_run_id=run_q2["valuation_run_id"],
                  csm_movement_type_code=mtype, amount=amt, currency_code="GBP")
    # an onerous PAA group (motor) - the loss-component story
    cg_on = w.add("contract_group", contract_group_id=w.nid("cg"),
                  legal_entity_id="le_se", line_of_business_code="MOTOR",
                  cohort_year=2026, measurement_model_code="PAA",
                  onerous=True, currency_code="GBP")
    for mtype, amt in (("OPENING", 0.00), ("NEW_BUSINESS", 0.00)):
        w.add("csm_movement", csm_movement_id=w.nid("csm"),
              contract_group_id=cg_on["contract_group_id"],
              valuation_run_id=run_q2["valuation_run_id"],
              csm_movement_type_code=mtype, amount=amt, currency_code="GBP")

    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0,
                    help="Volume multiplier; semantics and heroes are scale-invariant")
    args = ap.parse_args()

    entities = load_entities()
    binding = load_binding()
    w = build_world(args.scale)

    order = ["legal_entity", "party", "product", "product_coverage", "underwriting_question",
             "appetite_rule", "policy", "quote", "underwriting_decision", "coverage",
             "insured_object", "vehicle", "premium_transaction", "endorsement",
             "commission_transaction", "claim", "claim_transaction", "complaint",
             "treaty", "treaty_layer", "submission", "cession", "cat_event", "event_loss",
             "document", "business_event", "contact_point", "consent",
             "data_subject_request", "fraud_signal", "expense_transaction",
             "receivable_transaction", "chart_of_account", "accounting_period",
             "statement_line", "journal", "journal_line", "investment_holding",
             "investment_transaction", "tax_transaction", "financial_plan", "fx_rate",
             "assumption_set", "scenario_set",
             "valuation_run", "valuation_run_assumption", "valuation_result",
             "contract_group", "csm_movement", "model_point", "party_role"]
    missing = set(order) - set(entities)
    assert not missing, f"world emits unknown entities: {missing}"

    header = ("-- Generated by tools/world_engine.py — the deterministic Bricksurance world.\n"
              f"-- Scale {args.scale}. Bricksurance is fictional; every row is synthetic.\n\n")
    stmts = [insert(binding, entities[name], w.t[name]) for name in order if w.t[name]]
    OUT.write_text(header + "\n\n".join(stmts) + "\n")
    counts = ", ".join(f"{k}={len(v)}" for k, v in w.t.items() if v)
    print(f"Wrote {OUT.relative_to(ROOT)} ({counts})")


if __name__ == "__main__":
    main()
