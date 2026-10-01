# SANKET AI — Uncertainty, Abstention and Evaluation Contract

## Purpose

SANKET AI must be designed to **know when not to translate**. A communication aid that always emits a label can convert poor tracking, an unsupported sign, signer shift, occlusion, or ambiguous motion into a confident but incorrect message.

This specification turns the existing `NEED_REPEAT` idea into an auditable selective-prediction subsystem with measurable acceptance/rejection behavior.

---

## 1. Terminology

Keep these concepts separate:

- **model score** — raw logits or model-specific score;
- **probability estimate** — normalized output such as softmax;
- **calibrated confidence** — score transformed/tuned against held-out calibration data;
- **tracking quality** — quality/completeness of multimodal landmark evidence;
- **prediction stability** — consistency across adjacent temporal windows;
- **candidate margin** — separation between top candidates;
- **coverage** — fraction of eligible inputs for which the system chooses to emit a translation;
- **selective risk** — error rate among the predictions the system accepts;
- **abstention** — deliberate refusal to commit to a translation;
- **unsupported / OOD-like input** — input outside the tested vocabulary/distribution; this is not automatically equivalent to low confidence.

Do not call raw softmax “certainty”.

---

## 2. User-visible decision states

The decision layer must output one of:

```
ACCEPTED
NEED_REPEAT
NO_SIGN
TRACKING_LOST
UNSUPPORTED
COLLECTING
```

Optional internal states:

```
AMBIGUOUS
LOW_CONFIDENCE
UNSTABLE
OUT_OF_DOMAIN_SUSPECTED
MODEL_UNAVAILABLE
```

Internal reasons may map to a simpler accessible user message.

### ACCEPTED
Requirements:
- sufficient tracking;
- sufficient temporal evidence;
- confidence above validated threshold;
- candidate margin acceptable;
- prediction stable;
- no hard policy rejection.

### NEED_REPEAT
Use when evidence plausibly contains a supported sign but the system cannot safely choose a meaning.

### UNSUPPORTED
Use only when the implementation has a defensible mechanism or explicit vocabulary mismatch. Do not pretend a closed-set classifier can perfectly detect every unknown sign.

### TRACKING_LOST
Use when the perception layer itself is insufficient.

### NO_SIGN
Use for neutral/background/non-sign activity, not as a synonym for “unknown”.

---

## 3. Decision record

Every completed recognition attempt should be representable as:

```json
{
  "attempt_id": "uuid",
  "timestamp": "ISO-8601",
  "state": "ACCEPTED",
  "raw_top_k": [
    {"label": "doctor", "score": 4.81},
    {"label": "help", "score": 2.11}
  ],
  "calibrated_top_k": [
    {"label": "doctor", "confidence": 0.88},
    {"label": "help", "confidence": 0.08}
  ],
  "tracking_quality": 0.94,
  "stability": 0.91,
  "top1_top2_margin": 0.80,
  "activity_score": 0.73,
  "domain": "hospital",
  "context_adjustment_applied": true,
  "reason_codes": ["CONFIDENCE_OK", "TRACKING_OK", "STABLE"],
  "model_version": "string",
  "feature_schema": "string",
  "latency_ms": 0
}
```

Numbers above are schema examples only, not project performance claims.

---

## 4. Baseline selective decision rule

Start with a transparent rule before complex uncertainty models:

```python
if tracking_quality < tracking_threshold:
    return TRACKING_LOST

if activity_score < activity_threshold:
    return NO_SIGN

if frames_available < minimum_temporal_evidence:
    return COLLECTING

if calibrated_confidence < accept_threshold:
    return NEED_REPEAT

if top1_top2_margin < margin_threshold:
    return NEED_REPEAT

if stability < stability_threshold:
    return NEED_REPEAT

return ACCEPTED
```

Thresholds must be selected from validation/calibration data and stored with the model artifact.

Do not tune thresholds by repeatedly trying the final test set or only the planned judge gestures.

---

## 5. Calibration protocol

Recommended first-line approach:
1. train model on training split;
2. choose checkpoint using validation split;
3. reserve calibration data or a clearly defined validation subset;
4. fit temperature scaling or another simple calibration method;
5. freeze calibration parameters;
6. evaluate once on held-out test signers.

Store:
- calibration method;
- calibration split IDs;
- temperature/parameters;
- threshold;
- timestamp;
- model hash/version.

If data volume is too small for a separate calibration set, document the compromise explicitly.

---

## 6. Risk–coverage evaluation

Accuracy alone is insufficient for a system that can abstain.

