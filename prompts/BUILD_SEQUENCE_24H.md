# SANKET AI — 24-Hour Hackathon Build Sequence

This is the execution order for a 24-hour final. It is designed to maximize the chance of finishing a strong working prototype instead of building many unstable features.

## Before the clock starts
Have ready:
- repository structure and pinned environments,
- master prompt/specification,
- consented demo videos/landmark samples,
- approved demo vocabulary,
- sign clips for reverse output,
- UI wireframe,
- sample model checkpoint if rules permit pre-trained/prepared assets,
- architecture diagram,
- offline copies of dependencies where practical.

Always follow event rules on what may be prepared in advance.

## Hour 0–1 — Environment lock
- clone repo,
- create/confirm implementation branch,
- run backend and frontend,
- verify Python/Node versions,
- verify camera permissions,
- add `/api/health`,
- verify WebSocket echo/handshake,
- record exact working commands.

**Gate:** both apps start from documented commands.

## Hour 1–4 — Camera + multimodal perception
- implement camera panel,
- throttle frames,
- MediaPipe/equivalent hands, pose, face features,
- signal-health response,
- landmark overlay,
- missing-landmark masks,
- mirroring correctness.

**Gate:** judges could already see hands/face/body tracking.

## Hour 4–7 — Dataset and model path
- finalize demo vocabulary,
- collect/validate samples,
- preprocess feature sequences,
- train compact temporal baseline,
- save label map + schema + normalization,
- generate initial confusion matrix.

**Gate:** model recognizes prerecorded held-out examples.

## Hour 7–10 — Real-time decoder
- rolling feature buffer,
- activity/no-sign detection,
- temporal prediction,
- smoothing,
- duplicate suppression,
- cooldown,
- measured latency/FPS.

**Gate:** live recognition produces stable tokens instead of frame-by-frame spam.

## Hour 10–12 — Self-correction
- confidence threshold,
- top-1/top-2 margin,
- tracking quality,
- stability check,
- ACCEPTED / NEED_REPEAT / NO_SIGN / TRACKING_LOST states,
- UI explanation for each state.

**Gate:** deliberately unclear signing causes “please repeat”.

## Hour 12–14 — Core communication
- transcript,
- TTS,
- session turns,
- domain selector,
- context reranking,
- feedback/correction capture.

**Gate:** sign → text → speech works end-to-end.

## Hour 14–16 — Reverse communication
- typed text input,
- phrase/sign clip registry,
- exact phrase lookup,
- word/sign fallback,
- honest unsupported-message state,
- optional speech input.

**Gate:** non-signer can send a supported message back visually in ISL.

## Hour 16–18 — Accessibility/emergency
- high contrast,
- text scaling,
- keyboard controls,
- ARIA live transcript,
- visual/haptic alerts,
- Braille-friendly text view,
- emergency communication grid.

**Gate:** accessibility features are functional, not decorative.

## Hour 18–20 — WebRTC calling OR reliability buffer
Only attempt call mode if all P0 gates are green.

- room ID,
- offer/answer/ICE signaling,
- peer video,
- caption channel,
- connection states.

If call mode becomes unstable, freeze it as experimental and spend this time fixing the interpreter.

## Hour 20–21 — Demo Replay Mode
- bundle consented prerecorded samples,
- deterministic playback,
- same inference path where possible,
- visible DEMO REPLAY badge,
- camera/network failure fallback.

## Hour 21–22 — Testing and hardening
- cold restart,
- fresh browser,
- camera denied,
- no model,
- backend restart,
- malformed websocket,
- low light,
- one hand missing,
- unsupported sign,
- speech/TTS unsupported.

## Hour 22–23 — Metrics + documentation
Generate actual:
- supported vocabulary size,
- held-out metrics,
- confusion matrix,
- P50/P95 latency,
- FPS,
- repeat-request rate if measured.

Update README screenshots and limitations.

## Hour 23–24 — Demo rehearsal only
No large new features.

Run the exact 3–5 minute demo repeatedly:
1. problem,
2. live sign,
3. multimodal overlay,
4. text/speech,
5. intentional uncertainty → repeat,
6. domain/context,
7. reverse communication,
8. accessibility/emergency,
9. calling if stable,
10. impact/scaling.

## Stop rules
Freeze a feature when:
- it breaks P0,
- it needs an external service you cannot guarantee,
- it has no deterministic demo path,
- it cannot be explained honestly,
- it consumes more time than its judge-visible value.

## Team split suggestion
With four members, a practical split is:
- Member A: ML/data/inference,
- Member B: backend/WebSocket/WebRTC,
- Member C: frontend/accessibility/product UI,
- Member D: integration/testing/demo/docs.

Cross-review at each gate so no subsystem exists only on one laptop.
