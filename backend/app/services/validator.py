from __future__ import annotations

from typing import Any

from app.models.schemas import AnalyticalPlan, FileProfile
from app.services.session_store import Session

NUMERIC_OPS = {
    "total",
    "sum",
    "average",
    "minimum",
    "maximum",
    "group_by",
    "comparison",
    "trend",
    "top_n",
    "bottom_n",
    "percentage_change",
    "cross_file_join",
}

DATE_OPS = {"trend"}


class PlanValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _numeric_fields(session: Session) -> list[str]:
    names: list[str] = []
    for f in session.files.values():
        for col in f.profile.columns:
            if col.semantic_type == "numeric" and col.name not in names:
                names.append(col.name)
    return names


def _find_column(name: str | None, session: Session) -> tuple[str, str] | None:
    if not name:
        return None
    for f in session.files.values():
        for col in f.profile.columns:
            if col.name.lower() == name.lower():
                return f.filename, col.name
    return None


def _column_values(session: Session, column: str) -> set[str]:
    values: set[str] = set()
    for f in session.files.values():
        if column in f.dataframe.columns:
            values.update(f.dataframe[column].dropna().astype(str).str.strip().head(8000).tolist())
    return values


def validate_plan(plan: AnalyticalPlan, session: Session) -> AnalyticalPlan:
    if not session.files:
        raise PlanValidationError("Upload at least one CSV or Excel file before asking a question.")

    if plan.operation not in {
        "total",
        "sum",
        "average",
        "count",
        "minimum",
        "maximum",
        "filter",
        "group_by",
        "comparison",
        "trend",
        "top_n",
        "bottom_n",
        "percentage_change",
        "cross_file_join",
    }:
        raise PlanValidationError(
            "I can currently answer questions involving totals, averages, filters, "
            "comparisons, trends, grouping, and top/bottom results."
        )

    resolved_files: list[str] = []
    if plan.files:
        available = {f.filename.lower(): f.filename for f in session.files.values()}
        available_ids = {f.file_id: f.filename for f in session.files.values()}
        for name in plan.files:
            if name in available_ids:
                resolved_files.append(available_ids[name])
            elif name.lower() in available:
                resolved_files.append(available[name.lower()])
            else:
                raise PlanValidationError(
                    f"I couldn't find a file named '{name}' in this session. "
                    f"Uploaded files: {', '.join(available.values())}."
                )
        plan.files = resolved_files

    if plan.operation in NUMERIC_OPS and plan.operation != "count":
        if not plan.metric:
            numeric = _numeric_fields(session)
            extra = f"\n\nAvailable numeric fields:\n" + "\n".join(f"• {n}" for n in numeric) if numeric else ""
            raise PlanValidationError("This question needs a numeric field to measure." + extra)
        found = _find_column(plan.metric, session)
        if not found:
            numeric = _numeric_fields(session)
            extra = "\n".join(f"• {n}" for n in numeric) if numeric else "• (none)"
            raise PlanValidationError(
                f"I couldn't answer this because no uploaded dataset contains a {plan.metric} field.\n\n"
                f"Available numeric fields:\n{extra}"
            )
        plan.metric = found[1]
        semantic = None
        for f in session.files.values():
            for col in f.profile.columns:
                if col.name == plan.metric:
                    semantic = col.semantic_type
        if semantic and semantic not in {"numeric"} and plan.operation != "count":
            raise PlanValidationError(
                f"'{plan.metric}' is not a numeric field, so totals, averages, and similar calculations aren't valid."
            )

    resolved_groups: list[str] = []
    for col in plan.group_by:
        found = _find_column(col, session)
        if not found:
            raise PlanValidationError(
                f"The requested field '{col}' wasn't found in your uploaded data."
            )
        resolved_groups.append(found[1])
    plan.group_by = resolved_groups

    if plan.time_column:
        found = _find_column(plan.time_column, session)
        if not found:
            # month / year may be derived
            found = _find_column("month", session)
        if plan.operation in DATE_OPS and not found and "month" not in [c.lower() for files in session.files.values() for c in files.dataframe.columns]:
            raise PlanValidationError("I need a date or month column to calculate a trend.")
        if found:
            plan.time_column = found[1]

    for flt in plan.filters + ([plan.having] if plan.having else []):
        if plan.having and flt is plan.having and flt.column.lower() in {"value", "metric", (plan.metric or "").lower()}:
            flt.column = "value"
            continue
        found = _find_column(flt.column, session)
        if not found:
            raise PlanValidationError(
                f"The requested field '{flt.column}' wasn't found in your uploaded data."
            )
        flt.column = found[1]
        if flt.operator in {"eq", "contains"} and flt.value is not None and flt.operator == "eq":
            values = _column_values(session, flt.column)
            raw = str(flt.value).strip()
            resolved = _resolve_filter_value(flt.column, raw, values)
            if resolved is not None:
                flt.value = resolved
            elif values and raw not in values:
                raise PlanValidationError(
                    f"I found the {flt.column} field, but {raw} does not appear in the uploaded data."
                )

    if plan.join:
        left = _find_file(session, plan.join.left_file)
        right = _find_file(session, plan.join.right_file)
        if not left or not right:
            raise PlanValidationError("The requested join refers to a file that isn't uploaded.")
        if plan.join.left_on not in left.dataframe.columns:
            raise PlanValidationError(f"Join column '{plan.join.left_on}' was not found in {left.filename}.")
        if plan.join.right_on not in right.dataframe.columns:
            raise PlanValidationError(f"Join column '{plan.join.right_on}' was not found in {right.filename}.")
        plan.join.left_file = left.filename
        plan.join.right_file = right.filename

    if plan.operation in {"top_n", "bottom_n"} and not plan.limit:
        plan.limit = 5
    if plan.operation in {"top_n", "bottom_n"} and not plan.group_by:
        raise PlanValidationError("Top/bottom questions need a category to rank, such as product or region.")

    return plan


MONTH_ALIASES = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}


def _resolve_filter_value(column: str, raw: str, values: set[str]) -> str | None:
    if raw in values:
        return raw
    match = next((v for v in values if v.lower() == raw.lower()), None)
    if match:
        return match
    if column.lower() in {"month", "order_date"}:
        alias = MONTH_ALIASES.get(raw.lower())
        if alias:
            period = next((v for v in values if v.endswith(f"-{alias}") or v[5:7] == alias), None)
            if period:
                return period
    return None


def _find_file(session: Session, name: str):
    for f in session.files.values():
        if f.filename == name or f.file_id == name or f.filename.lower() == name.lower():
            return f
    return None


def available_schema_summary(profiles: list[FileProfile]) -> dict[str, Any]:
    return {
        "files": [
            {
                "filename": p.filename,
                "rows": p.row_count,
                "columns": [
                    {
                        "name": c.name,
                        "type": c.semantic_type,
                        "samples": c.sample_values[:4],
                    }
                    for c in p.columns
                ],
            }
            for p in profiles
        ]
    }
