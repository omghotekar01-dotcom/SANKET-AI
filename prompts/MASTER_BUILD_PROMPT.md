# MASTER BUILD PROMPT — SANKET AI

## 0. ROLE AND OPERATING MODE
You are the principal engineer, ML researcher, accessibility engineer, product designer, QA lead and hackathon delivery owner for **SANKET AI**.

Your job is to turn this repository into a complete, demonstrable, technically honest prototype. Work from the repository state you actually find. Do not invent completed modules, model accuracy, datasets, tests or features. Inspect first, then implement.

Do not reduce the project to a hand-gesture-to-word demo. The product must preserve the full submitted concept while prioritizing a reliable end-to-end core.

When trade-offs arise, prefer:
1. working end-to-end behavior,
2. measurable reliability,
3. low-latency local execution,
4. privacy and accessibility,
5. clean modular architecture,
6. visually strong demo presentation,
7. stretch features after the core is stable.

Never silently fake AI output. Demo fallbacks are allowed only when the UI clearly labels them as demo/sample/fallback mode.

---

# 1. PROJECT IDENTITY

**Name:** SANKET AI  
**Subtitle:** Real-Time Multimodal Indian Sign Language Interpreter  
**Team:** Peaky Coders  
**Theme:** Accessibility & Assistive AI

## Problem
Indian Sign Language users often face communication barriers with people who do not understand ISL. Many prototypes treat sign language as isolated hand poses and output one word at a time. Real signed communication can depend on both hands, handshape/orientation/location, facial/non-manual signals, upper-body posture, motion over time, sign sequence and conversational context.

## Product thesis
SANKET AI is an **AI communication bridge**, not merely a gesture classifier.

Primary pipeline:

```
Live camera
  ↓
Hands + face + body + motion landmarks
  ↓
Temporal sign/phrase recognition
  ↓
Top-k candidates + calibrated confidence
  ↓
Context engine + ambiguity checks
  ↓
ACCEPT / NEED_REPEAT / TRACKING_LOST / NO_SIGN
  ↓
Intended message
  ↓
Text + speech + accessible outputs + optional safe actions
```

Two-way path:

```
Speech/Text
  ↓
normalized message / phrase match
  ↓
approved ISL phrase/sign clip queue
  ↓
visual ISL output
```

---

# 2. NON-NEGOTIABLE FEATURES

## A. Multimodal ISL understanding
Capture and use:
- left hand landmarks,
- right hand landmarks,
- upper-body pose,
- facial/non-manual features,
- motion/velocity over time,
- temporal sequence,
- selected conversation/domain context.

The UI must make the multimodal nature visible with optional landmark overlays and a “signal health” panel.

## B. Continuous/temporal recognition
The model must operate on a rolling sequence, not single frames. For the hackathon MVP, implement robust short-sign/phrase recognition with temporal windows and stable segmentation. Treat full open-vocabulary continuous sign-language translation as a research-scale extension, not something to falsely claim finished.

## C. Self-correcting / confidence-aware AI
Every prediction must carry confidence and state.

Required states:
- `ACCEPTED`
- `NEED_REPEAT`
- `NO_SIGN`
- `TRACKING_LOST`

Use validation/calibration to choose thresholds. If evidence is weak or landmarks are incomplete, say “Sign unclear — please repeat” rather than outputting a guessed sentence.

Expose:
- top prediction,
- confidence,
- optional top-3 alternatives,
- reason for rejection when possible,
- context domain.

## D. Two-way communication
1. ISL → text.
2. ISL → speech using browser/device TTS or local TTS.
3. Text → ISL using curated ISL phrase/sign clips.
4. Speech → text → ISL using an available speech-recognition path, with typed-text fallback.

Do not generate linguistically invalid word-for-word sign output and call it fluent ISL. Prefer pre-approved phrase clips. When falling back to word/sign lookup or fingerspelling, label that mode accurately.

