from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    print("SANKET AI runtime check")
    print("Python:", sys.version.split()[0], platform.platform())
    ok = True

    if sys.version_info[:2] not in {(3, 11), (3, 12)}:
        print("python       INCOMPATIBLE - use Python 3.11 or 3.12")
        ok = False

    if platform.architecture()[0] != "64bit":
        print("python       INCOMPATIBLE - 64-bit Python is required")
        ok = False

    try:
        import fastapi  # noqa: F401
        print("fastapi      OK")
    except Exception as exc:
        print("fastapi      ERROR", exc)
        ok = False

    try:
        import uvicorn  # noqa: F401
        print("uvicorn      OK")
    except Exception as exc:
        print("uvicorn      ERROR", exc)
        ok = False

    try:
        import numpy as np
        numpy_ok = np.__version__ == "1.26.4"
        print(f"numpy        {'OK' if numpy_ok else 'INCOMPATIBLE'} - {np.__version__}")
        ok &= numpy_ok
    except Exception as exc:
        print("numpy        ERROR", exc)
        ok = False

    try:
        import cv2
        cv_ok = cv2.__version__.startswith("4.11.")
        print(f"opencv       {'OK' if cv_ok else 'INCOMPATIBLE'} - {cv2.__version__}")
        ok &= cv_ok
    except Exception as exc:
        print("opencv       ERROR", exc)
        ok = False

    try:
        import mediapipe as mp
        from mediapipe.python.solutions import holistic
        version_ok = getattr(mp, "__version__", "") == "0.10.21"
        holistic_ok = hasattr(holistic, "Holistic")
        mp_ok = version_ok and holistic_ok
        print(
            f"mediapipe    {'OK' if mp_ok else 'INCOMPATIBLE'} - "
            f"{getattr(mp, '__version__', 'unknown')} / Holistic={'yes' if holistic_ok else 'no'}"
        )
        ok &= mp_ok
    except Exception as exc:
        print("mediapipe    ERROR", exc)
        ok = False

    for exe in ["node", "npm"]:
        path = shutil.which(exe)
        print(f"{exe:12}", path or "MISSING")
        ok &= bool(path)

    node_modules = ROOT / "apps" / "web" / "node_modules"
    print("web deps     ", "OK" if node_modules.exists() else "MISSING")
    ok &= node_modules.exists()

    print(
        "Model:       ",
        "ARTIFACT PRESENT"
        if (ROOT / "ml" / "artifacts" / "demo-v1" / "manifest.json").exists()
        else "NOT TRAINED YET (camera tracking can still be tested)",
    )
    print("Raw video storage default: OFF")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
