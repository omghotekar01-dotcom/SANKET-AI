from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock
from uuid import uuid4


class LocalStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=2)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    utterance_id TEXT,
                    raw_label TEXT,
                    accepted INTEGER NOT NULL,
                    corrected_label TEXT,
                    note TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def save_feedback(self, data: dict) -> str:
        feedback_id = str(uuid4())
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO feedback(id,utterance_id,raw_label,accepted,corrected_label,note) VALUES(?,?,?,?,?,?)",
                (
                    feedback_id,
                    data.get("utterance_id"),
                    data.get("raw_label"),
                    1 if data.get("accepted") else 0,
                    data.get("corrected_label"),
                    data.get("note"),
                ),
            )
        return feedback_id

    def save_event(self, event_type: str, payload: dict) -> str:
        event_id = str(uuid4())
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO events(id,event_type,payload_json) VALUES(?,?,?)",
                (event_id, event_type, json.dumps(payload, separators=(",", ":"))),
            )
        return event_id

    def health(self) -> bool:
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False
