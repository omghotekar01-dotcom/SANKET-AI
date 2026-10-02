# SANKET AI — Deaf/ISL Community Validation, Fairness and Deployment Protocol

## Purpose

SANKET AI must not define “success” only as a model score. A technically accurate recognizer can still be unusable, linguistically wrong, culturally inappropriate, inaccessible, or systematically weaker for particular signers, environments or regional variants.

This specification converts community participation, linguistic validation and fairness into engineering gates.

## 1. Core product rule

Do not treat Deaf/Hard-of-Hearing people, ISL signers or interpreters merely as data sources.

Where feasible, involve:
- proficient ISL signers,
- Deaf/Hard-of-Hearing users,
- qualified/proficient ISL interpreters,
- accessibility practitioners,
- domain users for hospital/classroom/public-service scenarios.

Feedback must be able to change:
- vocabulary,
- sign variants,
- UI,
- confidence thresholds,
- reverse-output clips,
- failure messages,
- deployment scope,
- roadmap priorities.

## 2. Evidence basis

Recent sign-language work strengthens this requirement:

- The WSLP 2025 overview explicitly frames sign-language processing as requiring researchers, linguists and Deaf-community participation and established public ISL benchmark tracks.
- A CVPR 2026 perspective on Indian Sign Language deployment identifies dialect-aware data, representative sampling, fairness, certified-interpreter involvement, multimodal annotation, affordable hardware and equitable evaluation as unresolved deployment requirements.
- A 2026 large-vocabulary sign-dictionary deployment in Flemish Sign Language reports development through an equal partnership between a Deaf-led sign-language centre and AI researchers, providing a useful product-development precedent even though it is not an ISL dataset/system.
- Sign2Vis (ACL Findings 2025) includes a user study and argues for accessible, user-centered tools for DHH users.

These sources justify process requirements; they do not prove SANKET AI itself is community-validated until SANKET AI performs and records such validation.

## 3. Terminology discipline

Documentation must distinguish:
- Indian Sign Language (ISL),
- spoken/written Indian languages,
- ASL and other sign languages,
- signer,
- Deaf/Hard-of-Hearing user,
- interpreter,
- fingerspelling,
- lexical sign,
- regional/sign variant.

Do not describe ISL as:
- signed English,
- universal sign language,
- a collection of gestures,
- a word-for-word encoding of spoken language.

## 4. Regional and signer variation

The data model must support variant metadata without declaring one variant universally “correct”.

Suggested vocabulary record:

```json
{
  "concept_id": "medical.doctor",
  "display_text": "Doctor",
  "sign_variants": [
    {
      "variant_id": "doctor.v1",
      "region": "unknown_or_documented",
      "source": "verified_reference",
      "review_status": "reviewed",
      "notes": ""
    }
  ]
}
```

Rules:
- never infer a signer’s region from video;
- never label a variant “wrong” solely because it differs from training data;
- unsupported variants should be recorded as coverage gaps;
- region metadata must come from documented source/participant metadata, not visual inference.

## 5. Community-review artifact

Create a structured review form or JSON/CSV export containing:
- reviewer role,
- consent to record feedback,
- build/model version,
- task,
- sign/phrase ID,
- whether interpretation was understandable,
- whether meaning was correct,
- whether reverse ISL output was natural/acceptable,
- whether UI message was respectful/clear,
- correction,
- optional free-text note.

Do not require unnecessary personal identity fields.

## 6. Usability tasks

Test actual communication tasks, not only “perform sign X”.

### Task A — first-time interpretation
A signer opens the product and communicates a supported concept without developer coaching.

Measure:
- task success,
- time to first successful interpretation,
- repeat requests,
- manual corrections,
- observed confusion.

### Task B — uncertainty recovery
Deliberately create ambiguous/partial signing.

Verify:
- NEED_REPEAT is understood,
- recovery instruction is actionable,
- user can retry without resetting the session.

### Task C — reverse communication
A non-signer types/speaks a supported phrase.

Verify:
- signer can understand the displayed ISL representation,
- fallback mode is visible,
- text/clip relationship is not misleading.

### Task D — emergency interface
User locates a high-priority message quickly.

Measure:
- time to target,
- mistaken activation,
- readability,
- ability to recover/cancel.

### Task E — call captions
Verify captions:
- are readable,
- do not cover hands/face,
- distinguish provisional and accepted output,
- recover after recognition failure.

## 7. User-study metrics

Quantitative candidates:
- task completion rate,
- median task time,
- repeat rate,
- correction rate,
- accepted-prediction error rate,
- unsupported-sign rate,
- recovery success,
- satisfaction/usability rating.

Qualitative:
- misunderstood labels,
- unnatural reverse output,
- missing variants,
- distracting overlays,
- privacy concerns,
- desired scenarios,
- reasons for distrust.

Do not turn a tiny convenience sample into a population-level claim.

## 8. Fairness slices

Where ethically collected metadata and sufficient sample sizes permit, compare performance across relevant non-sensitive operational slices such as:
- signer ID,
- capture device,
- lighting condition,
- background complexity,
- camera distance,
- clothing/hand-background contrast,
- one-hand/two-hand sign group,
- static/dynamic sign group,
- sign variant,
- domain vocabulary.

Do not infer sensitive demographic attributes from video for fairness reporting.

If participants voluntarily provide demographic metadata under an appropriate study protocol, keep it separate, minimize access, and do not publish tiny identifiable groups.

## 9. Fairness metrics

For each valid slice report, when sample count permits:
- macro F1,
- accepted-prediction error,
- abstention/NEED_REPEAT rate,
- tracking-loss rate,
- latency,
- false activation rate.

