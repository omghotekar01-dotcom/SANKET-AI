# SANKET AI Prompt Pack

This folder is the implementation source-of-truth for **SANKET AI — Real-Time Multimodal Indian Sign Language Interpreter**, the Peaky Coders project for Hacktopia 2026.

## Read order
1. `MASTER_BUILD_PROMPT.md` — the self-contained master instruction for an AI coding agent or human engineering team.
2. `IMPLEMENTATION_BLUEPRINT.md` — engineering architecture, APIs, ML pipeline, data contracts and milestone plan.
3. `RESEARCH_BASIS.md` — verified research/official sources and constraints that justify key design choices.
4. `DEMO_ACCEPTANCE_CHECKLIST.md` — the objective definition of “demo-ready”.

## Non-negotiable product idea
SANKET AI must not become a generic hand-gesture classifier. Its identity is:

**Camera → multimodal perception → temporal ISL recognition → context + uncertainty validation → intended meaning → accessible communication/action outputs.**

The multimodal signal includes hands, face/non-manual signals, upper-body pose, motion across time and conversation/domain context. The system must visibly expose uncertainty rather than fabricate confident translations.

The core hackathon prototype must be usable with an ordinary webcam/laptop and no paid API. Advanced services are optional enhancements, never hard dependencies.
