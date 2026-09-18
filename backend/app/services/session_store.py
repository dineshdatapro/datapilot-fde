from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import pandas as pd

from app.models.schemas import FileProfile, Relationship


@dataclass
class StoredFile:
    file_id: str
    filename: str
    file_type: str
    path: str
    dataframe: pd.DataFrame
    profile: FileProfile


@dataclass
class Session:
    session_id: str
    files: dict[str, StoredFile] = field(default_factory=dict)
    relationships: list[Relationship] = field(default_factory=list)

    def file_list(self) -> list[dict[str, Any]]:
        out = []
        for f in self.files.values():
            out.append(
                {
                    "file_id": f.file_id,
                    "filename": f.filename,
                    "file_type": f.file_type,
                    "row_count": f.profile.row_count,
                    "column_count": f.profile.column_count,
                    "columns": [c.model_dump() for c in f.profile.columns],
                }
            )
        return out


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        session = Session(session_id=str(uuid4()))
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None) -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create()

    def delete_file(self, session_id: str, file_id: str) -> bool:
        session = self.get(session_id)
        if not session or file_id not in session.files:
            return False
        del session.files[file_id]
        return True


store = SessionStore()
