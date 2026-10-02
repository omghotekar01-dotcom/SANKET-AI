from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from ..schemas import RecognitionState


@dataclass(frozen=True)
class GateConfig:
    tracking_threshold: float = 0.48
    motion_threshold: float = 0.0015
    accept_threshold: float = 0.72
    margin_threshold: float = 0.12


@dataclass(frozen=True)
class GateDecision:
    state: RecognitionState
    reason: str


def decide(tracking_quality: float, activity: float, probabilities, config: GateConfig = GateConfig()) -> GateDecision:
    probs = np.sort(np.asarray(probabilities, dtype=np.float32))[::-1]
    top1 = float(probs[0]) if len(probs) else 0.0
    top2 = float(probs[1]) if len(probs) > 1 else 0.0
    if tracking_quality < config.tracking_threshold:
        return GateDecision(RecognitionState.TRACKING_LOST, "Insufficient hand/body/face tracking")
    if activity < config.motion_threshold:
        return GateDecision(RecognitionState.NO_SIGN, "No meaningful signing motion detected")
    if top1 < config.accept_threshold:
        return GateDecision(RecognitionState.NEED_REPEAT, "Recognition confidence is below the validated threshold")
    if top1 - top2 < config.margin_threshold:
        return GateDecision(RecognitionState.NEED_REPEAT, "Top candidates are too close to distinguish safely")
    return GateDecision(RecognitionState.ACCEPTED, "Prediction passed tracking, motion, confidence and ambiguity gates")
