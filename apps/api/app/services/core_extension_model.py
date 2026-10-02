from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .feature_schema import resample_sequence
from .temporal_model import ModelPrediction

CORE_EXTENSION_TARGETS = {"yes", "no", "help", "water", "where"}


class CoreExtensionModel:
    """Quality-gated five-sign BiLSTM trained by SANKET from public ISL video."""

    MIN_TOP1 = 0.55
    MIN_MACRO_F1 = 0.50
    MIN_ACCEPTED_ACCURACY = 0.75
    MIN_COVERAGE = 0.40
    MIN_TEST_SAMPLES_PER_CLASS = 2

    is_bootstrap = False
    input_schema = "native"

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "model.keras"
        self.norm_path = self.model_dir / "normalization.npz"
        self.manifest_path = self.model_dir / "manifest.json"
        self.report_path = self.model_dir / "evaluation.json"
        self.loaded = False
        self.load_error: str | None = None
        self.quality_reason = "not evaluated"
        self._model = None
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None
        self._labels: list[str] = []
        self._manifest: dict = {}
        self.reload()

    def _check_quality(self, manifest: dict, report: dict) -> tuple[bool, str]:
        labels = {str(x) for x in manifest.get("labels", [])}
        test = report.get("test") or {}
        top1 = float(test.get("top1_accuracy", 0.0))
        macro_f1 = float(test.get("macro_f1", 0.0))
        accepted = float(test.get("accepted_accuracy", 0.0))
        coverage = float(test.get("coverage", 0.0))
        samples = int(test.get("samples", 0))
        problems: list[str] = []

        if manifest.get("training_origin") != "public_core_extension_bilstm":
            problems.append("unexpected training origin")
        if labels != CORE_EXTENSION_TARGETS:
            problems.append(f"unexpected labels {sorted(labels)}")
        required_samples = len(labels) * self.MIN_TEST_SAMPLES_PER_CLASS
        if samples < required_samples:
            problems.append(f"test samples {samples} < {required_samples}")
        if top1 < self.MIN_TOP1:
            problems.append(f"top1 {top1:.2f} < {self.MIN_TOP1:.2f}")
        if macro_f1 < self.MIN_MACRO_F1:
            problems.append(f"macro F1 {macro_f1:.2f} < {self.MIN_MACRO_F1:.2f}")
        if accepted < self.MIN_ACCEPTED_ACCURACY:
            problems.append(
                f"accepted accuracy {accepted:.2f} < {self.MIN_ACCEPTED_ACCURACY:.2f}"
            )
        if coverage < self.MIN_COVERAGE:
            problems.append(f"coverage {coverage:.2f} < {self.MIN_COVERAGE:.2f}")

        if problems:
            return False, "Core extension quality gate failed: " + "; ".join(problems)
        return True, (
            f"passed: top1={top1:.2f}, macroF1={macro_f1:.2f}, "
            f"accepted={accepted:.2f}, coverage={coverage:.2f}, n={samples}"
        )

    def reload(self) -> bool:
        self.loaded = False
        self._model = None
        required = [self.model_path, self.norm_path, self.manifest_path, self.report_path]
        if not all(path.exists() for path in required):
            self.load_error = "No quality-gated core extension artifact is installed."
            self.quality_reason = self.load_error
            return False

        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            report = json.loads(self.report_path.read_text(encoding="utf-8"))
            quality_ok, reason = self._check_quality(manifest, report)
            self.quality_reason = reason
            if not quality_ok:
                self.load_error = reason
                return False

            import keras  # KERAS_BACKEND=openvino is set by bootstrap_model

            if keras.backend.backend() != "openvino":
                raise RuntimeError(f"expected OpenVINO backend, got {keras.backend.backend()}")
            model = keras.saving.load_model(self.model_path, compile=False)
            norm = np.load(self.norm_path)
            mean = norm["mean"].astype(np.float32)
            std = norm["std"].astype(np.float32)
            labels = list(manifest["labels"])
            seq_len = int(manifest["sequence_length"])
            feature_dim = int(manifest["feature_dim"])
            if tuple(model.input_shape)[-2:] != (seq_len, feature_dim):
                raise ValueError(f"unexpected input shape {model.input_shape}")
            if tuple(model.output_shape)[-1] != len(labels):
                raise ValueError(f"unexpected output shape {model.output_shape}")
            probe = np.zeros((1, seq_len, feature_dim), dtype=np.float32)
            out = np.asarray(model.predict(probe, verbose=0), dtype=np.float32)
            if out.shape != (1, len(labels)):
                raise ValueError(f"probe output mismatch {out.shape}")

            self._model = model
            self._mean = mean
            self._std = std
            self._labels = labels
            self._manifest = manifest
            self.loaded = True
            self.load_error = None
            return True
        except Exception as exc:
            self.load_error = f"Core extension load failed: {exc}"
            self.quality_reason = self.load_error
            return False

    @property
    def labels(self) -> list[str]:
        return list(self._labels) if self.loaded else []

    @property
    def version(self):
        return self._manifest.get("model_version") if self.loaded else None

    @property
    def backend(self) -> str:
        return "core_extension_bilstm_openvino" if self.loaded else "core_extension:none"

    @property
    def source(self) -> str:
        return str(self._manifest.get("source", "SANKET public core extension"))

    @property
    def schema_version(self):
        return str(self._manifest.get("feature_schema", "holistic-v1"))

    @property
    def sequence_length(self) -> int:
        return int(self._manifest.get("sequence_length", 48))

    @property
    def accept_threshold(self) -> float:
        return float(self._manifest.get("accept_threshold", 0.65))

    @property
    def margin_threshold(self) -> float:
        return float(self._manifest.get("margin_threshold", 0.08))

    @property
    def motion_threshold(self) -> float:
        return float(self._manifest.get("motion_threshold", 0.0010))

    @property
    def tracking_threshold(self) -> float:
        return float(self._manifest.get("tracking_threshold", 0.48))

    def predict(self, sequence: np.ndarray) -> ModelPrediction:
        if not self.loaded or self._model is None or self._mean is None or self._std is None:
            raise RuntimeError(self.load_error or "core extension unavailable")
        seq = resample_sequence(sequence.astype(np.float32, copy=False), self.sequence_length)
        seq = (seq - self._mean) / self._std
        probs = np.asarray(
            self._model.predict(np.expand_dims(seq, 0), verbose=0),
            dtype=np.float32,
        )[0]
        total = float(probs.sum())
        if probs.shape[0] != len(self._labels) or total <= 0 or not np.isfinite(total):
            raise ValueError("invalid core extension probabilities")
        return ModelPrediction(labels=self._labels, probabilities=probs / total)
