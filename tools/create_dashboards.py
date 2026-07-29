#!/usr/bin/env python3
"""Create Lakeview dashboards over the CERTIFIED metric views.

Purpose is twofold: (1) they're genuinely useful views of the governed metrics,
and (2) they are high-authority sources for Genie Ontology to harvest — dashboards
built on certified, owned, fresh metric views are exactly what its authority
weighting ranks to the top. So the ontology uncovers our governed definitions,
not a mess.

Datasets query the metric views with MEASURE() (verified to work in Lakeview),
so the numbers ARE the governed definitions — nothing re-implemented here.

Usage: uv run --with databricks-sdk tools/create_dashboards.py --profile DEFAULT
"""
import argparse
import json
import uuid

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import Dashboard

CATALOG = "lr_serverless_aws_us_catalog"
PARENT = "/Workspace/Shared/bricksurance-data-core/dashboards"
COLORS = ["#12566e", "#c57a1f", "#1f7a4d", "#8BCAE7", "#AB4057", "#b07600"]


def _id():
    return uuid.uuid4().hex[:8]


def ds(name, display, sql_lines):
    return {"name": name, "displayName": display, "queryLines": sql_lines}


def text(name, md, x, y, w, h):
    return {"widget": {"name": name, "multilineTextboxSpec": {"lines": [md]}},
            "position": {"x": x, "y": y, "width": w, "height": h}}


def counter(name, dsname, field, title, x, y, w=2, h=3, fmt=None):
    enc = {"value": {"fieldName": field, "displayName": title}}
    return {"widget": {"name": name,
                       "queries": [{"name": "main_query", "query": {
                           "datasetName": dsname,
                           "fields": [{"name": field, "expression": f"`{field}`"}],
                           "disaggregated": True}}],
                       "spec": {"version": 2, "widgetType": "counter", "encodings": enc,
                                "frame": {"showTitle": True, "title": title}}},
            "position": {"x": x, "y": y, "width": w, "height": h}}


def bar(name, dsname, xf, yf, title, x, y, w=3, h=6, sort_desc=True, color=None):
    xenc = {"fieldName": xf, "scale": {"type": "categorical"}, "displayName": xf}
    if sort_desc:
        xenc["scale"]["sort"] = {"by": "y-reversed"}
    enc = {"x": xenc,
           "y": {"fieldName": yf, "scale": {"type": "quantitative"}, "displayName": yf},
           "label": {"show": True}}
    if color:
        enc["color"] = {"fieldName": color, "scale": {"type": "categorical"}, "displayName": color}
    return {"widget": {"name": name,
                       "queries": [{"name": "main_query", "query": {
                           "datasetName": dsname,
                           "fields": [{"name": xf, "expression": f"`{xf}`"},
                                      {"name": yf, "expression": f"`{yf}`"}]
                                     + ([{"name": color, "expression": f"`{color}`"}] if color else []),
                           "disaggregated": True}}],
                       "spec": {"version": 3, "widgetType": "bar", "encodings": enc,
                                "frame": {"showTitle": True, "title": title},
                                "mark": {"colors": COLORS}}},
            "position": {"x": x, "y": y, "width": w, "height": h}}


def line(name, dsname, xf, yf, cf, title, x, y, w=6, h=6):
    return {"widget": {"name": name,
                       "queries": [{"name": "main_query", "query": {
                           "datasetName": dsname,
                           "fields": [{"name": xf, "expression": f"`{xf}`"},
                                      {"name": yf, "expression": f"`{yf}`"},
                                      {"name": cf, "expression": f"`{cf}`"}],
                           "disaggregated": True}}],
                       "spec": {"version": 3, "widgetType": "line",
                                "encodings": {
                                    "x": {"fieldName": xf, "scale": {"type": "quantitative"}, "displayName": "Development lag"},
                                    "y": {"fieldName": yf, "scale": {"type": "quantitative"}, "displayName": "Cumulative paid"},
                                    "color": {"fieldName": cf, "scale": {"type": "categorical"}, "displayName": "Accident year"}},
                                "frame": {"showTitle": True, "title": title},
                                "mark": {"colors": COLORS}}},
            "position": {"x": x, "y": y, "width": w, "height": h}}


