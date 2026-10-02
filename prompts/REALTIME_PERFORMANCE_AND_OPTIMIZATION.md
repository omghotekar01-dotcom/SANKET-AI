# SANKET AI — Real-Time Performance and Optimization

## 1. Performance objective

The system should feel conversational. Optimize end-to-end latency rather than only model inference time.

Latency components:
- capture,
- encode/transport,
- landmark detection,
- feature preprocessing,
- model inference,
- smoothing/decision,
- UI render,
- TTS start.

Measure each.

## 2. Frame strategy

Start:
- camera preview 640×480;
- recognition 10–15 FPS;
- send/process latest frame only;
- discard stale queued frames.

Do not process 30 FPS if model needs 150 ms/frame.

## 3. Backpressure

Client:
- only one or small bounded number of in-flight frames.

Server:
- acknowledge sequence IDs;
- ignore stale frame IDs.

Goal:
- latency remains bounded under load.

## 4. Adaptive quality

If latency rises:
1. reduce inference FPS;
2. reduce frame resolution;
3. disable landmark drawing;
4. reduce face feature complexity;
5. keep hand/pose essentials.

Never silently disable core modalities without signalling degraded mode.

## 5. Landmark optimization

- use compact face blendshapes or selected landmarks rather than all 468+ points when possible;
- crop detection region only if robust;
- reuse trackers across frames;
- avoid repeated model initialization.

## 6. Model optimization

Order:
1. correct PyTorch baseline;
2. TorchScript/compile if stable;
3. ONNX;
4. quantization;
5. browser/WASM/WebGPU.

Benchmark after every optimization.

## 7. Buffering

Use fixed-size ring buffers.

Store:
- normalized feature vectors,
not:
- unbounded raw frames.

## 8. UI rendering

- draw landmarks with requestAnimationFrame;
- avoid React state updates for every landmark coordinate;
- use canvas;
- throttle diagnostics;
- transcript updates only on state changes/acceptance.

## 9. WebRTC

Keep recognition separate from media transport.

If local captions are generated:
- do not send full camera frames to backend again if browser can infer locally;
- use data channel for compact caption metadata where practical.

## 10. Metrics

Track:
- capture FPS,
- inference FPS,
- landmark ms,
- model ms,
- decision ms,
- end-to-end ms,
- websocket RTT if used,
- dropped frames,
- queue depth.

## 11. Benchmark conditions

Record:
- device CPU/GPU,
- OS,
- browser,
- camera resolution,
- model version,
- model backend,
- number of classes.

## 12. Target behavior

No universal latency claim should be hard-coded.

For demo:
- set a target based on measured hardware;
- optimize until interaction feels natural;
- display actual P50/P95.

## 13. Slow hardware mode

Provide:
- lower resolution;
- lower FPS;
- simplified face features;
- smaller model;
- disable decorative overlays.

## 14. Browser inference

ONNX Runtime Web path:
- WASM baseline;
- WebGPU when available;
- capability detection;
- server/local Python fallback.

Never make WebGPU mandatory.

## 15. Startup performance

- lazy load non-core routes;
- load interpreter model before enabling start;
- show model-loading state;
- preload reverse ISL clips used in demo.

## 16. Regression gate

Any new feature that increases P95 latency significantly must justify the tradeoff or be disabled in demo mode.
