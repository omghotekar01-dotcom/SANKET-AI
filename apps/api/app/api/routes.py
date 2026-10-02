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
from ..services.context_service import DOMAINS, domain_descriptors
from ..services.replay_service import SCENARIOS
from ..services.language_service import supported_languages
from ..services.vocabulary_service import CORE_VOCABULARY, core_coverage

router = APIRouter(prefix="/api")
store = LocalStore(settings.db_path)
clip_service = ClipService(settings.clip_registry)
collector_service = CollectorService(settings.collected_dir)

@router.get("/health")
def health():
    from ..runtime import core_extension, model, perception

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
        "core_extension_loaded": core_extension.loaded,
        "core_extension_version": core_extension.version,
        "core_extension_labels": core_extension.labels,
        "core_extension_quality": core_extension.quality_reason,
        "core_extension_error": core_extension.load_error,
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
        "supported_languages": supported_languages(),
    }


@router.get("/domains")
def domains():
    return domain_descriptors()


@router.get("/signs")
def signs():
    from ..runtime import core_extension, model

    live = list(model.labels) if model.loaded else []
    if core_extension.loaded:
        for label in core_extension.labels:
            if label not in live:
                live.append(label)
    coverage = core_coverage(live)
    target_ids = [item["id"] for item in CORE_VOCABULARY]
    return {
        "live_vocabulary": live,
        "live_vocabulary_size": len(live),
        "model_backend": model.backend,
        "model_source": model.source,
        "model_is_bootstrap": model.is_bootstrap,
        "core_extension_loaded": core_extension.loaded,
        "core_extension_labels": core_extension.labels,
        "core_extension_quality": core_extension.quality_reason,
        "core_vocabulary": CORE_VOCABULARY,
        "core_supported": coverage["supported"],
        "core_missing": coverage["missing"],
        "core_supported_count": coverage["supported_count"],
        "core_total": coverage["total"],
        "core_coverage": coverage["fraction"],
        "target_vocabulary": target_ids,
        # Backward-compatible field: unlike the old implementation this means
        # genuinely live target signs, not planned labels.
        "supported_demo_vocabulary": coverage["supported"],
        "claim": (
            "live_vocabulary is the exact vocabulary emitted by the currently "
            "loaded recognizer. core_supported is the intersection with SANKET's "
            "21-sign project contract; core_missing is never presented as working."
        ),
    }


@router.get("/languages")
def languages():
    return supported_languages()


@router.post("/translate/text-to-isl")
def text_to_isl(body: TextToISLRequest):
    return clip_service.translate(body.text, body.language)


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
    from ..runtime import core_extension, model

    loaded = model.reload()
    core_extension.reload()
    return {
        "loaded": loaded,
        "model_version": model.version,
        "model_backend": model.backend,
        "model_source": model.source,
        "model_is_bootstrap": model.is_bootstrap,
        "vocabulary_size": len(model.labels) + len(core_extension.labels),
        "core_extension_loaded": core_extension.loaded,
        "core_extension_labels": core_extension.labels,
        "core_extension_error": core_extension.load_error,
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
