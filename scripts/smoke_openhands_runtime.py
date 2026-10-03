from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.config import settings
from apps.api.app.services.openhands_include_model import OpenHandsIncludeModel
from apps.api.app.services.vocabulary_service import safe_bootstrap_labels


EXPECTED_SAFE = {
    "hello", "thank_you", "doctor", "hospital",
    "medicine", "police", "student", "teacher",
}


def main() -> int:
    model = OpenHandsIncludeModel(settings.openhands_dir)
    assert model.loaded, model.load_error
    assert len(model.labels) == 263, len(model.labels)
    assert set(safe_bootstrap_labels(model.labels)) == EXPECTED_SAFE

    # Non-degenerate synthetic 27-node clip verifies the complete graph forward pass.
    rng = np.random.default_rng(42)
    sequence = rng.normal(0.5, 0.08, size=(36, 54)).astype(np.float32)
    points = sequence.reshape(36, 27, 2)
    points[:, 3] = [0.35, 0.45]
    points[:, 4] = [0.65, 0.45]
    pred = model.predict(sequence)
    assert pred.probabilities.shape == (263,), pred.probabilities.shape
    assert np.isfinite(pred.probabilities).all()
    assert abs(float(pred.probabilities.sum()) - 1.0) < 1e-4

    print(
        "OpenHands smoke test: OK - official INCLUDE SL-GCN loaded, "
        f"inferred {len(model.labels)} classes, safe overlap {len(EXPECTED_SAFE)}/8."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
