# SANKET AI — WebRTC Reliability, Call Quality and Caption Synchronization

> Status: engineering specification. This document does not claim that production-grade calling is already implemented.

## 1. Why this exists

A demo call that works on one laptop over one Wi-Fi network is not evidence of a reliable communication system. SANKET AI combines a latency-sensitive video call with an even more latency-sensitive interpretation/caption stream. The implementation therefore needs explicit transport, synchronization, observability, accessibility and failure contracts.

Authoritative references:
- W3C WebRTC Recommendation update, 13 March 2025: https://www.w3.org/news/2025/updated-w3c-recommendation-webrtc-real-time-communication-in-browsers/
- W3C WebRTC Statistics API publication history/current draft: https://www.w3.org/standards/history/webrtc-stats/
- W3C WCAG 3.0 Working Draft (10 September 2026), captions guidance: https://www.w3.org/TR/2026/WD-wcag-3.0-20260910/
- W3C WAI captions guidance: https://www.w3.org/WAI/media/av/captions/
- W3C WAI transcripts guidance: https://www.w3.org/WAI/media/av/transcripts/
- W3C status-message guidance: https://www.w3.org/WAI/WCAG21/Understanding/status-messages

WCAG 3.0 is a Working Draft, not a finished conformance standard. Use its current caption-placement/customization guidance as design input, not as a claim of WCAG 3 conformance.

## 2. Scope and non-claims

P0:
- one-to-one browser call;
- local camera/microphone controls;
- visible connection state;
- local SANKET interpretation;
- timestamped accepted caption events;
- graceful loss/reconnect behavior.

P1:
- TURN-backed connectivity;
- remote caption transport;
- synchronized transcript;
- quality diagnostics.

P2/research:
- multiparty;
- server-side SFU;
- recording;
- end-to-end encrypted application metadata beyond standard WebRTC guarantees;
- production SLA.

Never claim “works everywhere”, “zero latency”, “always peer-to-peer”, or “end-to-end encrypted” without verifying the exact deployed topology and threat model.

## 3. Architecture

Separate planes:

1. **Media plane** — WebRTC audio/video.
2. **Signaling plane** — room lifecycle, SDP/ICE exchange.
3. **Interpretation plane** — local perception + temporal decoder.
4. **Caption metadata plane** — compact structured interpretation events.
5. **Observability plane** — WebRTC stats and SANKET timing metrics.

Recognition must not depend on round-tripping full call video through signaling.

Preferred caption path:
- infer locally on signer device;
- commit an interpretation only after decoder acceptance;
- send compact caption event over RTCDataChannel where available;
- WebSocket fallback may be used but must be labeled/observed separately.

## 4. Room lifecycle state machine

States:
`IDLE -> CREATING/JOINING -> SIGNALING -> CONNECTING -> CONNECTED -> DEGRADED -> RECONNECTING -> ENDED`

Terminal failure:
`FAILED`

Rules:
- UI state derives from actual peer/signaling state, not a timer.
- “Connected” requires usable peer connection, not merely room membership.
- “Reconnecting” must not show stale remote video as live.
- explicit Leave closes tracks, data channels, peer connection and room subscription.
- browser refresh/abandonment must expire presence after a bounded server-side interval.

## 5. Signaling contract

Minimum message envelope:

```json
{
  "v": 1,
  "type": "offer|answer|ice|join|leave|caption|heartbeat|error",
  "room_id": "opaque-id",
  "peer_id": "ephemeral-id",
  "seq": 42,
  "sent_at_ms": 0,
  "payload": {}
}
```

Requirements:
- schema validate every message;
- bound payload size;
- reject unknown message versions/types;
- room IDs are random/opaque;
- peer IDs are ephemeral;
- sequence numbers detect duplicate/out-of-order control messages;
- do not place raw frames, model tensors or unrestricted actions in signaling payloads.

## 6. Caption event contract

```json
{
  "v": 1,
  "caption_id": "uuid",
  "source_peer_id": "ephemeral-id",
  "source": "isl_recognition|speech|typed",
  "status": "provisional|committed|retracted",
  "text": "I need water",
  "language": "en-IN",
  "sign_start_ms": 0,
  "sign_end_ms": 0,
  "committed_at_ms": 0,
  "confidence_band": "high|medium|low",
  "reason_codes": [],
  "model_version": "string",
  "sequence": 12
}
```

Do not transmit raw biometric landmarks as caption metadata unless a separately reviewed feature explicitly requires it.

## 7. Caption synchronization model

Three times matter:
- **event time**: when the sign/speech occurred;
- **commit time**: when SANKET accepted the interpretation;
- **display time**: when remote UI rendered it.