Important:
A model can have similar accuracy but force one group/environment to repeat far more often. Therefore abstention and tracking failure are fairness metrics too.

## 10. Minimum sample guard

Never display comparative percentages for tiny slices without the sample count.

Reports must include:
- N signers,
- N samples,
- N classes,
- confidence intervals when feasible,
- explicit “insufficient evidence” where appropriate.

## 11. Model-selection rule

Do not choose the model solely by global accuracy.

Prefer a model that offers a better combination of:
- held-out signer performance,
- calibration,
- low false activation,
- acceptable abstention,
- lower worst-slice failure,
- latency suitable for target hardware.

A tiny global-score improvement does not justify a major worst-slice regression.

## 12. Variant coverage register

Maintain:

```
concept_id
variant_id
source
region_if_documented
training_samples
validation_samples
test_samples
supported_live
reverse_clip_available
review_status
known_confusions
```

The UI may say “current demo vocabulary/variants” rather than implying all ISL forms are covered.

## 13. Reverse-output validation

Every reverse ISL phrase shown as “verified” should have:
- provenance,
- permission/license status,
- review status,
- version,
- concept/phrase mapping.

Generated/avatar output must be labelled experimental until intelligibility and naturalness are validated.

Word-by-word concatenation must not be presented as fluent ISL.

## 14. Feedback triage

Classify feedback:
- linguistic correctness,
- recognition failure,
- variant coverage,
- UI/accessibility,
- privacy,
- performance,
- reverse-output quality,
- feature request.

Severity:
- S0 safety/serious miscommunication,
- S1 blocks core communication,
- S2 frequent usability problem,
- S3 improvement.

S0/S1 issues affecting demo vocabulary should block release until fixed, removed from supported scope, or clearly mitigated.

## 15. Correction workflow

User correction must not directly update model weights.

Pipeline:
1. collect correction metadata with consent;
2. review;
3. validate label/variant;
4. add to a versioned dataset candidate set;
5. retrain offline;
6. run full regression evaluation;
7. promote only if release gates pass.

## 16. Research-vs-product firewall

A paper/dataset result can justify an experiment, not a product claim.

Examples:
- a benchmark reports strong ISL recognition → SANKET AI may test that approach;
- another sign-language deployment works at 11k signs → it proves a design pattern can scale, not that SANKET AI already scales to 11k signs;
- a user study in another sign language informs methodology, not ISL user preferences.

## 17. Accessibility co-validation

Community review should include:
- text readability,
- caption placement,
- high contrast,
- reduced motion,
- keyboard operation,
- haptic meaning,
- emergency layout,
- camera framing instructions.

Accessibility controls must not imply every Deaf user has the same preferences.

## 18. Privacy during studies

Before collecting study recordings:
- explain whether raw video/audio is saved;
- separate product-use consent from research/data-contribution consent;
- provide stop/withdraw mechanism appropriate to the study;
- use pseudonymous IDs;
- avoid public demo footage without explicit permission.

## 19. Deployment scenario validation

Before claiming readiness for a domain, run scenario-specific tests.

### Hospital
Test:
- noisy/low-light room,
- high-stakes ambiguity,
- medical phrase coverage.

Do not claim clinical interpretation equivalence.

### Classroom
Test:
- distance,
- multiple people,
- long sessions,
- teacher/student turn-taking.

### Public-service counter
Test:
- background movement,
- short interactions,
- privacy of transcript.

### Emergency
Test:
- rapid access,
- low literacy alternatives where appropriate,
- explicit statement that the UI does not guarantee dispatch.

## 20. Judge-demo evidence

If community validation has actually occurred, show:
- number and type of reviewers without unnecessary identities,
- tasks performed,
- changes made because of feedback,
- unresolved limitations.

If it has not occurred, say:
“Community validation is a required next gate in our specification; the current prototype has not yet completed that gate.”

Never invent endorsements.

## 21. Acceptance criteria

Community/fairness readiness requires:
- [ ] vocabulary variants have provenance;
- [ ] supported-scope language is precise;
- [ ] user tasks are defined;
- [ ] review form/artifact exists;
- [ ] corrections cannot directly poison production model;
- [ ] slice metrics include abstention/tracking failures;
- [ ] no sensitive attributes are inferred for fairness analysis;
- [ ] reverse-output verification state is visible;
- [ ] S0/S1 linguistic issues block affected claims;
- [ ] README separates completed validation from planned validation.

## 22. Research references

1. Singh et al. “Overview of the First Workshop on Sign Language Processing (WSLP 2025).” ACL Anthology, 2025.
   https://aclanthology.org/2025.wslp-main.1/

2. Wadhera, Mahmud, Dhaneshwar. “Towards Inclusive Sign Language Recognition: Dataset Gaps, Ethical Challenges, and Deployment Barriers in the Indian Context.” CVPR Workshops, 2026.
   https://openaccess.thecvf.com/content/CVPR2026W/MSLR/html/Wadhera_Towards_Inclusive_Sign_Language_Recognition_Dataset_Gaps_Ethical_Challenges_and_CVPRW_2026_paper.html

3. Vandendriessche et al. “Scalable Video-Based Search in the VGT Dictionary.” EAMT, 2026.
   https://aclanthology.org/2026.eamt-2.15/

4. Wan et al. “Sign2Vis: Automated Data Visualization from Sign Language.” Findings of ACL, 2025.
   https://aclanthology.org/2025.findings-acl.918/

## Final principle

A model is not inclusive because the README says it is.

SANKET AI may claim community-centered, fair or deployment-ready behavior only to the extent that the corresponding review, slice evaluation and acceptance evidence actually exists.