def table(name, dsname, cols, title, x, y, w=6, h=6):
    return {"widget": {"name": name,
                       "queries": [{"name": "main_query", "query": {
                           "datasetName": dsname,
                           "fields": [{"name": c, "expression": f"`{c}`"} for c, _ in cols],
                           "disaggregated": True}}],
                       "spec": {"version": 2, "widgetType": "table",
                                "encodings": {"columns": [{"fieldName": c, "displayName": d} for c, d in cols]},
                                "frame": {"showTitle": True, "title": title}}},
            "position": {"x": x, "y": y, "width": w, "height": h}}


def dashboard_json(datasets, layout):
    return json.dumps({
        "datasets": datasets,
        "pages": [{"name": _id(), "displayName": "Overview",
                   "pageType": "PAGE_TYPE_CANVAS", "layout": layout}],
        "uiSettings": {"theme": {"widgetHeaderAlignment": "ALIGNMENT_UNSPECIFIED"}},
    })


def build_underwriting():
    S = f"{CATALOG}.bricksurance_semantics.underwriting_metrics"
    kpi = ds("uw_kpi", "Underwriting KPIs (GBP)", [
        f"SELECT MEASURE(gross_written_premium) AS gwp, MEASURE(claims_incurred) AS incurred, "
        f"MEASURE(loss_ratio_written) AS loss_ratio, MEASURE(policy_count) AS policies "
        f"FROM {S} WHERE currency_code='GBP'"])
    lob = ds("uw_lob", "By line of business (GBP)", [
        f"SELECT line_of_business, MEASURE(gross_written_premium) AS gwp, "
        f"MEASURE(claims_incurred) AS incurred, MEASURE(loss_ratio_written) AS loss_ratio "
        f"FROM {S} WHERE currency_code='GBP' GROUP BY line_of_business"])
    layout = [
        text("t", "## Underwriting — certified metrics (Bricksurance SE)", 0, 0, 6, 1),
        text("s", "Gross written premium and written-basis loss ratio, from the certified `underwriting_metrics` metric view (GBP). Synthetic data.", 0, 1, 6, 1),
        counter("c1", "uw_kpi", "gwp", "Gross written premium", 0, 2),
        counter("c2", "uw_kpi", "incurred", "Claims incurred", 2, 2),
        counter("c3", "uw_kpi", "loss_ratio", "Loss ratio (written)", 4, 2),
        bar("b1", "uw_lob", "line_of_business", "gwp", "GWP by line of business", 0, 5, 3, 6),
        bar("b2", "uw_lob", "line_of_business", "loss_ratio", "Loss ratio by line of business", 3, 5, 3, 6),
        table("tb", "uw_lob", [("line_of_business", "Line"), ("gwp", "GWP"), ("incurred", "Incurred"), ("loss_ratio", "Loss ratio")], "Underwriting by line", 0, 11, 6, 5),
    ]
    return "Bricksurance — Underwriting metrics", dashboard_json([kpi, lob], layout)


