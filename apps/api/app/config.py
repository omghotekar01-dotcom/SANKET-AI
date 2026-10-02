from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "SANKET AI"
    app_version: str = "0.3.0"
    environment: str = os.getenv("APP_ENV", "development")
    web_origin: str = os.getenv("WEB_ORIGIN", "http://localhost:5173")
    model_dir: Path = REPO_ROOT / os.getenv("MODEL_DIR", "ml/artifacts/demo-v1")
    bootstrap_dir: Path = REPO_ROOT / os.getenv("BOOTSTRAP_MODEL_DIR", "ml/artifacts/bootstrap-50")
    core_extension_dir: Path = REPO_ROOT / os.getenv("CORE_EXTENSION_MODEL_DIR", "ml/artifacts/core-extension-v1")
    db_path: Path = REPO_ROOT / os.getenv("DB_PATH", "data/local/sanket.db")
    collected_dir: Path = REPO_ROOT / "data/local/collected"
    clip_registry: Path = REPO_ROOT / "assets/sign_clips/registry.json"
    clip_dir: Path = REPO_ROOT / "assets/sign_clips"
    enable_raw_video_capture: bool = _bool("ENABLE_RAW_VIDEO_CAPTURE", False)
    enable_experimental_calling: bool = _bool("ENABLE_EXPERIMENTAL_CALLING", True)
    enable_bootstrap_model: bool = _bool("ENABLE_BOOTSTRAP_MODEL", True)
    recognition_fps: int = int(os.getenv("RECOGNITION_FPS", "10"))
    sequence_length: int = int(os.getenv("SEQUENCE_LENGTH", "48"))


settings = Settings()
