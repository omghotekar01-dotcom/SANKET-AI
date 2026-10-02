from __future__ import annotations

from importlib import metadata
import json
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    tf_absent = tensorflow_version is None
    print("tensorflow  ", "ABSENT - OK" if tf_absent else f"UNEXPECTED - {tensorflow_version}")
    ok &= tf_absent

    keras_version = _version("keras")
    keras_ok = keras_version == "3.15.1"
    print("keras        ", f"{'OK' if keras_ok else 'INCOMPATIBLE'} - {keras_version}")
    ok &= keras_ok

    openvino_version = _version("openvino")
    openvino_ok = openvino_version == "2026.4.1"
    print("openvino     ", f"{'OK' if openvino_ok else 'INCOMPATIBLE'} - {openvino_version}")
    ok &= openvino_ok

    protobuf_version = _version("protobuf")
    protobuf_ok = protobuf_version == "4.25.9"
    print("protobuf     ", f"{'OK' if protobuf_ok else 'INCOMPATIBLE'} - {protobuf_version}")
    ok &= protobuf_ok

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
        from apps.api.app.services.landmark_service import HolisticLandmarkService, mp_holistic
        holistic_api_ok = bool(mp_holistic is not None and hasattr(mp_holistic, "Holistic"))
        perception = HolisticLandmarkService()
        holistic_runtime_ok = perception.available
        print("holistic API ", "OK - Solutions Holistic" if holistic_api_ok else "MISSING/INCOMPATIBLE")
        print("vision runtime", "OK" if holistic_runtime_ok else f"ERROR - {perception.reason}")
        ok &= holistic_api_ok and holistic_runtime_ok
        perception.close()
    except Exception as exc:
        print("holistic API  ERROR", exc)
        ok = False

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
