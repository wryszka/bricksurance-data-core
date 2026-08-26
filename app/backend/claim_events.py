"""The interactive spine — record a claim and watch it ripple through the estate.

This is the foundation the workbenches will stand on: the base data layer stops
being static synthetic data and becomes writable. Recording a claim inserts the
claim + its transactions, posts the balanced GL journal, and (if the policy is
ceded) records the reinsurance recovery. Everything derived — the reserving
triangle, loss ratio, IBNR, outstanding reserve, financial position, trial
balance — recomputes for free, because those are views over the transactions.

So a single "huge claim" moves claims, reserving, finance AND reinsurance at
once, not just a claims demo. That's the whole point.

GL posting rule (mirrors tools/world_engine.py, verified):
  reserve movement -> Dr 5000 (claims incurred) / Cr 2000 (claims reserves)
  payment          -> Dr 5000 (claims incurred) / Cr 1000 (cash)
Every journal's two lines net to zero, so the trial balance stays balanced.
"""
from __future__ import annotations

import uuid

from .db import q, run_sql


def _new_id(prefix: str) -> str:
    # Distinct 'live' prefix so events never collide with the seeded world.
    return f"{prefix}_live_{uuid.uuid4().hex[:10]}"


def _esc(s) -> str:
    return str(s).replace("'", "''")


def _account_ids() -> dict:
    rows = run_sql(
        f"SELECT account_number, account_id FROM {q('finance', 'chart_of_account')}")
    return {r[0]: r[1] for r in rows}


def _period_for(when: str) -> str | None:
    rows = run_sql(
        f"SELECT accounting_period_id FROM {q('finance', 'accounting_period')} "
        f"WHERE DATE '{when}' BETWEEN start_date AND end_date "
        f"AND legal_entity_id = 'le_se' LIMIT 1")
    if rows:
        return rows[0][0]
    rows = run_sql(
        f"SELECT accounting_period_id FROM {q('finance', 'accounting_period')} "
        f"WHERE legal_entity_id = 'le_se' ORDER BY end_date DESC LIMIT 1")
    return rows[0][0] if rows else None


def _policy_context(policy_number: str) -> dict | None:
    rows = run_sql(
        f"SELECT p.policy_id, p.line_of_business_code, p.currency_code, "
        f"p.legal_entity_id, "
        f"(SELECT coverage_id FROM {q('policy', 'coverage')} c "
        f" WHERE c.policy_id = p.policy_id LIMIT 1) AS coverage_id "
        f"FROM {q('policy', 'policy')} p WHERE p.policy_number = '{_esc(policy_number)}'")
    if not rows:
        return None
    r = rows[0]
    ctx = {"policy_id": r[0], "line_of_business_code": r[1], "currency_code": r[2],
           "legal_entity_id": r[3], "coverage_id": r[4]}
    # is the policy ceded, and at what share? (quota-share)
    ces = run_sql(
        f"SELECT c.ceded_share, t.treaty_reference FROM {q('reinsurance', 'cession')} c "
        f"JOIN {q('reinsurance', 'treaty')} t ON t.treaty_id = c.treaty_id "
        f"WHERE c.policy_id = '{ctx['policy_id']}' ORDER BY c.ceded_share DESC LIMIT 1")
    if ces:
        ctx["ceded_share"] = float(ces[0][0]) if ces[0][0] is not None else None
        ctx["treaty_reference"] = ces[0][1]
    return ctx


def _snapshot(currency: str) -> dict:
    """The cross-domain figures that a claim moves — captured before and after
    so the app can show the ripple."""
    C = currency.replace("'", "")[:3] or "GBP"
    um = q("semantics", "underwriting_metrics")
    jl = q("finance", "journal_line")

    def one(sql, default=0.0):
        rows = run_sql(sql)
        try:
            return float(rows[0][0]) if rows and rows[0][0] is not None else default
        except (TypeError, ValueError):
            return default

    return {
        "currency": C,
        "claims_incurred": one(
            f"SELECT CAST(MEASURE(claims_incurred) AS DECIMAL(18,2)) FROM {um} WHERE currency_code='{C}'"),
        "outstanding_reserve": one(
            f"SELECT CAST(MEASURE(outstanding_reserve) AS DECIMAL(18,2)) FROM {um} WHERE currency_code='{C}'"),
        "loss_ratio_written": one(
            f"SELECT CAST(MEASURE(loss_ratio_written) AS DECIMAL(10,4)) FROM {um} WHERE currency_code='{C}'"),
        "trial_balance": one(
            f"SELECT CAST(SUM(amount) AS DECIMAL(18,2)) FROM {jl}"),
        "claim_count": int(one(
            f"SELECT MEASURE(claim_count) FROM {um} WHERE currency_code='{C}'")),
    }


