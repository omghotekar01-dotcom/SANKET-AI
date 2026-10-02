# Data, Consent and Licenses

## Local collection

The default collector stores normalized landmark arrays (`.npz`) plus metadata. Raw video collection is disabled. Every locally recorded sample requires an explicit consent checkbox and a pseudonymous signer ID.

## Public starter training

SANKET includes an automated research bootstrap trainer that downloads public isolated-ISL clips at build time, converts them to SANKET landmark features, trains a small starter recognizer, and commits **only the derived model artifact**. Source videos are never committed to this repository.

Current aggregate used by the bootstrap trainer:
- `vidit031/isl-isolated-40words` on Hugging Face.
- Only rows sourced from **INCLUDE** and **CISLR** are considered.
- The aggregate card lists INCLUDE as CC-BY-4.0 and CISLR as AFL-3.0 in its source-mix table.
- Per-clip source/license/provenance stays in the temporary training metadata.
- The derived evaluation is a stratified sample holdout and must **not** be described as signer-independent validation.

The public bootstrap is for research/demo initialization only. Team-collected signer-diverse data should replace it for stronger project claims.

## External 50-class fallback

The repository can also download the pinned MIT-licensed 50-class BiLSTM described in `THIRD_PARTY_NOTICES.md`. That model is clearly marked as external bootstrap weights and is not represented as SANKET-trained.

## Reverse ISL clips

The asset lab accepts only intentional `.webm`/`.mp4` uploads. A clip is used as a verified reverse-ISL phrase only when the uploader marks that its ISL form/meaning has been checked. Keep source and permission notes for every clip.

Do not copy dictionary/research videos into this repository unless their terms clearly permit redistribution.

## Claim rule

Availability of a dataset or external model does not justify claiming unrestricted ISL translation. Report only the vocabulary, split, source and evaluation actually represented by the active artifact.
