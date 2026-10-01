# SANKET AI — Browser Inference and Accessible Calling

## Browser inference
Browser execution must be capability-detected. Current ONNX Runtime Web documentation shows WebAssembly as the broad CPU-compatible path, while WebGPU support varies by browser/platform.

Required fallback order:
1. attempt WebGPU when available;
2. fall back to WASM when WebGPU is unavailable or initialization fails;
3. fall back to configured local FastAPI inference when browser inference fails;
4. expose the actual active backend in Diagnostics.

Suggested states: BROWSER_WEBGPU, BROWSER_WASM, LOCAL_SERVER, UNAVAILABLE.

Before enabling a browser model, validate input/output shapes, run a known self-test vector, record model/version/provider, and benchmark warm-up plus steady-state latency. Do not assume GPU is faster for a small landmark model.

Never display “on-device” when frames or landmarks are actually sent to a backend.

## Accessible calling
Call mode should provide:
- live interpreted text where available;
- persistent transcript option;
- caption toggle;
- adjustable caption size/contrast;
- placement that avoids obscuring hands, face, or other important visual information;
- clear degraded/unavailable state;
- keyboard-accessible mute, camera, captions, leave and reconnect controls.

For SANKET interpretation, distinguish provisional model output from accepted text. Only accepted interpretation should become a committed transcript turn or assistive-technology announcement.

A transcript is useful for screen readers, refreshable Braille workflows, searching prior turns, and recovery when captions disappear quickly.

## Diagnostics capability matrix
Expose:
- browser/platform;
- WebGPU available;
- WASM available;
- active inference backend;
- camera/microphone permission;
- vibration support;
- speech synthesis/recognition support;
- WebRTC support.

## Acceptance tests
- WebGPU-capable path tested.
- WASM fallback tested.
- Forced WebGPU failure falls back cleanly.
- Model self-test catches incompatible artifact.
- Diagnostics identifies actual provider.
- Captions can be toggled and enlarged.
- Captions do not cover the primary signing area.
- Accepted interpretations enter transcript.
- Provisional guesses are not announced as final.
- Keyboard reaches all call controls.
- Caption failure does not terminate video call.
- Transcript remains usable at 200% zoom.

## Source basis
- https://onnxruntime.ai/docs/tutorials/web/
- https://onnxruntime.ai/docs/get-started/with-javascript/web.html
- https://onnxruntime.ai/docs/tutorials/web/ep-webgpu.html
- https://www.w3.org/WAI/media/av/captions/
- https://www.w3.org/WAI/media/av/transcripts/
- https://www.w3.org/WAI/WCAG21/Understanding/captions-live

## Claims discipline
Do not claim WebGPU works everywhere. Do not claim all inference is on-device unless it truly is. Do not claim WCAG automatically requires captions for every private two-person web call; provide them because they directly serve SANKET AI's accessibility mission.
