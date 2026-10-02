# SANKET AI — Final implementation audit

This file is a release truth table. "Implemented" means code exists and is covered by an automated or deterministic acceptance path. It does **not** mean unrestricted ISL translation.

| Requirement | Status | Current proof / limitation |
|---|---|---|
| R01 Real-time interpretation | Implemented | Camera → MediaPipe → temporal recognizer WebSocket. Live vocabulary is finite. |
| R02 Hands + face + body + motion | Implemented | Holistic feature schemas expose both hands, pose, selected non-manual facial landmarks and motion. |
| R03 Continuous behavior | Implemented | Rolling temporal window, activity gate, stable prediction requirement, cooldown and held-sign suppression. |
| R04 Context-aware | Implemented | External JSON domain packs rerank existing evidence only. |
| R05 Confidence / self-correction | Implemented | Tracking, motion, confidence, top-2 margin and temporal stability can yield NEED_REPEAT. |
| R06 ISL → text | Implemented | ACCEPTED event → transcript. |
| R07 ISL → speech | Implemented | Opt-in browser TTS for accepted text. |
| R08 Text → ISL | Implemented framework / assets required | Only verified registered clips are presented as verified ISL; no fabricated reverse translation. |
| R09 Speech → ISL | Implemented framework / assets required | Browser speech recognition feeds the same verified-clip resolver; typing fallback always remains. |
| R10 Two-way communication | Implemented | Conversation mode + live interpreter provide both directions. |
| R11 Braille accessibility | Implemented | Semantic text is screen-reader / refreshable-Braille compatible; no certified contracted-Braille claim. |
| R12 Environmental sound alerts | Implemented experimental | Local Web Audio feature classifier detects alarm-like sustained tones; deterministic self-test; not safety-certified. |
| R13 Haptics | Implemented | Capability-detected vibration with visual equivalents. |
| R14 Emergency assistance | Implemented | HELP/DOCTOR/POLICE/FIRE/ACCIDENT/DANGER/WATER/PAIN phrase grid; no dispatch claim. |
| R15 Sign-language calling | Implemented hackathon path | WebRTC + signaling + accepted SANKET captions; same-network/two-tab path, no TURN guarantee. |
| R16 Safe interface actions | Implemented | Opt-in Stop/Repeat/Danger in-app actions only; no shell/OS execution. |
| R17 Low-cost | Implemented | Webcam/laptop/open-source stack; no paid core API. |
| R18 Domain scalability | Implemented | `domain_packs.json` adds/changes contexts without recognizer-core edits. |
| R19 Feedback | Implemented | Correct/Fix controls persist metadata; never auto-retrain. |
| R20 Privacy | Implemented | Recognition does not persist raw camera video; data collection requires consent and stores landmarks. |
| R21 Offline resilience | Implemented demo fallback | Labelled Demo Replay works independently of live recognition claims. |
| R22 Explainability | Implemented | Diagnostics exposes model source/version/backend, perception, DB, schema and metrics availability. |
| R23 Dataset integrity | Implemented | Signer-aware split when signer metadata permits; limitations are reported. |
| R24 Honest evaluation | Implemented | Metrics endpoint only publishes generated evaluation reports; external bootstrap has no SANKET accuracy claim. |
| R25 Accessibility-first UI | Implemented | Keyboard-native controls, ARIA/live regions, contrast, text scaling, reduced motion and haptics. |

## Exact 21-sign recognition contract

The project contract is fixed to:

`hello, thank_you, yes, no, help, doctor, hospital, water, pain, medicine, police, fire, danger, accident, stop, where, name, student, teacher, repeat, understand`.

The installed 50-word external bootstrap currently intersects that contract at:

`hello, thank_you, doctor, hospital, medicine, police, student, teacher`.

All other contract signs remain **missing** until a real evaluated recognizer can emit them. They appear as missing in the UI and are prioritized in Training Studio. SANKET deliberately does not convert those names into fake recognition capability.

## Release rule

The repository may be called code-clean only after the current main commit passes:
- Python compile,
- backend/ML pytest,
- production React/TypeScript build,
- Linux MediaPipe + 50-class inference smoke test,
- Windows MediaPipe + 50-class inference smoke test.

Model quality and vocabulary coverage are separate from software build correctness.
