from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ml" / "artifacts" / "bootstrap-50"
UPSTREAM_COMMIT = "99ed8ffc47ccf3106d498e704f5c1b7e547758d7"
BASE = (
    "https://raw.githubusercontent.com/"
    "Kartik200428/Real-time-Indic-Sign-language-to-speech-translator/"
    f"{UPSTREAM_COMMIT}/"
)

ASSETS = {
    "isl_model_solo.keras": {
        "path": "models/isl_model_solo.keras",
        "size": 9_783_895,
        "git_blob_sha1": "c903b38b34dafb8ceeb36ebb9c656d8629981e66",
    },
}


def git_blob_sha(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("utf-8"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid(path: Path, spec: dict) -> bool:
    if not path.exists() or path.stat().st_size != spec["size"]:
        return False
    return git_blob_sha(path) == spec["git_blob_sha1"]


def download(name: str, spec: dict) -> None:
    target = OUT / name
    if valid(target, spec):
        print(f"[bootstrap] {name}: already verified")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    if tmp.exists():
        tmp.unlink()

    url = BASE + spec["path"]
    print(f"[bootstrap] downloading {name} ({spec['size'] / 1024 / 1024:.1f} MB)")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "SANKET-AI-Hacktopia/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response, tmp.open("wb") as out:
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                total += len(chunk)
                print(f"  {min(100, total * 100 // spec['size']):3d}%", end="\r", flush=True)
        print(" " * 12, end="\r")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"Could not download {name}: {exc}") from exc

    if not valid(tmp, spec):
        actual_size = tmp.stat().st_size if tmp.exists() else 0
        actual_sha = git_blob_sha(tmp) if tmp.exists() else "missing"
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(
            f"Integrity check failed for {name}: size={actual_size}, git_blob_sha1={actual_sha}"
        )

    os.replace(tmp, target)
    print(f"[bootstrap] {name}: verified")


def write_manifest() -> None:
    labels = json.loads((ROOT / "ml" / "bootstrap" / "labels.json").read_text(encoding="utf-8"))
    manifest = {
        "model_version": "bootstrap-bilstm-50-v1",
        "source": "Kartik200428/Real-time-Indic-Sign-language-to-speech-translator",
        "source_commit": UPSTREAM_COMMIT,
        "license": "MIT",
        "license_file": "third_party/KARTIK_ISL_MODEL_LICENSE.txt",
        "labels": labels,
        "sequence_length": 30,
        "feature_dim": 378,
        "feature_schema": "bootstrap-holistic-378-v1",
        "claim_note": (
            "External bootstrap weights. Not trained or evaluated by SANKET AI. "
            "A locally trained SANKET artifact takes priority only after its held-out "
            "evaluation clears the SANKET quality gate."
        ),
        "assets": ASSETS,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> int:
    try:
        for name, spec in ASSETS.items():
            download(name, spec)
        write_manifest()
    except Exception as exc:
        print(f"[bootstrap] ERROR: {exc}", file=sys.stderr)
        return 1
    print("[bootstrap] 50-word bootstrap assets are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
