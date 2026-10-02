# SANKET AI — Streaming Segmentation and Incremental Decoding

## Why this specification exists

A webcam can run continuously while the model still behaves like an isolated-clip classifier. That is not sufficient for a real conversational system.

SANKET AI must explicitly solve the streaming problem:

**When does signing begin? When is there enough evidence to predict? When is a sign/phrase complete? When should provisional output become committed output? When should the buffer reset?**

This document defines the contract between perception, temporal segmentation, recognition, context and the user-facing transcript.

---

## 1. Product-level distinction

Use these terms precisely:

- **Live isolated recognition:** the camera is always running, but each accepted unit belongs to a finite isolated-sign vocabulary.
- **Streaming recognition:** the system autonomously detects activity/boundaries and emits recognized units from an unbroken camera stream.
- **Continuous sign-language translation:** the system interprets multi-sign discourse/sentences and produces target-language text while resolving temporal and linguistic structure.
- **Incremental translation:** output can be produced before the complete utterance/discourse has ended.

A working rolling-window isolated-sign system MUST NOT be marketed as unrestricted continuous ISL translation.

---

## 2. Required streaming states

The decoder SHALL expose an explicit state machine:

```
IDLE
  -> PRE_ROLL
  -> ACTIVE
  -> CANDIDATE
  -> COMMIT
  -> COOLDOWN
  -> IDLE
```

Exceptional states:
- TRACKING_LOST
- NEED_REPEAT
- UNSUPPORTED
- RESETTING

### IDLE
No meaningful signing activity is detected. Maintain only a small pre-roll ring buffer.

### PRE_ROLL
Activity may have started but evidence is insufficient. Preserve frames/features immediately before the trigger so the first movement is not clipped.

### ACTIVE
A signing unit is in progress. Accumulate temporal features and continuously update boundary evidence.

### CANDIDATE
The recognizer has a provisional hypothesis but the boundary/temporal evidence is not yet strong enough to commit.

### COMMIT
A stable supported unit has passed recognition, confidence and boundary gates. Emit exactly one committed transcript event.

### COOLDOWN
Suppress accidental repeated emission until a neutral transition, new movement pattern, or explicit boundary condition occurs.

---

## 3. Boundary evidence

Do not use a single arbitrary timer as the only segmentation mechanism.

Candidate boundary evidence may include:
- hand velocity and acceleration;
- wrist/hand displacement;
- pose motion;
- landmark stability;
- hands entering/leaving signing space;
- neutral/rest pose probability;
- recognizer entropy/confidence trajectory;
- candidate-label stability;
- inter-unit pause duration;
- context/language readiness for research-scale translation.

The MVP may use deterministic heuristics, but all thresholds MUST be configurable and logged.

---

## 4. Pre-roll and post-roll

A common streaming failure is clipping the beginning or end of a sign.

Maintain:
- a bounded pre-roll feature buffer while IDLE;
- a small post-boundary grace interval before finalizing when appropriate.

When activity begins, prepend pre-roll features to the active segment.

Never maintain an unbounded raw-frame history.

---

## 5. Provisional versus committed output

The UI MUST distinguish:

### Provisional
- unstable;
- may change;
- not spoken by TTS;
- not written permanently into conversation history;
- not transmitted as final caption to a remote peer.

### Committed
- passed boundary and uncertainty gates;
- appended to transcript;
- may trigger TTS;
- may be sent as accepted caption metadata;
- may trigger only whitelisted actions.

This prevents unstable frame-level predictions from becoming false statements.

---

## 6. Commit gate

A candidate MAY commit only if required conditions pass.

Example:

```
tracking_quality >= T_tracking
AND activity_evidence >= T_activity
AND calibrated_confidence >= T_accept
AND top1_margin >= T_margin
AND candidate_stability >= T_stability
AND boundary_evidence >= T_boundary
AND duplicate_guard == false
```

Exact thresholds come from validation, not intuition.

For classes known to require face/pose cues, modality-specific quality gates may additionally apply.

---

## 7. Timeout behavior

