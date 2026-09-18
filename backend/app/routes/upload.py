from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.services.file_processor import ALLOWED_EXTENSIONS, FileProcessError, process_upload
from app.services.relationship_detector import detect_relationships
from app.services.session_store import store

router = APIRouter(prefix="/api", tags=["upload"])


def _session_payload(session):
    total_rows = sum(f.profile.row_count for f in session.files.values())
    total_cols = sum(f.profile.column_count for f in session.files.values())
    return {
        "session_id": session.session_id,
        "files": session.file_list(),
        "overview": {
            "file_count": len(session.files),
            "total_rows": total_rows,
            "total_columns": total_cols,
            "relationships": [r.model_dump() for r in session.relationships],
        },
    }


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    session_id: str | None = Form(default=None),
):
    session = store.get_or_create(session_id)
    existing_names = {f.filename.lower() for f in session.files.values()}
    uploaded = []

    for upload in files:
        filename = upload.filename or "upload"
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a CSV or Excel file.")

        data = await upload.read()
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(status_code=400, detail="This file exceeds the 10 MB upload limit.")

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.write(data)
        tmp.close()
        try:
            stored = process_upload(Path(tmp.name), filename)
        except FileProcessError as exc:
            Path(tmp.name).unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if stored.filename.lower() in existing_names:
            Path(tmp.name).unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=f"A file named {stored.filename} is already in this session. Rename it or remove the existing file.",
            )
        existing_names.add(stored.filename.lower())
        session.files[stored.file_id] = stored
        uploaded.append(stored.filename)

    session.relationships = detect_relationships(session.files)
    payload = _session_payload(session)
    payload["uploaded"] = uploaded
    return payload


def _demo_dir() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "sample_data",
        Path("/sample_data"),
        Path.cwd().parent / "sample_data",
        Path.cwd() / "sample_data",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


@router.post("/demo")
async def load_demo(session_id: str | None = None):
    session = store.get_or_create(session_id)
    root = _demo_dir()
    demo_files = ["sales_january.csv", "sales_february.xlsx", "customers.csv"]
    existing_names = {f.filename.lower() for f in session.files.values()}
    for name in demo_files:
        path = root / name
        if not path.exists():
            raise HTTPException(status_code=500, detail="Demo datasets are missing from sample_data/.")
        if name.lower() in existing_names:
            continue
        dest = Path(tempfile.gettempdir()) / f"datapilot_{session.session_id}_{name}"
        shutil.copy(path, dest)
        stored = process_upload(dest, name)
        session.files[stored.file_id] = stored
    session.relationships = detect_relationships(session.files)
    return _session_payload(session)


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return _session_payload(session)


@router.delete("/session/{session_id}")
async def reset_session(session_id: str):
    session = store.get(session_id)
    if session:
        session.files.clear()
        session.relationships = []
        return _session_payload(session)
    session = store.create()
    return _session_payload(session)


@router.delete("/session/{session_id}/files/{file_id}")
async def delete_file(session_id: str, file_id: str):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if not store.delete_file(session_id, file_id):
        raise HTTPException(status_code=404, detail="File not found.")
    session.relationships = detect_relationships(session.files)
    return _session_payload(session)