def build_reserving():
    R = f"{CATALOG}.bricksurance_reserving.reserving_metrics"
    E = f"{CATALOG}.bricksurance_reserving.reserve_estimate"
    tri = ds("rsv_tri", "Paid development (CP, GBP)", [
        f"SELECT accident_year, development_lag, MEASURE(paid_to_date) AS cumulative_paid "
        f"FROM {R} WHERE line_of_business='Commercial Property' AND currency_code='GBP' "
        f"GROUP BY accident_year, development_lag"])
    est = ds("rsv_est", "Reserve estimates (CP, GBP, chain-ladder)", [
        f"SELECT accident_year, ultimate_loss, paid_to_date, ibnr "
        f"FROM {E} WHERE line_of_business_code='COMMERCIAL_PROPERTY' AND currency_code='GBP' "
        f"AND reserving_method_code='CHAIN_LADDER'"])
    layout = [
        text("t", "## Reserving — loss-development triangle (Commercial Property, GBP)", 0, 0, 6, 1),
        text("s", "Cumulative paid by accident year and development lag, and chain-ladder ultimate/IBNR — from the certified `reserving_metrics` view and `reserve_estimate`. Synthetic data.", 0, 1, 6, 1),
        line("l1", "rsv_tri", "development_lag", "cumulative_paid", "accident_year", "Cumulative paid development by accident year", 0, 2, 6, 6),
        bar("b1", "rsv_est", "accident_year", "ultimate_loss", "Projected ultimate by accident year", 0, 8, 3, 6, sort_desc=False),
        bar("b2", "rsv_est", "accident_year", "ibnr", "IBNR by accident year", 3, 8, 3, 6, sort_desc=False),
        table("tb", "rsv_est", [("accident_year", "Accident year"), ("paid_to_date", "Paid"), ("ibnr", "IBNR"), ("ultimate_loss", "Ultimate")], "Reserve estimates (chain-ladder)", 0, 14, 6, 5),
    ]
    return "Bricksurance — Reserving triangle", dashboard_json([tri, est], layout)


def build_valuation():
    V = f"{CATALOG}.bricksurance_semantics.valuation_metrics"
    meas = ds("val_meas", "Valuation measures (GBP)", [
        f"SELECT valuation_measure_code, MEASURE(total_amount) AS amount "
        f"FROM {V} WHERE currency_code='GBP' GROUP BY valuation_measure_code"])
    lob = ds("val_lob", "Technical provisions by line (GBP)", [
        f"SELECT line_of_business, MEASURE(total_amount) AS amount "
        f"FROM {V} WHERE currency_code='GBP' AND valuation_measure_code='TECHNICAL_PROVISION' "
        f"GROUP BY line_of_business"])
    layout = [
        text("t", "## Valuation & capital — Solvency II / IFRS 17 measures (GBP)", 0, 0, 6, 1),
        text("s", "Published valuation figures (SCR, BEL, technical provisions, IBNR…) from the certified `valuation_metrics` view — one surface across regimes. Synthetic data.", 0, 1, 6, 1),
        bar("b1", "val_meas", "valuation_measure_code", "amount", "By valuation measure", 0, 2, 6, 6),
        bar("b2", "val_lob", "line_of_business", "amount", "Technical provisions by line", 0, 8, 3, 6),
        table("tb", "val_meas", [("valuation_measure_code", "Measure"), ("amount", "Amount (GBP)")], "Valuation measures", 3, 8, 3, 6),
    ]
    return "Bricksurance — Valuation & capital", dashboard_json([meas, lob], layout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="DEFAULT")
    args = ap.parse_args()
    w = WorkspaceClient(profile=args.profile)
    running = [wh for wh in w.warehouses.list() if wh.state and wh.state.value == "RUNNING"]
    wid = (running or list(w.warehouses.list()))[0].id
    # ensure parent folder
    try:
        w.workspace.mkdirs(PARENT)
    except Exception:  # noqa: BLE001
        pass
    existing = {d.display_name: d.dashboard_id for d in w.lakeview.list()}
    for builder in (build_underwriting, build_reserving, build_valuation):
        name, serialized = builder()
        if name in existing:
            w.lakeview.update(dashboard_id=existing[name],
                              dashboard=Dashboard(display_name=name, serialized_dashboard=serialized))
            w.lakeview.publish(dashboard_id=existing[name], warehouse_id=wid)
            print(f"updated+published: {name} ({existing[name]})")
        else:
            d = w.lakeview.create(dashboard=Dashboard(
                display_name=name, warehouse_id=wid, parent_path=PARENT,
                serialized_dashboard=serialized))
            w.lakeview.publish(dashboard_id=d.dashboard_id, warehouse_id=wid)
            print(f"created+published: {name} ({d.dashboard_id})")


if __name__ == "__main__":
    main()
