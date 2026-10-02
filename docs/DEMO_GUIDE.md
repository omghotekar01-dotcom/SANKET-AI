# Hacktopia Demo Guide

## Before judging

1. Run backend tests: `python -m pytest apps/api/tests -q`.
2. Open Diagnostics; verify perception/model states.
3. If using live recognition, show the exact supported vocabulary and real evaluation report.
4. Test the chosen webcam and lighting.
5. Keep a labelled Demo Replay ready.
6. For reverse communication, preload only consented verified phrase clips used in the demo.

## 3–5 minute flow

1. Explain that SANKET AI uses hands + face/non-manual + body + temporal motion rather than a single hand pose.
2. Start live camera; show signal-health indicators.
3. Perform a supported sign; show accepted text and TTS.
4. Deliberately make the input unclear; demonstrate `NEED_REPEAT` rather than a guess.
5. Switch to Hospital/Emergency context and explain it reranks evidence but cannot invent meaning.
6. Type a verified reverse phrase and play its consented ISL clip.
7. Show high contrast/emergency communication.
8. Show Diagnostics with actual model version/availability.
9. Only show WebRTC if the same-network/two-tab test is stable.

If live perception/model fails, use **Run labelled demo replay** and say explicitly that it is a deterministic fallback, not live AI output.
