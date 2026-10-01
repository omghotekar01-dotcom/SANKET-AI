# SANKET AI — Dataset Provenance and Evaluation Governance

This specification keeps linguistic references, model-training data, evaluation data, reverse-output media, and demo assets traceable. It also prevents misleading evaluation caused by signer/session leakage.

## 1. Dataset registry

Maintain `data/metadata/dataset_registry.yaml`.

For every source record:
- stable dataset ID and version;
- canonical paper/source URL;
- source type: first-party, official reference, research dataset, demo asset;
- date retrieved;
- documented license/terms URL;
- attribution requirements;
- whether research, training, evaluation, redistribution, public demo, and commercial use are allowed, prohibited, unknown, or require review;
- signer/sample counts only when actually documented;
- annotation type;
- notes and known limitations.

If permission is unclear, record `unknown` or `review_required`. Never infer permission from public availability.

## 2. Separate asset classes

Treat these independently:

### Linguistic/reference sources
Used to understand or validate a sign. Reference access does not automatically grant permission to redistribute its video.

### Training data
Consumed by model optimization.

### Evaluation data
Reserved for measurement.

### Reverse-output media
Videos/clips shown by text or speech → ISL. These require display/bundling permission independent of model-training permission.

### Demo replay assets
Prefer consented first-party recordings.

### Derived features
Landmarks/embeddings still retain provenance and may remain subject to source terms/privacy expectations.

## 3. ISLRTC dictionary boundary

The current official ISLRTC FAQ states that its ISL Dictionary contains 10,000 terms, includes regional variants and several domain categories, and may be used for research, teaching, and development of ISL-related technology under stated conditions including acknowledgement and restrictions on resale/profiteering.

Canonical source:
https://islrtc.nic.in/faq/

Engineering rules:
- treat ISLRTC as a reference source by default;
- preserve required acknowledgement;
- do not describe 10,000 dictionary terms as SANKET AI's recognized vocabulary;
- do not assume one English/Hindi word maps one-to-one to an ISL sign;
- preserve documented variants/synonyms and concept distinctions;
- do not bundle or commercialize source media unless the applicable terms clearly permit the intended use;
- re-check terms before commercial deployment.

The FAQ itself documents synonyms, homonyms, regional signs, and concepts for which direct word-to-sign mapping is insufficient. This is a product requirement, not trivia.

## 4. External dataset intake gate

Before an external dataset becomes an active dependency, document:
- canonical publication;
- canonical dataset page;
- distributor/owner;
- actual published terms;
- whether access is gated;
- redistribution conditions;
- commercial-use status;
- attribution;
- participant/consent limitations if documented;
- sign language and region;
- isolated vs continuous vs fingerspelling vs translation task;
- annotation type;
- availability of signer IDs.

A paper being downloadable is not evidence that all associated data may be redistributed or commercialized.

## 5. Dataset cards

Create `docs/datasets/<dataset-id>.md` containing:
- citation;
- purpose;
- language;
- documented signer population;
- sample count;
- annotations;
- recording conditions;
- known biases;
- access/license terms;
- allowed SANKET AI uses;
- unclear/prohibited uses;
- preprocessing;
- split policy;
- model versions trained from it;
- required attribution.

## 6. First-party collection

Before recording:
- explain what is collected;
- state whether raw video is retained;
- state intended demo/research use;
- assign a pseudonymous signer ID;
- allow recording to stop.

Capture:
- signer ID;
- label/phrase ID;
- take/session ID;
- device;
- environment category;
- FPS/resolution;
- feature schema;
- consent status;
- raw-video retention flag.

After recording:
- verify label and consent metadata;
- remove unrelated footage;
- keep raw media outside git;
- record retention/deletion choice.

Do not infer demographic attributes from appearance.

## 7. Named evaluation regimes

### E0 — same-distribution diagnostic
Disjoint clips but may include familiar signers. Debugging only.

### E1 — signer-independent
No signer identity overlaps train and test. This is the primary prototype generalization test.

### E2 — session/environment shift
Different capture session, lighting, background, distance, or device.

### E3 — unseen signer + environment shift
Combines signer isolation and changed conditions.

### E4 — unknown/OOD
Unsupported signs, casual gestures, partial signs, occlusion, unrelated movement, degraded tracking. Used to test abstention and false activation.

### E5 — continuous stream
Long stream containing supported signs, transitions, neutral periods, repeated signs, and unsupported motion. Used to test segmentation and duplicate/false emissions.

Do not present E0 alone as evidence of real-world generalization.

## 8. Unseen-sequence evaluation

When SANKET AI progresses to continuous phrase/sentence recognition:
- keep exact target sequences disjoint where feasible;
- separately report signer-independent and unseen-sequence results;
- do not claim compositional generalization if test sentences repeat training sentences.

Methodological reference:
Isharah (2025) defines signer-independent and unseen-sentence continuous sign recognition benchmarks:
https://arxiv.org/abs/2506.03615

This is methodological inspiration only; it is not an ISL training source.

## 9. ISL fingerspelling evidence