Timeouts are safety/recovery tools, not proof of linguistic boundaries.

Possible timeouts:
- maximum active-segment duration;
- prolonged tracking loss;
- prolonged inactivity after a candidate;
- stalled provisional prediction.

On timeout:
- commit only if evidence is sufficient;
- otherwise emit NEED_REPEAT or discard as NO_SIGN;
- record the reason code.

Never force the highest-scoring label merely because a timeout fired.

---

## 8. Duplicate suppression

Repeated output is a major live-demo failure.

Track:
- last committed label;
- commit timestamp;
- neutral-transition evidence;
- motion trajectory change;
- cooldown state.

A repeated label can be valid if the signer intentionally signs it twice. Therefore duplicate suppression MUST end after adequate neutral/new-unit evidence rather than banning the same label for a fixed long interval.

---

## 9. Unknown activity

The system must distinguish:
- no meaningful signing activity;
- supported signing;
- visually active but unsupported/unknown signing;
- insufficient tracking.

Do not map every active movement to the nearest vocabulary class.

For an unknown active sequence:
- abstain;
- optionally display “Sign not in current supported vocabulary”;
- preserve diagnostic top-k internally;
- do not use context to invent a supported sign.

---

## 10. Context and segmentation

Context MAY:
- help rerank already-supported candidate units;
- help decide whether an utterance appears incomplete in research-scale translation;
- improve phrase-level formatting after commits.

Context MUST NOT:
- manufacture missing visual units;
- override a strong boundary failure;
- turn random motion into a valid sentence.

---

## 11. Research path: adaptive streaming

Recent continuous sign-language translation research shows that arbitrary fixed token policies can fragment discourse and that temporal pauses can provide useful boundary evidence. SANKET AI should therefore preserve timestamp/inter-unit timing information in its architecture, even if the hackathon MVP uses simpler segmentation.

Research experiment candidates:
1. fixed inactivity threshold;
2. adaptive pause threshold using moving statistics;
3. learned temporal boundary head;
4. boundary head + linguistic readiness;
5. segment-aware tokenization.

Do not adopt a research method merely because it improves another sign language/dataset; reproduce it on appropriate ISL data before making an ISL performance claim.

---

## 12. Timestamp contract

Every processed feature window/event SHOULD carry monotonic timing:

```json
{
  "frame_seq": 1842,
  "capture_ts_ms": 81342.7,
  "feature_ts_ms": 81358.1,
  "prediction_ts_ms": 81410.3
}
```

Every committed unit SHOULD include:
- segment start;
- segment end;
- commit time;
- end-to-end latency;
- boundary reason;
- model version.

This enables streaming evaluation rather than only offline clip accuracy.

---

## 13. WebSocket event contract

Recommended event types:

```
tracking
stream_state
provisional_prediction
boundary_candidate
accepted
need_repeat
unsupported
reset
stats
```

Example committed event:

```json
{
  "type": "accepted",
  "segment_id": "seg_0042",
  "label": "doctor",
  "display_text": "Doctor",
  "confidence": 0.91,
  "segment_start_ms": 80412,
  "segment_end_ms": 81380,
  "commit_ms": 81462,
  "boundary_reason": "motion_pause+stable_candidate",
  "domain": "hospital",
  "model_version": "demo-v1"
}
```

---

## 14. Streaming metrics

Offline clip accuracy alone is insufficient.

Measure:
- false activations per minute;
- missed supported units;
- duplicate emissions;
- boundary precision/recall when annotated boundaries exist;
- start-boundary error in milliseconds;
- end-boundary error in milliseconds;
- commit latency after true unit end;
- NEED_REPEAT rate;
- unsupported/unknown rejection rate;
- transcript edit rate if provisional text is shown;
- end-to-end P50/P95 latency.

For research-scale translation, additionally consider sentence-boundary quality and translation metrics appropriate to the task.

---

## 15. Test stream library

Create deterministic streams containing:

### S1 — neutral only
At least several minutes of:
- resting;
- typing;
- looking away;
- adjusting clothing;
- ordinary non-sign movements.

