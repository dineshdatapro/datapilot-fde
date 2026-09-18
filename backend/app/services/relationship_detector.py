from __future__ import annotations

import pandas as pd

from app.models.schemas import Relationship
from app.services.session_store import StoredFile


def detect_relationships(files: dict[str, StoredFile]) -> list[Relationship]:
    items = list(files.values())
    found: list[Relationship] = []
    for i, left in enumerate(items):
        for right in items[i + 1 :]:
            found.extend(_pair_relationships(left, right))
    return found


def _pair_relationships(left: StoredFile, right: StoredFile) -> list[Relationship]:
    shared = set(left.dataframe.columns) & set(right.dataframe.columns)
    if len(shared) / max(len(left.dataframe.columns), 1) >= 0.7:
        return []

    rels: list[Relationship] = []
    left_cols = {c.name: c for c in left.profile.columns}
    right_cols = {c.name: c for c in right.profile.columns}
    skip = {"month", "year", "month_name"}

    candidates: list[tuple[str, str, str]] = []
    for lname, lcol in left_cols.items():
        if lname in skip:
            continue
        if lname in right_cols:
            rcol = right_cols[lname]
            if _is_join_key(lcol.semantic_type, lname) or _is_join_key(rcol.semantic_type, lname):
                candidates.append((lname, lname, "matching column names"))
            continue
        for rname, rcol in right_cols.items():
            if rname in skip:
                continue
            if lname.lower() == rname.lower() and (
                _is_join_key(lcol.semantic_type, lname) or _is_join_key(rcol.semantic_type, rname)
            ):
                candidates.append((lname, rname, "matching column names"))
            elif lcol.semantic_type == "identifier" and rcol.semantic_type == "identifier":
                if _token_overlap(lname, rname):
                    candidates.append((lname, rname, "similar identifier columns"))

    seen: set[tuple[str, str]] = set()
    for lname, rname, reason in candidates:
        key = (lname, rname)
        if key in seen:
            continue
        seen.add(key)
        overlap = _value_overlap(left.dataframe[lname], right.dataframe[rname])
        if overlap < 0.05 and reason != "matching column names":
            continue
        if overlap < 0.02:
            continue
        confidence = "high" if overlap >= 0.4 or reason == "matching column names" else "medium"
        rels.append(
            Relationship(
                left_file=left.filename,
                left_file_id=left.file_id,
                left_column=lname,
                right_file=right.filename,
                right_file_id=right.file_id,
                right_column=rname,
                confidence=confidence,
                overlap_ratio=round(overlap, 3),
                reason=f"{reason} with {overlap:.0%} value overlap",
            )
        )
    return rels


def _is_join_key(semantic: str, name: str) -> bool:
    lower = name.lower()
    return semantic == "identifier" or lower.endswith("_id") or lower in {"id", "uuid", "sku"}


def _token_overlap(a: str, b: str) -> bool:
    at = set(a.lower().replace("-", "_").split("_"))
    bt = set(b.lower().replace("-", "_").split("_"))
    return bool(at & bt)


def _value_overlap(a: pd.Series, b: pd.Series) -> float:
    sa = set(a.dropna().astype(str).head(5000).unique())
    sb = set(b.dropna().astype(str).head(5000).unique())
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    return inter / min(len(sa), len(sb))
