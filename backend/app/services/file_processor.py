from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pandas as pd

from app.models.schemas import FileProfile
from app.services.schema_profiler import profile_dataframe
from app.services.session_store import StoredFile
from app.utils.formatting import sanitize_filename

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


class FileProcessError(Exception):
    pass


def _read_dataframe(path: Path, ext: str) -> pd.DataFrame:
    try:
        if ext == ".csv":
            df = pd.read_csv(path)
        elif ext == ".xlsx":
            df = pd.read_excel(path, engine="openpyxl")
        else:
            df = pd.read_excel(path, engine="xlrd")
    except Exception as exc:  # noqa: BLE001
        raise FileProcessError(
            "This file couldn't be processed. Please verify that it is a valid CSV or Excel file."
        ) from exc
    return df


def _enrich_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    added_calendar = False
    for col in list(out.columns):
        name_l = str(col).lower()
        if not any(token in name_l for token in ("date", "time", "_at")):
            continue
        parsed = pd.to_datetime(out[col], errors="coerce", format="mixed")
        if parsed.notna().mean() >= 0.6:
            out[col] = parsed
            if not added_calendar:
                out["month"] = parsed.dt.to_period("M").astype(str)
                out["year"] = parsed.dt.year
                out["month_name"] = parsed.dt.strftime("%B")
                added_calendar = True
    return out


def process_upload(path: Path, original_name: str) -> StoredFile:
    filename = sanitize_filename(original_name)
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileProcessError("Unsupported file type. Please upload a CSV or Excel file.")

    df = _read_dataframe(path, ext)
    if df.empty:
        raise FileProcessError("This file is empty. Upload a spreadsheet that contains rows of data.")

    if all(str(c).startswith("Unnamed") for c in df.columns):
        raise FileProcessError(
            "This file doesn't appear to have column headers. Add a header row and try again."
        )

    df.columns = [str(c).strip() for c in df.columns]
    df = _enrich_dates(df)
    profile: FileProfile = profile_dataframe(str(uuid4()), filename, ext.lstrip("."), df)
    return StoredFile(
        file_id=profile.file_id,
        filename=filename,
        file_type=ext.lstrip("."),
        path=str(path),
        dataframe=df,
        profile=profile,
    )
