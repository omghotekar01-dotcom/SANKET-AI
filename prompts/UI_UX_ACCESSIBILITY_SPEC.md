# SANKET AI — UI, UX and Accessibility Specification

## 1. Product personality

The interface should feel:
- calm,
- trustworthy,
- inclusive,
- high-clarity,
- modern,
- functional.

Avoid cyberpunk/neon aesthetics that compete with the signer.

## 2. Main navigation

Primary destinations:
- Interpret
- Conversation
- Call
- Emergency
- Accessibility
- Diagnostics

Developer-only:
- Data Collection
- Model/Evaluation

## 3. Interpreter screen

Layout priority:
1. camera/signing area;
2. interpreted message;
3. state/confidence;
4. controls;
5. signal health;
6. diagnostics secondary.

Required states:
- Ready
- Listening/Tracking
- Collecting
- Accepted
- Need repeat
- No sign
- Tracking lost
- Unsupported
- Error

## 4. Camera region

Must provide:
- large signer framing;
- optional landmarks;
- camera selector;
- mirror preview toggle;
- framing guide;
- permission state.

Do not overlay dense text over the signer’s hands.

## 5. Transcript

Features:
- chronological turns;
- timestamp optional;
- source icon: ISL / typed / speech;
- confidence visible only where useful;
- repeat last;
- copy;
- clear session.

Avoid showing raw model labels as user-facing prose.

## 6. Confidence UX

Do not show false precision like 91.3827%.

Use:
- High / Medium / Low,
or rounded percentage,
plus state.

For judges/diagnostics, raw calibrated value may be visible.

## 7. Need-repeat UX

Message:
“Sign unclear — please repeat.”

Optional reason:
- hand left frame,
- movement incomplete,
- low confidence.

Never blame the signer.

## 8. Conversation mode

Two participant lanes:
- Signer side;
- Non-signer side.

Each turn should make clear:
- input mode,
- interpreted text,
- reverse visual response.

## 9. Reverse ISL pane

Show:
- phrase currently playing,
- clip source/verification metadata in info panel,
- progress,
- repeat,
- slower playback if supported.

Clearly label:
- verified phrase clip,
- sequence fallback,
- fingerspelling fallback.

## 10. Emergency mode

Design:
- full-screen,
- large targets,
- high contrast,
- minimal navigation.

Cards:
- HELP
- DOCTOR
- POLICE
- FIRE
- ACCIDENT
- DANGER
- WATER
- PAIN

Selecting a card should:
- display large text,
- optionally speak,
- optionally vibrate,
- never claim external dispatch unless actually connected.

## 11. Accessibility settings

Include:
- text size,
- contrast mode,
- reduced motion,
- caption preference,
- vibration preference,
- speech output volume/voice if available,
- landmark overlay on/off.

Persist locally.

## 12. Keyboard

Minimum:
- Tab through all controls;
- Enter/Space activate;
- Escape close dialogs;
- shortcuts optional but never required.

## 13. Screen readers

Requirements:
- semantic headings;
- button names;
- form labels;
- ARIA live region for accepted transcript;
- avoid announcing every frame-level prediction;
- errors announced once;
- status text should be meaningful without color.

## 14. Color

Color must not be the only signal.

Pair status colors with:
- icon,
- text,
- border/shape.

## 15. Motion

Avoid:
- bouncing cards,
- constant decorative particles,
- fast transitions.

Use subtle transitions that do not distract from signing.

## 16. Responsive behavior

Desktop:
- camera + transcript side-by-side.

Tablet:
- stacked or 60/40.

Mobile:
- camera first,
- transcript beneath,
- sticky essential controls.

Call mode mobile:
- remote video primary,
- self-view small,
- captions over safe lower region.

## 17. Loading

Model load:
- explicit progress/state;
- do not show fake percentage unless measurable.

Camera startup:
- skeleton/frame placeholder;
- permission explanation.

## 18. Empty states

Examples:
- no transcript yet;
- no camera;
- no reverse clip;
- no call peer;
- no metrics.

Each empty state should tell user what to do next.

## 19. Diagnostics drawer

Show:
- model version;
- feature schema;
- current domain;
- camera FPS;
- inference FPS;
- P50/P95 latency after enough samples;
- hand/face/pose status;
- current state;
- last accepted token;
- demo/fallback badge.

## 20. Demo presentation mode

Optional toggle:
- larger transcript,
- simplified controls,
- judges can see confidence and latency,
- hide developer clutter.

## 21. Copywriting

Prefer:
- “Ready to interpret”
- “Sign unclear — please repeat”
- “Tracking lost — move back into frame”
- “This sign is not in the current demo vocabulary”
- “Text-to-ISL clip unavailable”

Avoid:
- “AI failed”
- “Invalid user”
- “Wrong gesture”

## 22. Accessibility acceptance tests

Before release:
- full core flow keyboard-only;
- screen reader announces accepted text;
- 200% browser zoom;
- high contrast;
- mobile portrait;
- motion reduction;
- captions readable over video;
- emergency controls usable one-handed.