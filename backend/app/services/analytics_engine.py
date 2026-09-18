from __future__ import annotations

from typing import Any

import pandas as pd

from app.models.schemas import AnalyticalPlan, FilterClause, JoinSpec
from app.services.session_store import Session, StoredFile
from app.utils.formatting import infer_value_kind


class AnalyticsError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def execute_plan(plan: AnalyticalPlan, session: Session) -> dict[str, Any]:
    df, files_used = _prepare_frame(plan, session)
    rows_analyzed = int(len(df))
    df = filter_data(df, plan.filters)

    op = plan.operation
    if op in {"total", "sum"}:
        result = aggregate(df, plan.metric, "sum")
    elif op == "average":
        result = aggregate(df, plan.metric, "mean")
    elif op == "count":
        result = {"value": int(len(df)), "metric": plan.metric or "rows", "aggregation": "count"}
    elif op == "minimum":
        result = aggregate(df, plan.metric, "min")
    elif op == "maximum":
        result = aggregate(df, plan.metric, "max")
    elif op == "filter":
        result = _table_result(df, plan)
    elif op in {"group_by", "top_n", "bottom_n", "comparison", "trend", "cross_file_join"}:
        group_cols = list(plan.group_by)
        if op == "trend":
            grain_col = _trend_column(df, plan)
            group_cols = [grain_col]
        if not group_cols:
            result = aggregate(df, plan.metric, plan.aggregation or "sum")
        else:
            grouped = group_by(df, group_cols, plan.metric, plan.aggregation or "sum")
            grouped = _apply_having(grouped, plan.having)
            sort_dir = plan.sort or ("asc" if op == "bottom_n" else "desc")
            if op == "trend":
                grouped = grouped.sort_values(group_cols[0])
            elif "value" in grouped.columns:
                grouped = grouped.sort_values("value", ascending=sort_dir == "asc")
            ranked = grouped.copy()
            if plan.limit:
                grouped = grouped.head(int(plan.limit))
            elif op in {"top_n", "bottom_n"}:
                grouped = grouped.head(5)
            result = _grouped_result(grouped, group_cols, plan)
            result["chart_rows"] = _grouped_result(ranked.head(12), group_cols, plan)["rows"]
            if op == "percentage_change" or (op == "comparison" and len(grouped) == 2):
                result["percentage_change"] = _pct_change(grouped)
    elif op == "percentage_change":
        group_cols = plan.group_by or [_trend_column(df, plan)]
        grouped = group_by(df, group_cols, plan.metric, plan.aggregation or "sum")
        grouped = grouped.sort_values(group_cols[0])
        result = _grouped_result(grouped, group_cols, plan)
        result["percentage_change"] = _pct_change(grouped)
    else:
        raise AnalyticsError(
            "I can currently answer questions involving totals, averages, filters, "
            "comparisons, trends, grouping, and top/bottom results."
        )

    result["files_used"] = files_used
    result["rows_analyzed"] = rows_analyzed
    result["rows_after_filter"] = int(len(df))
    result["metric"] = plan.metric
    result["aggregation"] = _resolved_agg(plan)
    result["group_by"] = plan.group_by
    result["filters"] = [f.model_dump() for f in plan.filters]
    result["value_kind"] = infer_value_kind(plan.metric, result.get("value"))
    return result


def _resolved_agg(plan: AnalyticalPlan) -> str:
    if plan.aggregation:
        return plan.aggregation
    mapping = {
        "average": "mean",
        "minimum": "min",
        "maximum": "max",
        "count": "count",
        "total": "sum",
        "sum": "sum",
    }
    return mapping.get(plan.operation, "sum")