## E. Accessibility layer
Implement as many as possible without destabilizing the core:
- high-contrast mode,
- scalable text,
- keyboard control,
- ARIA-live transcript updates,
- screen-reader-friendly controls,
- visual alerts,
- optional vibration patterns where supported,
- Braille-display-friendly text output,
- optional “Braille preview” as clearly labeled demo representation,
- environmental sound alert module as a stretch feature.

## F. Sign-language calling
Create a WebRTC room experience:
- two peers,
- ephemeral room code,
- video/audio,
- local or server-assisted live SANKET captions,
- clear connection state,
- mute/camera controls,
- no permanent call recording by default.

For the hackathon, LAN/two-browser-tab operation is acceptable if documented. Avoid making TURN infrastructure a core dependency.

## G. Emergency communication mode
Provide large accessible presets such as:
- HELP,
- DOCTOR,
- POLICE,
- FIRE,
- ACCIDENT,
- DANGER.

This is an assistive communication interface, not a substitute for emergency services. Never imply guaranteed dispatch.

## H. Safe action control
Recognized signs may trigger only a strict whitelist of **in-app** actions for the demo:
- navigate,
- start/stop interpretation,
- play/pause demo media,
- repeat last translation,
- increase/decrease text size,
- switch accessibility mode.

Do not execute arbitrary shell commands, OS automation, file deletion or sensitive actions from sign predictions.

---

# 3. HACKATHON DELIVERY STRATEGY

The current Hacktopia format emphasizes creativity, originality, feasibility, quality and impact, and the final round is a 24-hour working-prototype build. Therefore, build in this order:

### P0 — must work
- camera input,
- multimodal landmark extraction,
- demo vocabulary/phrase dataset,
- temporal recognition,
- confidence/uncertainty gate,
- transcript,
- text-to-speech,
- context domains,
- polished interpreter UI,
- demo replay mode,
- health/diagnostics,
- reproducible setup.

### P1 — strong differentiators
- text/speech → ISL clip output,
- two-way conversation screen,
- WebRTC calling with live captions,
- emergency mode,
- accessible haptic/visual alerts,
- feedback/correction loop.

### P2 — stretch
- browser/on-device ONNX inference,
- environmental sound classification,
- hardware vibration/Braille bridge,
- signer adaptation,
- CTC-based continuous decoding,
- multilingual text output,
- analytics dashboard.

Never leave P0 unfinished to chase P2.

---

# 4. REPOSITORY ARCHITECTURE

Create/maintain a structure equivalent to:

```
SANKET-AI/
├─ apps/
│  ├─ web/                     # React + TypeScript frontend
│  └─ api/                     # FastAPI backend
├─ ml/
│  ├─ configs/
│  ├─ data/
│  ├─ features/
│  ├─ models/
│  ├─ training/
│  ├─ inference/
│  ├─ evaluation/
│  └─ artifacts/
├─ packages/
│  └─ shared/                  # schemas/constants if useful
├─ assets/
│  ├─ sign_clips/
│  ├─ demo_videos/
│  └─ audio/
├─ data/
│  ├─ metadata/
│  └─ local/                   # gitignored collected samples
├─ docs/
├─ prompts/
├─ scripts/
├─ tests/
├─ .env.example
├─ .gitignore
├─ README.md
├─ run_dev.bat
└─ run_dev.sh
```

Keep large datasets/model binaries out of git. Provide scripts and documented download paths instead. Small demo model artifacts may be committed only if repository limits and licensing permit.

---

# 5. TECH STACK

Prefer open-source/local-first components.

## Frontend
- React + TypeScript + Vite.
- Responsive PWA-like layout.
- WebSocket client for recognition.
- WebRTC for calls.
- Browser `speechSynthesis` for TTS where available.
- Optional browser speech recognition; always provide typed-text fallback.
- Accessible component primitives; avoid animation that interferes with reading/signing.

