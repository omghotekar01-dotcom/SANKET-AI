from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ml" / "artifacts" / "openhands-include"
OUT.mkdir(parents=True, exist_ok=True)

MODEL_URL = "https://github.com/AI4Bharat/OpenHands/releases/download/checkpoints_v1/include_slgcn.zip"
META_URL = "https://github.com/AI4Bharat/OpenHands/releases/download/checkpoints_v1/include_metadata.zip"
MODEL_ZIP_SIZE = 40_608_718
META_ZIP_SIZE = 47_041
CKPT_MEMBER = "include/sl_gcn/epoch=112-step=12203.ckpt"
CSV_MEMBER = "Train_Test_Split/train_include.csv"


def _download(url: str, target: Path, expected_size: int) -> None:
    if target.exists() and target.stat().st_size == expected_size:
        print(f"[OpenHands] {target.name}: already downloaded")
        return
    tmp = target.with_suffix(target.suffix + ".part")
    if tmp.exists():
        tmp.unlink()
    req = urllib.request.Request(url, headers={"User-Agent": "SANKET-AI-Hacktopia/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=90) as response, tmp.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"download failed for {url}: {exc}") from exc
    if tmp.stat().st_size != expected_size:
        size = tmp.stat().st_size
        tmp.unlink()
        raise RuntimeError(f"unexpected download size for {url}: {size} != {expected_size}")
    os.replace(tmp, target)


def _canonical(raw: str) -> str:
    value = re.sub(r"^\s*\d+\.\s*", "", raw).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return {"thankyou": "thank_you"}.get(value, value)


def main() -> int:
    model_zip = OUT / "include_slgcn.zip"
    meta_zip = OUT / "include_metadata.zip"
    ckpt_path = OUT / "upstream.ckpt"
    try:
        _download(MODEL_URL, model_zip, MODEL_ZIP_SIZE)
        _download(META_URL, meta_zip, META_ZIP_SIZE)

        with zipfile.ZipFile(meta_zip) as zf:
            rows = list(csv.DictReader(io.StringIO(zf.read(CSV_MEMBER).decode("utf-8-sig"))))
        raw_labels = sorted({row["Word"] for row in rows})
        labels = [_canonical(label) for label in raw_labels]
        if len(labels) != 263 or len(set(labels)) != 263:
            raise RuntimeError(f"unexpected INCLUDE label map: {len(labels)} / {len(set(labels))}")

        with zipfile.ZipFile(model_zip) as zf:
            ckpt_path.write_bytes(zf.read(CKPT_MEMBER))

        import pytorch_lightning  # noqa: F401
        import torch

        try:
            checkpoint = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        except TypeError:
            checkpoint = torch.load(ckpt_path, map_location="cpu")
        upstream_state = checkpoint.get("state_dict")
        if not isinstance(upstream_state, dict):
            raise RuntimeError("official checkpoint has no state_dict")
        state = {
            key.removeprefix("model."): value
            for key, value in upstream_state.items()
            if key.startswith("model.")
        }
        classifier = state.get("decoder.classifier.weight")
        if classifier is None or tuple(classifier.shape) != (263, 256):
            raise RuntimeError("official INCLUDE classifier shape mismatch")
        torch.save(state, OUT / "state_dict.pt")

        manifest = {
            "model_version": "openhands-include-slgcn-v1",
            "source": "AI4Bharat/OpenHands",
            "source_release": "checkpoints_v1/include_slgcn.zip",
            "architecture": "SL-GCN / decoupled GCN",
            "dataset": "INCLUDE",
            "dataset_license": "CC-BY-4.0",
            "code_license": "Apache-2.0",
            "license_file": "third_party/AI4BHARAT_OPENHANDS_LICENSE.txt",
            "labels": labels,
            "raw_labels": raw_labels,
            "feature_schema": "openhands-mediapipe-holistic-minimal-27-v1",
            "input_channels": 2,
            "nodes": 27,
            "upstream_reported_include_test_accuracy": 0.935,
            "claim_scope": (
                "93.5% is the OpenHands paper result on the INCLUDE benchmark. "
                "It is not a measured SANKET webcam accuracy claim."
            ),
        }
        (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        for path in (model_zip, meta_zip, ckpt_path):
            if path.exists():
                path.unlink()

        print(f"[OpenHands] ready: {len(labels)} classes")
        return 0
    except Exception as exc:
        print(f"[OpenHands] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
