from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

import cv2
import numpy as np
from huggingface_hub import hf_hub_download
from mediapipe.python.solutions import holistic as mp_holistic

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.app.services.feature_schema import FACE_INDICES, POSE_INDICES, SCHEMA

HF_REPO = "vidit031/isl-isolated-40words"
ALLOWED_SOURCES = {"INCLUDE", "CISLR"}
PREFERRED = [
    "help", "hospital", "water", "yes", "no", "stop",
    "thank you", "where", "teacher", "student", "hello", "today",
]


def slug_label(word: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", word.strip().lower()).strip("_")


class OfflineHolisticExtractor:
    """Stable offline extractor using MediaPipe 0.10.21 legacy Holistic.

    Live SANKET uses Tasks. Both paths expose the same landmark families; this
    extractor maps them into the exact native 226-D SANKET feature contract.
    """

    def __init__(self) -> None:
        self.holistic = mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            refine_face_landmarks=False,
            min_detection_confidence=0.45,
            min_tracking_confidence=0.45,
        )

    def close(self) -> None:
        self.holistic.close()

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
                values.append(float(getattr(lm, "visibility", 1.0) or 0.0))
        return np.asarray(values, dtype=np.float32), True

    @staticmethod
    def _normalize_xyz(
        values: np.ndarray,
        origin_x: float,
        origin_y: float,
        scale: float,
        stride: int,
    ) -> np.ndarray:
        out = values.copy()
        for i in range(0, len(out), stride):
            out[i] = (out[i] - origin_x) / scale
            out[i + 1] = (out[i + 1] - origin_y) / scale
            out[i + 2] = out[i + 2] / scale
        return out

    def extract(self, bgr: np.ndarray) -> np.ndarray | None:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        result = self.holistic.process(rgb)

        left, has_left = self._points(result.left_hand_landmarks, 21, 3)
        right, has_right = self._points(result.right_hand_landmarks, 21, 3)
        pose, has_pose = self._points(
            result.pose_landmarks, len(POSE_INDICES), 4, POSE_INDICES
        )
        face, has_face = self._points(
            result.face_landmarks, len(FACE_INDICES), 3, FACE_INDICES
        )

        if not (has_left or has_right or has_pose):
            return None

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
        masks = np.asarray(
            [has_left, has_right, has_pose, has_face], dtype=np.float32
        )
        vector = np.concatenate([left, right, pose, face, masks]).astype(np.float32)
        if vector.shape[0] != SCHEMA.feature_dim:
            raise RuntimeError(
                f"offline feature schema mismatch {vector.shape[0]} != {SCHEMA.feature_dim}"
            )
        return vector


def load_metadata() -> list[dict]:
    path = hf_hub_download(HF_REPO, "metadata.csv", repo_type="dataset")
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def select_rows(
    rows: list[dict],
    class_count: int,
    max_per_class: int,
    min_per_class: int,
):
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        source = (row.get("dataset") or "").strip()
        review = (row.get("review_status") or "").strip().lower()
        if source not in ALLOWED_SOURCES:
            continue
        if review and review not in {"accepted", "ok"}:
            continue
        word = (row.get("normalized_word") or row.get("word") or "").strip().lower()
        if not word or not row.get("video_path"):
            continue
        grouped[word].append(row)

    eligible = {k: v for k, v in grouped.items() if len(v) >= min_per_class}
    if len(eligible) < 3:
        raise RuntimeError(
            f"Only {len(eligible)} classes have >= {min_per_class} clips in allowed sources."
        )

    selected: list[str] = [w for w in PREFERRED if w in eligible]
    for word, clips in sorted(
        eligible.items(), key=lambda kv: (-len(kv[1]), kv[0])
    ):
        if word not in selected:
            selected.append(word)
        if len(selected) >= class_count:
            break
    selected = selected[:class_count]

    return {
        word: sorted(
            eligible[word],
            key=lambda r: (
                (r.get("dataset") or ""),
                -(float(r.get("quality_score") or 0)),
                r.get("video_path") or "",
            ),
        )[:max_per_class]
        for word in selected
    }


def extract_sequence(
    video_path: Path,
    extractor: OfflineHolisticExtractor,
    max_frames: int = 42,
):
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        return None

    wanted = set(
        np.linspace(0, total - 1, min(max_frames, total), dtype=int).tolist()
    )
    sequence: list[np.ndarray] = []
    frame_index = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_index in wanted:
            vector = extractor.extract(frame)
            if vector is not None:
                sequence.append(vector)
        frame_index += 1

    cap.release()
    if len(sequence) < 8:
        return None
    return np.stack(sequence).astype(np.float32)


