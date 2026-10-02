from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
import numpy as np

from apps.api.app.services.feature_schema import append_velocity, resample_sequence


@dataclass
class Sample:
    sample_id: str
    label: str
    signer_id: str
    sequence: np.ndarray
    metadata: dict


def _authorized(meta: dict) -> bool:
    if bool(meta.get("consent")):
        return True
    return bool(
        meta.get("source_type") == "public_research_dataset"
        and meta.get("usage_authorized") is True
    )


def load_samples(root: Path) -> list[Sample]:
    samples: list[Sample] = []
    for meta_path in sorted(root.glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if not _authorized(meta):
            continue
        feature_path = root / meta["feature_path"]
        if not feature_path.exists():
            continue
        seq = np.load(feature_path)["sequence"].astype(np.float32)
        samples.append(
            Sample(
                meta["sample_id"],
                meta["label"],
                meta.get("signer_id", "unknown"),
                seq,
                meta,
            )
        )
    return samples


def _stratified_single_signer(samples: list[Sample], seed: int):
    rng = random.Random(seed)
    by_label: dict[str, list[Sample]] = {}
    for sample in samples:
        by_label.setdefault(sample.label, []).append(sample)

    train: list[Sample] = []
    val: list[Sample] = []
    test: list[Sample] = []

    for _, rows in sorted(by_label.items()):
        rows = rows[:]
        rng.shuffle(rows)
        if len(rows) < 3:
            train.extend(rows)
            continue
        test.append(rows[0])
        val.append(rows[1])
        train.extend(rows[2:])

    return train, val, test, {
        "mode": "stratified_sample_split_no_signer_claim",
        "limitation": (
            "Samples were stratified by label, but signer-independent generalization "
            "is not demonstrated. Treat these metrics as bootstrap-only."
        ),
    }


def split_samples(samples: list[Sample], seed: int = 42) -> tuple[list[Sample], list[Sample], list[Sample], dict]:
    signers = sorted({s.signer_id for s in samples})
    rng = random.Random(seed)

    if len(signers) >= 3 and "public-aggregate" not in signers:
        shuffled = signers[:]
        rng.shuffle(shuffled)
        test_signer = shuffled[0]
        val_signer = shuffled[1]
        train = [s for s in samples if s.signer_id not in {test_signer, val_signer}]
        val = [s for s in samples if s.signer_id == val_signer]
        test = [s for s in samples if s.signer_id == test_signer]
        return train, val, test, {
            "mode": "signer_disjoint",
            "train_signers": sorted({s.signer_id for s in train}),
            "val_signers": [val_signer],
            "test_signers": [test_signer],
        }

    if len(signers) == 2:
        test_signer = signers[-1]
        pool = [s for s in samples if s.signer_id != test_signer]
        rng.shuffle(pool)
        cut = max(1, int(len(pool) * 0.2))
        val, train = pool[:cut], pool[cut:]
        test = [s for s in samples if s.signer_id == test_signer]
        return train, val, test, {
            "mode": "held_out_test_signer",
            "train_signers": sorted({s.signer_id for s in train}),
            "val_signers": sorted({s.signer_id for s in val}),
            "test_signers": [test_signer],
            "limitation": "Validation signer overlaps training signer.",
        }

    return _stratified_single_signer(samples, seed)


def vectorize(sample: Sample, sequence_length: int) -> np.ndarray:
    return append_velocity(resample_sequence(sample.sequence, sequence_length))
