from __future__ import annotations

import json
from pathlib import Path

_PACK_PATH = Path(__file__).resolve().parents[1] / "domain_packs.json"


def _load_domains() -> dict[str, dict]:
    payload = json.loads(_PACK_PATH.read_text(encoding="utf-8"))
    if "general" not in payload:
        raise RuntimeError("domain_packs.json must define general")
    normalized: dict[str, dict] = {}
    for key, value in payload.items():
        if not isinstance(value, dict):
            raise RuntimeError(f"domain {key} must be an object")
        boost = value.get("boost", [])
        if not isinstance(boost, list) or not all(isinstance(x, str) for x in boost):
            raise RuntimeError(f"domain {key}.boost must be a list of strings")
        normalized[key] = {
            "label": str(value.get("label") or key.replace("_", " ").title()),
            "boost": {item.strip().lower().replace("_", " ") for item in boost},
        }
    return normalized


DOMAIN_PACKS = _load_domains()
DOMAINS = {key: value["boost"] for key, value in DOMAIN_PACKS.items()}


def domain_descriptors() -> list[dict[str, str]]:
    return [{"id": key, "label": value["label"]} for key, value in DOMAIN_PACKS.items()]


def rerank(labels: list[str], probabilities, domain: str):
    import numpy as np

    probs = np.asarray(probabilities, dtype=np.float32).copy()
    allowed = DOMAINS.get(domain, set())
    if allowed:
        for i, label in enumerate(labels):
            normalized = label.replace("_", " ").strip().lower()
            if normalized in allowed:
                probs[i] *= 1.08
        total = probs.sum()
        if total > 0:
            probs /= total
    return probs