def _prepare_frame(plan: AnalyticalPlan, session: Session) -> tuple[pd.DataFrame, list[str]]:
    files = list(session.files.values())
    if plan.files:
        wanted = {n.lower() for n in plan.files}
        files = [f for f in files if f.filename.lower() in wanted or f.file_id in plan.files]
        if not files:
            raise AnalyticsError("None of the referenced files are available in this session.")

    join = plan.join or _infer_join(plan, session)
    if join:
        left = _file_by_name(session, join.left_file)
        right = _file_by_name(session, join.right_file)
        left_peers = [
            f
            for f in session.files.values()
            if join.left_on in f.dataframe.columns and set(left.dataframe.columns) & set(f.dataframe.columns)
        ]
        if plan.metric:
            metric_peers = [f for f in left_peers if plan.metric in f.dataframe.columns]
            if metric_peers:
                left_peers = metric_peers
        left_frame = _concat_compatible(left_peers or [left], _needed_columns(plan))
        merged = join_datasets(left_frame, right.dataframe, join)
        names = [f.filename for f in (left_peers or [left])] + [right.filename]
        return merged, list(dict.fromkeys(names))

    needed = _needed_columns(plan)
    matching = [f for f in files if any(col in f.dataframe.columns for col in needed)]
    if plan.metric:
        with_metric = [f for f in files if plan.metric in f.dataframe.columns]
        if with_metric:
            matching = with_metric

    if not matching:
        matching = files

    compatible = _concat_compatible(matching, needed)
    names = [f.filename for f in matching]
    return compatible, names


def _needed_columns(plan: AnalyticalPlan) -> list[str]:
    cols = []
    if plan.metric:
        cols.append(plan.metric)
    cols.extend(plan.group_by)
    cols.extend(f.column for f in plan.filters)
    if plan.time_column:
        cols.append(plan.time_column)
    return cols


def _infer_join(plan: AnalyticalPlan, session: Session) -> JoinSpec | None:
    if not session.relationships:
        return None
    metric_files = []
    group_files = []
    if plan.metric:
        metric_files = [f for f in session.files.values() if plan.metric in f.dataframe.columns]
    for col in plan.group_by:
        group_files.extend([f for f in session.files.values() if col in f.dataframe.columns])
    if not metric_files or not group_files:
        return None
    metric_ids = {f.file_id for f in metric_files}
    group_ids = {f.file_id for f in group_files}
    if metric_ids & group_ids:
        return None
    ranked: list[tuple[int, JoinSpec]] = []
    for rel in session.relationships:
        if (rel.left_file_id in metric_ids and rel.right_file_id in group_ids) or (
            rel.right_file_id in metric_ids and rel.left_file_id in group_ids
        ):
            score = 0
            if rel.left_column.lower().endswith("_id") or rel.right_column.lower().endswith("_id"):
                score += 5
            if rel.confidence == "high":
                score += 2
            score += int(rel.overlap_ratio * 10)
            ranked.append(
                (
                    score,
                    JoinSpec(
                        left_file=rel.left_file,
                        right_file=rel.right_file,
                        left_on=rel.left_column,
                        right_on=rel.right_column,
                    ),
                )
            )
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _file_by_name(session: Session, name: str) -> StoredFile:
    for f in session.files.values():
        if f.filename == name or f.file_id == name:
            return f
    raise AnalyticsError(f"File '{name}' is not in the session.")


def _concat_compatible(files: list[StoredFile], needed: list[str]) -> pd.DataFrame:
    frames = []
    for f in files:
        df = f.dataframe.copy()
        df["_source_file"] = f.filename
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def join_datasets(left: pd.DataFrame, right: pd.DataFrame, spec: JoinSpec) -> pd.DataFrame:
    l = left.copy()
    r = right.copy()
    overlap = set(l.columns) & set(r.columns) - {spec.left_on, spec.right_on}
    if spec.left_on == spec.right_on:
        return l.merge(r, how="left", on=spec.left_on, suffixes=("", "_right"))
    r = r.rename(columns={c: f"{c}_right" for c in overlap})
    return l.merge(r, how="left", left_on=spec.left_on, right_on=spec.right_on)


def filter_data(df: pd.DataFrame, filters: list[FilterClause]) -> pd.DataFrame:
    out = df
    for flt in filters:
        if flt.column not in out.columns:
            continue
        series = out[flt.column]
        op = flt.operator
        val = flt.value
        if op == "eq":
            out = out[series.astype(str).str.lower() == str(val).lower()]
        elif op == "neq":
            out = out[series.astype(str).str.lower() != str(val).lower()]
        elif op == "contains":
            out = out[series.astype(str).str.contains(str(val), case=False, na=False)]
        elif op == "in":
            values = val if isinstance(val, list) else [val]
            lowered = {str(v).lower() for v in values}
            out = out[series.astype(str).str.lower().isin(lowered)]
        elif op in {"gt", "gte", "lt", "lte"}:
            numeric = pd.to_numeric(series, errors="coerce")
            cmp = pd.to_numeric(pd.Series([val]), errors="coerce").iloc[0]
            if pd.isna(cmp):
                continue
            if op == "gt":
                out = out[numeric > cmp]
            elif op == "gte":
                out = out[numeric >= cmp]
            elif op == "lt":
                out = out[numeric < cmp]
            else:
                out = out[numeric <= cmp]
    return out


