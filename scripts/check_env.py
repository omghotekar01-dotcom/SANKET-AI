from __future__ import annotations

from importlib import metadata
import json
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VISION_DIR = ROOT / "ml" / "artifacts" / "bootstrap-50"
LOCAL_MODEL = ROOT / "ml" / "artifacts" / "demo-v1"


def _version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


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

    for package in ["fastapi", "uvicorn"]:
        version = _version(package)
        print(f"{package:12}", f"OK - {version}" if version else "MISSING")
        ok &= bool(version)

    numpy_version = _version("numpy")
    numpy_ok = numpy_version == "1.26.4"
    print("numpy       ", f"{'OK' if numpy_ok else 'INCOMPATIBLE'} - {numpy_version}")
    ok &= numpy_ok

    opencv_version = _version("opencv-contrib-python")
    opencv_ok = bool(opencv_version and opencv_version.startswith("4.11."))
    print("opencv      ", f"{'OK' if opencv_ok else 'INCOMPATIBLE'} - {opencv_version}")
    ok &= opencv_ok

    mediapipe_version = _version("mediapipe")
    mediapipe_ok = mediapipe_version == "0.10.21"
    print("mediapipe   ", f"{'OK' if mediapipe_ok else 'INCOMPATIBLE'} - {mediapipe_version}")
    ok &= mediapipe_ok

    holistic_path = VISION_DIR / "holistic_landmarker.task"
    holistic_ok = holistic_path.exists() and holistic_path.stat().st_size >= 10_000_000
    print("holistic task", "OK" if holistic_ok else "MISSING")
    ok &= holistic_ok

    try:
        from mediapipe.tasks.python import vision as mv
        task_api_ok = hasattr(mv, "HolisticLandmarker")
    except Exception:
        task_api_ok = False
    print("holistic API ", "OK" if task_api_ok else "MISSING/INCOMPATIBLE")
    ok &= task_api_ok

    for exe in ["node", "npm"]:
        path = shutil.which(exe)
        print(f"{exe:12}", path or "MISSING")
        ok &= bool(path)

    node_modules = ROOT / "apps" / "web" / "node_modules"
    print("web deps     ", "OK" if node_modules.exists() else "MISSING")
    ok &= node_modules.exists()

    manifest_path = LOCAL_MODEL / "manifest.json"
    model_path = LOCAL_MODEL / "model.npz"
    if manifest_path.exists() and model_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            print(
                "sign model   ",
                f"OK - {manifest.get('model_version')} / {len(manifest.get('labels', []))} classes",
            )
        except Exception:
            print("sign model   PRESENT but manifest is unreadable")
            ok = False
    else:
        print("sign model   NOT INSTALLED YET - camera tracking still works")

    print("external ML  optional; not required for startup")
    print("Raw video storage default: OFF")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
