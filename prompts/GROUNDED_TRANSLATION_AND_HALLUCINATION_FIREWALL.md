# SANKET AI — Grounded Translation and Hallucination Firewall

## Purpose

SANKET AI must never turn weak visual evidence into fluent but unsupported language. Fluency is not evidence. User-visible meaning must be traceable to recognized signing, explicit user input, or a verified deterministic mapping.

## 1. Capability levels

Every build declares one level:
- **T0:** finite isolated sign/phrase recognition.
- **T1:** streaming finite-vocabulary recognition with temporal segmentation.
- **T2:** constrained phrase translation from accepted recognized evidence.
- **T3:** research continuous translation evaluated on held-out continuous data.
- **T4:** deployment-grade continuous translation with community validation, shift testing and operational monitoring.

Do not describe T0–T2 as unrestricted continuous ISL translation.

## 2. Evidence ledger

Each committed utterance stores:
- utterance ID and time range;
- source mode;
- capability level;
- accepted recognized units;
- model version;
- confidence and tracking quality;
- context domain;
- normalization/paraphrase rule ID if used;
- final surface text;
- support status;
- abstention reason.

The final sentence must never be the only artifact retained for debugging.

## 3. Evidence boundary

Valid evidence:
- recognized manual signs;
- non-manual, pose and motion features used by the recognizer;
- temporal boundaries;
- approved domain vocabulary;
- explicit typed/speech input;
- verified phrase mappings.

Not evidence:
- an LLM's world knowledge;
- a plausible continuation of conversation;
- language-model probability;
- expected demo script;
- inferred personal attributes.

## 4. Context firewall

Context may:
- rerank visually supported candidates;
- resolve approved ambiguity when evidence is sufficiently close;
- select a verified domain-specific display label;
- choose a meaning-preserving surface paraphrase from an approved set.

Context must not:
- introduce unsupported entities or actions;
- turn UNKNOWN into a guessed sign;
- override tracking loss or abstention;
- silently replace weak evidence.

When context changes ranking, diagnostics retain pre-context top-k, post-context ranking and the responsible rule/model.

## 5. Optional language-model boundary

A language model is never a P0 recognition dependency.

If used, it receives only structured accepted evidence and performs bounded language tasks such as punctuation, approved paraphrasing or spoken-language rendering.

It must never:
- decide which sign occurred from unsupported evidence;
- convert an abstention into a translation;
- execute arbitrary actions;
- add unsupported semantic content.

For the hackathon, deterministic templates and reviewed paraphrases are preferred.

## 6. Semantic support checking

Where generative text is used, inspect meaningful atoms:
- entities;
- action;
- object;
- polarity/negation;
- quantity;
- location;
- time;
- urgency/modality.

Classify each as SUPPORTED, INFERRED_ALLOWED, UNSUPPORTED or UNKNOWN.

Meaning-changing unsupported atoms cause rejection or downgrade.

## 7. Negation and polarity

Negation errors can reverse meaning. Evaluation must include positive/negative and other polarity contrasts available in the supported vocabulary.

If the recognizer cannot reliably distinguish a required non-manual cue, that pair must not be presented as safely supported.

## 8. Entity preservation

Names, numbers, acronyms and technical terms must not be invented.

Fallback:
1. recognized lexical sign;
2. verified fingerspelling result;
3. explicit typed/speech entity;
4. UNKNOWN / request repetition or spelling.

Do not silently autocorrect a fingerspelled proper noun.

## 9. High-consequence contexts

In emergency, healthcare and public-service modes:
- use stricter unsupported-content rules;
- preserve raw accepted evidence beside normalized text;
- expose uncertainty;
- do not generate instructions unrelated to recognized evidence;
- do not imply external services were contacted unless an integration actually confirms it.

## 10. Hallucination taxonomy

Track:
- H1 insertion — unsupported concept added;
- H2 deletion — supported concept omitted;
- H3 substitution — concept replaced;
- H4 polarity — negation/modality changed;
- H5 entity — name/number/location changed;
- H6 temporal — time/order changed;
- H7 causal — unsupported cause/effect introduced;
- H8 context overreach — context/history overrides current evidence.

Severity:
- S0 cosmetic;
- S1 meaning-preserving;
- S2 meaning-changing;
- S3 high-consequence.

