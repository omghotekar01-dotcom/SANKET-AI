from __future__ import annotations

from importlib import metadata
import json
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "ml" / "artifacts" / "bootstrap-50"


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

    tensorflow_version = _version("tensorflow")
    tf_ok = bool(tensorflow_version and tensorflow_version.startswith("2.16."))
    print("tensorflow  ", f"{'OK' if tf_ok else 'MISSING/INCOMPATIBLE'} - {tensorflow_version}")
    ok &= tf_ok

    model_path = BOOTSTRAP / "isl_model_solo.keras"
    holistic_path = BOOTSTRAP / "holistic_landmarker.task"
    manifest_path = BOOTSTRAP / "manifest.json"

    model_ok = model_path.exists() and model_path.stat().st_size == 9_783_895
    holistic_ok = holistic_path.exists() and holistic_path.stat().st_size == 13_683_609
    manifest_ok = False
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_ok = (
                manifest.get("source_commit") == "d77b58e663fa5a30aef475002415b96b7d468f96"
                and len(manifest.get("labels", [])) == 50
            )
        except Exception:
            manifest_ok = False

    print("bootstrap ML ", "OK" if model_ok else "MISSING")
    print("holistic task", "OK" if holistic_ok else "MISSING")
    print("bootstrap meta", "OK" if manifest_ok else "MISSING/INVALID")
    ok &= model_ok and holistic_ok and manifest_ok

    for exe in ["node", "npm"]:
        path = shutil.which(exe)
        print(f"{exe:12}", path or "MISSING")
        ok &= bool(path)

    node_modules = ROOT / "apps" / "web" / "node_modules"
    print("web deps     ", "OK" if node_modules.exists() else "MISSING")
    ok &= node_modules.exists()

    local_model = ROOT / "ml" / "artifacts" / "demo-v1" / "manifest.json"
    print(
        "Local model: ",
        "PRESENT - will override bootstrap"
        if local_model.exists()
        else "not trained; verified 50-word bootstrap will be used",
    )
    print("Raw video storage default: OFF")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