Generate a threshold sweep and report:
- coverage;
- accepted-sample accuracy;
- accepted-sample macro F1 where meaningful;
- selective risk;
- abstention rate;
- false-accept count;
- false-reject count.

Plot:
- risk vs coverage;
- accuracy vs coverage;
- threshold vs coverage.

The target is not “abstain as much as possible”. The target is a useful communication system with a defensible error/coverage tradeoff.

---

## 7. Calibration evaluation

Where sample size permits, report:
- reliability diagram;
- expected calibration error (ECE), with binning method documented;
- negative log likelihood or Brier score where appropriate;
- before/after calibration comparison.

Calibration metrics can themselves be unstable on small datasets. Always publish sample count and binning/configuration.

---

## 8. Signer shift and environmental shift

Evaluate abstention under controlled shifts:

### Signer shift
- held-out signer;
- different dominant hand where valid;
- different signing speed;
- different body proportions.

### Visual shift
- bright vs dim;
- plain vs cluttered background;
- different camera distance;
- partial crop;
- mild motion blur.

### Tracking shift
- one hand briefly missing;
- face landmarks unavailable;
- pose degraded;
- hand overlap.

For each shift, measure whether:
1. recognition degrades;
2. confidence changes appropriately;
3. abstention increases when evidence worsens.

A model whose accuracy collapses while confidence remains high is not demo-ready for self-correction claims.

---

## 9. Hard-negative evaluation

Create a dedicated hard-negative set containing:
- non-sign hand movement;
- touching face/hair;
- typing;
- waving if not a target sign;
- gestures visually similar to supported signs;
- partial/incomplete target signs;
- transition movements;
- unsupported signs when ethically/licensably available.

Measure false accepts separately from ordinary classification errors.

---

## 10. Context safety

Context may rerank `top_k`, but the uncertainty layer must retain:
- pre-context candidates;
- post-context candidates;
- adjustment amount;
- final reason.

Context must not convert extremely weak visual evidence into a confident accepted sentence.

Implement a maximum context influence or other bounded policy.

If context changes top-1, record that event for evaluation.

---

## 11. Multimodal quality-aware abstention

Track modality health separately:

```
left_hand_quality
right_hand_quality
pose_quality
face_quality
motion_quality
```

For each sign/class, optionally maintain modality requirements:

```json
{
  "label": "example",
  "requires": {
    "left_hand": "optional",
    "right_hand": "required",
    "pose": "helpful",
    "face": "important"
  }
}
```

The decision layer can reject an attempt when a modality known to be important for that sign is unavailable.

Do not create class-specific rules without evidence or linguistic validation.

---

## 12. Temporal stability

Avoid accepting a one-window spike.

Possible stability signals:
- same top-1 for N recent windows;
- exponentially smoothed class probability;
- low prediction entropy variation;
- agreement between overlapping windows.

The chosen strategy must be benchmarked for both:
- false acceptance reduction;
- added latency.

---

## 13. Unknown/OOD handling

Closed-set confidence is not reliable proof of novelty detection.

Hackathon-safe hierarchy:
1. explicit background/no-sign class;
2. confidence/margin/stability rejection;
3. optional distance/energy/OOD score if validated;
4. `UNSUPPORTED` only when evidence supports that wording;
5. otherwise `NEED_REPEAT`.

Do not claim “detects every unknown ISL sign”.

Future research may benchmark:
- energy scores;
- embedding distance to class prototypes;
- deep ensembles;
- MC dropout;
- conformal prediction/prediction sets;
- dedicated open-set recognition.

These remain experimental until measured on SANKET AI data.

---

## 14. Conformal prediction research path

Conformal methods are worth evaluating because they can produce prediction sets under explicit assumptions rather than a single overconfident label.

Potential UI mapping:
- singleton prediction set → candidate for ACCEPTED;
- multiple plausible labels → NEED_REPEAT / alternatives;
- empty/invalid handling → reject.

Requirements before claiming conformal coverage:
- define exchangeability/data assumptions;
- use a proper calibration split;
- state target coverage;
- measure empirical coverage on held-out data;
- do not imply guarantees under arbitrary signer/domain distribution shift.

This is a research extension, not a mandatory 24-hour dependency.

---

## 15. Human correction loop

When user corrects an accepted prediction, store:
- attempt ID;
- original prediction;
- original confidence;
- corrected label if supplied;
- context;
- modality quality;
- model version.

Corrections are valuable for:
- hard-negative mining;
- calibration audit;
- confusion analysis;
- future retraining.

Never update production weights immediately from a single correction.

---

## 16. Evaluation data integrity

