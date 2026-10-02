# AGENTS.md — SANKET AI Build Entry Point

This repository contains the Hacktopia 2026 **SANKET AI** project.

Before changing code, every coding agent or human contributor must read, in order:

1. `prompts/MASTER_BUILD_PROMPT.md`
2. `prompts/PROJECT_REQUIREMENTS_MATRIX.md`
3. `prompts/IMPLEMENTATION_BLUEPRINT.md`
4. `prompts/RESEARCH_BASIS.md`
5. `prompts/BUILD_SEQUENCE_24H.md`
6. `prompts/DEMO_ACCEPTANCE_CHECKLIST.md`
7. `prompts/JUDGE_DEMO_AND_QA.md`
8. `prompts/IMPLEMENTATION_STATUS.md`

The deeper specifications under `prompts/` remain additive source-of-truth documents and must not be silently contradicted by implementation changes.

## Mission
Build a **real-time multimodal Indian Sign Language communication bridge** that uses:
- hands,
- facial/non-manual signals,
- body/pose,
- motion across time,
- context,
- confidence/ambiguity validation,

and produces accessible communication through:
- text,
- speech,
- reverse text/speech-to-ISL playback,
- emergency communication,
- visual/haptic/Braille-friendly outputs,
- WebRTC sign-language calling,
- safe in-app actions.

## Core rule
Do not collapse SANKET AI into a generic hand-gesture classifier.

## Execution rule
Build vertical slices and keep the app runnable after every meaningful change.

Do not:
- fabricate accuracy,
- invent dataset licenses,
- claim continuous open-vocabulary ISL translation when only a finite vocabulary is implemented,
- silently store raw camera video,
- execute arbitrary OS commands from gestures,
- introduce paid API dependencies into the core demo,
- rewrite stable modules without a measurable reason.

## Implementation rule
The current prototype follows the same architecture: React + TypeScript frontend, FastAPI backend, MediaPipe/equivalent multimodal perception, bounded temporal features, confidence-aware finite-vocabulary recognition, explicit failure states, verified reverse-ISL assets, accessibility/emergency flows, and optional WebRTC calling.

Live ISL recognition must remain visibly unavailable until a real trained/evaluated artifact is present. Demo Replay must remain clearly labelled and separate from live AI output.

## Definition of success
The project is only “demo-ready” when the end-to-end loop repeatedly works:
camera → multimodal landmarks → temporal model → confidence gate → interpreted output → accessible communication,
with a deterministic demo-replay fallback and visible failure states.
