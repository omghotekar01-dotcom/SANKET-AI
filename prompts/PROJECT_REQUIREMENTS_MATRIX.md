# SANKET AI — Project Requirements Traceability Matrix

This file converts the submitted Hacktopia concept into buildable requirements. Every claimed feature must map to code, a visible demo behavior, and an acceptance check.

| ID | Submitted / Planned Capability | Required Implementation | Visible Proof | Acceptance Condition | Priority |
|---|---|---|---|---|---|
| R01 | Real-time ISL interpretation | Camera capture + temporal recognition pipeline | Live interpreter screen | Supported sign is recognized from live camera within measured latency | P0 |
| R02 | Hands + Face + Body + Motion | MediaPipe/equivalent multimodal landmarks + temporal features | Landmark/signal-health overlay | Both hands, pose, face/non-manual signal and motion state are exposed | P0 |
| R03 | Continuous signing behavior | Rolling buffer, activity gate, smoothing, cooldown/background class | Live transcript without repeated spam | Held sign does not emit endlessly; transitions are handled | P0 |
| R04 | Context-aware interpretation | Domain selector + reranking/constraints | General/Hospital/Classroom/Emergency mode | Context changes candidate handling without inventing unsupported output | P0 |
| R05 | Self-correcting AI | Confidence calibration + tracking quality + top-2 margin + stability | NEED_REPEAT state | Intentionally weak/ambiguous sample is rejected instead of guessed | P0 |
| R06 | ISL → Text | Accepted recognition → transcript | Transcript panel | Accepted sign produces readable text | P0 |
| R07 | ISL → Speech | TTS from accepted text | Speaker output | Accepted text can be spoken and muted | P0 |
| R08 | Text → ISL | Curated phrase/sign clip retrieval | Sign playback pane | Supported typed phrase shows correct approved clip | P1 |
| R09 | Speech → ISL | Speech-to-text + text-to-ISL path, with typing fallback | Conversation mode | Spoken or typed phrase reaches same ISL renderer | P1 |
| R10 | Two-way communication | Conversation UI with separate turns | Person A / Person B panels | Signer and non-signer can exchange at least one complete turn each | P1 |
| R11 | Braille accessibility | Semantic text output + optional Unicode Braille preview | Accessibility center | Screen-reader/Braille-friendly text exists; preview is accurately labelled | P1 |
| R12 | Environmental sound alerts | Separate compact audio event classifier | Visual alert card | At least one supported alert class triggers a visual notification | P2 |
| R13 | Directional / haptic vibration | Capability-detected browser/device vibration patterns | Haptic test button | Supported device vibrates; visual equivalent always exists | P1 |
| R14 | Emergency assistance | Large accessible emergency phrase grid | Emergency page | HELP/DOCTOR/POLICE/FIRE/ACCIDENT/DANGER are immediately accessible | P1 |
| R15 | Sign-language calling | WebRTC peer connection + SANKET captions | Call screen | Two peers/tabs can connect and exchange media; captions shown if stable | P1 |
| R16 | Computer/interface action control | Whitelisted in-app action mapper | Demo media/nav controls | Only approved local UI actions can be triggered | P2 |
| R17 | Low-cost feasibility | Standard webcam/laptop + open-source stack | Setup documentation | Core works without specialized hardware or paid APIs | P0 |
| R18 | Domain scalability | Modular vocabulary/context packs | Domain config files | New domain can be added without rewriting recognizer core | P1 |
| R19 | Feedback/self-improvement | User correction/feedback capture | “Correct / Fix” action | Feedback is stored as metadata without auto-corrupting model weights | P1 |
| R20 | Privacy | Local-first processing; raw recording off by default | Privacy indicator/settings | Camera works without silently persisting video | P0 |
| R21 | Offline resilience | Demo Replay Mode + local assets | “Demo Replay” badge | Core judge flow can run from bundled consented samples if camera/network fails | P0 |
| R22 | Explainable demo | Diagnostics with confidence/FPS/latency/model version | Diagnostics drawer | Judges can see actual system state and measured performance | P0 |
| R23 | Dataset integrity | Signer-aware metadata and train/val/test split | Evaluation report | Split avoids same-signer leakage where feasible | P0 |
| R24 | Honest evaluation | Macro F1, confusion matrix, latency, repeat rate | Metrics page/report | All displayed numbers are generated from real evaluation logs | P0 |
| R25 | Accessibility-first UI | Keyboard, contrast, text scaling, ARIA/live regions | Accessibility center | Core flow is usable without mouse-only interactions | P1 |

## Scope interpretation

### What “continuous” means for the hackathon MVP
The application operates continuously on a live camera stream with temporal windows, segmentation/activity logic, smoothing and duplicate suppression. It may support a finite vocabulary/phrase set.

Do **not** describe this as unrestricted open-vocabulary continuous ISL translation unless such a model is actually trained, evaluated and integrated.

### What “AI verification” means
AI verification is not a second magical model. It is an explicit validation layer using tracking quality, calibrated confidence, temporal stability, candidate margin and context compatibility.

### What “Braille output” means
The software provides semantically correct accessible text suitable for screen readers/refreshable Braille systems. A visual Unicode Braille representation is only a preview unless a proper translation/grade system is integrated.

## Release gate
A feature can appear in the final pitch as “working” only when:
1. implementation exists,
2. acceptance test passes,
3. it can be demonstrated without editing code,
4. failure behavior is visible,
5. the README explains limitations.
