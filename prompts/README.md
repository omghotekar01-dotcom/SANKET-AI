# SANKET AI Prompt Pack

This folder is the implementation source-of-truth for **SANKET AI — Real-Time Multimodal Indian Sign Language Interpreter**, the Peaky Coders project for Hacktopia 2026.

## Read order
1. `MASTER_BUILD_PROMPT.md` — the self-contained master instruction for an AI coding agent or human engineering team.
2. `PROJECT_REQUIREMENTS_MATRIX.md` — converts every submitted/planned capability into implementation, visible proof and acceptance conditions.
3. `IMPLEMENTATION_BLUEPRINT.md` — engineering architecture, APIs, ML pipeline, data contracts and milestone plan.
4. `RESEARCH_BASIS.md` — verified research/official sources and constraints that justify key design choices.
5. `BUILD_SEQUENCE_24H.md` — execution order for the 24-hour Hacktopia finale.
6. `DEMO_ACCEPTANCE_CHECKLIST.md` — the objective definition of “demo-ready”.
7. `JUDGE_DEMO_AND_QA.md` — demo sequence, likely judge questions, evidence-backed answer guidance and claims discipline.

The repository root also contains `AGENTS.md`, which is the first entry point for any AI coding agent and forces the above read order before implementation.

## Non-negotiable product idea
SANKET AI must not become a generic hand-gesture classifier. Its identity is:

**Camera → multimodal perception → temporal ISL recognition → context + uncertainty validation → intended meaning → accessible communication/action outputs.**

The multimodal signal includes hands, face/non-manual signals, upper-body pose, motion across time and conversation/domain context. The system must visibly expose uncertainty rather than fabricate confident translations.

The core hackathon prototype must be usable with an ordinary webcam/laptop and no paid API. Advanced services are optional enhancements, never hard dependencies.

## Prompt-pack status
The prompt pack covers:
- project identity and scope,
- submitted feature traceability,
- repository architecture,
- frontend/backend contracts,
- multimodal CV/ML pipeline,
- data collection, consent and licensing rules,
- model training/evaluation,
- real-time temporal decoding,
- confidence calibration and self-correction,
- context-aware interpretation,
- reverse text/speech-to-ISL communication,
- WebRTC calling,
- emergency/accessibility/Braille/haptic behavior,
- privacy and security,
- offline/demo fallbacks,
- testing and measurable metrics,
- 24-hour build order,
- judge demo and Q&A,
- final acceptance criteria.

Future research updates should refine these documents rather than create contradictory parallel specifications.

## Deep-spec expansion

The following documents extend the master prompt into failure-resistant implementation guidance:

- `FAILURE_MODES_AND_RECOVERY.md` — camera, tracking, model, network, WebRTC, storage, latency and demo recovery behavior.
- `ML_DATASET_TRAINING_PLAYBOOK.md` — vocabulary design, consented data collection, signer-aware splits, augmentation, model training, calibration, evaluation and model cards.
- `UI_UX_ACCESSIBILITY_SPEC.md` — page-by-page product behavior, states, responsive layout, screen-reader/keyboard requirements and demo presentation mode.
- `SECURITY_PRIVACY_THREAT_MODEL.md` — camera/mic/privacy risks, WebSocket/WebRTC abuse controls, dataset consent, logging and action safety.
- `REALTIME_PERFORMANCE_AND_OPTIMIZATION.md` — latency budget, backpressure, adaptive quality, ONNX/browser optimization and regression gates.
- `DEPLOYMENT_OPERATIONS_AND_OFFLINE.md` — one-command startup, offline packaging, health checks, versioning, crash recovery and post-hackathon deployment paths.
- `HACKATHON_RISK_REGISTER.md` — concrete technical/demo/research risks with mitigations and fallbacks.
- `IMPLEMENTATION_BACKLOG.md` — epics and checkable engineering tasks from foundation through final demo.

The prompt library should keep expanding modularly as new risks, research evidence or implementation constraints are discovered. Prefer new actionable specifications and testable requirements over repetitive prose.

