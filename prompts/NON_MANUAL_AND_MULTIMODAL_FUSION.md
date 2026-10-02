# SANKET AI — Non-Manual Signals and Motion-Aware Multimodal Fusion

## Purpose

SANKET AI explicitly promises **hands + face + body + motion + context**. This document turns “face/body/motion” from a marketing phrase into a testable engineering contract.

A sign-language recognizer must not assume that the hands alone contain every linguistically relevant cue. Sign-language research has repeatedly documented non-manual articulators such as head movement, eyebrows, eye blinks, mouth shapes and body movement as meaningful signals. Recent 2026 work also demonstrates that computer-vision landmark outputs can be processed as interpretable kinematic measurements for non-manual articulators.

This does **not** mean every supported ISL sign requires every facial feature. The implementation must measure whether each modality helps and must degrade safely when a modality is missing.

---

## 1. Modalities

The perception layer exposes four independent evidence streams:

### M1 — Hands
Per hand:
- 21 landmarks,
- x/y/z where available,
- handedness,
- presence/confidence,
- wrist-relative coordinates,
- joint-angle features where useful,
- first-order temporal deltas.

### M2 — Upper body
Selected landmarks:
- nose/head reference,
- shoulders,
- elbows,
- wrists,
- hips if stable.

Derived:
- shoulder width,
- torso orientation,
- elbow angles,
- wrist-to-shoulder position,
- head/torso displacement.

### M3 — Non-manual face/head
Prefer compact, privacy-minimizing features over raw face imagery.

Candidate features:
- eyebrow movement,
- eye closure/blink signals,
- mouth/jaw shape coefficients,
- head yaw/pitch/roll,
- head translation relative to shoulders,
- selected face blendshapes.

Do not infer identity, emotion, disability, age, gender, ethnicity or medical state.

### M4 — Motion
For each relevant landmark/feature:
- velocity,
- acceleration only if stable,
- direction,
- path length,
- temporal phase,
- movement onset/offset.

Motion must be computed from time-aligned observations rather than frame order assumptions.

---

## 2. Timestamp discipline

Every frame/feature packet must include:
- capture timestamp,
- sequence number,
- source FPS estimate.

Temporal deltas should use actual elapsed time when possible.

If frames are dropped:
- do not pretend sampling remained uniform;
- interpolate only when justified;
- preserve a missing-frame/mask signal.

---

## 3. Coordinate normalization

Normalize spatial features before fusion.

Recommended hierarchy:
1. stable torso/body origin;
2. shoulder-width or torso-scale normalization;
3. hand-local coordinates for fine articulation;
4. preserve global hand location relative to face/torso.

Do not normalize away linguistically meaningful location.

Example:
- wrist-local handshape captures finger configuration;
- body-relative wrist location captures whether the sign occurs near head/chest/space.

Both can matter.

---

## 4. Mirroring and handedness

Webcam preview may be mirrored for user comfort.

Inference representation must have an explicit policy:
- display mirror is UI-only;
- model handedness follows training schema;
- feature metadata records whether transformation occurred.

Create a unit test using an asymmetric sample to ensure a mirrored preview does not silently swap semantic left/right features.

---

## 5. Non-manual kinematics

For selected face/head signals, calculate temporal descriptors such as:
- displacement from neutral baseline,
- velocity,
- peak magnitude,
- onset time,
- offset time,
- duration.

Neutral baseline may be estimated:
- at session calibration,
- from recent no-sign frames,
- or from normalized blendshape values.

Never require a long biometric calibration procedure for the hackathon demo.

---

## 6. Multimodal fusion strategies

### Baseline A — Early fusion
Concatenate normalized hand, body, non-manual and motion features per timestep.

Pros:
- simple,
- fast,
- easy to debug.

Cons:
- one noisy modality can dominate;
- dimensional imbalance.

Use this first.

### Baseline B — Modality encoders
Separate encoders:
- hand encoder,
- pose encoder,
- non-manual encoder,
- motion encoder.

Then fuse latent representations before temporal classification.

Pros:
- ablation-friendly;
- missing modality handling;
- modality-specific capacity.

### Stretch C — Gated fusion
Learn or compute modality reliability gates.

Example:
```
z = g_hand*z_hand + g_pose*z_pose + g_face*z_face + g_motion*z_motion
```

Gates must depend on signal quality/presence, not hidden demographic inference.

---

## 7. Missing-modality behavior

Each modality has:
- presence mask,
- quality score,
- freshness/timestamp.

If face is missing but hands are strong:
- model may continue for signs validated to work without face;
- confidence should reflect training/evaluation behavior.

If a required modality is missing:
- NEED_REPEAT or TRACKING_LOST.

Never fill missing face/body evidence with a plausible fabricated value.

---

## 8. Modality requirement metadata

Each supported class/phrase may optionally declare:

```json
{
  "label": "example",
  "modalities": {
    "hands": "required",
    "pose": "helpful",
    "non_manual": "required",
    "motion": "required"
  }
}
```

Values:
- required,
- helpful,
- optional.

This metadata must come from linguistic validation/empirical evidence, not guesses.

For the MVP, if class-specific metadata is unavailable, use global quality gating and document the limitation.

---

## 9. Ablation experiments

The project must measure whether multimodality actually helps.

Train/evaluate comparable configurations:

A. hands only  
B. hands + pose  
C. hands + motion  
D. hands + pose + motion  
E. hands + pose + motion + non-manual

