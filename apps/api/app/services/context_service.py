from __future__ import annotations

DOMAINS = {
    "general": set(),
    "classroom": {"hello", "thank you", "yes", "no", "student", "teacher", "repeat", "understand", "water", "school"},
    "hospital": {"help", "doctor", "hospital", "water", "pain", "medicine", "patient", "yes", "no", "repeat", "sick", "healthy"},
    "emergency": {"help", "doctor", "police", "fire", "accident", "danger", "stop", "water", "pain", "hospital", "medicine"},
    "public_service": {"help", "police", "where", "name", "yes", "no", "repeat", "school", "hospital"},
}


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
