# SANKET AI — Fingerspelling and Unknown-Term Specification

## Purpose
A finite-vocabulary ISL system will encounter names, acronyms, technical terms, places and unsupported signs. The product needs an explicit fallback instead of forcing every sequence into a known class.

A 2025 ACL Workshop on Sign Language Processing paper introduced a continuous Indian Sign Language fingerspelling dataset with 1,308 segments from 499 videos, totaling 70.85 minutes and 14,814 characters. It motivates treating fingerspelling as a temporal sequence problem.

Research source:
https://aclanthology.org/2025.wslp-main.6/

## Required recognition states
The decoder should distinguish:
- lexical sign/phrase candidate;
- fingerspelling candidate;
- unknown sign;
- need repeat;
- no sign;
- tracking lost.

Do not force every temporal segment into the lexical vocabulary.

## Architecture
Keep fingerspelling separate from the primary lexical classifier.

Temporal segment can feed:
1. lexical recognizer;
2. fingerspelling gate and character decoder;
3. unknown/background detector;
4. arbitration and confidence gate.

This prevents a finite K-class classifier from pretending to understand arbitrary names.

## Continuous fingerspelling
Continuous fingerspelling includes transitions between characters. Therefore:
- do not assume fixed frames per letter;
- do not require a neutral pose between letters;
- preserve temporal context;
- prefer sequence decoding such as CTC or encoder-decoder approaches over frame voting.

## Arbitration
Recommended logic:
- accept lexical output only above its validated threshold;
- otherwise consider the fingerspelling path only if its own gate has evidence;
- accept a spelling only above its independently validated threshold;
- otherwise return NEED_REPEAT or UNKNOWN_SIGN.

Never transform weak lexical evidence into a plausible-looking name automatically.

## Proper nouns
For person names, organizations, places, products and acronyms:
- preserve decoded character order;
- allow confirmation/editing;
- avoid silently autocorrecting an uncertain sequence into a famous name.

## Reverse text/speech → ISL fallback
Use:
1. verified phrase clip;
2. verified lexical-sign sequence;
3. verified fingerspelling renderer;
4. plain text with “ISL rendering unavailable”.

Do not describe word-by-word English rendering as fluent ISL.

## Text-to-fingerspelling
Maintain a verified ISL manual-alphabet asset set.
Requirements:
- supported-character registry;
- adjustable playback speed;
- clear word boundaries;
- source text shown beside playback;
- explicit unsupported-character state.

Never synthesize an unverified handshape and present it as correct.

## Dataset provenance
Before using the 2025 dataset:
- inspect current distribution terms;
- record license and attribution;
- record source provenance;
- check redistribution and model-use conditions;
- keep large dataset files outside git.

A publicly readable paper does not by itself grant unrestricted dataset or commercial rights.

## Evaluation
Recognition metrics:
- Character Error Rate;
- exact sequence accuracy;
- insertion/deletion/substitution counts;
- per-character confusion;
- signer-disjoint evaluation where feasible;
- latency.

System metrics:
- false fingerspelling activation;
- lexical-to-fingerspelling misrouting;
- fingerspelling-to-lexical misrouting;
- repeat-request rate.

## UI
Show provisional spelling separately from committed transcript text.
Screen readers should receive the finalized accepted sequence rather than every unstable intermediate character.

## Calling
Fingerspelled output can share the transcript/caption lane. Caption placement must not obscure the signer’s hands, face or other visually essential signing information.

W3C accessibility reference:
https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded

## Acceptance tests
- lexical sign does not trigger fingerspelling;
- known spelling does not become a random lexical sign;
- unsupported motion is rejected;
- repeated characters work;
- fast and slow spelling are tested;
- temporary landmark loss is handled;
- different signer is tested;
- mirrored preview does not alter semantics;
- unsupported reverse-render character is visible;
- provisional output never enters final transcript before acceptance.

## Hackathon scope
P0:
- UNKNOWN_SIGN state;
- honest reverse fallback.

P1:
- verified text-to-fingerspelling playback for names/terms.

P2 / research:
- continuous fingerspelling recognition.

## Claims discipline
Until evaluated, describe continuous fingerspelling recognition as a research extension. Do not claim that SANKET AI understands every name or automatically translates every unknown word.

## Engineering consequence
SANKET AI should explicitly separate lexical signing, continuous fingerspelling and unknown signing, with independent confidence/evaluation and a non-fabricated fallback path.
