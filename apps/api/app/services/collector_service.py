from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Lock
from uuid import uuid4
import numpy as np


@dataclass
class ActiveCollection:
    collector_id: str
    label: str
    signer_id: str
    consent: bool
    environment_tag: str | None
    save_raw_video: bool
    created_at: str
    vectors: list[np.ndarray] = field(default_factory=list)


class CollectorService:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.active: dict[str, ActiveCollection] = {}
        self._lock = Lock()

    def start(self, *, label: str, signer_id: str, consent: bool, environment_tag: str | None, save_raw_video: bool) -> ActiveCollection:
        if not consent:
            raise ValueError("Explicit consent is required for dataset collection")
        if save_raw_video:
            raise ValueError("Raw video storage is disabled in this prototype; collect landmarks only")
        item = ActiveCollection(str(uuid4()), label, signer_id, consent, environment_tag, save_raw_video, datetime.now(timezone.utc).isoformat())
        with self._lock:
            self.active[item.collector_id] = item
        return item

    def append(self, collector_id: str, vector: np.ndarray) -> None:
        item = self.active.get(collector_id)
        if item is not None:
            item.vectors.append(vector.astype(np.float32, copy=True))

    def stop(self, collector_id: str) -> dict:
        with self._lock:
            item = self.active.pop(collector_id, None)
        if item is None:
            raise KeyError("collector not found")
        if len(item.vectors) < 8:
            raise ValueError("Too few tracked frames; record at least 8 usable frames")
        sample_id = str(uuid4())
        npz_path = self.root / f"{sample_id}.npz"
        meta_path = self.root / f"{sample_id}.json"
        np.savez_compressed(npz_path, sequence=np.stack(item.vectors))
        meta = {
            "sample_id": sample_id, "label": item.label, "signer_id": item.signer_id,
            "consent": item.consent, "environment_tag": item.environment_tag,
            "created_at": item.created_at, "frame_count": len(item.vectors),
            "feature_schema": "holistic-v1", "raw_video_path": None, "feature_path": npz_path.name,
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return meta
