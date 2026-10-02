from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.config import settings
from apps.api.app.services.bootstrap_model import BootstrapKerasModel
from apps.api.app.services.landmark_service import HolisticLandmarkService
from apps.api.app.services.vocabulary_service import core_coverage


def main() -> int:
    perception = HolisticLandmarkService()
    if not perception.available:
        raise RuntimeError(perception.reason or "MediaPipe perception unavailable")

    # Deliberately non-square, matching the browser capture path that crashed on
    # Windows when Holistic Tasks was used.
    frame = np.zeros((216, 384, 3), dtype=np.uint8)
    cv2.rectangle(frame, (105, 30), (280, 210), (170, 170, 170), -1)
    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        raise RuntimeError("Could not create smoke-test JPEG")

    result = perception.extract_jpeg(encoded.tobytes())
    assert result.vector.shape == (226,), result.vector.shape
    assert result.bootstrap_vector.shape == (378,), result.bootstrap_vector.shape
    perception.close()

    model = BootstrapKerasModel(settings.bootstrap_dir)
    assert model.loaded, model.load_error
    assert len(model.labels) == 50, len(model.labels)
    coverage = core_coverage(model.labels)
    expected_core = {
        "hello", "thank_you", "doctor", "hospital",
        "medicine", "police", "student", "teacher",
    }
    assert set(coverage["supported"]) == expected_core, coverage
    assert coverage["supported_count"] == 8, coverage
    assert coverage["total"] == 21, coverage

    # Run one real inference pass too, not only model deserialization.
    prediction = model.predict(np.zeros((30, 378), dtype=np.float32))
    assert prediction.probabilities.shape == (50,), prediction.probabilities.shape
    assert np.isfinite(prediction.probabilities).all()
    assert abs(float(prediction.probabilities.sum()) - 1.0) < 1e-4

    print(
        "Live runtime smoke test: OK - MediaPipe Solutions processed a "
        f"384x216 JPEG; OpenVINO loaded and inferred {len(model.labels)} classes; "
        f"core contract coverage {coverage['supported_count']}/{coverage['total']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