Measure:
`recognition_delay = committed_at - sign_end`
`transport_delay = remote_receive - committed_at`
`render_delay = display - remote_receive`
`caption_end_to_end = display - sign_end`

Do not report “caption latency” without defining which interval is measured.

Clock caveat:
- wall clocks on two devices can differ;
- one-way network latency therefore cannot be derived safely from independent Date.now() values alone;
- use local monotonic timing for within-device stages;
- use RTT/echo-based synchronization or explicitly report only measurements that do not require synchronized clocks.

## 8. Provisional vs committed captions

Default remote transcript should show **committed** interpretations.

If provisional captions are enabled:
- visually distinguish them;
- allow replacement/retraction by ID;
- never persist them as final transcript without a commit event;
- screen readers should not be spammed with every frame-level hypothesis.

For high-consequence domains, provisional text must not be presented as authoritative.

## 9. Caption placement

Because hands, face and upper body carry linguistic information, captions must not cover those regions.

Default:
- dedicated caption/transcript region outside the signing viewport where screen size permits.

Mobile fallback:
- bottom overlay only when safe-area/landmark occupancy allows;
- user can move/resize or switch to transcript panel;
- preserve readable contrast.

Current W3C WCAG 3 Working Draft guidance explicitly calls for live captions and for captions not to hide visual information needed to understand video. Treat this as a design requirement even though WCAG 3 remains a draft.

## 10. WebRTC quality telemetry

Sample `RTCPeerConnection.getStats()` periodically at a modest interval, not every render frame.

Candidate metrics where supported:
- selected candidate pair;
- round-trip time;
- packets lost;
- jitter;
- bytes sent/received;
- frames encoded/decoded;
- frames dropped;
- frame width/height;
- frames per second;
- available outgoing bitrate where exposed;
- codec;
- candidate type/local/remote network characteristics only to the extent necessary for diagnostics.

Privacy:
- do not persist IP/network identifiers in ordinary analytics;
- redact diagnostic exports by default.

## 11. Quality state

Use measured thresholds configured from testing, not invented universal constants.

Possible state:
- GOOD
- DEGRADED
- POOR
- RECONNECTING

Inputs may include:
- sustained packet loss;
- RTT trend;
- jitter;
- frozen/dropped video;
- media track mute/end;
- data-channel state;
- caption transport delay.

Use hysteresis so UI does not oscillate between GOOD and DEGRADED.

## 12. Adaptive degradation order

When call quality deteriorates:
1. preserve call/control state;
2. preserve readable committed text;
3. preserve signer-visible video;
4. reduce nonessential UI animation/overlays;
5. reduce video quality/frame rate if browser/network adaptation is insufficient;
6. keep local recognition functioning if possible;
7. fall back to transcript/text communication if media becomes unusable.

Do not sacrifice captions first.

## 13. ICE/TURN

A LAN-only success is not production connectivity.

Before claiming internet-ready calling:
- test across different networks;
- test restrictive NAT/firewall conditions;
- configure TURN if needed;
- test relay candidate path;
- record whether selected path is host, server-reflexive or relay for diagnostics without exposing sensitive network details to ordinary users.

If TURN is not configured in the hackathon build, document calling as demo/LAN constrained rather than hiding the limitation.

## 14. Reconnection

On transient signaling loss:
- existing WebRTC media may continue; do not tear it down automatically solely because signaling disconnected.

On peer connection failure:
- expose reconnect state;
- attempt bounded ICE restart/rejoin strategy;
- prevent duplicate peer connections;
- preserve committed local transcript;
- after timeout, end cleanly and offer retry.

Never run infinite silent reconnect loops.

## 15. Camera/microphone controls

Mute:
- visibly reflects actual track state.

Camera off:
- stop or disable video track according to chosen privacy behavior;
- local sign recognition cannot pretend to continue if its camera source is unavailable.

Device switch:
- prefer replacing track without rebuilding the entire call when supported;
- verify recognition input follows intended camera.

On page exit:
- stop local media tracks.

## 16. Caption transport ordering

Caption channel should use monotonically increasing sequence numbers.

Receiver:
- deduplicate by caption_id;
- ignore stale duplicate commits;
- allow explicit retraction;
- preserve transcript order by event/sequence semantics;
- never reorder a later committed emergency phrase behind stale provisional content.

If using RTCDataChannel:
- choose ordered/reliable behavior for final caption/control events unless experiments prove another policy;
- do not assume a lossy channel is acceptable merely because media itself tolerates loss.

## 17. Accessibility

Call UI must be keyboard-operable.

Status changes such as:
- “Call connected”;
- “Connection degraded”;
- “Reconnecting”;
- “Camera unavailable”

must be programmatically available to assistive technology. Avoid assertive live-region spam for ordinary telemetry.

