from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np

# MediaPipe 0.10.x still calls MessageFactory.GetPrototype in a few generated
# protobuf modules. Protobuf 6/7 removed that method, while TensorFlow 2.20
# requires a newer protobuf. Restore the old method as a tiny compatibility
# adapter before importing MediaPipe. It delegates to the supported
# message_factory.GetMessageClass implementation.
try:
    from google.protobuf import message_factory as _message_factory
    if not hasattr(_message_factory.MessageFactory, "GetPrototype"):
        def _get_prototype(self, descriptor):
            return _message_factory.GetMessageClass(descriptor)
        _message_factory.MessageFactory.GetPrototype = _get_prototype
except Exception:
    pass

from .feature_schema import FACE_INDICES, POSE_INDICES, SCHEMA

BOOTSTRAP_FACE_INDICES = (
    70, 63, 105, 66, 107, 55, 65, 52,
    300, 293, 334, 296, 336, 285, 295, 282,
    33, 133, 159, 145, 362, 263, 386, 374,
    61, 37, 0, 267, 291, 321, 314, 17,
    78, 81, 13, 311, 308, 317, 14, 87,
)

try:
    import mediapipe as mp  # type: ignore
    from mediapipe.tasks.python import BaseOptions  # type: ignore
    from mediapipe.tasks.python import vision as mv  # type: ignore
except Exception:  # pragma: no cover
    mp = None
    BaseOptions = None
    mv = None


@dataclass
class PerceptionResult:
    vector: np.ndarray
    bootstrap_vector: np.ndarray
    tracking: dict
    overlay: dict
    latency_ms: float


class HolisticLandmarkService:
    """Run one Holistic Tasks pass and expose native + bootstrap feature vectors."""

    def __init__(self, model_asset_path: Path) -> None:
        self.model_asset_path = Path(model_asset_path)
        self.available = False
        self.reason: str | None = None
        self._holistic = None

        if mp is None or BaseOptions is None or mv is None:
            self.reason = "MediaPipe Tasks runtime is unavailable. Run START_SANKET.bat."
            return
        if not self.model_asset_path.exists():
            self.reason = "Holistic task asset is missing. Run START_SANKET.bat."
            return

        try:
            options = mv.HolisticLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(self.model_asset_path)),
                running_mode=mv.RunningMode.IMAGE,
                min_face_detection_confidence=0.5,
                min_face_landmarks_confidence=0.5,
                min_pose_detection_confidence=0.5,
                min_pose_landmarks_confidence=0.5,
                min_hand_landmarks_confidence=0.5,
            )
            self._holistic = mv.HolisticLandmarker.create_from_options(options)
            self.available = True
        except Exception as exc:
            self.reason = f"MediaPipe Holistic task failed to initialize: {exc}"

    @staticmethod
    def _compact_points(landmarks, count: int, dims: int, indices=None) -> tuple[np.ndarray, bool]:
        if not landmarks:
            return np.zeros(count * dims, dtype=np.float32), False
        picks = range(count) if indices is None else indices
        values: list[float] = []
        for i in picks:
            lm = landmarks[i]
            values.extend([float(lm.x), float(lm.y), float(lm.z)])
            if dims == 4:
                values.append(float(getattr(lm, "visibility", 1.0) or 0.0))
        return np.asarray(values, dtype=np.float32), True

    @staticmethod
    def _normalize_xyz(values: np.ndarray, origin_x: float, origin_y: float, scale: float, stride: int) -> np.ndarray:
        out = values.copy()
        for i in range(0, len(out), stride):
            out[i] = (out[i] - origin_x) / scale
            out[i + 1] = (out[i + 1] - origin_y) / scale
            out[i + 2] = out[i + 2] / scale
        return out

    @staticmethod
    def _wrist_relative(landmarks) -> np.ndarray:
        if not landmarks:
            return np.zeros(21 * 3, dtype=np.float32)
        coords = np.asarray([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
        coords -= coords[0]
        return coords.flatten()

    @staticmethod
    def _bootstrap_pose(landmarks) -> np.ndarray:
        if not landmarks:
            return np.zeros(33 * 4, dtype=np.float32)
        return np.asarray(
            [[lm.x, lm.y, lm.z, float(getattr(lm, "visibility", 1.0) or 0.0)] for lm in landmarks],
            dtype=np.float32,
        ).flatten()

    @staticmethod
    def _bootstrap_face(landmarks) -> np.ndarray:
        if not landmarks or len(landmarks) <= max(BOOTSTRAP_FACE_INDICES):
            return np.zeros(len(BOOTSTRAP_FACE_INDICES) * 3, dtype=np.float32)
        nose = np.asarray([landmarks[1].x, landmarks[1].y, landmarks[1].z], dtype=np.float32)
        points = np.asarray(
            [[landmarks[i].x, landmarks[i].y, landmarks[i].z] for i in BOOTSTRAP_FACE_INDICES],
            dtype=np.float32,
        )
        points -= nose
        return points.flatten()

    def extract_jpeg(self, jpeg: bytes) -> PerceptionResult:
        if not self.available or self._holistic is None or mp is None:
            raise RuntimeError(self.reason or "perception unavailable")

        started = perf_counter()
        arr = np.frombuffer(jpeg, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("invalid JPEG frame")

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._holistic.detect(mp_image)

        left_lms = result.left_hand_landmarks
        right_lms = result.right_hand_landmarks
        pose_lms = result.pose_landmarks
        face_lms = result.face_landmarks

        left, has_left = self._compact_points(left_lms, 21, 3)
        right, has_right = self._compact_points(right_lms, 21, 3)
        pose, has_pose = self._compact_points(pose_lms, len(POSE_INDICES), 4, POSE_INDICES)
        face, has_face = self._compact_points(face_lms, len(FACE_INDICES), 3, FACE_INDICES)

        origin_x, origin_y, scale = 0.5, 0.5, 0.35
        if pose_lms and len(pose_lms) > 12:
            ls = pose_lms[11]
            rs = pose_lms[12]
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
            raise RuntimeError(f"native feature schema mismatch {vector.shape[0]} != {SCHEMA.feature_dim}")

        bootstrap_vector = np.concatenate(
            [
                self._bootstrap_pose(pose_lms),
                self._bootstrap_face(face_lms),
                self._wrist_relative(left_lms),
                self._wrist_relative(right_lms),
            ]
        ).astype(np.float32)
        if bootstrap_vector.shape[0] != 378:
            raise RuntimeError(f"bootstrap feature schema mismatch {bootstrap_vector.shape[0]} != 378")

        quality = (
            0.35 * bool(has_left or has_right)
            + 0.25 * bool(has_left and has_right)
            + 0.2 * bool(has_pose)
            + 0.2 * bool(has_face)
        )

        return PerceptionResult(
            vector=vector,
            bootstrap_vector=bootstrap_vector,
            tracking={
                "left_hand": has_left,
                "right_hand": has_right,
                "pose": has_pose,
                "face": has_face,
                "quality": float(quality),
            },
            overlay={
                "left_hand": self._xy(left_lms),
                "right_hand": self._xy(right_lms),
                "pose": self._xy(pose_lms, POSE_INDICES),
            },
            latency_ms=(perf_counter() - started) * 1000,
        )

    @staticmethod
    def _xy(landmarks, indices=None) -> list[list[float]]:
        if not landmarks:
            return []
        picks = range(len(landmarks)) if indices is None else indices
        return [
            [round(float(landmarks[i].x), 4), round(float(landmarks[i].y), 4)]
            for i in picks
        ]
