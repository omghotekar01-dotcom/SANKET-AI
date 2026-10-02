from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..config import REPO_ROOT, settings
from ..db.session import LocalStore
from ..schemas import CollectorStartRequest, CollectorStopRequest, FeedbackRequest, TextToISLRequest
from ..services.clip_service import ClipService
from ..services.collector_service import CollectorService
from ..services.context_service import DOMAINS
from ..services.replay_service import SCENARIOS

router = APIRouter(prefix="/api")
store = LocalStore(settings.db_path)
clip_service = ClipService(settings.clip_registry)
collector_service = CollectorService(settings.collected_dir)

DEMO_SIGNS = ["hello","thank_you","yes","no","help","doctor","hospital","water","pain","medicine","police","fire","danger","accident","stop","where","name","student","teacher","repeat","understand"]


@router.get("/health")
def health():
    from ..runtime import model, perception
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "model_loaded": model.loaded,
        "model_version": model.version,
        "model_error": model.load_error,
        "perception_available": perception.available,
        "perception_reason": perception.reason,
        "database": "ok" if store.health() else "degraded",
        "feature_schema": "holistic-v1",
    }


@router.get("/config")
def config():
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "raw_video_capture": settings.enable_raw_video_capture,
        "calling_enabled": settings.enable_experimental_calling,
        "recognition_fps": settings.recognition_fps,
        "sequence_length": settings.sequence_length,
        "privacy": "Raw camera video is not stored by default.",
    }


@router.get("/domains")
def domains():
    return [{"id": key, "label": key.replace("_", " ").title()} for key in DOMAINS]


@router.get("/signs")
def signs():
    return {"supported_demo_vocabulary": DEMO_SIGNS, "claim": "planned/training vocabulary; live support requires a loaded evaluated model artifact"}


@router.post("/translate/text-to-isl")
def text_to_isl(body: TextToISLRequest):
    return clip_service.translate(body.text)


@router.post("/feedback")
def feedback(body: FeedbackRequest):
    return {"id": store.save_feedback(body.model_dump()), "stored": True, "retraining": False}


@router.get("/demo/scenarios")
def demo_scenarios():
    return SCENARIOS


@router.post("/collector/start")
def collector_start(body: CollectorStartRequest):
    try:
        item = collector_service.start(**body.model_dump())
        return {"collector_id": item.collector_id, "label": item.label, "raw_video_saved": False}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/collector/stop")
def collector_stop(body: CollectorStopRequest):
    try:
        return collector_service.stop(body.collector_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/sign-clips/register")
async def register_sign_clip(
    phrase: str = Form(...),
    source: str = Form("team-recorded"),
    license_note: str = Form("Consented team/community recording"),
    verified: bool = Form(False),
    file: UploadFile = File(...),
):
    normalized = phrase.strip()
    if not normalized or len(normalized) > 120:
        raise HTTPException(400, "Phrase must be 1-120 characters")
    suffix = Path(file.filename or "clip.webm").suffix.lower()
    if suffix not in {".webm", ".mp4"}:
        raise HTTPException(400, "Only .webm or .mp4 clips are accepted")
    payload = await file.read(20 * 1024 * 1024 + 1)
    if len(payload) > 20 * 1024 * 1024:
        raise HTTPException(413, "Clip exceeds 20 MB")
    local_dir = settings.clip_dir / "local"
    local_dir.mkdir(parents=True, exist_ok=True)
    relative = f"local/{uuid4().hex}{suffix}"
    (settings.clip_dir / relative).write_bytes(payload)
    entries = []
    if settings.clip_registry.exists():
        entries = json.loads(settings.clip_registry.read_text(encoding="utf-8"))
    entry = {
        "phrase": normalized,
        "mode": "verified_phrase" if verified else "unverified_local",
        "file": relative,
        "source": source.strip() or "team-recorded",
        "license_note": license_note.strip() or "Local recording",
        "verified": bool(verified),
    }
    entries.append(entry)
    settings.clip_registry.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    clip_service.reload()
    return {"stored": True, "entry": entry, "usable_for_reverse_isl": bool(verified)}


@router.get("/metrics")
def metrics():
    from ..runtime import model
    report_path = settings.model_dir / "evaluation.json"
    if not report_path.exists():
        return {"available": False, "message": "No evaluated model artifact loaded yet."}
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return {"available": True, "model_version": model.version, "report": report}
    except Exception as exc:
        raise HTTPException(500, f"Evaluation report unreadable: {exc}") from exc


@router.post("/model/reload")
def model_reload():
    from ..runtime import model
    loaded = model.reload()
    return {"loaded": loaded, "model_version": model.version, "error": model.load_error}


@router.post("/model/train")
def model_train():
    """Train the fixed local baseline command and reload it.

    This endpoint intentionally exposes no user-supplied command or path.
    """
    from ..runtime import model

    command = [sys.executable, "-m", "ml.training.train_template"]
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(504, "Training exceeded the 3 minute local timeout.") from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "Training failed.").strip()
        raise HTTPException(400, detail[-3500:])

    loaded = model.reload()
    report_path = settings.model_dir / "evaluation.json"
    report = None
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            report = None

    return {
        "trained": True,
        "loaded": loaded,
        "model_version": model.version,
        "model_error": model.load_error,
        "evaluation": report,
        "output": completed.stdout[-3500:],
    }
