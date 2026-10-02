from __future__ import annotations

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import settings
from .ws.recognition import recognition_socket
from .ws.signaling import signaling_socket

app = FastAPI(title="SANKET AI API", version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)
settings.clip_dir.mkdir(parents=True, exist_ok=True)
app.mount("/sign_clips", StaticFiles(directory=settings.clip_dir), name="sign_clips")


@app.get("/")
def root():
    return {"name": "SANKET AI", "api": "/docs", "health": "/api/health"}


@app.websocket("/ws/recognize")
async def ws_recognize(websocket: WebSocket):
    await recognition_socket(websocket)


@app.websocket("/ws/signaling/{room_id}")
async def ws_signaling(websocket: WebSocket, room_id: str):
    await signaling_socket(websocket, room_id)
