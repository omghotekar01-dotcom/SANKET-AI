# SANKET AI — Implementation Status

This file is additive to the existing prompt/specification system and should be applied on top of `docs/deep-spec-expansion-v1` rather than replacing prior prompt files.

## Working software

- FastAPI health/config/domain/sign/feedback/collector/reverse-ISL/model endpoints.
- Recognition and WebRTC signaling WebSockets.
- React/TypeScript/Vite product UI.
- Camera capture with display-only mirroring and bounded frame transport.
- MediaPipe Holistic server adapter when the optional compatible dependency is installed.
- Versioned 226-dimensional raw landmark feature schema plus temporal velocity features.
- Temporal template baseline training/loading/evaluation.
- Signer-disjoint split when sufficient signers exist; explicit limitations otherwise.
- Confidence/margin/motion/tracking/stability gating.
- Context reranking without evidence invention.
- Accepted-only transcript + browser TTS.
- Reverse phrase registry and verified local clip upload.
- Emergency/accessibility/haptic behavior.
- Demo Replay with visible labelling.
- WebRTC two-peer calling with SANKET caption metadata when recognition is available.
- Diagnostics showing real model/evaluation state.
- Automated backend/ML tests and startup scripts.

## Requires project data before it can be called working live ISL recognition

- Consent-based recordings for the exact final vocabulary from multiple signers.
- Trained/evaluated model artifact produced from those recordings.
- Verified ISL phrase clips for the reverse-communication demo.

These are evidence/data tasks, not missing fake placeholders. The software reports them as unavailable until real artifacts exist.

## Experimental / optional

- WebRTC beyond same-network/two-tab use; production internet calling generally needs TURN.
- Browser speech recognition; typed text remains the fallback.
- Broader continuous/open-vocabulary ISL translation remains research-scale and is not claimed.