def aggregate(df: pd.DataFrame, metric: str | None, how: str) -> dict[str, Any]:
    if metric is None or metric not in df.columns:
        raise AnalyticsError("The requested metric is not present in the prepared dataset.")
    series = pd.to_numeric(df[metric], errors="coerce")
    if how == "sum":
        value = float(series.sum(skipna=True))
    elif how == "mean":
        value = float(series.mean(skipna=True)) if series.notna().any() else 0.0
    elif how == "min":
        value = float(series.min(skipna=True)) if series.notna().any() else 0.0
    elif how == "max":
        value = float(series.max(skipna=True)) if series.notna().any() else 0.0
    elif how == "count":
        value = int(series.notna().sum())
    else:
        value = float(series.sum(skipna=True))
    if how != "mean" and float(value).is_integer():
        coerced: Any = int(value)
    else:
        coerced = round(value, 4)
    return {"value": coerced, "metric": metric, "aggregation": how, "kind": "kpi"}


def group_by(df: pd.DataFrame, group_cols: list[str], metric: str | None, how: str) -> pd.DataFrame:
    missing = [c for c in group_cols if c not in df.columns]
    if missing:
        raise AnalyticsError(f"The requested field wasn't found in your uploaded data: {', '.join(missing)}.")
    grouped = df.groupby(group_cols, dropna=False)
    if how == "count" or metric is None:
        out = grouped.size().reset_index(name="value")
    else:
        series = pd.to_numeric(df[metric], errors="coerce")
        tmp = df.copy()
        tmp["_metric"] = series
        agg_map = {"sum": "sum", "mean": "mean", "min": "min", "max": "max", "count": "count"}
        out = tmp.groupby(group_cols, dropna=False)["_metric"].agg(agg_map.get(how, "sum")).reset_index(name="value")
    out["value"] = out["value"].fillna(0)
    return out


def _apply_having(df: pd.DataFrame, having: FilterClause | None) -> pd.DataFrame:
    if not having:
        return df
    clause = FilterClause(column="value", operator=having.operator, value=having.value)
    if having.column != "value" and having.column in df.columns:
        clause.column = having.column
    return filter_data(df, [clause])


def _trend_column(df: pd.DataFrame, plan: AnalyticalPlan) -> str:
    if plan.time_column and plan.time_column in df.columns:
        return plan.time_column
    for candidate in ("month", "month_name", "order_date", "date"):
        if candidate in df.columns:
            return candidate
    if plan.group_by:
        return plan.group_by[0]
    raise AnalyticsError("I need a date or month column to calculate a trend.")


def _grouped_result(grouped: pd.DataFrame, group_cols: list[str], plan: AnalyticalPlan) -> dict[str, Any]:
    rows = []
    for rec in grouped.to_dict(orient="records"):
        label = " / ".join(str(rec[c]) for c in group_cols)
        value = rec.get("value", 0)
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        elif isinstance(value, float):
            value = round(value, 4)
        item = {"name": label, "value": value}
        for c in group_cols:
            item[c] = rec[c]
        rows.append(item)
    top = rows[0] if rows else None
    return {
        "kind": "grouped",
        "rows": rows,
        "top": top,
        "value": top["value"] if top else 0,
        "label": top["name"] if top else None,
        "metric": plan.metric,
        "aggregation": _resolved_agg(plan),
    }


def _table_result(df: pd.DataFrame, plan: AnalyticalPlan) -> dict[str, Any]:
    preview = df.head(50)
    cols = [c for c in preview.columns if not c.startswith("_")][:12]
    records = preview[cols].astype(str).to_dict(orient="records")
    return {
        "kind": "table",
        "rows": records,
        "columns": cols,
        "value": int(len(df)),
        "metric": plan.metric,
        "aggregation": "count",
    }


def _pct_change(grouped: pd.DataFrame) -> float | None:
    if "value" not in grouped.columns or len(grouped) < 2:
        return None
    values = grouped["value"].tolist()
    first, last = float(values[0]), float(values[-1])
    if first == 0:
        return None
    return round(((last - first) / first) * 100, 2)
