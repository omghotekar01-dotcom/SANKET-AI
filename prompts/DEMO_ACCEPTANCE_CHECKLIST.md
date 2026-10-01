# SANKET AI — Demo Acceptance Checklist

A checkbox becomes green only after it is actually tested.

## Repository
- [ ] Fresh clone instructions work.
- [ ] `.env.example` exists.
- [ ] No secrets committed.
- [ ] Large/raw datasets are gitignored.
- [ ] Windows startup script works.
- [ ] Linux/macOS startup script works or limitation is documented.

## Frontend
- [ ] Camera permission flow is understandable.
- [ ] Live video fits desktop and mobile layouts.
- [ ] Transcript is readable at a distance.
- [ ] State is visible: accepted / repeat / no sign / tracking lost.
- [ ] Domain selector works.
- [ ] High contrast works.
- [ ] Keyboard navigation works.
- [ ] ARIA labels/live transcript are present.
- [ ] Demo replay is visibly labelled.

## Vision
- [ ] Left hand tracking visible.
- [ ] Right hand tracking visible.
- [ ] Pose tracking visible.
- [ ] Face/non-manual signal available.
- [ ] Missing detections do not create NaN/crashes.
- [ ] Mirror behavior is consistent.

## ML
- [ ] Model artifact loads.
- [ ] Label map matches model output dimension.
- [ ] Feature schema matches model input.
- [ ] Evaluation uses held-out signer(s) where feasible.
- [ ] Confusion matrix generated.
- [ ] Low confidence is rejected.
- [ ] Background/no-sign is handled.
- [ ] Held sign does not spam duplicate words.
- [ ] Actual latency is measured.

## Conversation
- [ ] ISL → text works.
- [ ] Accepted text can be spoken.
- [ ] Text → ISL curated clip works.
- [ ] Speech path has text fallback.
- [ ] Unsupported phrase gives an honest fallback.

## Differentiators
- [ ] Context domain changes reranking/allowed vocabulary.
- [ ] Unclear sign demonstrates NEED_REPEAT.
- [ ] Feedback/correction can be captured.
- [ ] Emergency screen works.
- [ ] Visual alert works.
- [ ] Vibration feature capability-detects support.
- [ ] Braille-friendly output is labelled accurately.
- [ ] Call mode connects two peers if included in final demo.
- [ ] Call captions are stable enough to demo.

## Privacy / Safety
- [ ] Raw camera video is not saved by default.
- [ ] Dataset collection requires explicit user action.
- [ ] Consent flag is stored with collected samples.
- [ ] No face identity/emotion inference.
- [ ] No arbitrary OS command execution.
- [ ] Emergency mode does not claim guaranteed emergency dispatch.

## Judge demo
- [ ] 3–5 minute script rehearsed.
- [ ] Supported signs list is printed/available.
- [ ] Lighting/camera position tested.
- [ ] Offline demo replay backup works.
- [ ] Architecture diagram ready.
- [ ] Metrics are actual measured values.
- [ ] Limitations slide/answer is ready.
- [ ] No feature shown in pitch is represented as complete unless it is actually working.

## Final rule
Do not mark the project “100% complete” just because every page exists. It is complete for the hackathon only when the core communication loop works repeatedly under demo conditions and failure states are handled visibly.
