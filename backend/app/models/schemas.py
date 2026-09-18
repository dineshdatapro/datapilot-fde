from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


Operation = Literal[
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
]

Aggregation = Literal["sum", "mean", "count", "min", "max"]
FilterOperator = Literal["eq", "neq", "gt", "gte", "lt", "lte", "contains", "in"]


class FilterClause(BaseModel):
    column: str
    operator: FilterOperator = "eq"
    value: Any = None
    file: Optional[str] = None


class JoinSpec(BaseModel):
    left_file: str
    right_file: str
    left_on: str
    right_on: str


class AnalyticalPlan(BaseModel):
    operation: Operation
    metric: Optional[str] = None
    aggregation: Optional[Aggregation] = None
    group_by: list[str] = Field(default_factory=list)
    sort: Optional[Literal["asc", "desc"]] = None
    limit: Optional[int] = None
    filters: list[FilterClause] = Field(default_factory=list)
    having: Optional[FilterClause] = None
    files: list[str] = Field(default_factory=list)
    join: Optional[JoinSpec] = None
    time_column: Optional[str] = None
    time_grain: Optional[Literal["day", "month", "year"]] = "month"


class ColumnProfile(BaseModel):
    name: str
    pandas_dtype: str
    semantic_type: str
    missing_count: int
    unique_count: int
    sample_values: list[Any]


class FileProfile(BaseModel):
    file_id: str
    filename: str
    file_type: str
    row_count: int
    column_count: int
    columns: list[ColumnProfile]


class Relationship(BaseModel):
    left_file: str
    left_file_id: str
    left_column: str
    right_file: str
    right_file_id: str
    right_column: str
    confidence: str
    overlap_ratio: float
    reason: str


class VisualizationSpec(BaseModel):
    type: Literal[
        "kpi",
        "bar",
        "line",
        "grouped_bar",
        "horizontal_bar",
        "pie",
        "table",
        "none",
    ]
    title: str
    data: list[dict[str, Any]] = Field(default_factory=list)
    x_key: str = "name"
    y_key: str = "value"
    series_keys: list[str] = Field(default_factory=list)
    value_format: str = "number"


class QueryResponse(BaseModel):
    question: str
    answer: str
    verified: bool
    files_used: list[str]
    rows_analyzed: int
    plan: dict[str, Any]
    result: dict[str, Any]
    visualization: VisualizationSpec
    analysis: dict[str, Any]
    error: Optional[str] = None
