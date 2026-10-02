from __future__ import annotations

import importlib.util
import platform
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main()->int:
    print("SANKET AI runtime check")
    print("Python:",sys.version.split()[0], platform.platform())
    ok=True

    if sys.version_info[:2] not in {(3,11),(3,12)}:
        print("python      WARN - Python 3.11 or 3.12 is required for the supported vision setup.")
        ok=False

    for module in ["fastapi","uvicorn","numpy","cv2"]:
        found=importlib.util.find_spec(module) is not None
        print(f"{module:12}", "OK" if found else "MISSING")
        ok &= found

    mp_ok=False
    try:
        import mediapipe as mp
        mp_ok=bool(hasattr(mp,"solutions") and hasattr(mp.solutions,"holistic"))
    except Exception as exc:
        print("mediapipe   ERROR",exc)
    if mp_ok:
        print(f"{'mediapipe':12} OK - Holistic available")
    else:
        print(f"{'mediapipe':12} MISSING/INCOMPATIBLE - run setup_windows.bat")
    ok &= mp_ok

    for exe in ["node","npm"]:
        found=shutil.which(exe) is not None
        print(f"{exe:12}", found and shutil.which(exe) or "MISSING")
        ok &= found

    print("Model:", "LOADED ARTIFACT PRESENT" if (ROOT/"ml/artifacts/demo-v1/manifest.json").exists() else "NOT TRAINED YET (camera tracking can still be tested)")
    print("Raw video storage default: OFF")
    return 0 if ok else 1


if __name__=="__main__":
    raise SystemExit(main())
