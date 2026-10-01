# SANKET AI — Judge Demo and Q&A Defense Pack

Use this as the final demo-defense source. Do not memorize exaggerated claims. Demonstrate evidence.

## 3–5 minute judge flow

### 1. Problem
“Most small sign-language demos recognize isolated hand poses. Real communication can involve two hands, facial/non-manual signals, body movement, motion over time and context. SANKET AI is designed as a multimodal ISL communication bridge.”

### 2. Show live multimodal perception
Open the interpreter and show:
- left/right hand tracking,
- pose/body signal,
- face/non-manual signal,
- motion/activity,
- domain.

### 3. Translate one supported sign/phrase
Show:
- accepted prediction,
- actual confidence,
- text,
- TTS.

### 4. Demonstrate the differentiator
Perform a deliberately unclear or partially occluded sign.

Expected:
- low tracking/confidence,
- `NEED_REPEAT`,
- “Sign unclear — please repeat.”

Then repeat clearly and show acceptance.

### 5. Context
Switch domain, e.g. General → Hospital.
Explain that context reranks/limits plausible candidates; it does not invent signs.

### 6. Two-way communication
Type/speak a supported reply and show the approved ISL clip/sequence.

### 7. Accessibility
Show one or two:
- high contrast,
- large text,
- visual + haptic alert,
- Braille-friendly text,
- emergency mode.

### 8. Calling
Only show WebRTC if stable. If experimental, say so.

### 9. Close
Show actual supported vocabulary, latency and evaluation report. Explain how vocabulary/domain packs and on-device inference can scale after the hackathon.

---

## Likely judge questions

### “Isn’t this just another sign-language translator?”
Answer with implementation evidence:
- multimodal hands + face + body + temporal motion,
- uncertainty rejection,
- context,
- bidirectional communication,
- accessibility ecosystem,
- real-time calling/action integration.

The differentiator is the system design and failure handling, not a claim that no sign-language translator exists.

### “How are you different from ASL projects?”
SANKET AI is explicitly scoped to Indian Sign Language and uses ISL references/datasets where permitted. Do not imply ISL is ASL with different labels.

### “How many signs do you support?”
State the exact number supported by the current tested build. Then separate:
- current prototype vocabulary,
- available research resources,
- future scaling plan.

Never use a dictionary’s total term count as if the model already recognizes all of them.

### “What is your accuracy?”
Show the actual evaluation report and clarify:
- data split,
- held-out signer status,
- metric used,
- vocabulary size.

Do not answer with training accuracy.

### “Why face and body?”
Non-manual signals and body/pose can carry linguistic information. Technically, these signals also improve temporal/motion context and can help distinguish otherwise similar manual signs.

### “What if the AI is wrong?”
The system exposes confidence, tracking quality and ambiguity. Below threshold, it asks for repetition. It prefers abstention to a confident incorrect output.

### “Are you using an LLM to guess sentences?”
The recognizer must remain evidence-grounded. Context may rerank candidates or normalize output, but must not fabricate unsupported signed content.

### “Can this work offline?”
Core recognition is designed local-first. The hackathon implementation may use local backend inference; ONNX/browser inference is an optimization path. Demo Replay Mode provides deterministic fallback.

### “Where is the data stored?”
By default raw camera video is not persisted. Dataset collection is a separate explicit consented mode. Session metadata can be stored locally.

### “What about privacy of face data?”
Face/non-manual features are used only for sign-language cues, not identity/emotion/medical inference. Raw video persistence is off by default.

### “Why not just use a human interpreter?”
SANKET AI is not positioned as a replacement for professional interpreters in every situation. It is an assistive bridge for everyday, immediate and low-resource interactions, with clear limitations.

### “How will it scale?”
Technical scale:
- larger consented/licensed datasets,
- signer-diverse evaluation,
- domain vocabulary packs,
- optimized ONNX inference,
- client-side/on-device execution,
- model registry and telemetry using privacy-preserving metadata.

Deployment markets can include education, healthcare, public services, transport, accessibility software and communication platforms, subject to validation and procurement requirements.

### “What is your business model?”
Potential routes:
- institutional licenses,
- enterprise accessibility SDK/API,
- deployment/support contracts,
- domain-specific packages.

Do not claim existing customers or revenue unless real.

### “Can Braille users use this?”
The product exposes semantic text in an accessible way that screen readers/refreshable Braille systems can consume. A Unicode Braille display in the prototype is a preview, not a substitute for a certified Braille translator.

### “Can it call emergency services automatically?”
Not in the default prototype. Emergency mode is an assistive communication interface. Do not claim guaranteed emergency dispatch.

### “Can signs control the laptop?”
Only whitelisted in-app demo actions should be allowed. Arbitrary OS/shell actions are intentionally blocked for safety.

### “What if lighting is poor or a hand leaves frame?”
Tracking quality falls; the system switches to `TRACKING_LOST` or `NEED_REPEAT` instead of forcing a translation.

### “What is technically hardest?”
Generalization across signers, continuous segmentation, non-manual features, ambiguity and honest confidence calibration. Explain which of these the prototype solves now and which remain research work.

---

## Claims discipline

Use these forms:
- “Our prototype currently supports X tested signs/phrases.”
- “We measured Y on held-out data under these conditions.”
- “The architecture is designed to scale to…”
- “This module is experimental.”
- “This is our next-stage research path.”

Avoid:
- “100% accurate,”
- “works for every ISL sign,”
- “replaces interpreters,”
- “understands every sentence,”
- “works on all devices,”
- “AI automatically fixes every wrong translation.”

## Final judge impression target
The demo should leave three concrete ideas:
1. SANKET AI understands more than a hand pose.
2. It knows when it is uncertain.
3. It is designed as a practical two-way accessibility communication system, not a one-screen classifier.
