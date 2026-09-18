from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd


CURRENCY_HINTS = ("revenue", "amount", "price", "sales", "cost", "fee", "mrr", "arr")


def infer_value_kind(column: str | None, value: Any) -> str:
    name = (column or "").lower()
    if any(h in name for h in CURRENCY_HINTS):
        return "currency"
    if "percent" in name or name.endswith("_pct") or name.endswith("_rate"):
        return "percentage"
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return "date"
    return "number"


def format_indian_number(value: float | int, decimals: int = 0) -> str:
    negative = value < 0
    value = abs(float(value))
    integer, frac = f"{value:.{decimals}f}".split(".")
    s = integer
    if len(s) <= 3:
        grouped = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while rest:
            parts.append(rest[-2:])
            rest = rest[:-2]
        grouped = ",".join(reversed(parts)) + "," + last3
    if decimals > 0 and int(frac) != 0:
        out = f"{grouped}.{frac}"
    else:
        out = grouped
    return f"-{out}" if negative else out


def format_compact_inr(value: float | int) -> str:
    n = float(value)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 10_000_000:
        return f"{sign}₹{n / 10_000_000:.1f} Cr".replace(".0 Cr", " Cr")
    if n >= 100_000:
        return f"{sign}₹{n / 100_000:.1f} L".replace(".0 L", " L")
    if n >= 1000:
        return f"{sign}₹{format_indian_number(n, 0)}"
    if n == int(n):
        return f"{sign}₹{int(n)}"
    return f"{sign}₹{n:.2f}"


def format_value(value: Any, kind: str = "number") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if kind == "date":
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return str(value)
        return ts.strftime("%d %b %Y")
    if kind == "percentage":
        return f"{float(value):.1f}%"
    if kind == "currency":
        return format_compact_inr(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if float(value).is_integer():
            return format_indian_number(int(value), 0)
        return format_indian_number(float(value), 2)
    return str(value)


def sanitize_filename(name: str) -> str:
    base = name.replace("\\", "/").split("/")[-1]
    cleaned = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in base)
    cleaned = cleaned.strip().replace(" ", "_")
    return cleaned or "upload"
