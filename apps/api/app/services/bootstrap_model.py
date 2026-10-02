from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from .feature_schema import resample_sequence
from .temporal_model import ModelPrediction

# Keras 3 can run inference through OpenVINO without TensorFlow. Set the backend
# before importing keras so the recognizer does not pull TensorFlow/protobuf into
# the MediaPipe process.
os.environ.setdefault("KERAS_BACKEND", "openvino")


class BootstrapKerasModel:
    """MIT-licensed external 50-class BiLSTM used as a bootstrap fallback."""

    backend = "bootstrap_bilstm_50_openvino"
    source = "Kartik200428/Real-time-Indic-Sign-language-to-speech-translator"
    is_bootstrap = True

    def __init__(self, bootstrap_dir: Path):
        self.bootstrap_dir = bootstrap_dir
        self.model_path = bootstrap_dir / "isl_model_solo.keras"
        self.manifest_path = bootstrap_dir / "manifest.json"
        self.loaded = False
        self.version: str | None = None
        self.schema_version: str | None = "bootstrap-holistic-378-v1"
        self.labels: list[str] = []
        self.sequence_length = 30
        self.input_dim = 378
        self.accept_threshold = 0.60
        self.margin_threshold = 0.06
        self.motion_threshold = 0.00008
        self.tracking_threshold = 0.35
        self.load_error: str | None = None
        self._model = None
        self.reload()

    def reload(self) -> bool:
        self.loaded = False
        self._model = None

        if not self.model_path.exists() or not self.manifest_path.exists():
            self.load_error = "Verified bootstrap model assets are not installed."
            return False

        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            labels = list(manifest["labels"])
            if len(labels) != 50:
                raise ValueError(f"expected 50 labels, found {len(labels)}")
            if int(manifest.get("feature_dim", 0)) != self.input_dim:
                raise ValueError("bootstrap feature dimension mismatch")

            import keras  # type: ignore

            if keras.backend.backend() != "openvino":
                raise RuntimeError(
                    f"expected Keras OpenVINO backend, got {keras.backend.backend()}"
                )

            model = keras.saving.load_model(self.model_path, compile=False)
            input_shape = tuple(model.input_shape)
            output_shape = tuple(model.output_shape)
            if input_shape[-2:] != (self.sequence_length, self.input_dim):
                raise ValueError(f"unexpected model input shape {input_shape}")
            if output_shape[-1] != len(labels):
                raise ValueError(f"unexpected model output shape {output_shape}")

            # Compile the inference graph immediately. This catches unsupported
            # layer/backend combinations during startup rather than on the first
            # live sign.
            probe = np.zeros((1, self.sequence_length, self.input_dim), dtype=np.float32)
            probe_out = np.asarray(model.predict(probe, verbose=0), dtype=np.float32)
            if probe_out.shape != (1, len(labels)):
                raise ValueError(f"unexpected OpenVINO probe output {probe_out.shape}")

            self._model = model
            self.labels = labels
            self.version = str(manifest.get("model_version", "bootstrap-bilstm-50-v1"))
            self.schema_version = str(manifest.get("feature_schema", self.schema_version))
            self.loaded = True
            self.load_error = None
            return True
        except Exception as exc:
            self.load_error = f"Bootstrap OpenVINO model load failed: {exc}"
            return False

    def predict(self, sequence: np.ndarray) -> ModelPrediction:
        if not self.loaded or self._model is None:
            raise RuntimeError(self.load_error or "bootstrap model is not loaded")

        seq = resample_sequence(sequence.astype(np.float32, copy=False), self.sequence_length)
        if seq.shape != (self.sequence_length, self.input_dim):
            raise ValueError(f"bootstrap feature mismatch {seq.shape}")

        probs = self._model.predict(np.expand_dims(seq, 0), verbose=0)
        probs = np.asarray(probs, dtype=np.float32)[0]
        if probs.shape[0] != len(self.labels):
            raise ValueError("bootstrap output/label mismatch")
        total = float(probs.sum())
        if total <= 0 or not np.isfinite(total):
            raise ValueError("bootstrap model returned invalid probabilities")
        probs = probs / total
        return ModelPrediction(labels=self.labels, probabilities=probs)
