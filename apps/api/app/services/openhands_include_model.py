from __future__ import annotations

import json
from pathlib import Path
import re

import numpy as np

from .temporal_model import ModelPrediction


def canonical_include_label(raw: str) -> str:
    value = re.sub(r"^\s*\d+\.\s*", "", raw).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return {"thankyou": "thank_you"}.get(value, value)


class OpenHandsIncludeModel:
    """Official AI4Bharat OpenHands SL-GCN trained on 263-class INCLUDE."""

    backend = "ai4bharat_include_slgcn_pytorch"
    source = "AI4Bharat/OpenHands INCLUDE SL-GCN"
    is_bootstrap = True
    input_schema = "openhands"
    sequence_length = 48
    schema_version = "openhands-mediapipe-holistic-minimal-27-v1"
    accept_threshold = 0.62
    margin_threshold = 0.10
    motion_threshold = 0.0008
    tracking_threshold = 0.35

    _EDGES = [
        [2, 0], [1, 0], [0, 3], [0, 4], [3, 5], [4, 6], [5, 7],
        [6, 17], [7, 8], [7, 9], [9, 10], [7, 11], [11, 12],
        [7, 13], [13, 14], [7, 15], [15, 16], [17, 18], [17, 19],
        [19, 20], [17, 21], [21, 22], [17, 23], [23, 24], [17, 25],
        [25, 26],
    ]

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.state_path = self.model_dir / "state_dict.pt"
        self.manifest_path = self.model_dir / "manifest.json"
        self.loaded = False
        self.load_error: str | None = None
        self.version: str | None = None
        self.labels: list[str] = []
        self._network = None
        self._torch = None
        self.reload()

    def reload(self) -> bool:
        self.loaded = False
        self._network = None
        self._torch = None

        if not self.state_path.exists() or not self.manifest_path.exists():
            self.load_error = "Official OpenHands INCLUDE model pack is not installed."
            return False

        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            labels = [str(x) for x in manifest["labels"]]
            if len(labels) != 263 or len(set(labels)) != 263:
                raise ValueError(f"expected 263 unique INCLUDE labels, found {len(labels)}")

            import torch
            import torch.nn as nn
            from .vendor.openhands_decoupled_gcn import DecoupledGCN

            edges = self._EDGES

            class _FC(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.classifier = nn.Linear(256, len(labels))

                def forward(self, x):
                    return self.classifier(x)

            class _Network(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.encoder = DecoupledGCN(
                        in_channels=2,
                        graph_args={"num_nodes": 27, "inward_edges": edges},
                    )
                    self.decoder = _FC()

                def forward(self, x):
                    return self.decoder(self.encoder(x))

            network = _Network()
            try:
                state = torch.load(self.state_path, map_location="cpu", weights_only=True)
            except TypeError:
                state = torch.load(self.state_path, map_location="cpu")
            network.load_state_dict(state, strict=True)
            network.eval()

            with torch.inference_mode():
                probe = torch.zeros((1, 2, 32, 27), dtype=torch.float32)
                logits = network(probe)
            if tuple(logits.shape) != (1, 263):
                raise ValueError(f"unexpected OpenHands output shape {tuple(logits.shape)}")

            self._torch = torch
            self._network = network
            self.labels = labels
            self.version = str(manifest.get("model_version", "openhands-include-slgcn-v1"))
            self.loaded = True
            self.load_error = None
            return True
        except Exception as exc:
            self.load_error = f"OpenHands INCLUDE model load failed: {exc}"
            return False

    @staticmethod
    def _normalize_clip(sequence: np.ndarray) -> np.ndarray:
        if sequence.ndim != 2 or sequence.shape[1] != 54:
            raise ValueError(f"expected [time,54] OpenHands pose sequence, got {sequence.shape}")
        points = sequence.astype(np.float32, copy=False).reshape(len(sequence), 27, 2).copy()
        left_shoulder = points[:, 3]
        right_shoulder = points[:, 4]
        center = np.mean((left_shoulder + right_shoulder) / 2.0, axis=0)
        mean_dist = float(np.mean(np.linalg.norm(left_shoulder - right_shoulder, axis=1)))
        if np.isfinite(mean_dist) and mean_dist > 1e-6:
            points = (points - center) / mean_dist
        return points

    def predict(self, sequence: np.ndarray) -> ModelPrediction:
        if not self.loaded or self._network is None or self._torch is None:
            raise RuntimeError(self.load_error or "OpenHands INCLUDE model is not loaded")

        points = self._normalize_clip(sequence)
        x = self._torch.from_numpy(points).permute(2, 0, 1).unsqueeze(0).contiguous()
        with self._torch.inference_mode():
            logits = self._network(x)
            probs = self._torch.softmax(logits, dim=-1)[0].cpu().numpy().astype(np.float32)

        total = float(probs.sum())
        if probs.shape != (263,) or not np.isfinite(total) or total <= 0:
            raise ValueError("OpenHands INCLUDE model returned invalid probabilities")
        return ModelPrediction(labels=self.labels, probabilities=probs / total)
