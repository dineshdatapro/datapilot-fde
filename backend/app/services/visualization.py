from __future__ import annotations

from typing import Any

from app.models.schemas import AnalyticalPlan, VisualizationSpec
from app.utils.formatting import infer_value_kind


def select_visualization(plan: AnalyticalPlan, result: dict[str, Any]) -> VisualizationSpec:
    kind = result.get("kind")
    metric = plan.metric or "value"
    value_format = infer_value_kind(metric, result.get("value"))
    title = _title(plan)

    if kind == "kpi" or plan.operation in {"total", "sum", "average", "count", "minimum", "maximum"}:
        if not result.get("rows"):
            return VisualizationSpec(
                type="kpi",
                title=title,
                data=[{"name": metric, "value": result.get("value", 0)}],
                value_format=value_format,
            )

    rows = result.get("chart_rows") or result.get("rows") or []
    if kind == "table":
        return VisualizationSpec(type="table", title=title, data=rows, value_format=value_format)

    if not rows or not isinstance(rows[0], dict) or "value" not in rows[0]:
        return VisualizationSpec(type="none", title=title, value_format=value_format)

    chart_rows = [{"name": str(r.get("name", "")), "value": r.get("value", 0), **{k: v for k, v in r.items() if k not in {"name", "value"}}} for r in rows]

    if plan.operation == "trend":
        return VisualizationSpec(type="line", title=title, data=chart_rows, value_format=value_format)
    if plan.operation in {"top_n", "bottom_n"}:
        return VisualizationSpec(type="horizontal_bar", title=title, data=chart_rows, value_format=value_format)
    if plan.operation == "comparison":
        return VisualizationSpec(type="bar", title=title, data=chart_rows, value_format=value_format)
    if plan.operation == "group_by" and len(chart_rows) <= 6 and _looks_share(plan):
        return VisualizationSpec(type="pie", title=title, data=chart_rows, value_format=value_format)
    if plan.operation in {"group_by", "cross_file_join", "percentage_change"}:
        return VisualizationSpec(type="bar", title=title, data=chart_rows, value_format=value_format)
    return VisualizationSpec(type="bar", title=title, data=chart_rows, value_format=value_format)


def _looks_share(plan: AnalyticalPlan) -> bool:
    text = " ".join(plan.group_by).lower()
    return any(k in text for k in ("segment", "category", "region"))


def _title(plan: AnalyticalPlan) -> str:
    metric = (plan.metric or "Records").replace("_", " ").title()
    agg = {"sum": "Total", "mean": "Average", "count": "Count", "min": "Minimum", "max": "Maximum"}.get(
        plan.aggregation or "", ""
    )
    if plan.operation == "trend":
        return f"{metric} trend"
    if plan.operation == "comparison":
        return f"{metric} comparison"
    if plan.group_by:
        by = ", ".join(g.replace("_", " ") for g in plan.group_by)
        return f"{agg or 'Total'} {metric.lower()} by {by}".strip()
    return f"{agg or 'Total'} {metric.lower()}".strip().title()