Committed transcript can use an appropriate log/live-region pattern; frame-level predictions must not.

Users should be able to:
- change caption size;
- change contrast/background;
- show/hide captions;
- open persistent transcript;
- identify speaker/source;
- avoid captions obscuring signing.

W3C WAI guidance also supports transcripts as an important alternative for a wider range of accessibility needs.

## 18. Failure matrix

Test at minimum:

| Scenario | Expected behavior |
|---|---|
| signaling server unavailable before join | actionable join failure; local interpreter still usable |
| signaling drops after connected | media preserved if peer connection remains alive |
| peer disconnects | visible ended/reconnect state; transcript retained |
| data channel closes | call continues; captions explicitly unavailable or fallback transport used |
| TURN unavailable | no false “internet ready” claim; actionable connection failure |
| packet loss increases | measured degradation state; captions remain prioritized |
| camera revoked | video/recognition stop honestly; audio/text may continue |
| mic revoked | video/sign/text continue |
| recognition model fails | call continues; caption subsystem shows unavailable |
| caption message duplicated | one transcript entry |
| caption arrives out of order | deterministic ordering |
| provisional caption retracted | removed/replaced without becoming final history |
| remote peer refreshes | stale peer cleaned up; bounded reconnect/rejoin |
| mobile rotates | video/captions remain usable and do not obscure signer |
| screen reader enabled | committed updates useful; no frame-level announcement flood |

## 19. Performance experiments

Measure on at least:
- same-machine/local test;
- same LAN two-device;
- different network when possible;
- throttled/packet-loss simulation where tooling permits.

Record:
- call setup time;
- recognition delay;
- caption transport/render delay;
- end-to-end caption delay;
- video FPS/resolution;
- RTT/jitter/loss;
- reconnect time;
- CPU/memory where practical.

Report median and tail behavior only from collected data. Never manufacture P95 values.

## 20. Demo diagnostics panel

Judge/debug panel may show:
- connection state;
- signaling state;
- data-channel state;
- selected path category;
- RTT/jitter/loss;
- incoming/outgoing FPS;
- caption event sequence;
- recognition delay;
- caption transport delay where validly measurable;
- model version.

Keep raw network identifiers hidden.

## 21. Security boundary

- validate signaling authorization/room membership;
- never execute arbitrary actions received from peer;
- captions are untrusted text: render as text, never HTML;
- sanitize/log safely;
- bound transcript/message size;
- do not record calls by default;
- recording, if ever added, requires explicit visible consent flow and separate retention policy.

Standard WebRTC transport protections do not by themselves justify broad claims about application-level end-to-end privacy when TURN, signaling, recording, analytics or server-side recognition may be involved.

## 22. Acceptance gates

### P0 demo-ready
- [ ] two browsers can create/join/leave a call repeatedly;
- [ ] tracks stop on exit;
- [ ] committed sign interpretation appears in transcript;
- [ ] caption events are deduplicated and ordered;
- [ ] recognition failure does not kill call;
- [ ] call failure does not kill local interpreter;
- [ ] captions do not obscure hands/face in supported layouts;
- [ ] keyboard-only core call flow works;
- [ ] no raw video is persisted by default;
- [ ] demo limitation (LAN/TURN/etc.) is disclosed.

### P1 internet-ready claim gate
- [ ] TURN path configured and tested;
- [ ] cross-network tests recorded;
- [ ] reconnect tests pass;
- [ ] getStats-based diagnostics work;
- [ ] quality degradation tested;
- [ ] privacy/security review completed.

### Production-roadmap gate
Requires further security review, abuse controls, scalable signaling/TURN infrastructure, monitoring, retention policy, accessibility testing with users, and reliability testing. A hackathon prototype must not silently cross this boundary.

## 23. Judge-safe explanation

Good:
“SANKET keeps media transport, interpretation and caption metadata separate. Recognition can continue locally, final captions are timestamped structured events, and the call degrades toward text rather than pretending unreliable video or predictions are valid.”

Avoid:
“Our AI video calling works everywhere with zero latency and perfect encryption.”

## 24. Implementation backlog

- [ ] versioned signaling schemas;
- [ ] caption event TypeScript/Pydantic models;
- [ ] RTCDataChannel caption path;
- [ ] fallback caption transport;
- [ ] sequence/deduplication logic;
- [ ] getStats sampler;
- [ ] quality-state reducer with hysteresis;
- [ ] caption timing instrumentation;
- [ ] reconnect state machine;
- [ ] TURN configuration flag + diagnostics;
- [ ] responsive non-obscuring caption layouts;
- [ ] screen-reader status strategy;
- [ ] deterministic failure tests;
- [ ] cross-network test report;
- [ ] privacy-redacted diagnostics export.
