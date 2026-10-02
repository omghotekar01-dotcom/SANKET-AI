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


def load_samples(root: Path) -> list[Sample]:
    samples: list[Sample] = []
    for meta_path in sorted(root.glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if not meta.get("consent"):
            continue
        feature_path = root / meta["feature_path"]
        if not feature_path.exists():
            continue
        seq = np.load(feature_path)["sequence"].astype(np.float32)
        samples.append(Sample(meta["sample_id"], meta["label"], meta["signer_id"], seq, meta))
    return samples


def split_samples(samples: list[Sample], seed: int = 42) -> tuple[list[Sample], list[Sample], list[Sample], dict]:
    signers = sorted({s.signer_id for s in samples})
    rng = random.Random(seed)
    if len(signers) >= 3:
        shuffled = signers[:]; rng.shuffle(shuffled)
        test_signer = shuffled[0]; val_signer = shuffled[1]
        train = [s for s in samples if s.signer_id not in {test_signer, val_signer}]
        val = [s for s in samples if s.signer_id == val_signer]
        test = [s for s in samples if s.signer_id == test_signer]
        return train, val, test, {"mode":"signer_disjoint","train_signers":sorted({s.signer_id for s in train}),"val_signers":[val_signer],"test_signers":[test_signer]}
    if len(signers) == 2:
        # Train on one signer, test on the other; validation uses a held-out fraction of train signer.
        test_signer = signers[-1]
        pool = [s for s in samples if s.signer_id != test_signer]
        rng.shuffle(pool)
        cut = max(1, int(len(pool) * 0.2))
        val, train = pool[:cut], pool[cut:]
        test = [s for s in samples if s.signer_id == test_signer]
        return train, val, test, {"mode":"held_out_test_signer","train_signers":sorted({s.signer_id for s in train}),"val_signers":sorted({s.signer_id for s in val}),"test_signers":[test_signer],"limitation":"Validation signer overlaps training signer."}

    shuffled = samples[:]; rng.shuffle(shuffled)
    n = len(shuffled)
    n_test = max(1, int(n * 0.2)); n_val = max(1, int(n * 0.2))
    test = shuffled[:n_test]; val = shuffled[n_test:n_test+n_val]; train = shuffled[n_test+n_val:]
    return train, val, test, {"mode":"sample_split_single_signer","limitation":"Only one signer available; results do not demonstrate signer-independent generalization."}


def vectorize(sample: Sample, sequence_length: int) -> np.ndarray:
    return append_velocity(resample_sequence(sample.sequence, sequence_length))
