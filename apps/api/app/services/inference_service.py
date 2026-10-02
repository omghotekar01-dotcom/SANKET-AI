from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import perf_counter
import numpy as np

from ..schemas import Alternative, PredictionEvent, RecognitionState, TrackingInfo
from .confidence_service import GateConfig, decide
from .context_service import rerank
from .temporal_model import TemporalTemplateModel


@dataclass
class DecoderConfig:
    sequence_length: int = 48
    minimum_frames: int = 20
    stable_predictions: int = 2
    cooldown_frames: int = 10


class RecognitionSession:
    def __init__(self, model: TemporalTemplateModel, domain: str = "general", config: DecoderConfig | None = None):
        self.model = model
        self.domain = domain
        self.config = config or DecoderConfig(sequence_length=model.sequence_length if model.loaded else 48)
        self.frames: deque[np.ndarray] = deque(maxlen=self.config.sequence_length)
        self._last_vector: np.ndarray | None = None
        self._activity: deque[float] = deque(maxlen=8)
        self._candidate: str | None = None
        self._stable_count = 0
        self._cooldown = 0
        self._last_accepted: str | None = None

    def reset(self) -> None:
        self.frames.clear(); self._activity.clear(); self._last_vector = None
        self._candidate = None; self._stable_count = 0; self._cooldown = 0; self._last_accepted = None

    def set_domain(self, domain: str) -> None:
        self.domain = domain

    def push(self, vector: np.ndarray, tracking: dict) -> PredictionEvent | None:
        started = perf_counter()
        if self._last_vector is not None:
            self._activity.append(float(np.mean(np.abs(vector - self._last_vector))))
        self._last_vector = vector
        self.frames.append(vector)
        if self._cooldown > 0:
            self._cooldown -= 1
        if len(self.frames) < self.config.minimum_frames:
            return None
        if not self.model.loaded:
            return None

        pred = self.model.predict(np.stack(self.frames))
        probs = rerank(pred.labels, pred.probabilities, self.domain)
        order = np.argsort(probs)[::-1]
        top_idx = int(order[0])
        label = pred.labels[top_idx]
        confidence = float(probs[top_idx])
        activity = float(np.mean(self._activity)) if self._activity else 0.0
        gate = decide(float(tracking.get("quality", 0)), activity, probs, GateConfig(
            tracking_threshold=self.model.tracking_threshold,
            motion_threshold=self.model.motion_threshold,
            accept_threshold=self.model.accept_threshold,
            margin_threshold=self.model.margin_threshold,
        ))

        if gate.state == RecognitionState.ACCEPTED:
            if self._candidate == label:
                self._stable_count += 1
            else:
                self._candidate, self._stable_count = label, 1
            if self._stable_count < self.config.stable_predictions:
                gate = type(gate)(RecognitionState.NEED_REPEAT, "Collecting one more stable temporal prediction")
            elif self._cooldown > 0 and self._last_accepted == label:
                gate = type(gate)(RecognitionState.NO_SIGN, "Duplicate held sign suppressed during cooldown")
            else:
                self._last_accepted = label
                self._cooldown = self.config.cooldown_frames
        else:
            self._candidate, self._stable_count = None, 0

        alternatives = [Alternative(label=pred.labels[int(i)], confidence=float(probs[int(i)])) for i in order[1:4]]
        return PredictionEvent(
            state=gate.state,
            label=label if gate.state == RecognitionState.ACCEPTED else None,
            display_text=label.replace("_", " ").title() if gate.state == RecognitionState.ACCEPTED else None,
            confidence=confidence,
            alternatives=alternatives,
            tracking=TrackingInfo(**tracking),
            domain=self.domain,
            reason=gate.reason,
            latency_ms=(perf_counter() - started) * 1000,
            model_version=self.model.version,
            feature_schema=self.model.schema_version or "holistic-v1",
        )
