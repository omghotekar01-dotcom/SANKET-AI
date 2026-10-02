from __future__ import annotations

import re

MARATHI_TO_CANONICAL = {
    "नमस्कार": "hello",
    "धन्यवाद": "thank you",
    "हो": "yes",
    "नाही": "no",
    "मदत": "help",
    "डॉक्टर": "doctor",
    "रुग्णालय": "hospital",
    "हॉस्पिटल": "hospital",
    "पाणी": "water",
    "वेदना": "pain",
    "दुखणे": "pain",
    "औषध": "medicine",
    "पोलीस": "police",
    "पोलिस": "police",
    "आग": "fire",
    "धोका": "danger",
    "अपघात": "accident",
    "थांबा": "stop",
    "कुठे": "where",
    "नाव": "name",
    "विद्यार्थी": "student",
    "शिक्षक": "teacher",
    "पुन्हा": "repeat",
    "समजले": "understand",
    "भाऊ": "brother",
    "कर्णबधिर": "deaf",
    "स्वप्न": "dream",
    "व्यायाम": "exercise",
    "कुटुंब": "family",
    "वडील": "father",
    "मित्र": "friend",
    "शुभ सकाळ": "good morning",
    "घर": "house",
    "तुम्ही कसे आहात": "how are you",
    "मी": "i",
    "पुरुष": "man",
    "सकाळ": "morning",
    "आई": "mother",
    "रात्र": "night",
    "रुग्ण": "patient",
    "शाळा": "school",
    "संकेत": "sign",
    "बहीण": "sister",
    "खेळ": "sport",
    "वेळ": "time",
    "आज": "today",
    "उद्या": "tomorrow",
    "स्त्री": "woman",
    "काल": "yesterday",
    "जिवंत": "alive",
    "वाईट": "bad",
    "चांगले": "good",
    "आनंदी": "happy",
    "तो": "he",
    "निरोगी": "healthy",
    "ते": "it",
    "वृद्ध": "old",
    "दुःखी": "sad",
    "ती": "she",
    "आजारी": "sick",
    "मजबूत": "strong",
    "आम्ही": "we",
    "कमकुवत": "weak",
    "तुम्ही": "you",
    "तरुण": "young",
}

PHRASE_ALIASES = {
    "पुन्हा करा": "repeat",
    **MARATHI_TO_CANONICAL,
}


def normalize_unicode_text(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_\u0900-\u097F\s]", " ", text.lower())
    return " ".join(text.split())


def detect_language(text: str) -> str:
    return "mr" if re.search(r"[\u0900-\u097F]", text) else "en"


def canonicalize_text(text: str, language: str = "auto") -> tuple[str, str, str]:
    normalized = normalize_unicode_text(text)
    detected = detect_language(text) if language == "auto" else language
    if detected != "mr":
        return normalized, detected, normalized

    if normalized in PHRASE_ALIASES:
        canonical = PHRASE_ALIASES[normalized]
        return normalized, "mr", canonical

    tokens = normalized.split()
    canonical_tokens = [MARATHI_TO_CANONICAL.get(token, token) for token in tokens]
    return normalized, "mr", " ".join(canonical_tokens)


def supported_languages() -> list[dict[str, str]]:
    return [
        {"id": "en", "label": "English", "locale": "en-IN"},
        {"id": "mr", "label": "मराठी", "locale": "mr-IN"},
        {"id": "both", "label": "English + मराठी", "locale": "bilingual"},
    ]
