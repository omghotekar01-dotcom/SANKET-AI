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

PLANNED_DEMO_SIGNS = [
    "hello", "thank_you", "yes", "no", "help", "doctor", "hospital",
    "water", "pain", "medicine", "police", "fire", "danger", "accident",
    "stop", "where", "name", "student", "teacher", "repeat", "understand",
]


@router.get("/health")
def health():
    from ..runtime import model, perception

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "model_loaded": model.loaded,
        "model_version": model.version,
        "model_backend": model.backend,
        "model_source": model.source,
        "model_is_bootstrap": model.is_bootstrap,
        "model_vocabulary_size": len(model.labels),
        "model_error": model.load_error,
        "model_selection_reason": model.selection_reason,
        "perception_available": perception.available,
        "perception_reason": perception.reason,
        "database": "ok" if store.health() else "degraded",
        "feature_schema": model.schema_version or "holistic-v1",
    }


@router.get("/config")
def config():
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "raw_video_capture": settings.enable_raw_video_capture,
        "calling_enabled": settings.enable_experimental_calling,
        "bootstrap_enabled": settings.enable_bootstrap_model,
        "recognition_fps": settings.recognition_fps,
        "sequence_length": settings.sequence_length,
        "privacy": "Raw camera video is not stored by default.",
    }


@router.get("/domains")
def domains():
    return [{"id": key, "label": key.replace("_", " ").title()} for key in DOMAINS]


@router.get("/signs")
def signs():
    from ..runtime import model

    return {
        "live_vocabulary": model.labels if model.loaded else [],
        "live_vocabulary_size": len(model.labels) if model.loaded else 0,
        "model_backend": model.backend,
        "model_source": model.source,
        "model_is_bootstrap": model.is_bootstrap,
        "planned_custom_vocabulary": PLANNED_DEMO_SIGNS,
        "supported_demo_vocabulary": PLANNED_DEMO_SIGNS,
        "claim": (
            "live_vocabulary is the exact active recognizer vocabulary. "
            "Bootstrap weights are external MIT-licensed weights, not SANKET-trained metrics."
        ),
    }


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
        return {
            "collector_id": item.collector_id,
            "label": item.label,
            "raw_video_saved": False,
        }
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

    return {
        "stored": True,
        "entry": entry,
        "usable_for_reverse_isl": bool(verified),
    }


@router.get("/metrics")
def metrics():
    from ..runtime import model

    report_path = settings.model_dir / "evaluation.json"
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            return {
                "available": True,
                "kind": "sanket_local_evaluation",
                "model_version": model.version,
                "report": report,
            }
        except Exception as exc:
            raise HTTPException(500, f"Evaluation report unreadable: {exc}") from exc

    if model.loaded and model.is_bootstrap:
        return {
            "available": False,
            "kind": "external_bootstrap",
            "model_version": model.version,
            "vocabulary_size": len(model.labels),
            "source": model.source,
            "message": (
                "The external bootstrap recognizer is loaded, but SANKET has not "
                "reproduced a held-out evaluation for those external weights. "
                "No accuracy number is claimed here."
            ),
        }

    return {
        "available": False,
        "kind": "none",
        "message": "No evaluated SANKET model artifact is loaded yet.",
    }


@router.post("/model/reload")
def model_reload():
    from ..runtime import model

    loaded = model.reload()
    return {
        "loaded": loaded,
        "model_version": model.version,
        "model_backend": model.backend,
        "model_source": model.source,
        "model_is_bootstrap": model.is_bootstrap,
        "vocabulary_size": len(model.labels),
        "error": model.load_error,
    }


@router.post("/model/train")
def model_train():
    """Train only the fixed local SANKET baseline command, then prefer it over bootstrap."""
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
        "model_backend": model.backend,
        "model_source": model.source,
        "model_is_bootstrap": model.is_bootstrap,
        "model_error": model.load_error,
        "evaluation": report,
        "output": completed.stdout[-3500:],
    }
