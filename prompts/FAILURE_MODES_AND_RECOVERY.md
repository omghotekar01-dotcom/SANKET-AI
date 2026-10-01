# SANKET AI — Failure Modes and Recovery Specification

This document defines how the product must behave when reality is messy. The system must fail visibly, safely and recoverably.

## 1. Camera and input failures

### Permission denied
Behavior:
- show a clear permission-denied state;
- explain how to re-enable permission;
- keep typed conversation and demo replay available;
- never loop permission dialogs.

Acceptance:
- application remains usable without camera access.

### Camera unavailable / busy
Behavior:
- detect missing device or device already used by another app;
- show retry + device selector;
- do not crash recognition services.

### Low light / glare / backlight
Behavior:
- expose degraded tracking quality;
- reduce confidence;
- recommend better lighting only after persistent degradation;
- never silently convert low-quality tracking into a confident sentence.

### Partial body visibility
Behavior:
- hand-only signs may continue if enough evidence exists;
- signs requiring pose/non-manual features must reduce confidence;
- diagnostics must identify which signals are missing.

### Occlusion
Examples:
- one hand behind another,
- face covered,
- hand leaves frame,
- sleeves/background confuse detector.

Behavior:
- mark missing signals,
- preserve short temporal history,
- reject prediction if evidence is insufficient.

### Mirrored preview mismatch
Rule:
- display mirroring and inference coordinates must be explicitly separated;
- handedness must remain consistent with training data.

## 2. Tracking failures

States:
- GOOD
- DEGRADED
- TRACKING_LOST

Tracking score can combine:
- required landmarks present,
- landmark visibility,
- frame-to-frame consistency,
- hand count,
- body reference availability.

Recovery:
- clear stale temporal buffer after prolonged loss;
- require fresh stable frames before new prediction.

## 3. Recognition failures

### Unsupported sign
Behavior:
- show “Sign not in current supported vocabulary” when the system has enough tracking but no confident class.

### Ambiguous sign
Behavior:
- use NEED_REPEAT;
- optionally show top alternatives in diagnostics, not as authoritative translation.

### Repeated held sign
Use:
- neutral-frame detection,
- cooldown,
- duplicate suppression,
- state transition.

### Rapid consecutive signs
Use:
- temporal segmentation,
- minimum dwell,
- boundary detector if available,
- suppress duplicate outputs only when same token repeats without neutral transition.

### Wrong but confident prediction
Mitigations:
- signer-independent validation,
- calibration,
- top-2 margin,
- context compatibility,
- user correction feedback.

Never hide wrong predictions during evaluation.

## 4. Context failures

### Wrong domain selected
Behavior:
- allow immediate switch;
- context reranking must never completely override strong visual evidence.

### Context overreach
Forbidden:
- using an LLM to invent a sentence from weak sign evidence.

Rule:
- language/context layer may normalize or rerank only candidate meanings supported by perception.

## 5. Speech/TTS failures

### Speech recognition unavailable
Fallback:
- typed text.

### TTS unavailable
Fallback:
- persistent visible text.

### Wrong language/voice
Behavior:
- allow voice/language selection;
- do not make TTS a blocker.

## 6. Reverse ISL output failures

### Exact phrase unavailable
Fallback ladder:
1. exact approved phrase clip;
2. approved multi-sign sequence;
3. word-level clips;
4. fingerspelling;
5. “No verified ISL rendering available.”

Never fabricate fluent ISL.

### Missing media file
Behavior:
- display unavailable state,
- log missing asset,
- continue conversation via text.

## 7. WebRTC failures

### Room not found
- return to join screen;
- keep local interpreter available.

### ICE failure
- show connection failure;
- support retry;
- LAN/demo mode may use simpler networking if documented.

### Peer disconnect
- preserve local transcript;
- show reconnect state;
- never pretend call is live.

### Caption pipeline failure
- video call continues;
- caption panel explicitly shows unavailable/degraded state.

## 8. Database failures

### SQLite locked/corrupt
- recognition must still function without persistence where possible;
- queue lightweight logs in memory;
- expose storage warning.

### Migration mismatch
- startup validation must fail loudly with actionable message.

## 9. Model failures

### Model missing
- app launches into diagnostics/demo shell;
- exact missing artifact is shown.

### Label map mismatch
- block inference;
- never index labels blindly.

### Feature schema mismatch
- reject startup/inference;
- show expected vs actual schema versions.

### NaN / invalid tensor
- drop sample,
- log structured error,
- reset sequence buffer if needed.

## 10. Performance failures

### Latency spike
Behavior:
- drop stale frames,
- lower frame rate/resolution,
- keep most recent frame,
- show measured latency.

### CPU overload
Behavior:
- adaptive inference interval;
- optional reduced face feature set;
- disable non-critical visualization before disabling recognition.

### Memory growth
Requirements:
- bounded buffers,
- bounded logs,
- object URL cleanup,
- release media streams on page change.

## 11. Network failures

Core recognition should remain local where possible.

When external network is lost:
- local recognition survives,
- TTS survives if browser-local,
- reverse clips survive if bundled,
- call mode can fail gracefully,
- no blank screen.

## 12. Demo failure ladder

If live demo fails:
1. retry camera once;
2. switch camera/device if available;
3. restart recognition backend only;
4. use bundled prerecorded sample through same inference path;
5. use clearly labelled Demo Replay Mode.

The team must rehearse this ladder.

## 13. Recovery UX rules

Every error should provide:
- what happened,
- whether user data is safe,
- what still works,
- one primary recovery action,
- optional diagnostics.

Avoid generic “Something went wrong”.

## 14. Logging

Structured event fields:
- timestamp,
- subsystem,
- event code,
- severity,
- session ID,
- model version,
- feature schema,
- latency if relevant,
- no raw biometric frames by default.

## 15. Release gate

Before demo:
- simulate camera denied;
- unplug camera;
- cover one hand;
- leave frame;
- use unsupported sign;
- force backend restart;
- remove model file;
- disable network;
- stop peer connection;
- disable TTS/speech recognition.

Every scenario must have a controlled visible result.