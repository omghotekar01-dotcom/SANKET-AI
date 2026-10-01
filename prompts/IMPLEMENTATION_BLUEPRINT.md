# SANKET AI — Implementation Blueprint

## 1. Vertical slices
### Slice 1 — App shell + health
React UI, FastAPI health endpoint, WebSocket connection indicator, run scripts.

### Slice 2 — Camera → backend → landmarks
Capture 640×480 or lower preview, throttle frames, decode server-side, extract holistic landmarks, return signal-health metadata, draw overlay.

### Slice 3 — Dataset collector
Record labeled landmark windows with signer ID and consent flag. Raw video off by default.

### Slice 4 — Baseline temporal model
Train compact GRU/LSTM/Transformer on landmark sequences. Hold out at least one signer when sample count permits. Save:
- model artifact,
- label map,
- feature schema,
- normalization stats,
- training config,
- evaluation report.

### Slice 5 — Real-time decoder
Rolling window + activity gate + prediction + smoothing + cooldown + background class.

### Slice 6 — Confidence/self-correction
Calibrate threshold on validation data, add top-2 margin and tracking quality.

### Slice 7 — Context
Domain vocabulary and phrase-aware reranker. Never create unsupported output.

### Slice 8 — Output
Transcript + browser TTS + session history.

### Slice 9 — Reverse communication
Text input → phrase matcher → curated sign video clip queue. Add speech input only as optional enhancement.

### Slice 10 — Differentiators
WebRTC call, emergency mode, haptics/visual alerts, Braille-friendly view.

---

## 2. Suggested ML feature schema
A compact first schema can concatenate:
- left hand xyz,
- right hand xyz,
- selected upper-body pose xyz/visibility,
- selected facial blendshapes,
- presence flags,
- delta features.

Keep `feature_schema.json` next to the model.

Example:
```json
{
  "version": "holistic-v1",
  "sequence_length": 48,
  "fps_target": 15,
  "hands": {"points": 21, "dims": 3, "both": true},
  "pose_indices": [0, 11, 12, 13, 14, 15, 16, 23, 24],
  "face_mode": "blendshapes",
  "include_delta": true,
  "normalization": "shoulder_scale+wrist_local",
  "mirroring": "display-only"
}
```

Do not assume this exact schema is optimal; benchmark it and version changes.

---

## 3. Real-time inference state machine
```
IDLE
  ├─ motion detected → COLLECTING
  └─ no motion → NO_SIGN

COLLECTING
  ├─ insufficient frames → COLLECTING
  ├─ tracking failure → TRACKING_LOST
  └─ enough frames → PREDICT

PREDICT
  ├─ low confidence/margin → NEED_REPEAT
  ├─ unstable → COLLECTING
  └─ stable → ACCEPTED → COOLDOWN

COOLDOWN
  └─ neutral/background for N frames → IDLE
```

Use this to prevent repeated output of the same held sign.

---

## 4. Backend modules
```
apps/api/app/
├─ main.py
├─ config.py
├─ schemas.py
├─ api/
│  ├─ health.py
│  ├─ translation.py
│  ├─ feedback.py
│  └─ signs.py
├─ ws/
│  ├─ recognition.py
│  └─ signaling.py
├─ services/
│  ├─ landmark_service.py
│  ├─ inference_service.py
│  ├─ context_service.py
│  ├─ confidence_service.py
│  ├─ clip_service.py
│  └─ session_service.py
└─ db/
   ├─ models.py
   └─ session.py
```

---

## 5. Frontend routes/components
Suggested routes:
- `/` product intro / device check
- `/interpret`
- `/conversation`
- `/call`
- `/emergency`
- `/accessibility`
- `/diagnostics`
- `/collect` developer mode only

Key components:
- CameraPanel
- LandmarkCanvas
- PredictionCard
- TranscriptPanel
- SignalHealth
- DomainSelector
- ConfidenceMeter
- ISLClipPlayer
- CallRoom
- AccessibilityControls
- EmergencyGrid
- DiagnosticsDrawer

---

## 6. Recognition WebSocket protocol
Client messages:
- `hello` capabilities
- `frame` binary/image metadata
- `set_domain`
- `reset`
- `stop`

Server messages:
- `ready`
- `tracking`
- `prediction`
- `accepted`
- `need_repeat`
- `error`
- `stats`

Use a sequence number so stale responses can be ignored.

---

## 7. WebRTC architecture
Use FastAPI WebSocket only for signaling:
- create/join room,
- offer,
- answer,
- ICE candidate,
- leave.

Media is peer-to-peer. Captions can be produced independently by each local SANKET client and sent over a WebRTC data channel or signaling channel.

---

## 8. Demo vocabulary strategy
Do not attempt thousands of signs during the 24-hour build.

Create a balanced demo vocabulary with visible real-world value, for example:
- hello
- thank you
- yes
- no
- help
- doctor
- hospital
- water
- pain
- medicine
- police
- fire
- danger
- accident
- stop
- where
- name
- student
- teacher
- repeat

Add 5–10 short phrases only after individual/dynamic signs are reliable.

The exact sign definitions must be validated against trustworthy ISL references and, ideally, an ISL-proficient reviewer.

---

## 9. Evaluation
Create `ml/evaluation/report.py` to output JSON + Markdown with:
- sample count by class,
- signers per split,
- macro/micro F1,
- per-class precision/recall,
- top-k accuracy,
- confusion matrix path,
- latency benchmark,
- threshold calibration data.

Never let train/test clips from the same recording session leak across splits.

---

## 10. Build/dev commands
Target one-command startup:
- Windows: `run_dev.bat`
- macOS/Linux: `./run_dev.sh`

Each should:
1. validate env files,
2. start API,
3. start web app,
4. print local URLs,
5. fail loudly with useful messages.

Provide manual commands too.

---

## 11. Reliability gates
Do not progress to the next high-complexity feature until:
- app builds,
- health endpoint passes,
- websocket reconnect passes,
- latest model loads,
- one prerecorded sample passes,
- one live sample passes,
- low-confidence sample rejects.

---

## 12. Commercial/scaling path after hackathon
### B2B/B2G possibilities
- hospitals and clinics,
- schools/colleges,
- public-service counters,
- banks,
- transport hubs,
- call centers/video relay,
- accessibility SDK for software vendors.

### Technical scale
- browser/on-device landmark inference,
- quantized ONNX model,
- model/version registry,
- domain packs,
- federated or consented personalization research,
- multilingual spoken-text output,
- enterprise analytics using metadata rather than raw video.

Before commercial use, re-check all dataset/video licenses. Do not monetize ISLRTC dictionary data contrary to its stated conditions.