def build_landmarks(
    out_dir: Path,
    classes: int,
    max_per_class: int,
    min_per_class: int,
):
    rows = load_metadata()
    selected = select_rows(rows, classes, max_per_class, min_per_class)
    print("[public-train] selected:", {k: len(v) for k, v in selected.items()})

    extractor = OfflineHolisticExtractor()
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = Counter()
    provenance = Counter()

    try:
        for word, clips in selected.items():
            label = slug_label(word)
            for row in clips:
                source = (row.get("dataset") or "").strip()
                remote_path = row["video_path"]
                local_video = Path(
                    hf_hub_download(HF_REPO, remote_path, repo_type="dataset")
                )
                seq = extract_sequence(local_video, extractor)
                if seq is None:
                    print(f"[public-train] skipped low-tracking clip: {remote_path}")
                    continue

                sample_id = uuid4().hex
                npz_name = f"{sample_id}.npz"
                np.savez_compressed(out_dir / npz_name, sequence=seq)
                meta = {
                    "sample_id": sample_id,
                    "label": label,
                    "signer_id": "public-aggregate",
                    "consent": False,
                    "usage_authorized": True,
                    "source_type": "public_research_dataset",
                    "source_dataset": source,
                    "source_repository": row.get("repository"),
                    "source_license": row.get("license"),
                    "source_video_path": remote_path,
                    "review_status": row.get("review_status"),
                    "frame_count": int(seq.shape[0]),
                    "feature_schema": "holistic-v1",
                    "feature_path": npz_name,
                }
                (out_dir / f"{sample_id}.json").write_text(
                    json.dumps(meta, indent=2), encoding="utf-8"
                )
                saved[label] += 1
                provenance[source] += 1
                print(
                    f"[public-train] {label}: {saved[label]} "
                    f"({seq.shape[0]} usable frames)"
                )
    finally:
        extractor.close()

    usable = {k: v for k, v in saved.items() if v >= 3}
    if len(usable) < 3:
        raise RuntimeError(
            f"Too few usable classes after landmark extraction: {dict(saved)}"
        )

    for meta_path in out_dir.glob("*.json"):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta["label"] not in usable:
            feature = out_dir / meta["feature_path"]
            if feature.exists():
                feature.unlink()
            meta_path.unlink()

    return dict(usable), dict(provenance)


def annotate_artifact(out_dir: Path, counts: dict, provenance: dict):
    manifest_path = out_dir / "manifest.json"
    report_path = out_dir / "evaluation.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))

    manifest["model_version"] = "sanket-public-isolated-v1"
    manifest["source"] = "SANKET-trained from vidit031/isl-isolated-40words"
    manifest["training_origin"] = "public_research_dataset_bootstrap"
    manifest["public_sources"] = provenance
    manifest["license_note"] = (
        "Training clips were downloaded at build time and not redistributed. "
        "This bootstrap used only INCLUDE and CISLR rows from the aggregate corpus."
    )
    manifest["split"]["limitation"] = (
        "Public aggregate clips were evaluated with a stratified sample holdout. "
        "This does not demonstrate signer-independent generalization."
    )

    report["manifest"] = manifest
    report["class_counts"] = counts
    report["claims_note"] = (
        "Bootstrap metrics apply only to this isolated-sign public sample holdout. "
        "They are not evidence of unrestricted ISL translation or "
        "signer-independent performance."
    )

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    model_card = out_dir / "MODEL_CARD.md"
    original = model_card.read_text(encoding="utf-8") if model_card.exists() else ""
    model_card.write_text(
        "# SANKET public isolated-sign starter model\n\n"
        "This model was trained by SANKET AI from public isolated ISL video clips.\n\n"
        "- Aggregate: vidit031/isl-isolated-40words\n"
        "- Training sources restricted to INCLUDE and CISLR rows\n"
        "- Source videos are downloaded during training and are not committed\n"
        "- Offline feature extractor: MediaPipe 0.10.21 Holistic\n"
        "- Feature contract: SANKET native 226-D schema\n"
        "- Model: temporal template baseline\n"
        "- Evaluation: stratified sample holdout, not signer-disjoint\n\n"
        "Do not claim unrestricted ISL translation or signer-independent "
        "accuracy from this artifact.\n\n"
        + original,
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classes", type=int, default=8)
    parser.add_argument("--max-per-class", type=int, default=8)
    parser.add_argument("--min-per-class", type=int, default=3)
    parser.add_argument("--data", default="data/public_bootstrap_landmarks")
    parser.add_argument("--out", default="ml/artifacts/demo-v1")
    args = parser.parse_args()

    data_dir = REPO_ROOT / args.data
    out_dir = REPO_ROOT / args.out

    if data_dir.exists():
        for path in data_dir.glob("*"):
            if path.is_file():
                path.unlink()

    counts, provenance = build_landmarks(
        data_dir, args.classes, args.max_per_class, args.min_per_class
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ml.training.train_template",
            "--data",
            args.data,
            "--out",
            args.out,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        return completed.returncode

    annotate_artifact(out_dir, counts, provenance)
    print(
        json.dumps(
            {
                "artifact": str(out_dir),
                "class_counts": counts,
                "provenance": provenance,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
