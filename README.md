# SANKET AI

**Peaky Coders · Hacktopia 2026**  
Real-Time Multimodal Indian Sign Language Communication Bridge

SANKET AI is designed around **hands + facial/non-manual cues + upper-body pose + motion across time + context + explicit uncertainty**. It does not pretend that an isolated hand-pose classifier is continuous ISL translation.

The complete research/specification system is preserved under `prompts/`. Start with `AGENTS.md` before changing architecture or claims.

## What is implemented

- React + TypeScript assistive-product UI.
- Live webcam preview with framing/signal-health overlay.
- Local FastAPI recognition WebSocket with bounded frame flow.
- Server-side MediaPipe Holistic adapter (optional dependency; Python 3.11/3.12 recommended).
- Versioned multimodal feature schema and temporal buffering.
- Real finite-vocabulary temporal template baseline, not fake predictions.
- Consent-based landmark dataset collection; raw video off by default.
- Signer-aware train/validation/test splitting and honest limitations.
- Calibration temperature + selective acceptance threshold + ambiguity/motion/tracking gates.
- `ACCEPTED`, `NEED_REPEAT`, `NO_SIGN`, `TRACKING_LOST` behavior.
- Context domains that only rerank recognizer evidence.
- ISL → text → browser TTS.
- Text → verified ISL phrase clip registry with honest fallback.
- Local verified-clip upload lab for team/community recordings.
- Emergency communication, high contrast, larger text, reduced motion, ARIA live transcript and haptics capability detection.
- WebRTC two-peer call/signaling prototype for same-network/two-tab demos.
- Deterministic **labelled Demo Replay** fallback.
- Diagnostics and model/evaluation endpoints.
- Backend/ML automated tests.

## What cannot be truthfully bundled without your data

Two pieces require real project evidence rather than generated placeholders:

1. **A trained ISL model** — collect consented takes for the exact demo vocabulary/signers, then train/evaluate it.
2. **Verified reverse-ISL videos** — record/validate your own clips or use material whose terms explicitly permit your use/redistribution.

Until these exist, SANKET AI visibly reports `model_loaded=false` and reverse output uses an honest fallback. Demo Replay is clearly labelled.

## Windows setup (recommended)

Install Python **3.11**, Node.js 20+ and Git. Then:

```bat
setup_windows.bat
run_dev.bat
```

Manual setup:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r apps\api\requirements-dev.txt
pip install -r apps\api\requirements-vision.txt
cd apps\web
npm install
cd ..\..
python -m pytest apps\api\tests -q
run_dev.bat
```

Open `http://127.0.0.1:5173`. API docs are at `http://127.0.0.1:8000/docs`.

## Collect and train

Use **Collect data** in the app. For useful evaluation, collect multiple takes per class from **3+ signers** if possible.

```bat
.venv\Scripts\activate
python -m ml.training.train_template
python -m ml.evaluation.report
```

Then restart the backend or `POST /api/model/reload`.

## Test

```bash
python -m pytest apps/api/tests -q
cd apps/web
npm run typecheck
npm run build
```

For live camera testing also verify: camera permission denied/retry, low light, one hand out of frame, unsupported signs, backend restart, and Wi-Fi disconnected (except WebRTC between remote networks).

## Important limitations

- The shipped recognizer architecture is **finite-vocabulary temporal recognition**, not unrestricted open-vocabulary continuous ISL sentence translation.
- Context cannot invent a sentence unsupported by visual evidence.
- Browser speech recognition is optional; typed input is the fallback.
- Internet-wide WebRTC generally needs a tested TURN service; same-network/two-tab demo does not.
- Emergency mode does not dispatch services.

Read `docs/ARCHITECTURE.md`, `docs/ML_PIPELINE.md`, `docs/DATA_AND_LICENSES.md`, `docs/DEMO_GUIDE.md`, and `docs/PRIVACY_AND_ACCESSIBILITY.md` before the final demo.