def record_claim(policy_number: str, reserve_amount: float, cause_of_loss_code: str = "FIRE",
                 loss_date: str = "2026-08-01", description: str | None = None) -> dict:
    """Record a claim against an existing policy and let it ripple.

    Inserts: the claim, its opening case-reserve movement, the balanced GL
    journal, and (if the policy is ceded) a quota-share reinsurance recovery.
    Returns before/after snapshots so the caller can show the cross-domain
    effect. The reserving triangle, loss ratio, IBNR and financial position
    recompute automatically as views over the new transactions.
    """
    ctx = _policy_context(policy_number)
    if not ctx:
        raise ValueError(f"No policy '{policy_number}'")
    ccy = ctx["currency_code"]
    before = _snapshot(ccy)

    acct = _account_ids()
    period = _period_for(loss_date)
    claim_id = _new_id("clm")
    claim_number = f"CLM-LIVE-{uuid.uuid4().hex[:6].upper()}"
    src = "LIVE_EVENT"

    # 1. the claim
    run_sql(
        f"INSERT INTO {q('claim', 'claim')} VALUES ("
        f"'{claim_id}', '{ctx['policy_id']}', "
        f"{('NULL' if not ctx['coverage_id'] else chr(39)+_esc(ctx['coverage_id'])+chr(39))}, "
        f"'{claim_number}', 'OPEN', '{_esc(cause_of_loss_code)}', "
        f"DATE '{loss_date}', DATE '{loss_date}', "
        f"'{_esc(description or 'Large loss recorded via the interactive spine.')}', '{src}')")

    # 2. the opening case-reserve movement
    ctx_id = _new_id("ctx")
    run_sql(
        f"INSERT INTO {q('claim', 'claim_transaction')} VALUES ("
        f"'{ctx_id}', '{claim_id}', 'CASE_RESERVE_MOVEMENT', "
        f"{round(reserve_amount, 2)}, '{ccy}', DATE '{loss_date}', '{src}')")

    # 3. the balanced GL journal: Dr 5000 claims incurred / Cr 2000 reserves
    jid = _new_id("jnl")
    run_sql(
        f"INSERT INTO {q('finance', 'journal')} VALUES ("
        f"'{jid}', 'CLM-LIVE', '{ctx['legal_entity_id'] or 'le_se'}', "
        f"{('NULL' if not period else chr(39)+_esc(period)+chr(39))}, "
        f"DATE '{loss_date}', 'Claim reserve (live event)', '{src}')")
    run_sql(
        f"INSERT INTO {q('finance', 'journal_line')} VALUES "
        f"('{_new_id('jll')}', '{jid}', '{acct['5000']}', {round(reserve_amount, 2)}, '{ccy}', 'claim_transaction', '{ctx_id}'),"
        f"('{_new_id('jll')}', '{jid}', '{acct['2000']}', {round(-reserve_amount, 2)}, '{ccy}', 'claim_transaction', '{ctx_id}')")

    # 4. reinsurance recovery, if ceded (quota share) — a negative RECOVERY on the claim
    recovery = None
    if ctx.get("ceded_share"):
        recovery = round(reserve_amount * ctx["ceded_share"], 2)
        rec_id = _new_id("ctx")
        run_sql(
            f"INSERT INTO {q('claim', 'claim_transaction')} VALUES ("
            f"'{rec_id}', '{claim_id}', 'RECOVERY', {round(-recovery, 2)}, '{ccy}', "
            f"DATE '{loss_date}', '{src}')")

    after = _snapshot(ccy)
    return {
        "claim_number": claim_number,
        "policy_number": policy_number,
        "line_of_business": (ctx["line_of_business_code"] or "").replace("_", " ").title(),
        "currency": ccy,
        "reserve_amount": round(reserve_amount, 2),
        "ceded": bool(ctx.get("ceded_share")),
        "ceded_share": ctx.get("ceded_share"),
        "treaty_reference": ctx.get("treaty_reference"),
        "reinsurance_recovery": recovery,
        "before": before,
        "after": after,
        "ripple": {
            "claims_incurred_delta": round(after["claims_incurred"] - before["claims_incurred"], 2),
            "outstanding_reserve_delta": round(after["outstanding_reserve"] - before["outstanding_reserve"], 2),
            "loss_ratio_before": before["loss_ratio_written"],
            "loss_ratio_after": after["loss_ratio_written"],
            "trial_balance_after": after["trial_balance"],
            "trial_balance_still_zero": abs(after["trial_balance"]) < 0.01,
        },
        "note": ("One governed claim event: the claim and its transactions are "
                 "recorded, the GL journal is posted (balanced), and — because "
                 "the policy is ceded — the reinsurance recovery too. The reserving "
                 "triangle, loss ratio, IBNR and financial position all recompute "
                 "as views. Nothing was updated per-domain; it rippled by construction."),
    }


def list_reset_live() -> dict:
    """Remove all live-event rows so the demo starts clean (mirrors reset_governance)."""
    for tbl, col in [(q('finance', 'journal_line'), 'source_id'),
                     (q('finance', 'journal'), 'source_system_code'),
                     (q('claim', 'claim_transaction'), 'source_system_code'),
                     (q('claim', 'claim'), 'source_system_code')]:
        if col == 'source_system_code':
            run_sql(f"DELETE FROM {tbl} WHERE source_system_code = 'LIVE_EVENT'")
        else:
            run_sql(f"DELETE FROM {tbl} WHERE source_id LIKE 'ctx_live_%'")
    return {"reset": True}