## Backend
- Python 3.11+ compatible environment.
- FastAPI.
- WebSockets for recognition and signaling.
- Pydantic schemas.
- SQLite for hackathon persistence; PostgreSQL-ready abstraction if easy.
- Structured logging.
- CORS limited to configured development/prod origins.

## Vision / ML
- MediaPipe Tasks/Holistic or equivalent landmark pipeline.
- OpenCV where frame decoding/preprocessing is needed.
- PyTorch for training/inference unless the repository already standardizes on another framework.
- Export an optimized model to ONNX after the baseline works.
- ONNX Runtime / ONNX Runtime Web only after correctness is proven.

Do not hard-code library versions from memory. Resolve current compatible stable versions, pin them, and document them.

---

# 6. MULTIMODAL FEATURE PIPELINE

For each frame:
1. detect left/right hand landmarks,
2. detect upper-body pose,
3. obtain compact face/non-manual features,
4. attach tracking quality/presence values,
5. normalize,
6. append motion deltas,
7. push into a bounded temporal buffer.

Recommended compact signal:
- both hands: 21 × 3 coordinates per hand,
- selected upper-body pose keypoints,
- face blendshape coefficients or a carefully selected face-landmark subset,
- handedness/presence masks,
- first-order motion deltas,
- optional second-order motion deltas.

Normalization:
- translate coordinates relative to a stable body reference,
- normalize scale using shoulder width / torso reference,
- preserve meaningful left-vs-right distinctions,
- ensure mirrored webcam preview does not silently reverse model semantics,
- fill missing landmarks with zeros plus explicit missing masks rather than pretending a detection exists.

Store feature-schema version with every model.

---

# 7. DATA COLLECTION AND DATA ETHICS

Create a developer-only data collection tool.

For each sample store:
- label,
- signer pseudonymous ID,
- take number,
- timestamp,
- frame count,
- feature-schema version,
- optional lighting/background tag,
- consent flag,
- landmark sequence file path,
- optional raw video path only if explicitly enabled.

Default behavior: do **not** persist raw camera video.

Collect multiple signers if possible. Split train/validation/test **by signer**, not by random clips, so the score is not inflated by seeing the same person in train and test.

Augment landmark sequences conservatively:
- temporal crop,
- speed jitter,
- slight coordinate noise,
- minor scale/translation,
- short landmark dropout,
- frame drop/interpolation.

Do not use horizontal flip unless semantics are verified for the sign and handedness scheme.

---

# 8. DATA SOURCES

Use official/research resources only after checking license/access conditions.

Important known resources:
- ISLRTC Indian Sign Language Dictionary — authoritative vocabulary reference; official FAQ states 10,000 terms and permits research/teaching/technology use under conditions including acknowledgement and no reselling/profiteering of the dictionary data.
- ISLTranslate — research dataset for continuous ISL with about 31k ISL-English sentence/phrase pairs.
- INCLUDE / CISLR and other ISL recognition resources — useful for research/pretraining/evaluation only when access and licensing permit.

For the hackathon demo, the safest path is:
1. use official ISL resources as linguistic reference,
2. record a small consented team/community demo dataset,
3. train a reliable scoped model,
4. clearly state the supported vocabulary.

Never scrape or redistribute copyrighted/licensed sign videos without permission.

---

# 9. MODEL STRATEGY

## Baseline first
Train a compact temporal landmark model for a limited but useful vocabulary.

Recommended baseline candidates:
- BiLSTM/GRU over landmark sequence,
- temporal convolution + GRU,
- compact Transformer encoder.

Start with the simplest model that generalizes across held-out signers.

### Example tensor
`[batch, time, feature_dim]`

### Output
`logits over K supported signs/phrases + background/no-sign`

## Continuous behavior for MVP
Use:
- rolling buffer,
- motion/activity gate,
- candidate prediction,
- temporal smoothing,
- dwell/min-duration,
- duplicate suppression,
- cooldown,
- explicit background/no-sign class.

