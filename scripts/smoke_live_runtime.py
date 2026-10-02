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


def main() -> int:
    perception = HolisticLandmarkService()
    if not perception.available:
        raise RuntimeError(perception.reason or "MediaPipe perception unavailable")

    # A non-square frame deliberately matches the live browser path and catches
    # graph/projection failures that simple import checks miss.
    frame = np.zeros((216, 384, 3), dtype=np.uint8)
    cv2.rectangle(frame, (110, 35), (275, 205), (160, 160, 160), -1)
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

    print(
        "Live runtime smoke test: OK - "
        f"MediaPipe Solutions frame processed; {len(model.labels)}-class model loaded."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
