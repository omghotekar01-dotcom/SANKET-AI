from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
from huggingface_hub import hf_hub_download

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.training.bootstrap_public import HF_REPO, OfflineHolisticExtractor, extract_sequence, load_metadata, slug_label

TARGETS = ("yes", "no", "help", "water", "where")
ALLOWED_SOURCES = {"INCLUDE", "CISLR", "ISL500", "ISL-DATA", "ISL500 / ISL-DATA"}


def signer_hint(row: dict) -> str:
    for key in ("signer_id", "signer", "user_id", "source_signer", "subject"):
        value = (row.get(key) or "").strip()
        if value:
            return value
    joined = " ".join(str(v) for v in row.values())
    match = re.search(r"(?i)\b(user|signer|subject)[ _-]?0*(\d{1,3})\b", joined)
    if match:
        return f"{match.group(1).lower()}-{int(match.group(2)):03d}"
    return "unknown"


def select_rows(rows: list[dict], max_per_class: int, min_per_class: int):
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        source = (row.get("dataset") or "").strip()
        review = (row.get("review_status") or "").strip().lower()
        word = (row.get("normalized_word") or row.get("word") or "").strip().lower()
        if source not in ALLOWED_SOURCES or word not in TARGETS:
            continue
        if review and review not in {"accepted", "ok"}:
            continue
        if row.get("video_path"):
            grouped[word].append(row)

    counts = {word: len(grouped.get(word, [])) for word in TARGETS}
    missing = {word: count for word, count in counts.items() if count < min_per_class}
    if missing:
        raise RuntimeError(f"Not enough eligible clips: {missing}")

    selected = {}
    for word in TARGETS:
        rows_for_word = sorted(
            grouped[word],
            key=lambda r: (
                -(float(r.get("quality_score") or 0)),
                r.get("dataset") or "",
                r.get("video_path") or "",
            ),
        )[:max_per_class]
        selected[word] = rows_for_word
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/core_extension_landmarks")
    parser.add_argument("--max-per-class", type=int, default=18)
    parser.add_argument("--min-per-class", type=int, default=8)
    args = parser.parse_args()

    out = REPO_ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    for path in out.glob("*"):
        if path.is_file():
            path.unlink()

    selected = select_rows(load_metadata(), args.max_per_class, args.min_per_class)
    extractor = OfflineHolisticExtractor()
    counts = Counter()
    sources = Counter()
    licenses = Counter()
    signers = Counter()

    try:
        for word, rows in selected.items():
            for row in rows:
                remote_path = row["video_path"]
                local_video = Path(hf_hub_download(HF_REPO, remote_path, repo_type="dataset"))
                sequence = extract_sequence(local_video, extractor, max_frames=48)
                if sequence is None:
                    print("[core-extension] low tracking:", remote_path)
                    continue
                sample_id = hashlib.sha256(remote_path.encode("utf-8")).hexdigest()[:24]
                signer = signer_hint(row)
                np.savez_compressed(out / f"{sample_id}.npz", sequence=sequence)
                meta = {
                    "sample_id": sample_id,
                    "label": slug_label(word),
                    "signer_id": signer,
                    "source_dataset": row.get("dataset"),
                    "source_repository": row.get("repository"),
                    "source_license": row.get("license"),
                    "source_video_path": remote_path,
                    "frame_count": int(sequence.shape[0]),
                    "feature_schema": "holistic-v1",
                    "feature_path": f"{sample_id}.npz",
                }
                (out / f"{sample_id}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
                counts[word] += 1
                sources[str(row.get("dataset") or "unknown")] += 1
                licenses[str(row.get("license") or "unspecified")] += 1
                signers[signer] += 1
    finally:
        extractor.close()

    insufficient = {word: counts[word] for word in TARGETS if counts[word] < args.min_per_class}
    if insufficient:
        raise RuntimeError(f"Too few usable tracked clips: {insufficient}")

    manifest = {
        "targets": list(TARGETS),
        "counts": dict(counts),
        "sources": dict(sources),
        "licenses": dict(licenses),
        "signer_hints": dict(signers),
        "source_dataset": HF_REPO,
        "raw_video_redistributed": False,
    }
    (out / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