Keep:
- same split,
- same labels,
- comparable training budget,
- same metric definitions.

Report:
- macro F1,
- top-1,
- top-k,
- per-class recall,
- confusion changes,
- latency,
- feature dimensionality.

Do not claim “multimodal improves accuracy” unless the experiment demonstrates it.

---

## 10. Motion-aware experiment

Recent ISL research specifically explores motion-aware modeling, so SANKET AI should include a controlled experiment rather than only appending raw coordinates.

Candidate motion representation:
```
v_t = (x_t - x_(t-1)) / dt
```

Optional:
- normalized velocity magnitude,
- signed direction,
- short-window displacement.

Compare:
- positions only,
- positions + velocity.

Reject motion features if noise degrades held-out performance.

---

## 11. Lightweight temporal baseline

Recent 2025 ISL work demonstrates a MediaPipe-Holistic + Temporal Convolutional Network approach as a lightweight isolated-word baseline on a large-class ISL task.

Therefore include TCN as a required benchmark candidate alongside GRU/LSTM and compact Transformer.

Benchmark:
- accuracy/F1,
- parameters,
- CPU latency,
- memory,
- export compatibility.

Model selection for the hackathon should optimize **reliable end-to-end performance**, not paper novelty.

---

## 12. Face privacy boundary

Default runtime should transmit/store the minimum representation necessary.

Preferred progression:
1. extract face/non-manual features locally;
2. send compact feature vector if server inference is required;
3. do not persist raw face frames.

Diagnostics may show landmark overlays on the live frame but must not automatically save them.

---

## 13. Non-manual UI diagnostics

Signal Health should expose:
- Left hand: Good / Weak / Missing
- Right hand: Good / Weak / Missing
- Pose: Good / Weak / Missing
- Non-manual: Good / Weak / Missing
- Motion: Active / Neutral / Uncertain

Do not label the face channel “emotion”.

---

## 14. Context boundary

Context is downstream of perceptual evidence.

Correct:
```
multimodal evidence -> top-k candidates -> context reranking -> confidence gate
```

Forbidden:
```
weak visual evidence -> domain/LLM guesses likely sentence -> ACCEPTED
```

Store both raw and context-adjusted scores for auditability.

---

## 15. Dataset annotation extensions

When collecting SANKET data, optionally annotate:
- non-manual relevance,
- motion direction,
- one/two-handed,
- approximate sign duration,
- occlusion,
- tracking quality.

These are research annotations, not mandatory for every hackathon sample.

---

## 16. Test matrix

### Functional
- both hands visible;
- one hand temporarily occluded;
- face leaves frame;
- torso partly cropped;
- head movement present;
- static handshape;
- dynamic sign;
- rapid motion;
- neutral/no-sign.

### Temporal
- 5 FPS degraded stream;
- 10 FPS;
- 15 FPS;
- dropped frames;
- irregular timestamps.

### Environmental
- bright front light;
- backlight;
- cluttered background;
- different clothing;
- seated vs standing where sign remains valid.

### Mirroring
- preview mirrored;
- preview unmirrored;
- inference result remains consistent according to schema.

---

## 17. Acceptance criteria

The multimodal claim is demo-ready only if:

- [ ] hands, pose and non-manual features are actually extracted;
- [ ] motion is computed across time;
- [ ] each stream has presence/quality metadata;
- [ ] missing streams cannot create NaN or fabricated evidence;
- [ ] mirror/handedness policy is tested;
- [ ] at least one ablation comparison is generated;
- [ ] UI shows multimodal signal health;
- [ ] face channel is never presented as emotion recognition;
- [ ] raw face video is not stored by default;
- [ ] model/version package records the exact feature schema.

---

## 18. Evidence and research basis

### Non-manual markers
Imashev et al., CoNLL 2020, “A Dataset for Linguistic Understanding, Visual Evaluation, and Recognition of Sign Languages: The K-RSL.” The paper emphasizes that sign languages use facial expressions and head/body position and movement in addition to manual gestures, and studies non-manual components.

https://aclanthology.org/2020.conll-1.51/

### Non-manual kinematics
Bulla & Kimmelman, SignLang/LREC 2026, “Processing Kinematics of Nonmanual Markers in R.” The work describes processing computer-vision facial/body landmarks and head rotation into interpretable kinematic measurements for non-manual articulators.

https://aclanthology.org/2026.signlang-1.7/

### ISL temporal landmark baseline
Reddy & Kamakshi, WSLP 2025, “Pose-Based Temporal Convolutional Networks for Isolated Indian Sign Language Word Recognition.” The work uses MediaPipe Holistic landmark sequences with a TCN and reports benchmarks on the WSLP-AACL-2025 ISL task.

https://aclanthology.org/2025.wslp-main.8/

### ISL motion-aware modeling
Chowdhury & Sanyal, WSLP 2025, “Enhancing Indian Sign Language Translation via Motion-Aware Modeling.”

https://aclanthology.org/2025.wslp-main.7/

## 19. Claims discipline

Allowed:
- “SANKET AI’s architecture explicitly models manual, non-manual, body and temporal evidence.”
- “We evaluated whether additional modalities improve our held-out demo dataset.”
- “Our current model uses these exact modalities: …”

Not allowed without measured evidence:
- “Facial features increase accuracy by X%.”
- “Every ISL sign needs facial expression.”
- “Our multimodal model solves continuous ISL.”
- “The system understands emotion.”
