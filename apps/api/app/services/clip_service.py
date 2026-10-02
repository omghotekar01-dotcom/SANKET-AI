from __future__ import annotations

import json
import re
from pathlib import Path
from ..schemas import ISLClipItem, TextToISLResponse


def normalize_text(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return " ".join(text.split())


class ClipService:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.entries: list[dict] = []
        self.reload()

    def reload(self) -> None:
        if self.registry_path.exists():
            self.entries = json.loads(self.registry_path.read_text(encoding="utf-8"))
        else:
            self.entries = []

    def translate(self, text: str) -> TextToISLResponse:
        normalized = normalize_text(text)
        exact = next((e for e in self.entries if normalize_text(e["phrase"]) == normalized and e.get("verified", False)), None)
        if exact:
            return TextToISLResponse(normalized_text=normalized, mode="verified_phrase", items=[ISLClipItem(**{k: exact.get(k) for k in ["phrase","mode","file","source","license_note"]})])
        words = normalized.split()
        items: list[ISLClipItem] = []
        for word in words:
            entry = next((e for e in self.entries if normalize_text(e["phrase"]) == word and e.get("verified", False)), None)
            if entry:
                items.append(ISLClipItem(**{k: entry.get(k) for k in ["phrase","mode","file","source","license_note"]}))
            else:
                items.append(ISLClipItem(phrase=word, mode="fingerspelling_placeholder"))
        if items and all(i.mode != "fingerspelling_placeholder" for i in items):
            return TextToISLResponse(normalized_text=normalized, mode="verified_sequence", items=items, message="Sequence of verified sign clips; not claimed as fluent ISL grammar.")
        return TextToISLResponse(normalized_text=normalized, mode="fallback", items=items, message="No verified phrase clip is available. Unknown words require a verified fingerspelling renderer before production use.")