## 11. Translation evaluation

Do not rely on BLEU or ROUGE alone.

For generative translation experiments report:
- lexical metric(s) where useful;
- semantic metric(s);
- unsupported insertion rate;
- omission rate;
- entity preservation;
- polarity preservation;
- human/community review where feasible;
- latency;
- capability level;
- exact dataset and split.

Recent SLT evaluation research demonstrates limitations of text-overlap metrics under paraphrasing, hallucination and sentence-length variation. No single text metric is therefore a release gate.

## 12. Adversarial evaluation set

Include:
- meaning-preserving paraphrases;
- fluent output with one inserted entity;
- negation flip;
- number change;
- proper-name change;
- omitted critical term;
- ambiguous visual evidence plus strongly suggestive context;
- unsupported sign between supported signs;
- tracking loss mid-utterance;
- repeated sign;
- fingerspelling followed by lexical signing.

The evaluator must distinguish fluent-but-wrong output from valid paraphrase.

## 13. Small VLM research track

Small vision-language models may be benchmarked as research, not assumed to solve SANKET AI.

Experiment contract:
- freeze the existing baseline;
- use the same held-out split;
- report compute, memory and latency;
- report signer/environment slices;
- report hallucination, entity and polarity behavior;
- compare with the landmark-temporal baseline;
- do not replace a reliable baseline merely because generated text appears fluent.

ACL Findings 2026 work evaluating small VLMs for SLT, including an ISL dataset, reports that SLT remains challenging and highlights data imbalance. This motivates careful benchmarking rather than generic-VLM assumptions.

## 14. Transformation provenance

Each normalization/paraphrase rule stores:
- rule ID;
- input/output language;
- domain;
- reviewer/status;
- version;
- examples;
- deterministic vs generative status.

## 15. User corrections

When the user corrects output:
- retain original recognized evidence;
- store corrected text separately;
- never rewrite history to imply the model predicted the correction;
- do not automatically retrain production weights.

## 16. UI and diagnostics

Normal UI:
- accepted final text;
- visible NEED_REPEAT / UNKNOWN states.

Diagnostics:
- recognized units;
- confidence and tracking quality;
- context rerank;
- normalization path;
- model/version;
- support status.

Research/demo mode may show raw recognition beside normalized output and evidence trace.

## 17. API contract

A translation commit should include:
- event type;
- utterance ID;
- capability level;
- raw accepted units;
- surface text;
- support status;
- whether context was applied;
- normalization rule ID;
- warnings;
- model version;
- timestamp.

## 18. Release gates

A generative/context layer cannot enter the judge path unless:
- abstentions remain abstentions;
- entity and polarity tests pass;
- unsupported insertion is measured;
- original evidence is inspectable;
- the layer has a deterministic disable switch;
- core recognition works without it.

## 19. Judge defense

Truthful framing:
“SANKET AI separates visual recognition from language normalization. The language layer cannot invent evidence. When visual evidence is uncertain, the system abstains and requests repetition.”

## 20. Research basis

Retain these sources in the research ledger:
- Chowdhury & Sanyal, ACL Findings 2026, *Can Small Vision–Language Models Perform Sign Language Translation?* — https://aclanthology.org/2026.findings-acl.1609/
- Yazdani et al., LREC 2026, *A Critical Study of Automatic Evaluation in Sign Language Translation* — https://aclanthology.org/2026.lrec-1.749/
- ISLRTC, Government of India — https://islrtc.nic.in/

They inform research and evaluation design; they do not establish SANKET AI performance.

## 21. Acceptance tests

- [ ] Weak visual evidence plus strong context does not produce unsupported confident text.
- [ ] UNKNOWN cannot be converted into a guessed lexical sign by the language layer.
- [ ] Proper nouns are preserved or explicitly unresolved.
- [ ] Negation-flip cases are included in evaluation.
- [ ] High-consequence unsupported insertions are counted separately.
- [ ] Committed text is traceable to recognized evidence.
- [ ] Disabling language normalization leaves recognition functional.
- [ ] BLEU/ROUGE are never presented alone as proof of translation quality.
- [ ] UI and pitch state the actual T0–T4 capability level.
