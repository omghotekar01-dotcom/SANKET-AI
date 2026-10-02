# SANKET AI

**Peaky Coders · Hacktopia 2026**  
Real-Time Multimodal Indian Sign Language Communication Bridge

SANKET AI is designed around **hands + facial/non-manual cues + upper-body pose + motion across time + context + explicit uncertainty**. It does not pretend that an isolated hand-pose classifier is continuous ISL translation.

The complete research/specification system is preserved under `prompts/`. Start with `AGENTS.md` before changing architecture or claims.

## Fastest Windows start

Install these once:
- 64-bit Python 3.11 or 3.12
- Node.js 20+
- Git

Then double-click:

```text
START_SANKET.bat
```

That is now the normal launcher.

On the first run it automatically:
1. detects an incompatible/missing runtime,
2. rebuilds `.venv`,
3. installs the pinned compatible vision stack,
4. installs frontend dependencies,
5. builds the frontend,
6. runs backend/ML tests,
7. verifies MediaPipe Holistic,
8. starts the FastAPI backend,
9. waits for the API health check,
10. starts Vite and opens the browser.

On later runs it verifies the existing environment and starts immediately. The older `run_dev.bat` now forwards to the same one-click launcher.

### Vision compatibility

This project currently uses MediaPipe's legacy Holistic API because the feature schema/model pipeline was built around that landmark geometry. The compatible runtime is intentionally pinned to:

- MediaPipe `0.10.21`
- NumPy `1.26.4`
- OpenCV contrib `4.11.0.86`

Do not upgrade those individually without migrating the perception layer and retraining/evaluating the sign model.

## What is implemented

- Professional React + TypeScript live-video interface.
- Live webcam preview with hands/body/face tracking status.
- Local FastAPI recognition WebSocket with automatic reconnect.
- Pinned MediaPipe Holistic perception runtime.
- Versioned multimodal feature schema and temporal buffering.
- Real finite-vocabulary temporal template baseline, not fake predictions.
- Consent-based landmark dataset collection; raw video off by default.
- One-click local model training from the Training Studio.
- Signer-aware train/validation/test splitting and explicit limitations.
- Calibration + selective acceptance + ambiguity/motion/tracking gates.
- `ACCEPTED`, `NEED_REPEAT`, `NO_SIGN`, `TRACKING_LOST` behavior.
- Context domains that only rerank recognizer evidence.
- ISL → text → browser TTS.
- Text → verified ISL phrase clip registry with honest fallback.
- Local verified-clip upload workflow.
- Emergency communication, high contrast, larger text, reduced motion, ARIA live transcript and haptics capability detection.
- WebRTC two-peer call/signaling prototype for same-network/two-tab demos.
- Deterministic **labelled Demo Replay** fallback.
- Diagnostics and real evaluation endpoints.
- GitHub CI for backend/ML tests, vision compatibility and production web build.

## What still requires your real project data

Two pieces cannot be truthfully generated as placeholders:

1. **A trained ISL vocabulary model** — collect consented takes for your final signs, then click **Train model now** in Training Studio.
2. **Verified reverse-ISL videos** — record/validate your own clips or use assets whose terms permit your use/redistribution.

Until a trained artifact exists, SANKET can still test camera + MediaPipe tracking, but it will correctly show that the sign model needs training.

## First live test

Double-click `START_SANKET.bat`, then open **Live interpreter**.

Expected readiness:

```text
Local API      Connected
Vision         MediaPipe ready
Sign model     Needs training
Tracking       —
```

Press **Camera**. As you move, the Left / Right / Body / Face indicators should become active.

## Train your first vocabulary

Open **Training studio** and start with three signs such as:

```text
help
doctor
water
```

Record multiple takes for each sign. For a meaningful signer-disjoint evaluation, repeat the same vocabulary with 3+ different signers. Then press:

```text
Train model now
```

The backend trains, evaluates, saves and reloads the local model automatically.

## Important limitations

- The recognizer is **finite-vocabulary temporal recognition**, not unrestricted open-vocabulary continuous ISL sentence translation.
- Context cannot invent meaning unsupported by visual evidence.
- Browser speech recognition is optional; typed text remains the fallback.
- Internet-wide WebRTC generally needs a tested TURN service; same-network/two-tab demo is the supported current path.
- Emergency mode communicates urgent needs but does not dispatch emergency services.

Read `docs/ARCHITECTURE.md`, `docs/ML_PIPELINE.md`, `docs/DATA_AND_LICENSES.md`, `docs/DEMO_GUIDE.md`, and `docs/PRIVACY_AND_ACCESSIBILITY.md` before the final demo.
