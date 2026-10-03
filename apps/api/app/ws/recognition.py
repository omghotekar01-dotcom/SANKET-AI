from __future__ import annotations

import json
from time import perf_counter

from fastapi import WebSocket, WebSocketDisconnect

from ..api.routes import collector_service
from ..runtime import core_extension, model, perception
from ..services.context_service import DOMAINS
from ..services.inference_service import RecognitionSession
from ..services.vocabulary_service import SAFE_BOOTSTRAP_CORE_IDS, safe_bootstrap_labels
from ..schemas import RecognitionState

VALID_SCOPES = {"core_safe", "experimental_50"}


def _event_rank(event) -> tuple[int, float]:
    if event is None:
        return (-1, 0.0)
    rank = {
        RecognitionState.ACCEPTED: 4,
        RecognitionState.NEED_REPEAT: 3,
        RecognitionState.TRACKING_LOST: 2,
        RecognitionState.NO_SIGN: 1,
    }.get(event.state, 0)
    return (rank, float(event.confidence or 0.0))


def _choose_event(primary, extension):
    if extension is not None and extension.state == RecognitionState.ACCEPTED:
        return extension
    if primary is not None and primary.state == RecognitionState.ACCEPTED:
        return primary
    return max((e for e in (extension, primary) if e is not None), key=_event_rank, default=None)


async def recognition_socket(websocket: WebSocket):
    await websocket.accept()
    requested_scope = websocket.query_params.get("recognition_scope", "core_safe")
    scope = requested_scope if requested_scope in VALID_SCOPES else "core_safe"

    allowed_labels = None
    if model.loaded and model.is_bootstrap and scope == "core_safe":
        allowed_labels = set(SAFE_BOOTSTRAP_CORE_IDS)

    primary_session = RecognitionSession(model, allowed_labels=allowed_labels)
    extension_session = RecognitionSession(core_extension) if core_extension.loaded else None
    collector_id = websocket.query_params.get("collector_id")

    if model.loaded:
        primary_labels = (
            safe_bootstrap_labels(model.labels)
            if model.is_bootstrap and scope == "core_safe"
            else list(model.labels)
        )
    else:
        primary_labels = []

    live_labels = list(primary_labels)
    if core_extension.loaded:
        live_labels.extend(label for label in core_extension.labels if label not in live_labels)

    await websocket.send_json({
        "type": "ready",
        "model_loaded": bool(model.loaded or core_extension.loaded),
        "model_version": model.version,
        "model_backend": model.backend,
        "model_source": model.source,
        "model_is_bootstrap": model.is_bootstrap,
        "model_vocabulary_size": len(live_labels),
        "recognition_scope": scope,
        "scoped_vocabulary": live_labels,
        "experimental_vocabulary_size": len(model.labels) if model.loaded and model.is_bootstrap else len(live_labels),
        "core_extension_loaded": core_extension.loaded,
        "core_extension_labels": core_extension.labels,
        "perception_available": perception.available,
        "perception_reason": perception.reason,
        "collector_id": collector_id,
    })

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                return

            if message.get("bytes") is not None:
                if len(message["bytes"]) > 600_000:
                    await websocket.send_json({"type": "error", "message": "Frame payload too large"})
                    continue

                started = perf_counter()
                try:
                    result = perception.extract_jpeg(message["bytes"])
                except (RuntimeError, ValueError) as exc:
                    await websocket.send_json({"type": "perception_error", "message": str(exc)})
                    continue

                if collector_id:
                    collector_service.append(collector_id, result.vector)

                await websocket.send_json({
                    "type": "tracking",
                    "tracking": result.tracking,
                    "overlay": result.overlay,
                    "landmark_latency_ms": round(result.latency_ms, 2),
                })

                if not model.loaded and not core_extension.loaded:
                    await websocket.send_json({
                        "type": "model_unavailable",
                        "message": model.load_error or core_extension.load_error,
                        "tracking": result.tracking,
                        "latency_ms": round((perf_counter() - started) * 1000, 2),
                    })
                    continue

                primary_event = None
                if model.loaded:
                    primary_vector = (
                        result.bootstrap_vector
                        if model.input_schema == "bootstrap"
                        else result.vector
                    )
                    primary_event = primary_session.push(primary_vector, result.tracking)

                extension_event = None
                if extension_session is not None:
                    extension_event = extension_session.push(result.vector, result.tracking)

                event = _choose_event(primary_event, extension_event)
                if event is not None:
                    await websocket.send_json(event.model_dump(mode="json"))

            elif message.get("text") is not None:
                try:
                    payload = json.loads(message["text"])
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                    continue

                kind = payload.get("type")
                if kind == "set_domain":
                    domain = payload.get("domain", "general")
                    if domain not in DOMAINS:
                        await websocket.send_json({"type": "error", "message": "Unknown domain"})
                    else:
                        primary_session.set_domain(domain)
                        if extension_session is not None:
                            extension_session.set_domain(domain)
                        await websocket.send_json({"type": "domain", "domain": domain})
                elif kind == "reset":
                    primary_session.reset()
                    if extension_session is not None:
                        extension_session.reset()
                    await websocket.send_json({"type": "reset", "ok": True})
                elif kind == "ping":
                    await websocket.send_json({"type": "pong", "seq": payload.get("seq")})
                else:
                    await websocket.send_json({"type": "error", "message": "Unsupported message type"})
    except WebSocketDisconnect:
        return
