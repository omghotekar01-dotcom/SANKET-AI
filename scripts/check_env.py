from __future__ import annotations

from importlib import metadata
import json
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_DIR = ROOT / "ml" / "artifacts" / "bootstrap-50"
LOCAL_MODEL = ROOT / "ml" / "artifacts" / "demo-v1"


def _version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    print("SANKET AI full runtime check")
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
    tf_ok = tensorflow_version == "2.16.1"
    print("tensorflow  ", f"{'OK' if tf_ok else 'MISSING/INCOMPATIBLE'} - {tensorflow_version}")
    ok &= tf_ok

    jax_version = _version("jax")
    jaxlib_version = _version("jaxlib")
    jax_absent = jax_version is None and jaxlib_version is None
    print("jax          ", "ABSENT - OK" if jax_absent else f"REMOVE - jax={jax_version} jaxlib={jaxlib_version}")
    ok &= jax_absent

    holistic_path = BOOTSTRAP_DIR / "holistic_landmarker.task"
    holistic_ok = holistic_path.exists() and holistic_path.stat().st_size == 13_683_609
    print("holistic task", "OK" if holistic_ok else "MISSING/INVALID")
    ok &= holistic_ok

    bootstrap_model = BOOTSTRAP_DIR / "isl_model_solo.keras"
    bootstrap_manifest = BOOTSTRAP_DIR / "manifest.json"
    bootstrap_ok = bootstrap_model.exists() and bootstrap_model.stat().st_size == 9_783_895
    labels_ok = False
    if bootstrap_manifest.exists():
        try:
            manifest = json.loads(bootstrap_manifest.read_text(encoding="utf-8"))
            labels_ok = len(manifest.get("labels", [])) == 50
        except Exception:
            labels_ok = False
    print("50-word model", "OK" if bootstrap_ok and labels_ok else "MISSING/INVALID")
    ok &= bootstrap_ok and labels_ok

    try:
        from apps.api.app.services.bootstrap_model import BootstrapKerasModel
        runtime_model = BootstrapKerasModel(BOOTSTRAP_DIR)
        runtime_model_ok = runtime_model.loaded and len(runtime_model.labels) == 50
        print(
            "model runtime ",
            f"OK - {runtime_model.version}" if runtime_model_ok else f"ERROR - {runtime_model.load_error}",
        )
        ok &= runtime_model_ok
    except Exception as exc:
        print("model runtime  ERROR", exc)
        ok = False

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

    local_manifest = LOCAL_MODEL / "manifest.json"
    local_path = LOCAL_MODEL / "model.npz"
    if local_manifest.exists() and local_path.exists():
        try:
            manifest = json.loads(local_manifest.read_text(encoding="utf-8"))
            print(
                "local model  ",
                f"PRESENT - {manifest.get('model_version')} / {len(manifest.get('labels', []))} classes / "
                f"origin={manifest.get('training_origin', 'unknown')}",
            )
        except Exception:
            print("local model   PRESENT but manifest unreadable")
    else:
        print("local model   none - bootstrap will be used")

    print("Raw video storage default: OFF")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