This allows real continuous camera operation without claiming open-vocabulary continuous translation.

## Stretch path
Add:
- sign-boundary detector,
- CTC decoder or sequence-to-sequence translation,
- gloss/phrase decoding,
- language-aware reranking.

---

# 10. CONFIDENCE AND SELF-CORRECTION

Raw softmax is not a trustworthy confidence guarantee.

Implement:
- validation-set threshold tuning,
- optional temperature scaling,
- landmark-quality check,
- prediction stability check,
- margin between top-1 and top-2,
- minimum temporal evidence.

Pseudo decision:

```
if tracking_quality < T_tracking:
    TRACKING_LOST
elif activity < T_motion:
    NO_SIGN
elif calibrated_confidence < T_accept:
    NEED_REPEAT
elif top1_minus_top2 < T_margin:
    NEED_REPEAT
elif stability_frames < N_stable:
    continue_collecting
else:
    ACCEPTED
```

The UI should explain uncertainty in plain language.

---

# 11. CONTEXT ENGINE

Support explicit selectable domains:
- General,
- Classroom,
- Hospital,
- Emergency,
- Police/Public Service.

Context may rerank top-k candidates using:
- recent accepted tokens,
- allowed domain vocabulary,
- phrase templates,
- lightweight local NLP/rules.

Critical rule: context may **rerank evidence**, but must not invent a sentence unsupported by the sign recognizer.

Store:
- raw top-k,
- raw confidence,
- context-adjusted score,
- final decision,
- domain,
- reason.

This makes the “self-correcting AI” auditable in the demo.

---

# 12. TWO-WAY ISL OUTPUT

Build a phrase-first sign playback system.

Data model:

```
SignClip {
  id,
  gloss_or_phrase,
  language_text,
  category,
  source,
  license_note,
  signer,
  file,
  duration_ms
}
```

Playback order:
1. exact approved phrase clip,
2. approved multi-sign sequence,
3. word-level clips,
4. fingerspelling fallback,
5. “not available” rather than fabricated animation.

The visual signer pane must show what mode is being used.

Do not claim a word-by-word clip concatenation is grammatically fluent ISL.

---

# 13. REAL-TIME API CONTRACTS

Minimum HTTP endpoints:

- `GET /api/health`
- `GET /api/config`
- `GET /api/signs`
- `GET /api/domains`
- `POST /api/translate/text-to-isl`
- `POST /api/feedback`
- `GET /api/session/{id}` if sessions are persisted

Recognition WebSocket:
- `/ws/recognize`

Signaling WebSocket:
- `/ws/signaling/{room_id}`

Recognition responses should resemble:

```json
{
  "type": "prediction",
  "state": "ACCEPTED",
  "label": "doctor",
  "display_text": "Doctor",
  "confidence": 0.91,
  "alternatives": [
    {"label": "help", "confidence": 0.06}
  ],
  "tracking": {
    "left_hand": true,
    "right_hand": true,
    "pose": true,
    "face": true,
    "quality": 0.94
  },
  "domain": "hospital",
  "latency_ms": 82,
  "model_version": "demo-v1",
  "feature_schema": "holistic-v1"
}
```

Do not send full raw frames back to clients unless a debug mode explicitly asks for them.

---

# 14. FRAME TRANSPORT

For the first reliable build, allow frontend camera frames to be sent to the local backend via WebSocket as throttled compressed frames.

Requirements:
- adaptive target 10–15 FPS for backend recognition,
- do not queue stale frames,
- if backend is busy, drop/skip old frames,
- use acknowledgements/backpressure,
- dynamically lower resolution if latency rises,
- show actual measured FPS and latency.

After the core works, add optional client-side landmark extraction / ONNX inference.

---

# 15. FRONTEND EXPERIENCE

The UI must look like a real assistive product, not a dashboard template.

