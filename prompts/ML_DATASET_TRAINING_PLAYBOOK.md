# SANKET AI — ML, Dataset and Training Playbook

## 1. Goal

Build a reliable finite-vocabulary temporal ISL recognizer first, with architecture that can later expand toward continuous sentence translation.

## 2. Vocabulary selection

Choose signs that:
- are useful in real scenarios,
- differ enough to learn,
- include static and dynamic gestures,
- include one-hand and two-hand cases,
- include signs where face/body cues matter,
- support demo domains.

Suggested groups:
- social: hello, thank you, yes, no;
- medical: doctor, hospital, pain, medicine, water;
- emergency: help, fire, danger, accident, police, stop;
- education: teacher, student, repeat, understand;
- interaction: name, where, wait.

Validate actual sign forms using trustworthy ISL references.

## 3. Signer diversity

Minimum ideal:
- multiple signers,
- varied hand size,
- varied clothing,
- varied backgrounds,
- varied lighting,
- left/right dominant users where linguistically appropriate.

Never report generalization claims from one signer.

## 4. Data metadata

For every sample:
- sample ID,
- label,
- signer ID,
- capture session,
- timestamp,
- FPS,
- frame count,
- camera resolution,
- feature schema,
- environment tag,
- consent status,
- raw video path nullable,
- landmark path,
- notes.

## 5. Data splits

Preferred:
- signer-disjoint train/validation/test.

If dataset too small:
- leave-one-signer-out cross-validation;
- clearly document limitation.

Never randomly split adjacent clips from the same continuous recording into train/test.

## 6. Preprocessing

Steps:
1. decode/capture frame;
2. extract landmarks;
3. normalize translation;
4. normalize body scale;
5. preserve handedness;
6. add presence masks;
7. compute velocity/deltas;
8. resample sequence length if required;
9. store schema version.

## 7. Sequence normalization

Possible approaches:
- pad/truncate;
- temporal interpolation;
- variable-length RNN with mask;
- fixed 32/48/64 frame windows.

Benchmark rather than assuming one length.

## 8. Augmentation

Safe candidates:
- mild temporal speed change;
- temporal crop;
- small Gaussian coordinate noise;
- frame dropout/interpolation;
- scale jitter;
- translation jitter;
- limited landmark dropout.

Risky:
- horizontal flip,
- large rotations,
- synthetic face changes.

Only use transformations that preserve sign semantics.

## 9. Baseline models

Start with:
1. GRU/LSTM;
2. temporal CNN + GRU;
3. compact Transformer encoder.

Do not start with the heaviest architecture.

## 10. Input fusion

Option A:
- concatenate hand + pose + face + motion features.

Option B:
- separate encoders for hands/pose/face, then temporal fusion.

Hackathon baseline:
- concatenate normalized features with masks;
- compact temporal encoder;
- classifier head.

## 11. Losses

Baseline:
- cross-entropy classification.

For imbalance:
- class weighting or focal loss, only after checking class counts.

Continuous stretch:
- CTC or sequence-to-sequence objectives.

## 12. Training controls

Track:
- seed,
- config,
- dataset version,
- feature schema,
- optimizer,
- LR,
- epochs,
- batch size,
- early stopping,
- checkpoint metric.

Save best validation checkpoint, not final epoch blindly.

## 13. Metrics

For finite vocabulary:
- macro F1,
- weighted F1,
- top-1 accuracy,
- top-3 accuracy,
- per-class recall,
- confusion matrix.

For live decoder:
- false activation rate,
- duplicate emission rate,
- repeat-request rate,
- recognition latency,
- end-to-end latency.

## 14. Confidence calibration

Evaluate:
- reliability curve,
- expected calibration error if practical,
- temperature scaling,
- threshold sweep.

Choose threshold from validation set, not manually from demo examples.

## 15. No-sign/background

Capture explicit no-sign data:
- hands resting,
- moving into frame,
- adjusting hair/glasses,
- typing,
- random non-sign gestures,
- partial movement.

This is critical for live usability.

## 16. Hard negatives

Collect examples that confuse classes:
- visually similar signs,
- same start pose but different motion,
- similar handshape with different location,
- signs distinguished by non-manual cues.

Use confusion matrix to guide collection.

## 17. Model artifact package

Each deployed model must include:
- weights,
- label map,
- feature schema,
- normalization config,
- threshold config,
- training config,
- metrics report,
- dataset version,
- model version.

## 18. Reproducibility

Provide commands:
- collect,
- preprocess,
- train,
- evaluate,
- export,
- benchmark.

A teammate should be able to reproduce a model without opening a notebook manually.

## 19. ONNX export

After PyTorch model is stable:
- export ONNX;
- verify numerical parity;
- benchmark CPU;
- optionally quantize;
- verify accuracy does not materially regress.

## 20. Human review

Before demo:
- ISL-proficient reviewer validates supported sign labels/forms where possible;
- remove any sign whose meaning is uncertain.

## 21. Model card

Document:
- intended use,
- supported vocabulary,
- training data,
- signer count,
- known limitations,
- tested environments,
- metrics,
- privacy notes,
- out-of-scope uses.

## 22. Research-scale roadmap

Future:
- isolated-to-continuous transfer;
- gloss segmentation;
- CTC decoding;
- multimodal transformers;
- RGB + landmark fusion;
- signer adaptation;
- domain-conditioned translation;
- user personalization with consent;
- multilingual spoken-language rendering.

Do not market roadmap work as current capability.