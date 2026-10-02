from __future__ import annotations

from dataclasses import dataclass
import numpy as np

POSE_INDICES = (0, 11, 12, 13, 14, 15, 16, 23, 24)
FACE_INDICES = (0, 10, 13, 14, 17, 33, 61, 78, 105, 133, 145, 152, 159, 263, 291, 308, 334, 362, 374, 386)


@dataclass(frozen=True)
class FeatureSchema:
    version: str = "holistic-v1"
    hand_points: int = 21
    hand_dims: int = 3
    pose_points: int = len(POSE_INDICES)
    pose_dims: int = 4
    face_points: int = len(FACE_INDICES)
    face_dims: int = 3
    masks: int = 4

    @property
    def feature_dim(self) -> int:
        return self.hand_points * self.hand_dims * 2 + self.pose_points * self.pose_dims + self.face_points * self.face_dims + self.masks


SCHEMA = FeatureSchema()


def resample_sequence(sequence: np.ndarray, target_len: int) -> np.ndarray:
    if sequence.ndim != 2:
        raise ValueError("sequence must have shape [time, features]")
    if len(sequence) == 0:
        raise ValueError("sequence cannot be empty")
    if len(sequence) == target_len:
        return sequence.astype(np.float32, copy=False)
    old_x = np.linspace(0.0, 1.0, len(sequence), dtype=np.float32)
    new_x = np.linspace(0.0, 1.0, target_len, dtype=np.float32)
    output = np.empty((target_len, sequence.shape[1]), dtype=np.float32)
    for idx in range(sequence.shape[1]):
        output[:, idx] = np.interp(new_x, old_x, sequence[:, idx])
    return output


def append_velocity(sequence: np.ndarray) -> np.ndarray:
    velocity = np.diff(sequence, axis=0, prepend=sequence[:1])
    return np.concatenate([sequence, velocity], axis=1).astype(np.float32)
