from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import perf_counter

import numpy as np

from ..schemas import Alternative, PredictionEvent, RecognitionState, TrackingInfo
from .confidence_service import GateConfig, decide
from .context_service import rerank
from .vocabulary_service import normalize_label


@dataclass
class DecoderConfig:
    sequence_length: int = 48
    minimum_frames: int = 20
    stable_predictions: int = 2
    cooldown_frames: int = 10
    no_hand_reset_frames: int = 5


class RecognitionSession:
    def __init__(
        self,
        model,
        domain: str = "general",
        config: DecoderConfig | None = None,
        allowed_labels: set[str] | None = None,
    ):
        self.model = model
        self.domain = domain
        self.allowed_labels = (
            {normalize_label(label) for label in allowed_labels}
            if allowed_labels
            else None
        )

        if config is None:
            bootstrap = bool(getattr(model, "is_bootstrap", False))
            sequence_length = model.sequence_length if model.loaded else 48
            segment_mode = bool(getattr(model, "input_schema", "") == "openhands")
            config = DecoderConfig(
                sequence_length=sequence_length,
                minimum_frames=sequence_length if bootstrap else min(20, sequence_length),
                stable_predictions=1 if segment_mode else (3 if bootstrap else 2),
                cooldown_frames=0 if segment_mode else 10,
                no_hand_reset_frames=3 if segment_mode else 5,
            )

        self.config = config
        self.frames: deque[np.ndarray] = deque(maxlen=self.config.sequence_length)
        self._last_vector: np.ndarray | None = None
        self._activity: deque[float] = deque(maxlen=8)
        self._candidate: str | None = None
        self._stable_count = 0
        self._cooldown = 0
        self._last_accepted: str | None = None
        self._no_hand_frames = 0
        self._segment_mode = bool(getattr(model, "input_schema", "") == "openhands")
        self._segment_active = False
        self._await_idle = False
        self._idle_frames = 0
        self._pre_roll: deque[np.ndarray] = deque(maxlen=4)
        self._segment_activity: list[float] = []

    def reset(self) -> None:
        self.frames.clear()
        self._activity.clear()
        self._last_vector = None
        self._candidate = None
        self._stable_count = 0
        self._cooldown = 0
        self._last_accepted = None
        self._no_hand_frames = 0
        self._segment_active = False
        self._await_idle = False
        self._idle_frames = 0
        self._pre_roll.clear()
        self._segment_activity.clear()

    def set_domain(self, domain: str) -> None:
        self.domain = domain

    def _no_sign_event(self, tracking: dict, reason: str) -> PredictionEvent:
        return PredictionEvent(
            state=RecognitionState.NO_SIGN,
            confidence=0.0,
            alternatives=[],
            tracking=TrackingInfo(**tracking),
            domain=self.domain,
            reason=reason,
            model_version=self.model.version,
            feature_schema=self.model.schema_version or "unknown",
        )

    def push(self, vector: np.ndarray, tracking: dict) -> PredictionEvent | None:
        started = perf_counter()
        hands_present = bool(tracking.get("left_hand") or tracking.get("right_hand"))

        if not hands_present:
            self._no_hand_frames += 1
            if self._no_hand_frames >= self.config.no_hand_reset_frames:
                self.frames.clear()
                self._activity.clear()
                self._last_vector = None
                self._candidate = None
                self._stable_count = 0
                self._segment_active = False
                self._await_idle = False
                self._idle_frames = 0
                self._pre_roll.clear()
                self._segment_activity.clear()
                return self._no_sign_event(tracking, "Ready for a sign")
            return None

        self._no_hand_frames = 0

        delta = None
        if self._last_vector is not None:
            delta = float(np.mean(np.abs(vector - self._last_vector)))
            self._activity.append(delta)
        self._last_vector = vector

        if self._segment_mode:
            start_threshold = max(float(self.model.motion_threshold) * 0.75, 0.00035)
            idle_threshold = max(float(self.model.motion_threshold) * 0.45, 0.00020)

            if self._await_idle:
                if delta is not None and delta <= idle_threshold:
                    self._idle_frames += 1
                else:
                    self._idle_frames = 0
                if self._idle_frames >= 3:
                    self._await_idle = False
                    self._idle_frames = 0
                    self._pre_roll.clear()
                return None

            if not self._segment_active:
                self._pre_roll.append(vector)
                if delta is None or delta < start_threshold:
                    return None
                self.frames.clear()
                for item in self._pre_roll:
                    self.frames.append(item)
                self._segment_activity = [delta]
                self._segment_active = True
                return None

            self.frames.append(vector)
            if delta is not None:
                self._segment_activity.append(delta)
        else:
            self.frames.append(vector)

        if self._cooldown > 0:
            self._cooldown -= 1
        if len(self.frames) < self.config.minimum_frames:
            return None
        if not self.model.loaded:
            return None

        pred = self.model.predict(np.stack(self.frames))
        probs = rerank(pred.labels, pred.probabilities, self.domain)

        # Do not renormalize after safe-vocabulary masking. If an experimental
        # class owns most probability mass, the best safe label keeps its small
        # original probability and therefore fails the confidence gate.
        if self.allowed_labels is not None:
            mask = np.asarray(
                [normalize_label(label) in self.allowed_labels for label in pred.labels],
                dtype=bool,
            )
            probs = np.where(mask, probs, 0.0).astype(np.float32)

        order = np.argsort(probs)[::-1]
        top_idx = int(order[0])
        label = pred.labels[top_idx]
        confidence = float(probs[top_idx])
        activity = (
            float(max(self._segment_activity))
            if self._segment_mode and self._segment_activity
            else (float(np.mean(self._activity)) if self._activity else 0.0)
        )

        gate = decide(
            float(tracking.get("quality", 0)),
            activity,
            probs,
            GateConfig(
                tracking_threshold=self.model.tracking_threshold,
                motion_threshold=self.model.motion_threshold,
                accept_threshold=self.model.accept_threshold,
                margin_threshold=self.model.margin_threshold,
            ),
        )

        if gate.state == RecognitionState.ACCEPTED:
            if self._candidate == label:
                self._stable_count += 1
            else:
                self._candidate, self._stable_count = label, 1

            if self._stable_count < self.config.stable_predictions:
                gate = type(gate)(
                    RecognitionState.NEED_REPEAT,
                    "Holding for a stable temporal prediction",
                )
            elif self._cooldown > 0 and self._last_accepted == label:
                gate = type(gate)(
                    RecognitionState.NO_SIGN,
                    "Duplicate held sign suppressed",
                )
            else:
                self._last_accepted = label
                self._cooldown = self.config.cooldown_frames
        else:
            self._candidate, self._stable_count = None, 0

        alternative_indices = [
            int(i) for i in order[1:]
            if self.allowed_labels is None
            or normalize_label(pred.labels[int(i)]) in self.allowed_labels
        ][:3]
        alternatives = [
            Alternative(
                label=pred.labels[i],
                confidence=float(probs[i]),
            )
            for i in alternative_indices
        ]

        event = PredictionEvent(
            state=gate.state,
            label=label if gate.state == RecognitionState.ACCEPTED else None,
            display_text=(
                label.replace("_", " ").title()
                if gate.state == RecognitionState.ACCEPTED
                else None
            ),
            confidence=confidence,
            alternatives=alternatives,
            tracking=TrackingInfo(**tracking),
            domain=self.domain,
            reason=gate.reason,
            latency_ms=(perf_counter() - started) * 1000,
            model_version=self.model.version,
            feature_schema=self.model.schema_version or "unknown",
        )

        if self._segment_mode:
            # One isolated sign -> one decision. Require a short idle pause before
            # arming the next segment so a held sign cannot be repeatedly emitted.
            self.frames.clear()
            self._activity.clear()
            self._candidate = None
            self._stable_count = 0
            self._segment_active = False
            self._await_idle = True
            self._idle_frames = 0
            self._pre_roll.clear()
            self._segment_activity.clear()

        return event
