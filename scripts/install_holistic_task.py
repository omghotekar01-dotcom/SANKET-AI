from __future__ import annotations

import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ml" / "artifacts" / "bootstrap-50"
TARGET = OUT / "holistic_landmarker.task"
URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "holistic_landmarker/holistic_landmarker/float16/1/holistic_landmarker.task"
)
MIN_BYTES = 10_000_000


def valid(path: Path) -> bool:
    return path.exists() and path.stat().st_size >= MIN_BYTES


def main() -> int:
    if valid(TARGET):
        print(f"[vision] Holistic task asset ready: {TARGET} ({TARGET.stat().st_size} bytes)")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    tmp = TARGET.with_suffix(".task.part")
    if tmp.exists():
        tmp.unlink()

    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "SANKET-AI-Hacktopia/1.0"},
    )
    try:
        print("[vision] Downloading official Google MediaPipe Holistic task asset...")
        with urllib.request.urlopen(request, timeout=90) as response, tmp.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if tmp.exists():
            tmp.unlink()
        print(f"[vision] ERROR: {exc}", file=sys.stderr)
        return 1

    if not valid(tmp):
        size = tmp.stat().st_size if tmp.exists() else 0
        if tmp.exists():
            tmp.unlink()
        print(
            f"[vision] ERROR: downloaded Holistic task asset is unexpectedly small ({size} bytes)",
            file=sys.stderr,
        )
        return 1

    os.replace(tmp, TARGET)
    print(f"[vision] Holistic task asset installed: {TARGET} ({TARGET.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
