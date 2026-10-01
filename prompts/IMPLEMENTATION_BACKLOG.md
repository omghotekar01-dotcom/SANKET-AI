# SANKET AI — Implementation Backlog

## Epic A — Foundation
- [ ] monorepo/project structure
- [ ] React + TypeScript frontend
- [ ] FastAPI backend
- [ ] shared config
- [ ] one-command startup
- [ ] health endpoint
- [ ] structured logging
- [ ] .env.example
- [ ] lock dependencies

## Epic B — Camera and perception
- [ ] camera permissions
- [ ] device selector
- [ ] mirrored preview
- [ ] frame throttling
- [ ] MediaPipe hands
- [ ] pose
- [ ] face/non-manual features
- [ ] landmark masks
- [ ] signal-health metrics
- [ ] overlay canvas

## Epic C — Data collector
- [ ] developer-only route
- [ ] label picker
- [ ] signer ID
- [ ] consent toggle
- [ ] start/stop take
- [ ] landmark save
- [ ] optional raw video off by default
- [ ] metadata index

## Epic D — ML
- [ ] feature schema
- [ ] preprocessing
- [ ] split utility
- [ ] baseline GRU/LSTM
- [ ] training config
- [ ] early stopping
- [ ] model artifact package
- [ ] confusion matrix
- [ ] macro F1
- [ ] top-k
- [ ] latency benchmark
- [ ] threshold calibration
- [ ] ONNX export

## Epic E — Live decoder
- [ ] rolling buffer
- [ ] activity gate
- [ ] no-sign
- [ ] stable prediction
- [ ] duplicate suppression
- [ ] cooldown
- [ ] NEED_REPEAT
- [ ] TRACKING_LOST
- [ ] context domain
- [ ] transcript event

## Epic F — Communication
- [ ] transcript UI
- [ ] TTS
- [ ] conversation turns
- [ ] text input
- [ ] sign clip registry
- [ ] phrase matching
- [ ] clip player
- [ ] fingerspelling fallback
- [ ] optional speech input

## Epic G — Accessibility
- [ ] keyboard navigation
- [ ] ARIA live transcript
- [ ] high contrast
- [ ] large text
- [ ] reduced motion
- [ ] visual alerts
- [ ] haptics capability detection
- [ ] Braille-friendly text
- [ ] emergency mode

## Epic H — Calling
- [ ] signaling websocket
- [ ] room creation
- [ ] join
- [ ] offer/answer
- [ ] ICE
- [ ] peer video
- [ ] connection state
- [ ] caption metadata
- [ ] leave/reconnect

## Epic I — Privacy and safety
- [ ] raw recording off
- [ ] explicit collection mode
- [ ] sanitize asset IDs
- [ ] websocket size limits
- [ ] random room IDs
- [ ] no arbitrary commands
- [ ] local deletion/reset
- [ ] privacy indicators

## Epic J — Reliability
- [ ] camera denied
- [ ] camera unavailable
- [ ] model missing
- [ ] schema mismatch
- [ ] backend reconnect
- [ ] network offline
- [ ] TTS unavailable
- [ ] speech unavailable
- [ ] unsupported sign
- [ ] low light
- [ ] partial tracking

## Epic K — Demo
- [ ] demo replay
- [ ] bundled samples
- [ ] judge presentation mode
- [ ] actual metrics
- [ ] architecture diagram
- [ ] 3–5 minute script
- [ ] backup laptop test
- [ ] offline test
- [ ] final release tag

## Rule
Do not mark an item complete unless it is implemented, tested and reproducible.