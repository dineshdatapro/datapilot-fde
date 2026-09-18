from __future__ import annotations

from typing import Any

from app.models.schemas import AnalyticalPlan
from app.services.llm_planner import explain_result
from app.utils.formatting import format_value, infer_value_kind


def _public_result(plan: AnalyticalPlan, result: dict[str, Any]) -> dict[str, Any]:
    kind = infer_value_kind(plan.metric, result.get("value"))
    payload: dict[str, Any] = {
        "kind": result.get("kind"),
        "formatted_value": format_value(result.get("value"), kind),
        "value": result.get("value"),
        "label": result.get("label"),
        "metric": plan.metric,
        "aggregation": result.get("aggregation"),
        "percentage_change": result.get("percentage_change"),
        "row_count": len(result.get("rows") or []),
    }
    rows = result.get("rows") or []
    if rows and isinstance(rows[0], dict) and "value" in rows[0]:
        payload["rows"] = [
            {
                "name": r.get("name"),
                "value": r.get("value"),
                "formatted": format_value(r.get("value"), kind),
            }
            for r in rows[:12]
        ]
    return payload


async def generate_answer(question: str, plan: AnalyticalPlan, result: dict[str, Any]) -> str:
    public = _public_result(plan, result)
    try:
        text = await explain_result(question, public)
    except Exception:
        text = _fallback_answer(plan, result, public)
    return text.replace("**", "").strip()


def _fallback_answer(plan: AnalyticalPlan, result: dict[str, Any], public: dict[str, Any]) -> str:
    formatted = public["formatted_value"]
    metric = (plan.metric or "value").replace("_", " ")
    if result.get("kind") == "grouped" and result.get("label"):
        if plan.operation in {"top_n", "group_by"} and plan.limit == 1:
            return f"{result['label']} generated {formatted} in {metric}, the highest result in the uploaded data."
        return f"{metric.title()} grouped as requested. The leading category is {result['label']} at {formatted}."
    if plan.operation == "average":
        return f"The average {metric} is {formatted}."
    if plan.operation == "count":
        return f"There are {formatted} matching records in the uploaded data."
    if plan.operation == "comparison" and public.get("percentage_change") is not None:
        return f"{metric.title()} compared across groups. Latest relative change is {public['percentage_change']}%."
    return f"Total {metric} is {formatted}."
