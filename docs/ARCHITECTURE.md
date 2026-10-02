# SANKET AI Architecture

## Runtime flow

```text
Browser camera (preview mirrored only)
  -> throttled 320x240 JPEG over /ws/recognize
  -> MediaPipe Holistic on local FastAPI backend
  -> normalized left/right hand + selected pose + face/non-manual landmarks
  -> bounded temporal window + velocity features
  -> evaluated finite-vocabulary temporal model
  -> context reranking (evidence only)
  -> tracking + motion + confidence + margin + stability gates
  -> ACCEPTED / NEED_REPEAT / NO_SIGN / TRACKING_LOST
  -> semantic transcript -> browser TTS / accessible output
```

Raw camera frames are processed in memory and are not written to disk by normal interpretation. Dataset collection stores landmark arrays only and requires explicit consent.

## Main modules

- `apps/web`: React + TypeScript + Vite UI.
- `apps/api`: FastAPI, WebSockets, MediaPipe adapter, confidence decoder, local SQLite feedback.
- `ml`: dataset split, preprocessing, temporal template training and evaluation.
- `assets/sign_clips`: reverse-ISL registry and explicitly uploaded local clips.
- `data/local`: gitignored samples and SQLite runtime state.

## WebRTC

`/ws/signaling/{room}` only transports offer/answer/ICE/caption metadata. Audio/video is peer-to-peer. The shipped configuration has no TURN dependency and is intended for same-network/two-tab hackathon demos. Calling is not a dependency of the core interpreter.
