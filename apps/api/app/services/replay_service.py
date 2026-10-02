SCENARIOS = [
    {
        "id": "judge-core",
        "name": "Judge core communication loop",
        "label": "DEMO REPLAY",
        "events": [
            {"delay_ms": 600, "state": "TRACKING_LOST", "reason": "Signer is outside the framing guide"},
            {"delay_ms": 900, "state": "NEED_REPEAT", "reason": "Sign unclear — please repeat", "confidence": 0.51},
            {"delay_ms": 900, "state": "ACCEPTED", "label": "help", "display_text": "Help", "confidence": 0.91},
            {"delay_ms": 800, "state": "ACCEPTED", "label": "doctor", "display_text": "Doctor", "confidence": 0.89},
        ],
    }
]
