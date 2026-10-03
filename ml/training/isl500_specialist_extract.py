from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from huggingface_hub import hf_hub_download

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.training.bootstrap_public import HF_REPO, OfflineHolisticExtractor, extract_sequence

TARGETS = (
    "hello",
    "thank you",
    "yes",
    "no",
    "help",
    "water",
    "teacher",
    "student",
    "where",
)


def slug(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def load_rows() -> list[dict]:
    path = hf_hub_download(HF_REPO, "metadata.csv", repo_type="dataset")
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/isl500_specialist")
    parser.add_argument("--max-per-class", type=int, default=15)
    args = parser.parse_args()

    rows = load_rows()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if (row.get("dataset") or "").strip() != "ISL500":
            continue
        if (row.get("review_status") or "").strip().lower() not in {"", "accepted", "ok"}:
            continue
        word = (row.get("normalized_word") or row.get("word") or "").strip().lower()
        signer = (row.get("signer") or "").strip()
        if word in TARGETS and signer and row.get("video_path"):
            grouped[word].append(row)

    missing = {word: len(grouped.get(word, [])) for word in TARGETS if len(grouped.get(word, [])) < 10}
    if missing:
        raise RuntimeError(f"ISL500 signer coverage insufficient: {missing}")

    out = REPO_ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    for path in out.glob("*"):
        if path.is_file():
            path.unlink()

    extractor = OfflineHolisticExtractor()
    counts = Counter()
    signers = Counter()
    try:
        for word in TARGETS:
            clips = sorted(grouped[word], key=lambda r: (r.get("signer") or "", r.get("video_path") or ""))[:args.max_per_class]
            for row in clips:
                remote = row["video_path"]
                local = Path(hf_hub_download(HF_REPO, remote, repo_type="dataset"))
                sequence = extract_sequence(local, extractor, max_frames=48)
                if sequence is None:
                    print("[isl500-specialist] skipped low tracking", remote)
                    continue

                sample_id = hashlib.sha256(remote.encode("utf-8")).hexdigest()[:24]
                np.savez_compressed(out / f"{sample_id}.npz", sequence=sequence)
                meta = {
                    "sample_id": sample_id,
                    "label": slug(word),
                    "signer_id": row["signer"],
                    "consent": False,
                    "usage_authorized": True,
                    "source_type": "public_research_dataset",
                    "source_dataset": "ISL500",
                    "source_repository": "ISL500/ISL-DATA via vidit031/isl-isolated-40words",
                    "source_license": row.get("license") or "research/academic use only",
                    "source_video_path": remote,
                    "feature_schema": "holistic-v1",
                    "feature_path": f"{sample_id}.npz",
                    "frame_count": int(sequence.shape[0]),
                }
                (out / f"{sample_id}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
                counts[slug(word)] += 1
                signers[row["signer"]] += 1
    finally:
        extractor.close()

    expected = {slug(word) for word in TARGETS}
    usable = {label for label, count in counts.items() if count >= 10}
    if usable != expected:
        raise RuntimeError(f"Usable class coverage mismatch: {dict(counts)}")

    summary = {
        "targets": [slug(word) for word in TARGETS],
        "counts": dict(counts),
        "signers": dict(signers),
        "source": "ISL500 subset",
        "usage": "research/academic prototype only",
        "raw_video_redistributed": False,
    }
    (out / "dataset_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
