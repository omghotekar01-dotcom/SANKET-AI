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
- Local experimental environmental-sound alert classifier with a deterministic in-app self-test; microphone audio is not recorded or uploaded.
- Human correction controls that store accepted/fixed labels as feedback metadata without automatic retraining.
- JSON domain packs for General/Classroom/Hospital/Emergency/Public Service context reranking.
- WebRTC two-peer call/signaling prototype for same-network/two-tab demos.
- Deterministic **labelled Demo Replay** fallback.
- Diagnostics and real evaluation endpoints.
- GitHub CI for backend/ML tests, vision compatibility and production web build.

## Recognition coverage and what still needs real project data

The one-click setup installs a verified external MIT-licensed **50-word temporal bootstrap recognizer**. SANKET does not claim that model's upstream accuracy as our own.

The exact 21-sign project contract is:

`HELLO, THANK YOU, YES, NO, HELP, DOCTOR, HOSPITAL, WATER, PAIN, MEDICINE, POLICE, FIRE, DANGER, ACCIDENT, STOP, WHERE, NAME, STUDENT, TEACHER, REPEAT, UNDERSTAND`.

The bootstrap recognizer directly covers 8 of those 21: **HELLO, THANK YOU, DOCTOR, HOSPITAL, MEDICINE, POLICE, STUDENT, TEACHER**. The UI/API now calculate this intersection at runtime and mark every unsupported contract sign visibly as missing.

Two things still require defensible project data rather than fabricated placeholders:

1. **The remaining core signs** — collect consented real samples in Training Studio or integrate a separately licensed/evaluated recognizer. Experimental public-data extension models are not activated unless their held-out quality gate passes.
2. **Verified reverse-ISL videos** — record/validate your own clips or use assets whose terms permit your use/redistribution.

A locally trained SANKET model is preferred only after its held-out evaluation passes the quality gate.

## First live test

Double-click `START_SANKET.bat`, then open **Live interpreter**.

Expected readiness:

```text
Local API      Connected
Vision         MediaPipe ready
Sign model     Bootstrap · 50
Tracking       —
```

Press **Camera**. As you move, the Left / Right / Body / Face indicators should become active. Open the **Project contract** card to see exactly which of the 21 required signs are live on the current machine.

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
