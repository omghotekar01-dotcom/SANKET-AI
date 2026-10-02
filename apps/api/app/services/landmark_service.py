from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import cv2
import numpy as np

from .feature_schema import FACE_INDICES, POSE_INDICES, SCHEMA

try:
    # Import the legacy Holistic module directly. This is more explicit and
    # robust than depending on the top-level mp.solutions alias.
    from mediapipe.python.solutions import holistic as mp_holistic  # type: ignore
except Exception:  # pragma: no cover - optional/runtime dependency
    mp_holistic = None


@dataclass
class PerceptionResult:
    vector: np.ndarray
    tracking: dict
    overlay: dict
    latency_ms: float


class HolisticLandmarkService:
    def __init__(self) -> None:
        self.available = bool(mp_holistic is not None and hasattr(mp_holistic, "Holistic"))
        self.reason = (
            None
            if self.available
            else "MediaPipe Holistic is unavailable. Run START_SANKET.bat to repair the pinned vision runtime."
        )
        self._holistic = None
        if self.available:
            self._holistic = mp_holistic.Holistic(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                enable_segmentation=False,
                refine_face_landmarks=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )

    @staticmethod
    def _points(landmarks, count: int, dims: int, indices=None) -> tuple[np.ndarray, bool]:
        if landmarks is None:
            return np.zeros(count * dims, dtype=np.float32), False
        source = landmarks.landmark
        picks = range(count) if indices is None else indices
        values: list[float] = []
        for i in picks:
            lm = source[i]
            values.extend([float(lm.x), float(lm.y), float(lm.z)])
            if dims == 4:
                values.append(float(getattr(lm, "visibility", 1.0)))
        return np.asarray(values, dtype=np.float32), True

    @staticmethod
    def _normalize_xyz(values: np.ndarray, origin_x: float, origin_y: float, scale: float, stride: int) -> np.ndarray:
        out = values.copy()
        for i in range(0, len(out), stride):
            out[i] = (out[i] - origin_x) / scale
            out[i + 1] = (out[i + 1] - origin_y) / scale
            out[i + 2] = out[i + 2] / scale
        return out

    def extract_jpeg(self, jpeg: bytes) -> PerceptionResult:
        if not self.available or self._holistic is None:
            raise RuntimeError(self.reason or "perception unavailable")

        started = perf_counter()
        arr = np.frombuffer(jpeg, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("invalid JPEG frame")

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._holistic.process(rgb)

        left, has_left = self._points(result.left_hand_landmarks, 21, 3)
        right, has_right = self._points(result.right_hand_landmarks, 21, 3)
        pose, has_pose = self._points(result.pose_landmarks, len(POSE_INDICES), 4, POSE_INDICES)
        face, has_face = self._points(result.face_landmarks, len(FACE_INDICES), 3, FACE_INDICES)

        origin_x, origin_y, scale = 0.5, 0.5, 0.35
        if result.pose_landmarks is not None:
            ls = result.pose_landmarks.landmark[11]
            rs = result.pose_landmarks.landmark[12]
            origin_x = (ls.x + rs.x) / 2.0
            origin_y = (ls.y + rs.y) / 2.0
            scale = max(float(np.hypot(ls.x - rs.x, ls.y - rs.y)), 0.05)

        left = self._normalize_xyz(left, origin_x, origin_y, scale, 3)
        right = self._normalize_xyz(right, origin_x, origin_y, scale, 3)
        pose = self._normalize_xyz(pose, origin_x, origin_y, scale, 4)
        face = self._normalize_xyz(face, origin_x, origin_y, scale, 3)

        masks = np.asarray([has_left, has_right, has_pose, has_face], dtype=np.float32)
        vector = np.concatenate([left, right, pose, face, masks]).astype(np.float32)
        if vector.shape[0] != SCHEMA.feature_dim:
            raise RuntimeError(f"feature schema mismatch {vector.shape[0]} != {SCHEMA.feature_dim}")

        quality = (
            0.35 * (has_left or has_right)
            + 0.25 * (has_left and has_right)
            + 0.2 * has_pose
            + 0.2 * has_face
        )
        overlay = self._overlay(result)

        return PerceptionResult(
            vector=vector,
            tracking={
                "left_hand": has_left,
                "right_hand": has_right,
                "pose": has_pose,
                "face": has_face,
                "quality": float(quality),
            },
            overlay=overlay,
            latency_ms=(perf_counter() - started) * 1000,
        )

    @staticmethod
    def _overlay(result) -> dict:
        def xy(lms, indices=None):
            if lms is None:
                return []
            source = lms.landmark
            picks = range(len(source)) if indices is None else indices
            return [
                [round(float(source[i].x), 4), round(float(source[i].y), 4)]
                for i in picks
            ]

        return {
            "left_hand": xy(result.left_hand_landmarks),
            "right_hand": xy(result.right_hand_landmarks),
            "pose": xy(result.pose_landmarks, POSE_INDICES),
        }
