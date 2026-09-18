from __future__ import annotations

from typing import Any

import pandas as pd

from app.models.schemas import ColumnProfile, FileProfile

IDENTIFIER_HINTS = ("id", "uuid", "sku", "code")
BOOLEAN_VALUES = {"true", "false", "yes", "no", "y", "n", "0", "1"}


def _sample_values(series: pd.Series, n: int = 5) -> list[Any]:
    values = series.dropna().astype(str).unique().tolist()
    return values[:n]


def _semantic_type(name: str, series: pd.Series) -> str:
    lower = name.lower().strip()
    non_null = series.dropna()
    if non_null.empty:
        return "text"

    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime" if (non_null.dt.hour != 0).any() or (non_null.dt.minute != 0).any() else "date"
    if pd.api.types.is_numeric_dtype(series):
        unique_ratio = non_null.nunique() / max(len(non_null), 1)
        if lower.endswith("_id") or lower in IDENTIFIER_HINTS or (unique_ratio > 0.9 and non_null.nunique() > 20):
            if any(h in lower for h in IDENTIFIER_HINTS):
                return "identifier"
        return "numeric"

    unique = non_null.nunique()
    unique_ratio = unique / max(len(non_null), 1)
    sample = {str(v).strip().lower() for v in non_null.head(50)}
    if sample and sample.issubset(BOOLEAN_VALUES):
        return "boolean"
    if any(h in lower for h in IDENTIFIER_HINTS) or lower.endswith("_id"):
        return "identifier"
    if unique <= 40 or unique_ratio < 0.08:
        return "categorical"
    if any(k in lower for k in ("date", "time", "_at")):
        parsed = pd.to_datetime(non_null.head(40), errors="coerce", format="mixed")
        if parsed.notna().mean() > 0.8:
            return "date"
    return "text"


def profile_dataframe(file_id: str, filename: str, file_type: str, df: pd.DataFrame) -> FileProfile:
    columns: list[ColumnProfile] = []
    for name in df.columns:
        series = df[name]
        columns.append(
            ColumnProfile(
                name=str(name),
                pandas_dtype=str(series.dtype),
                semantic_type=_semantic_type(str(name), series),
                missing_count=int(series.isna().sum()),
                unique_count=int(series.nunique(dropna=True)),
                sample_values=_sample_values(series),
            )
        )
    return FileProfile(
        file_id=file_id,
        filename=filename,
        file_type=file_type,
        row_count=int(len(df)),
        column_count=int(len(df.columns)),
        columns=columns,
    )
