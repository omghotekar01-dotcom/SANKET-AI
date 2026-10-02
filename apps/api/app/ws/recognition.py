from __future__ import annotations

import json
from time import perf_counter

from fastapi import WebSocket, WebSocketDisconnect

from ..api.routes import collector_service
from ..runtime import model, perception
from ..services.context_service import DOMAINS
from ..services.inference_service import RecognitionSession


async def recognition_socket(websocket: WebSocket):
    await websocket.accept()
    session = RecognitionSession(model)
    collector_id = websocket.query_params.get("collector_id")

    await websocket.send_json({
        "type": "ready",
        "model_loaded": model.loaded,
        "model_version": model.version,
        "model_backend": model.backend,
        "model_source": model.source,
        "model_is_bootstrap": model.is_bootstrap,
        "model_vocabulary_size": len(model.labels),
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
                    # Local SANKET training always collects the compact native schema.
                    collector_service.append(collector_id, result.vector)

                await websocket.send_json({
                    "type": "tracking",
                    "tracking": result.tracking,
                    "overlay": result.overlay,
                    "landmark_latency_ms": round(result.latency_ms, 2),
                })

                if not model.loaded:
                    await websocket.send_json({
                        "type": "model_unavailable",
                        "message": model.load_error,
                        "tracking": result.tracking,
                        "latency_ms": round((perf_counter() - started) * 1000, 2),
                    })
                    continue

                inference_vector = (
                    result.bootstrap_vector
                    if model.input_schema == "bootstrap"
                    else result.vector
                )
                event = session.push(inference_vector, result.tracking)
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
                        session.set_domain(domain)
                        await websocket.send_json({"type": "domain", "domain": domain})
                elif kind == "reset":
                    session.reset()
                    await websocket.send_json({"type": "reset", "ok": True})
                elif kind == "ping":
                    await websocket.send_json({"type": "pong", "seq": payload.get("seq")})
                else:
                    await websocket.send_json({"type": "error", "message": "Unsupported message type"})
    except WebSocketDisconnect:
        return
