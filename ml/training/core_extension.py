from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import numpy as np
from huggingface_hub import hf_hub_download

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.training.bootstrap_public import (
    HF_REPO,
    OfflineHolisticExtractor,
    extract_sequence,
    load_metadata,
    slug_label,
)

TARGETS = ("yes", "no", "help", "stop", "water", "where")
ALLOWED_SOURCES = {"INCLUDE", "CISLR", "ISL500", "ISL-DATA", "ISL500 / ISL-DATA"}


def select_target_rows(rows: list[dict], max_per_class: int, min_per_class: int):
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        source = (row.get("dataset") or "").strip()
        review = (row.get("review_status") or "").strip().lower()
        word = (row.get("normalized_word") or row.get("word") or "").strip().lower()
        if source not in ALLOWED_SOURCES or word not in TARGETS:
            continue
        if review and review not in {"accepted", "ok"}:
            continue
        if not row.get("video_path"):
            continue
        grouped[word].append(row)

    counts = {word: len(grouped.get(word, [])) for word in TARGETS}
    missing = {word: count for word, count in counts.items() if count < min_per_class}
    if missing:
        raise RuntimeError(
            "Not enough eligible public/research clips for required core targets: "
            + json.dumps(missing, sort_keys=True)
        )

    return {
        word: sorted(
            grouped[word],
            key=lambda r: (
                -(float(r.get("quality_score") or 0)),
                r.get("dataset") or "",
                r.get("video_path") or "",
            ),
        )[:max_per_class]
        for word in TARGETS
    }


def build_data(out_dir: Path, max_per_class: int, min_per_class: int):
    selected = select_target_rows(load_metadata(), max_per_class, min_per_class)
    print("[core-extension] selected:", {k: len(v) for k, v in selected.items()})
    out_dir.mkdir(parents=True, exist_ok=True)
    extractor = OfflineHolisticExtractor()
    saved = Counter()
    sources = Counter()
    licenses = Counter()
    try:
        for word, rows in selected.items():
            label = slug_label(word)
            for row in rows:
                remote_path = row["video_path"]
                local_video = Path(hf_hub_download(HF_REPO, remote_path, repo_type="dataset"))
                seq = extract_sequence(local_video, extractor, max_frames=48)
                if seq is None:
                    print("[core-extension] low tracking:", remote_path)
                    continue
                sample_id = uuid4().hex
                npz_name = sample_id + ".npz"
                np.savez_compressed(out_dir / npz_name, sequence=seq)
                meta = {
                    "sample_id": sample_id,
                    "label": label,
                    "signer_id": "public-aggregate",
                    "consent": False,
                    "usage_authorized": True,
                    "source_type": "public_research_dataset",
                    "source_dataset": row.get("dataset"),
                    "source_repository": row.get("repository"),
                    "source_license": row.get("license"),
                    "source_video_path": remote_path,
                    "review_status": row.get("review_status"),
                    "frame_count": int(seq.shape[0]),
                    "feature_schema": "holistic-v1",
                    "feature_path": npz_name,
                }
                (out_dir / (sample_id + ".json")).write_text(
                    json.dumps(meta, indent=2), encoding="utf-8"
                )
                saved[label] += 1
                sources[str(row.get("dataset") or "unknown")] += 1
                licenses[str(row.get("license") or "unspecified")] += 1
    finally:
        extractor.close()

    insufficient = {word: saved[word] for word in TARGETS if saved[word] < 3}
    if insufficient:
        raise RuntimeError(f"Too few usable tracked clips: {insufficient}")
    return dict(saved), dict(sources), dict(licenses)


def annotate(out_dir: Path, counts: dict, sources: dict, licenses: dict):
    manifest_path = out_dir / "manifest.json"
    report_path = out_dir / "evaluation.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))

    manifest["model_version"] = "sanket-core-extension-v1"
    manifest["source"] = "SANKET-trained from vidit031/isl-isolated-40words"
    manifest["training_origin"] = "public_core_extension"
    manifest["public_sources"] = sources
    manifest["public_licenses"] = licenses
    manifest["target_contract"] = list(TARGETS)
    manifest["license_note"] = (
        "Eligible rows came from INCLUDE (CC-BY-4.0), CISLR (AFL-3.0), and "
        "ISL500/ISL-DATA (research/academic use only). Source videos were "
        "downloaded during training and are not redistributed. This derived "
        "extension remains research/academic-use only unless ISL500 authors "
        "grant broader terms."
    )
    manifest["split"]["limitation"] = (
        "Aggregate metadata does not provide a reliable signer identity for every clip; "
        "evaluation is a stratified sample holdout and is not a signer-independent claim."
    )
    report["manifest"] = manifest
    report["class_counts"] = counts
    report["claims_note"] = (
        "Metrics apply only to the six isolated core signs and this public sample holdout."
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "MODEL_CARD.md").write_text(
        "# SANKET core vocabulary extension v1\n\n"
        "Targets: yes, no, help, stop, water, where.\n\n"
        "Training source: vidit031/isl-isolated-40words aggregate using INCLUDE "
        "(CC-BY-4.0), CISLR (AFL-3.0), and ISL500/ISL-DATA (research/academic "
        "use only). Raw videos are not redistributed. This extension is for "
        "research/academic use and its evaluation is a sample holdout, not "
        "signer-independent.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-per-class", type=int, default=16)
    parser.add_argument("--min-per-class", type=int, default=3)
    parser.add_argument("--data", default="data/core_extension_landmarks")
    parser.add_argument("--out", default="ml/artifacts/core-extension-v1")
    args = parser.parse_args()

    data_dir = REPO_ROOT / args.data
    out_dir = REPO_ROOT / args.out
    if data_dir.exists():
        for path in data_dir.glob("*"):
            if path.is_file():
                path.unlink()

    counts, sources, licenses = build_data(
        data_dir, args.max_per_class, args.min_per_class
    )
    completed = subprocess.run(
        [
            sys.executable, "-m", "ml.training.train_template",
            "--data", args.data, "--out", args.out,
        ],
        cwd=REPO_ROOT, text=True, capture_output=True,
    )
    print(completed.stdout)
    if completed.returncode != 0:
        print(completed.stderr, file=sys.stderr)
        return completed.returncode

    annotate(out_dir, counts, sources, licenses)
    print(json.dumps({
        "artifact": str(out_dir),
        "counts": counts,
        "sources": sources,
        "licenses": licenses,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