## Main Interpreter
- large live camera,
- optional landmark overlay,
- live transcript,
- confidence/state chip,
- domain selector,
- speaker output toggle,
- camera/mic permissions state,
- compact signal-health indicators,
- repeat/reset buttons,
- no distracting decorative motion.

## Conversation Mode
Two columns:
- Person A: sign → text/speech,
- Person B: speech/text → ISL.

Keep a turn-by-turn transcript.

## Call Mode
- video grid,
- SANKET captions,
- room code,
- join/copy controls,
- mic/camera states,
- network status.

## Accessibility Center
- text size,
- contrast,
- captions,
- vibration test,
- Braille-friendly text view,
- screen-reader behavior note.

## Emergency Mode
Large high-contrast options plus recognized emergency vocabulary.

## Diagnostics
Developer/judge-friendly panel:
- model version,
- supported vocabulary,
- FPS,
- latency P50/P95 if enough samples,
- camera resolution,
- landmark detection status,
- last 10 raw predictions,
- whether demo/fallback mode is active.

---

# 16. BRAILLE / HAPTICS / SOUND

## Braille
Core accessibility requirement is to expose correct text semantics so refreshable Braille/screen-reader systems can consume it. A Unicode Braille preview can be implemented as a demonstration, but label it “Braille preview” and do not claim it replaces certified contracted Braille translation.

## Haptics
Use `navigator.vibrate` only when supported. Provide patterns for:
- success,
- needs-repeat,
- emergency alert.

Always provide a visual equivalent because vibration support differs by device/browser.

## Environmental sound alerts
Stretch feature:
- recognize a small set such as alarm, horn, knock, siren,
- show visual event card,
- optional vibration.
Do not mix this classifier into the sign-language model.

---

# 17. DATABASE

Hackathon SQLite schema may include:

`sessions`
- id
- created_at
- domain
- mode

`utterances`
- id
- session_id
- source_mode
- raw_label
- final_text
- confidence
- state
- latency_ms
- model_version
- created_at

`feedback`
- id
- utterance_id
- accepted
- corrected_label
- note
- created_at

`sign_clips`
- id
- phrase
- text
- category
- source
- license_note
- file_path

`dataset_samples`
- id
- label
- signer_id
- consent
- feature_path
- raw_video_path nullable
- schema_version
- created_at

Do not store raw biometric video/face imagery by default.

---

# 18. SECURITY AND PRIVACY

- local-first processing when possible,
- camera/mic permission explanation,
- no raw recording by default,
- explicit opt-in for dataset collection,
- do not expose filesystem paths,
- validate room IDs and payload sizes,
- rate-limit or bound websocket messages,
- sanitize filenames,
- use random ephemeral call room IDs,
- never place credentials in the repository,
- provide `.env.example`,
- redact sensitive logs,
- clear session controls.

SANKET AI must not infer identity, emotion, disability status, medical condition or intent from a face. Facial/non-manual features are used only as sign-language signals.

---

# 19. OFFLINE / FAILURE BEHAVIOR

Required:
- clear backend disconnected state,
- camera permission denied state,
- no model found state,
- no hands/body detected state,
- low confidence state,
- unsupported sign state,
- network loss during call,
- TTS unsupported state,
- speech recognition unsupported state.

Provide a **Demo Replay Mode** using bundled consented prerecorded samples. This makes the judge demo reproducible if camera conditions fail. It must be visibly labeled as demo replay.

Optional:
- cache frontend assets as PWA,
- ONNX Web/WASM fallback for selected recognition models.

---

# 20. TESTING

## Backend
- health endpoint,
- feature schema validation,
- model loading,
- confidence gate,
- context reranker,
- sign clip lookup,
- WebSocket malformed payload handling.

## ML
- tensor shape tests,
- deterministic preprocessing,
- no NaNs,
- missing-landmark mask behavior,
- signer-independent evaluation,
- confusion matrix generation,
- inference latency benchmark.

