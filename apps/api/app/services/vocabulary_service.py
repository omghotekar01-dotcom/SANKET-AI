from __future__ import annotations

import re
from typing import Iterable

CORE_VOCABULARY = [
    {"id": "hello", "display": "Hello", "category": "greeting"},
    {"id": "thank_you", "display": "Thank you", "category": "greeting"},
    {"id": "yes", "display": "Yes", "category": "basic"},
    {"id": "no", "display": "No", "category": "basic"},
    {"id": "help", "display": "Help", "category": "emergency"},
    {"id": "doctor", "display": "Doctor", "category": "medical"},
    {"id": "hospital", "display": "Hospital", "category": "medical"},
    {"id": "water", "display": "Water", "category": "basic"},
    {"id": "pain", "display": "Pain", "category": "medical"},
    {"id": "medicine", "display": "Medicine", "category": "medical"},
    {"id": "police", "display": "Police", "category": "emergency"},
    {"id": "fire", "display": "Fire", "category": "emergency"},
    {"id": "danger", "display": "Danger", "category": "emergency"},
    {"id": "accident", "display": "Accident", "category": "emergency"},
    {"id": "stop", "display": "Stop", "category": "emergency"},
    {"id": "where", "display": "Where", "category": "basic"},
    {"id": "name", "display": "Name", "category": "basic"},
    {"id": "student", "display": "Student", "category": "education"},
    {"id": "teacher", "display": "Teacher", "category": "education"},
    {"id": "repeat", "display": "Repeat", "category": "communication"},
    {"id": "understand", "display": "Understand", "category": "communication"},
]


def normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def core_coverage(active_labels: Iterable[str]) -> dict:
    active = {normalize_label(label) for label in active_labels}
    supported = [item["id"] for item in CORE_VOCABULARY if item["id"] in active]
    missing = [item["id"] for item in CORE_VOCABULARY if item["id"] not in active]
    total = len(CORE_VOCABULARY)
    return {
        "supported": supported,
        "missing": missing,
        "supported_count": len(supported),
        "total": total,
        "fraction": (len(supported) / total) if total else 0.0,
    }


# Default live mode deliberately exposes only the bootstrap classes that
# overlap SANKET's required project vocabulary. The broader external model is
# still available as an explicitly experimental mode.
SAFE_BOOTSTRAP_CORE_IDS = (
    "hello",
    "thank_you",
    "doctor",
    "hospital",
    "medicine",
    "police",
    "student",
    "teacher",
)


def safe_bootstrap_labels(active_labels: Iterable[str]) -> list[str]:
    allowed = set(SAFE_BOOTSTRAP_CORE_IDS)
    return [label for label in active_labels if normalize_label(label) in allowed]
