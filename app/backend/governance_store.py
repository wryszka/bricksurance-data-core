"""Data Core Atlas — the governance record layer (capture-only).

The model's TRUTH stays in the YAML specs (generated into Unity Catalog). This
module records the human governance PROCESS *around* the model — proposals to
change a definition/classification/owner, and data-quality issue flags — as
dated, attributed rows in a Delta table. It never edits the model tags directly:
a proposal is captured and a spec-diff stub is generated, to be taken through the
versioned evolution contract (docs/EVOLUTION.md). That is what keeps the app a
control rather than a parallel truth that drifts.

Scope (v1, deliberately lean): capture + spec-diff text. No auto-PR, no
write-back to the specs. Reset via tools/reset_governance.py.
"""
from __future__ import annotations

from .db import q, run_sql, client, WAREHOUSE_ID
from . import atlas

TABLE = q("reference", "governance_action")

DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
  action_id STRING NOT NULL COMMENT 'Surrogate id for the governance action.',
  action_type STRING NOT NULL COMMENT 'proposal | issue.',
  element STRING NOT NULL COMMENT 'Model element the action concerns.',
  element_kind STRING COMMENT 'entity | metric | attribute.',
  field STRING COMMENT 'What is proposed to change (classification, definition, owner...).',
  current_value STRING COMMENT 'Value in the model today.',
  proposed_value STRING COMMENT 'Value being proposed.',
  rationale STRING COMMENT 'Why — the steward''s justification.',
  raised_by STRING COMMENT 'Role/identity that raised it.',
  raised_on STRING COMMENT 'Date raised.',
  status STRING COMMENT 'open | acknowledged (capture-only; not applied).',
  spec_diff STRING COMMENT 'Generated spec-change stub for the evolution process.'
)
COMMENT 'Governance process record: proposals and issue flags against the model. Capture-only — the model truth stays in the YAML specs.'
"""


def ensure_table():
    run_sql(DDL)


def _spec_diff(element: str, element_kind: str, field: str,
               current: str, proposed: str, rationale: str) -> str:
    """A readable stub of the change to make in the source spec — the artifact
    a modeller takes through the evolution contract. Not applied automatically."""
    ix = atlas.index()
    domain = ""
    path = ""
    if element in ix["entities"]:
        domain = ix["entities"][element]["domain"]
        path = f"model/{domain}/{element}.yaml"
    elif element in ix["metric_views"]:
        domain = ix["metric_views"][element]["domain"]
        path = f"model/semantics/{element}.yaml"
    return (
        f"# Proposed change — take through docs/EVOLUTION.md (semver)\n"
        f"# file: {path or '(resolve element)'}\n"
        f"# element: {element} ({element_kind}), field: {field}\n"
        f"- {field}: {current or '(unset)'}\n"
        f"+ {field}: {proposed}\n"
        f"# rationale: {rationale}\n"
        f"# NOTE: capture-only. This is not applied; regenerate after editing the spec."
    )


def propose(element: str, element_kind: str, field: str, proposed_value: str,
            rationale: str, raised_by: str, current_value: str = "",
            as_of: str = "2026-07-19") -> dict:
    ensure_table()
    diff = _spec_diff(element, element_kind, field, current_value, proposed_value, rationale)
    # action_id derived deterministically-ish from content + a monotonic count.
    existing = run_sql(f"SELECT COUNT(*) FROM {TABLE}")
    n = int(existing[0][0]) + 1 if existing else 1
    aid = f"gov-{n:05d}"

    def esc(s: str) -> str:
        return (s or "").replace("'", "''")

    run_sql(
        f"INSERT INTO {TABLE} VALUES ("
        f"'{aid}', 'proposal', '{esc(element)}', '{esc(element_kind)}', "
        f"'{esc(field)}', '{esc(current_value)}', '{esc(proposed_value)}', "
        f"'{esc(rationale)}', '{esc(raised_by)}', '{as_of}', 'open', '{esc(diff)}')")
    return {"action_id": aid, "status": "open", "spec_diff": diff,
            "note": ("Captured. The model is unchanged — take the spec-diff "
                     "through the evolution contract to apply it.")}


def raise_issue(element: str, element_kind: str, rationale: str,
                raised_by: str, as_of: str = "2026-07-19") -> dict:
    ensure_table()
    existing = run_sql(f"SELECT COUNT(*) FROM {TABLE}")
    n = int(existing[0][0]) + 1 if existing else 1
    aid = f"gov-{n:05d}"

    def esc(s: str) -> str:
        return (s or "").replace("'", "''")

    run_sql(
        f"INSERT INTO {TABLE} VALUES ("
        f"'{aid}', 'issue', '{esc(element)}', '{esc(element_kind)}', "
        f"'', '', '', '{esc(rationale)}', '{esc(raised_by)}', '{as_of}', 'open', '')")
    return {"action_id": aid, "status": "open"}


def list_actions() -> list[dict]:
    ensure_table()
    rows = run_sql(
        f"SELECT action_id, action_type, element, element_kind, field, "
        f"current_value, proposed_value, rationale, raised_by, raised_on, "
        f"status, spec_diff FROM {TABLE} ORDER BY action_id DESC")
    cols = ["action_id", "action_type", "element", "element_kind", "field",
            "current_value", "proposed_value", "rationale", "raised_by",
            "raised_on", "status", "spec_diff"]
    return [dict(zip(cols, r)) for r in rows]
