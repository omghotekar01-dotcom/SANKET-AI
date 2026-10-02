from __future__ import annotations

from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect

_rooms: dict[str, set[WebSocket]] = defaultdict(set)


async def signaling_socket(websocket: WebSocket, room_id: str):
    if not room_id or len(room_id) > 64 or not room_id.replace("-", "").isalnum():
        await websocket.close(code=1008)
        return
    room = _rooms[room_id]
    if len(room) >= 2:
        await websocket.accept(); await websocket.send_json({"type": "room_full"}); await websocket.close(); return
    await websocket.accept()
    room.add(websocket)
    await websocket.send_json({"type": "joined", "room_id": room_id, "peer_count": len(room)})
    for peer in list(room):
        if peer is not websocket:
            await peer.send_json({"type": "peer_joined"})
    try:
        while True:
            payload = await websocket.receive_json()
            if len(str(payload)) > 100_000:
                await websocket.send_json({"type":"error","message":"Signaling payload too large"}); continue
            kind = payload.get("type")
            if kind not in {"offer", "answer", "ice", "caption", "leave", "ping"}:
                await websocket.send_json({"type": "error", "message": "Unsupported signaling message"}); continue
            if kind == "ping":
                await websocket.send_json({"type": "pong"}); continue
            for peer in list(room):
                if peer is not websocket:
                    await peer.send_json(payload)
            if kind == "leave":
                break
    except WebSocketDisconnect:
        pass
    finally:
        room.discard(websocket)
        for peer in list(room):
            try: await peer.send_json({"type": "peer_left"})
            except Exception: pass
        if not room:
            _rooms.pop(room_id, None)
