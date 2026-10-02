from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np

from .feature_schema import append_velocity, resample_sequence


@dataclass
class ModelPrediction:
    labels: list[str]
    probabilities: np.ndarray

    @property
    def top_label(self) -> str:
        return self.labels[int(np.argmax(self.probabilities))]


class TemporalTemplateModel:
    backend = "sanket_temporal_template"
    is_bootstrap = False

    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.loaded = False
        self.version = None
        self.source = "SANKET local training"
        self.schema_version = None
        self.labels: list[str] = []
        self.sequence_length = 48
        self.temperature = 1.0
        self.accept_threshold = 0.72
        self.margin_threshold = 0.12
        self.motion_threshold = 0.0015
        self.tracking_threshold = 0.48
        self.templates: np.ndarray | None = None
        self.feature_weights: np.ndarray | None = None
        self.load_error: str | None = None
        self.reload()

    def reload(self) -> bool:
        manifest_path = self.model_dir / "manifest.json"
        model_path = self.model_dir / "model.npz"
        self.loaded = False
        if not manifest_path.exists() or not model_path.exists():
            self.load_error = "No trained temporal model artifact found."
            return False
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload = np.load(model_path)
            self.templates = payload["templates"].astype(np.float32)
            self.feature_weights = payload["feature_weights"].astype(np.float32)
            self.labels = list(manifest["labels"])
            self.sequence_length = int(manifest["sequence_length"])
            self.temperature = float(manifest.get("temperature", 1.0))
            self.accept_threshold = float(manifest.get("accept_threshold", 0.72))
            self.margin_threshold = float(manifest.get("margin_threshold", 0.12))
            self.motion_threshold = float(manifest.get("motion_threshold", 0.0015))
            self.tracking_threshold = float(manifest.get("tracking_threshold", 0.48))
            self.version = str(manifest["model_version"])
            self.schema_version = str(manifest["feature_schema"])
            self.source = str(manifest.get("source", "SANKET local training"))
            if self.templates.shape[0] != len(self.labels):
                raise ValueError("label/template count mismatch")
            self.loaded = True
            self.load_error = None
            return True
        except Exception as exc:
            self.load_error = f"Model load failed: {exc}"
            return False

    def predict(self, sequence: np.ndarray) -> ModelPrediction:
        if not self.loaded or self.templates is None or self.feature_weights is None:
            raise RuntimeError(self.load_error or "model is not loaded")
        seq = append_velocity(resample_sequence(sequence, self.sequence_length))
        if seq.shape[1] != self.templates.shape[2]:
            raise ValueError(f"feature mismatch {seq.shape[1]} != {self.templates.shape[2]}")
        diff = (self.templates - seq[None, :, :]) ** 2
        distances = np.mean(diff * self.feature_weights[None, None, :], axis=(1, 2))
        logits = -distances / max(self.temperature, 1e-4)
        logits -= logits.max()
        exp = np.exp(logits)
        probs = exp / exp.sum()
        return ModelPrediction(labels=self.labels, probabilities=probs.astype(np.float32))
