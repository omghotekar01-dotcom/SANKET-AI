# SANKET AI — Security, Privacy and Threat Model

## 1. Sensitive surfaces

SANKET AI may process:
- live camera video,
- face landmarks,
- hand/body landmarks,
- microphone audio,
- call media,
- transcripts,
- optional dataset samples,
- feedback.

Treat these as privacy-sensitive.

## 2. Default privacy stance

- process locally where feasible;
- do not persist raw camera/audio by default;
- require explicit action for data collection;
- separate “use app” from “contribute dataset”;
- minimize logs;
- use pseudonymous signer IDs;
- expose clear reset/delete controls for local sessions.

## 3. Prohibited inference

Do not infer or store:
- identity,
- emotion,
- disability status,
- health status,
- ethnicity,
- age,
- gender,
- intent beyond communication context.

Facial features are linguistic/non-manual features only.

## 4. Threats

### Unauthorized camera/mic capture
Mitigation:
- browser permission model;
- clear active indicator;
- stop tracks on exit;
- no hidden background recording.

### Raw video leakage
Mitigation:
- raw storage off by default;
- explicit collection toggle;
- gitignore data directories;
- never commit captured samples.

### WebSocket abuse
Mitigation:
- payload size limit;
- message schema validation;
- rate/backpressure;
- session bounds;
- origin controls.

### Malicious room IDs
Mitigation:
- random room IDs;
- validation;
- expiry;
- no sequential predictable IDs if avoidable.

### WebRTC abuse
Mitigation:
- explicit join;
- camera/mic controls;
- no auto-answer;
- disconnect control;
- no recording by default.

### File path traversal
Mitigation:
- whitelist asset IDs;
- never accept raw arbitrary filesystem paths.

### Model poisoning via feedback
Mitigation:
- user feedback does not immediately retrain production model;
- store corrections for review;
- training pipeline consumes only curated dataset versions.

### Prompt/LLM injection
If an LLM is later added:
- never allow model text to execute commands;
- keep model isolated from shell/filesystem actions;
- context layer can only choose from structured candidate data.

### Gesture-triggered dangerous actions
Mitigation:
- whitelist in-app actions;
- confirmation for any sensitive operation;
- no shell/OS control.

## 5. Secrets

- no API keys in code;
- use env files;
- provide .env.example;
- never commit real secrets;
- rotate leaked credentials immediately.

## 6. Logging

Allowed:
- state transitions,
- latency,
- model version,
- error codes,
- anonymous session ID.

Avoid:
- raw images,
- audio,
- full faces,
- sensitive transcripts unless user explicitly wants session history.

## 7. Dataset consent

Data collection screen should explain:
- what is collected;
- whether raw video is saved;
- purpose;
- how to stop;
- how sample is identified.

Do not imply legal consent language you have not actually validated.

## 8. Retention

Hackathon default:
- local temporary data;
- manual deletion;
- no cloud upload unless explicitly configured.

Future production:
- define retention periods,
- deletion requests,
- encryption,
- access control,
- audit logs.

## 9. Transport security

Production:
- HTTPS/WSS;
- secure cookies/tokens if authentication exists.

Local hackathon:
- localhost may use HTTP;
- document that it is development mode.

## 10. Dependency risk

- pin versions;
- run dependency audit if available;
- minimize heavy packages;
- document known CVEs if unavoidable.

## 11. Denial of service

- bounded frame queue;
- drop old frames;
- bounded transcript;
- connection limits;
- avoid unbounded in-memory logs.

## 12. Privacy UI

Show:
- camera active;
- mic active;
- recording/data collection active;
- call connected;
- demo replay active.

These indicators must be visually distinct.

## 13. Threat-model release checklist

- [ ] Camera stops on exit.
- [ ] Raw frames are not written unexpectedly.
- [ ] Dataset collection is explicit.
- [ ] WebSocket validates payloads.
- [ ] Room IDs validated.
- [ ] No arbitrary action execution.
- [ ] No secrets in repository.
- [ ] Logs contain no biometric frames.
- [ ] Feedback cannot poison model automatically.
- [ ] Demo replay clearly labelled.