Every metric report must state:
- vocabulary/classes;
- sample counts;
- signer counts;
- train/validation/calibration/test split method;
- whether signers overlap;
- model version;
- feature schema;
- threshold/calibration version.

Do not combine clips from the same recording session across splits if that leaks near-duplicate information.

Sign-language dataset research has repeatedly highlighted dataset variability, imbalance and evaluation challenges; the project must expose these limitations rather than hide them.

---

## 17. Translation evaluation boundary

If SANKET AI later produces sentence-level translations, do not rely on one text-overlap metric alone.

At minimum separate:
- recognition/gloss correctness;
- semantic translation quality;
- hallucination/unsupported-content rate;
- human comprehensibility review where feasible.

Recent SLT evaluation research shows conventional lexical metrics can respond poorly to paraphrases and do not fully capture translation quality. Therefore BLEU/ROUGE-like metrics, if used, are supporting metrics rather than proof of usable sign-language translation.

---

## 18. Demo instrumentation

Diagnostics should expose:
- current decision state;
- calibrated confidence;
- top-3 candidates;
- tracking quality;
- stability;
- current threshold;
- latency;
- model version.

Judge presentation mode may simplify this to:
- prediction;
- confidence;
- ACCEPTED / PLEASE REPEAT;
- multimodal signal health.

Do not overwhelm the signer-facing product with research metrics.

---

## 19. Acceptance tests

### A. Clear supported sign
Expected: ACCEPTED repeatedly under normal conditions.

### B. Deliberately incomplete sign
Expected: NEED_REPEAT more often than false confident acceptance.

### C. Hands leave frame
Expected: TRACKING_LOST, not a semantic guess.

### D. Neutral movement
Expected: NO_SIGN.

### E. Visually similar class pair
Expected: calibrated decision; ambiguous cases can abstain.

### F. Held-out signer
Expected: report real performance and abstention; no hidden fallback.

### G. Low light / clutter
Expected: quality/confidence reflects degradation or system abstains.

### H. Wrong domain
Expected: visual evidence remains dominant; context does not invent output.

### I. Context changes top-1
Expected: event is logged and can be audited.

### J. Unsupported behavior
Expected: no claim of perfect unknown detection.

---

## 20. Metrics required for the “self-correcting” claim

Before pitching SANKET AI as confidence-aware/self-correcting, produce at least:
- held-out classification metrics;
- threshold used;
- coverage;
- accepted-prediction error rate;
- abstention/repeat rate;
- at least one controlled degraded-input test;
- examples of correct abstention;
- examples of remaining failure cases.

“Self-correcting” in the prototype means **detecting insufficient evidence, requesting repetition, using bounded context, and learning from reviewed feedback**. It does not mean autonomously knowing ground truth after every mistake.

---

## 21. Evidence basis

Relevant research/official scholarly sources to retain in the project research ledger:

1. **De Sisto et al., 2022 — “Challenges with Sign Language Datasets for Sign Language Recognition and Translation.”** LREC. Highlights dataset limitations and variability that make robust evaluation important.
   - https://aclanthology.org/2022.lrec-1.264/

2. **Holmes, Rushe & Ventresque, 2024 — “The Key Points: Using Feature Importance to Identify Shortcomings in Sign Language Recognition Models.”** LREC-COLING. Discusses keypoint-based SLR, unseen-signer motivation, variability, limited data and imbalance.
   - https://aclanthology.org/2024.lrec-main.1387/

3. **Yazdani et al., 2026 — “A Critical Study of Automatic Evaluation in Sign Language Translation.”** LREC 2026. Finds limitations in text-only SLT evaluation and motivates more holistic evaluation.
   - https://aclanthology.org/2026.lrec-1.749/

4. **CISLR: Corpus for Indian Sign Language Recognition**, EMNLP 2022, remains an important ISL-specific reference for recognition research.
   - https://aclanthology.org/2022.emnlp-main.707/

5. Conformal/selective prediction literature may inform future abstention experiments, but any statistical guarantee must be stated only under its actual assumptions and validated on the project’s data.

---

## 22. Implementation priority

### P0
- calibrated threshold;
- tracking-quality gate;
- stability gate;
- top-2 margin;
- NEED_REPEAT;
- risk/coverage report;
- hard-negative test.

### P1
- modality-specific quality;
- context-change audit;
- reliability diagram;
- correction logging.

### P2 / research
- conformal prediction sets;
- explicit open-set/OOD methods;
- ensembles;
- adaptive thresholds.

The P0 system must remain understandable enough that a judge can ask “Why did it reject this sign?” and the team can answer from logged evidence rather than hand-waving.