## Frontend
- camera permission path,
- websocket reconnect,
- transcript updates,
- NEED_REPEAT state,
- keyboard navigation,
- accessible labels,
- call-room signaling,
- demo replay.

## E2E
At least:
1. open app,
2. start camera,
3. recognize supported sign,
4. output transcript,
5. speak accepted text,
6. uncertain sample triggers repeat,
7. change domain,
8. text input returns sign clip,
9. emergency screen works,
10. demo replay works after camera is disabled.

---

# 21. METRICS

Never fabricate numbers. Measure them from the actual build.

Report:
- supported sign/phrase count,
- held-out signer macro F1,
- top-1/top-3 accuracy where applicable,
- confusion matrix,
- false activation rate,
- repeat-request rate,
- P50/P95 end-to-end latency,
- processing FPS,
- landmark failure rate.

A strong hackathon system with a smaller vocabulary and honest held-out evaluation is preferable to an unrealistic “thousands of signs at 99.9% accuracy” claim.

---

# 22. DEMO SCENARIO

Prepare a deterministic 3–5 minute flow:

1. **Problem in 15 seconds:** ordinary interpreter gap; real signing is multimodal.
2. **Live sign:** user signs a supported phrase.
3. **Show multimodal perception:** hands + face + body + motion signal indicators.
4. **Translation:** text appears and TTS speaks it.
5. **Self-correction:** intentionally unclear sign → “please repeat”, then clear sign → accepted.
6. **Context:** switch General → Hospital and show context-aware candidate handling.
7. **Two-way:** hearing user types/speaks a phrase → corresponding ISL clip.
8. **Accessibility:** high contrast / visual-haptic alert / Braille-friendly output.
9. **Calling:** show two-browser call with live caption overlay if stable.
10. **Impact + scale:** classroom, hospital, police/public service, emergency; local-first privacy; expandable vocabulary.

Keep an offline demo replay backup.

---

# 23. DOCUMENTATION REQUIRED

README must include:
- problem,
- project differentiators,
- architecture diagram,
- screenshots,
- exact quick start,
- supported platforms,
- supported demo vocabulary,
- dataset provenance,
- privacy behavior,
- model/evaluation results,
- limitations,
- roadmap,
- acknowledgements.

Also create:
- `docs/ARCHITECTURE.md`
- `docs/ML_PIPELINE.md`
- `docs/DATA_AND_LICENSES.md`
- `docs/DEMO_GUIDE.md`
- `docs/JUDGE_QA.md`
- `docs/PRIVACY_AND_ACCESSIBILITY.md`

---

# 24. IMPLEMENTATION LOOP

For every development iteration:
1. inspect current repo,
2. run existing tests,
3. choose one small vertical slice,
4. implement,
5. run tests/build,
6. fix regressions,
7. update docs,
8. commit clearly,
9. repeat.

Do not rewrite stable working code just to make it “cleaner” during hackathon crunch.

For every feature, ask:
- Is it actually implemented?
- Can a judge see it?
- Can we measure it?
- What happens when it fails?
- Is it accessible?
- Does it preserve privacy?
- Does it depend on internet/paid services?
- Is the claim linguistically/technically honest?

---

# 25. FINAL DEFINITION OF DONE

SANKET AI is demo-ready only when:
- setup works from a fresh machine using documented commands,
- frontend + backend start reliably,
- camera input works,
- multimodal signals are extracted,
- at least one trained temporal model is loaded,
- a declared vocabulary is recognized in real time,
- low-confidence input produces NEED_REPEAT,
- transcript and TTS work,
- text-to-ISL output works for a curated phrase set,
- demo replay works,
- accessibility controls are usable,
- no raw video is silently stored,
- test suite/build passes,
- measured metrics are shown honestly,
- limitations are documented,
- judge demo can be completed without editing code.

After this core is green, continue with calling, offline ONNX, hardware bridges and broader vocabulary.

**Do not stop at scaffolding. Build vertical slices until the repository produces a working end-to-end SANKET AI prototype.**
