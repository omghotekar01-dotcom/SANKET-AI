from __future__ import annotations

DOMAINS = {
    "general": set(),
    "classroom": {"hello", "thank_you", "yes", "no", "student", "teacher", "repeat", "understand", "water"},
    "hospital": {"help", "doctor", "hospital", "water", "pain", "medicine", "yes", "no", "repeat"},
    "emergency": {"help", "doctor", "police", "fire", "accident", "danger", "stop", "water", "pain"},
    "public_service": {"help", "police", "where", "name", "yes", "no", "repeat"},
}


def rerank(labels: list[str], probabilities, domain: str):
    import numpy as np
    probs = np.asarray(probabilities, dtype=np.float32).copy()
    allowed = DOMAINS.get(domain, set())
    if allowed:
        for i, label in enumerate(labels):
            if label in allowed:
                probs[i] *= 1.08
        probs /= probs.sum()
    return probs