Expected: near-zero false accepted signs.

### S2 — single supported sign
Neutral -> sign -> neutral.

Expected: exactly one accepted unit.

### S3 — same sign twice
Sign -> real neutral transition -> same sign.

Expected: exactly two accepted units.

### S4 — two different signs
Sign A -> transition -> Sign B.

Expected: ordered A, B.

### S5 — unsupported movement
Meaningful movement not in vocabulary.

Expected: abstention/unsupported, not nearest-class acceptance.

### S6 — interrupted sign
Begin supported sign, leave frame, return.

Expected: TRACKING_LOST/NEED_REPEAT unless sufficient evidence remains.

### S7 — variable speed
Same supported sign performed slow/normal/fast within reasonable range.

Expected: segmentation remains usable.

### S8 — short inter-sign gap
Two signs with small transition.

Expected: no accidental fusion where MVP supports separate units.

### S9 — long pause mid-conversation
Expected: clean segment closure without application reset.

### S10 — low-confidence sequence
Expected: provisional candidate never becomes committed unless gate passes.

---

## 16. Demo acceptance criteria

Streaming mode is demo-ready only when:
- camera can remain running without manual “capture sign” button;
- neutral movement does not continuously emit labels;
- supported sign produces one commit;
- held sign does not spam transcript;
- repeated intentional sign can still be emitted twice;
- low-confidence sequence abstains;
- tracking loss is visible;
- transcript contains committed output only;
- TTS speaks committed output only;
- measured commit latency is shown;
- Demo Replay can reproduce at least S1–S6.

---

## 17. Hackathon implementation order

### P0
- pre-roll ring buffer;
- activity gate;
- rolling inference;
- stability;
- commit gate;
- duplicate suppression;
- cooldown/neutral transition;
- committed transcript.

### P1
- unsupported/unknown activity state;
- annotated streaming test suite;
- boundary timing metrics;
- adaptive pause threshold.

### P2 / research
- learned boundary detector;
- sentence-level incremental translation;
- linguistic readiness estimator;
- segment-aware visual tokenization.

Do not let P2 destabilize P0.

---

## 18. Evidence ledger

### Temporal-Linguistic Adaptive Streaming for Continuous Sign Language Translation — ALVR 2026
The work studies incremental continuous sign-language translation and reports that temporal pauses can help detect discourse/sentence boundaries; it proposes adaptive temporal/linguistic streaming rather than treating incoming glosses as a flat stream.

Source:
https://aclanthology.org/2026.alvr-main.21/

Use in SANKET AI:
- motivates preserving timing and evaluating autonomous boundaries;
- informs a research-stage adaptive pause experiment.

Limitation:
- its reported results are not ISL-specific evidence and MUST NOT be quoted as SANKET AI performance.

### SAGE: Segment-Aware Gloss-Free Encoding for Token-Efficient Sign Language Translation — ICCV Workshops 2025
This work explores segment-aware visual tokenization for continuous translation and reports reduced sequence length/memory in its evaluated setting.

Source:
https://openaccess.thecvf.com/content/ICCV2025W/MSLR/html/Low_SAGE_Segment-Aware_Gloss-Free_Encoding_for_Token-Efficient_Sign_Language_Translation_ICCVW_2025_paper.html

Use in SANKET AI:
- supports researching explicit temporal segmentation and efficient segment-level representations.

Limitation:
- not evidence that the same gains will occur on ISL.

### WSLP 2025 overview
The first WSLP workshop established public ISL shared-task leaderboards for sentence-level ISL-to-English translation, isolated recognition and word-presence prediction, reinforcing that these are distinct tasks requiring distinct claims/evaluation.

Source:
https://aclanthology.org/2025.wslp-main.1/

Use in SANKET AI:
- reinforces strict terminology between isolated recognition and sentence-level translation.

---

## 19. Final rule

**A continuously open camera is not the same thing as continuous sign-language understanding.**

Any SANKET AI implementation or pitch that uses “continuous” MUST identify which streaming capability is actually implemented and show the corresponding boundary/latency evaluation.