The WSLP 2025 paper “Continuous Fingerspelling Dataset for Indian Sign Language” reports 1,308 segments from 499 videos, 70.85 minutes, and 14,814 characters, with interpreter validation on a subset and a sequence-recognition baseline.

Canonical source:
https://aclanthology.org/2025.wslp-main.6/

Rules:
- verify actual dataset distribution/license before use;
- do not infer commercial rights from paper availability;
- evaluate continuous fingerspelling with Character Error Rate and sequence-level metrics, not isolated-letter accuracy alone;
- keep fingerspelling evaluation separate from lexical sign recognition.

## 10. Evaluation manifest

Every demo/published metric must be reproducible from a manifest recording:
- evaluation ID;
- model version;
- dataset versions;
- feature schema;
- split regime;
- class list;
- confidence-threshold config;
- git commit;
- device/runtime;
- timestamp.

The reporting code must not label a result “signer-independent” unless split metadata proves signer disjointness.

## 11. Metric bundles

For finite vocabulary report together:
- class count;
- sample count;
- signer count;
- split regime;
- macro F1;
- per-class recall;
- confusion matrix;
- top-1 and optional top-k accuracy.

For confidence-aware/selective recognition:
- coverage;
- accepted-prediction error;
- abstention/repeat rate;
- false activation;
- risk–coverage curve when practical.

For live streams:
- false emissions;
- duplicate emissions;
- missed supported signs;
- end-to-end latency;
- stream duration;
- segmentation errors.

For fingerspelling:
- Character Error Rate;
- exact sequence match where meaningful;
- insertion/deletion/substitution breakdown.

Never compress these into one universal “accuracy”.

## 12. Cross-signer analysis

For E1/E3:
- compute per-signer metrics;
- inspect the worst-performing signer;
- inspect class × signer confusions;
- compare tracking quality;
- identify whether failures arise from model, detector, framing, or coverage.

Do not claim demographic fairness without appropriate, consented, reliable demographic labels and a study designed for that question. Use “cross-signer robustness” when that is what was measured.

## 13. Regional variation

The official ISLRTC FAQ explicitly notes regional signs.

Therefore:
- a concept may have multiple verified variants;
- store `concept_id`, `variant_id`, source, and documented region where known;
- do not mark a legitimate variant wrong merely because training used another;
- state which variants the demo model supports.

## 14. Leakage checks

Before training, automatically detect:
- duplicate hashes across splits;
- clips from the same source recording across train/test;
- signer overlap in E1/E3;
- near-duplicate sequences;
- augmented copies of test data in train;
- frames from one source video divided across partitions.

A declared signer-independent run must fail validation if signer overlap is detected.

## 15. Model lineage

Every deployed model package should contain a model card and machine-readable lineage:
- parent checkpoint;
- datasets/versions;
- training commit;
- preprocessing version;
- feature schema;
- hyperparameters/config;
- evaluation IDs;
- export/quantization steps;
- known limitations.

Exported or quantized models inherit the provenance restrictions of their training sources.

## 16. Reverse-output registry

Every clip used for text/speech → ISL records:
- clip ID;
- concept/phrase;
- source/signer;
- permission/license;
- attribution;
- variant;
- whether bundling, public demo, redistribution, and commercial use are allowed.

If bundling permission is unclear, do not ship a clip merely because it can be viewed online.

## 17. Research-to-product firewall

Give each external resource one or more statuses:
- `REFERENCE_ONLY`
- `EXPERIMENT_APPROVED`
- `DEMO_APPROVED`
- `REDISTRIBUTION_APPROVED`
- `COMMERCIAL_REVIEW_REQUIRED`

This prevents “we found a dataset” from silently becoming “we may ship it”.

## 18. Acceptance tests

- [ ] Every active dataset has registry metadata.
- [ ] Every external source has a canonical citation/URL.
- [ ] Unknown permissions are explicitly unknown.
- [ ] First-party samples carry consent metadata.
- [ ] Raw video stays outside git.
- [ ] E1 has no signer overlap.
- [ ] Leakage checker passes.
- [ ] Evaluation reports identify model, data, commit, and split.
- [ ] Regional variants are represented explicitly.
- [ ] Reverse-output clips have separate media permissions.
- [ ] Model cards contain training-data provenance.
- [ ] Commercial-readiness claims are blocked when source terms require review.

## 19. Judge-safe explanation

“We keep linguistic references, training data, evaluation data, and sign-output media as separate provenance classes. Our metrics identify the exact model and split, and our main robustness evaluation separates test signers from training where feasible. We also do not assume that a publicly viewable sign video or research paper automatically grants redistribution or commercial rights.”

## 20. Production gate

Before monetized deployment:
1. re-audit dataset/media terms;
2. replace research-only or unclear assets where necessary;
3. obtain appropriate legal review;
4. validate regional/semantic variants with qualified community/domain expertise;
5. expand signer/environment diversity;
6. run production privacy/security review;
7. publish updated model/data cards.

Hackathon feasibility and commercial data rights are separate questions.
