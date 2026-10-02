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
    is_bootstrap = False

    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.loaded = False
        self.version = None
        self.backend = "temporal_template"
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
        self.exemplars: np.ndarray | None = None
        self.exemplar_label_indices: np.ndarray | None = None
        self.exemplar_k = 1
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
            self.exemplars = (
                payload["exemplars"].astype(np.float32)
                if "exemplars" in payload.files else None
            )
            self.exemplar_label_indices = (
                payload["exemplar_label_indices"].astype(np.int32)
                if "exemplar_label_indices" in payload.files else None
            )
            self.labels = list(manifest["labels"])
            self.sequence_length = int(manifest["sequence_length"])
            self.temperature = float(manifest.get("temperature", 1.0))
            self.accept_threshold = float(manifest.get("accept_threshold", 0.72))
            self.margin_threshold = float(manifest.get("margin_threshold", 0.12))
            self.motion_threshold = float(manifest.get("motion_threshold", 0.0015))
            self.tracking_threshold = float(manifest.get("tracking_threshold", 0.48))
            self.version = str(manifest["model_version"])
            self.backend = str(manifest.get("backend", "temporal_template"))
            self.exemplar_k = int(manifest.get("exemplar_k", 1))
            self.schema_version = str(manifest["feature_schema"])
            self.source = str(manifest.get("source", "SANKET local training"))

            if self.templates.shape[0] != len(self.labels):
                raise ValueError("label/template count mismatch")
            if self.backend == "temporal_exemplar_knn":
                if self.exemplars is None or self.exemplar_label_indices is None:
                    raise ValueError("exemplar backend selected but exemplar arrays are missing")
                if len(self.exemplars) != len(self.exemplar_label_indices):
                    raise ValueError("exemplar/label count mismatch")
            self.loaded = True
            self.load_error = None
            return True
        except Exception as exc:
            self.load_error = f"Model load failed: {exc}"
            return False

    def _class_distances(self, seq: np.ndarray) -> np.ndarray:
        assert self.feature_weights is not None
        if self.backend == "temporal_exemplar_knn":
            assert self.exemplars is not None
            assert self.exemplar_label_indices is not None
            diff = (self.exemplars - seq[None, :, :]) ** 2
            sample_distances = np.mean(
                diff * self.feature_weights[None, None, :],
                axis=(1, 2),
            )
            class_distances = np.empty(len(self.labels), dtype=np.float32)
            for class_idx in range(len(self.labels)):
                rows = sample_distances[
                    self.exemplar_label_indices == class_idx
                ]
                if len(rows) == 0:
                    class_distances[class_idx] = np.inf
                    continue
                k = min(max(self.exemplar_k, 1), len(rows))
                class_distances[class_idx] = float(
                    np.mean(np.partition(rows, k - 1)[:k])
                )
            return class_distances

        assert self.templates is not None
        diff = (self.templates - seq[None, :, :]) ** 2
        return np.mean(
            diff * self.feature_weights[None, None, :],
            axis=(1, 2),
        )

    def predict(self, sequence: np.ndarray) -> ModelPrediction:
        if not self.loaded or self.feature_weights is None:
            raise RuntimeError(self.load_error or "model is not loaded")
        seq = append_velocity(
            resample_sequence(sequence, self.sequence_length)
        )
        if seq.shape[1] != self.feature_weights.shape[0]:
            raise ValueError(
                f"feature mismatch {seq.shape[1]} != {self.feature_weights.shape[0]}"
            )
        distances = self._class_distances(seq)
        logits = -distances / max(self.temperature, 1e-5)
        logits -= np.max(logits)
        exp = np.exp(logits)
        probs = exp / np.sum(exp)
        return ModelPrediction(
            labels=self.labels,
            probabilities=probs.astype(np.float32),
        )
