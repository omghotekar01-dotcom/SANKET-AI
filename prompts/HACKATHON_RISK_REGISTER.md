# SANKET AI — Hackathon Risk Register

| Risk | Probability | Impact | Early Signal | Mitigation | Fallback |
|---|---|---|---|---|---|
| Camera tracking unreliable in venue lighting | Medium | High | landmark quality drops | test lighting, framing guide, exposure | demo replay |
| Dataset too small | High | High | overfit train accuracy | restrict vocabulary, signer split | use smaller reliable demo set |
| Similar signs confused | High | High | confusion matrix clusters | collect hard negatives, use face/pose/motion | remove unstable sign |
| Model too slow | Medium | High | P95 latency rises | smaller model, lower FPS | prerecorded same-pipeline demo |
| MediaPipe version mismatch | Medium | Medium | startup/import errors | pin known working version | frozen environment |
| WebRTC fails on network | Medium | Medium | ICE failure | LAN test, local signaling | skip live call; show core interpreter |
| Speech recognition unavailable | High | Low | browser API absent | typed fallback | typing |
| TTS voice missing | Medium | Low | API returns no voices | text output | text-only |
| Reverse ISL clip missing | Medium | Medium | lookup fails | preload demo clips | text/fingerspelling fallback |
| Braille claim challenged | Medium | Medium | judge asks about translation | precise wording | show semantic accessible text |
| Judge asks “how many signs?” | Certain | Medium | — | exact tested count | no inflated claim |
| Judge asks accuracy | Certain | High | — | real evaluation report | explain limitations |
| Internet unavailable | Medium | High | no connectivity | local-first | full offline P0 |
| Backend crashes | Medium | High | websocket drops | one-command restart | demo replay |
| One teammate machine differs | Medium | High | package errors | lockfiles, setup script | primary + backup laptop |
| Raw video privacy concern | Medium | High | judge asks storage | off by default | show settings/code path |
| Overbuilding stretch features | High | High | P0 incomplete at hour 12 | strict priorities | freeze P2 |
| UI becomes cluttered | Medium | Medium | signer obscured | camera-first design | presentation mode |
| Unverified ISL sign | Medium | High | reviewer disputes sign | validate references | remove from demo |
| Dataset license conflict | Medium | High | unclear terms | provenance registry | team-collected consented samples |
| LLM fabricates translation | Medium | High | output unsupported by classifier | structured candidate boundary | disable LLM layer |
| Demo confidence fails | Medium | Medium | unclear sign accepted | tune threshold on validation | raise threshold |
| Sign held causes spam | High | Medium | repeated token | cooldown/neutral gate | manual clear |
| Call captions lag | Medium | Medium | stale captions | local inference/data channel | no captions in call demo |
| Emergency feature misunderstood | Medium | Medium | “does it call ambulance?” | clear UI disclaimer | communication-only mode |

## Top five priorities
1. Core recognition reliability.
2. Honest uncertainty rejection.
3. Offline demo path.
4. Reproducible startup on backup machine.
5. Exact claims backed by logs/metrics.

## Freeze rule
If a P1/P2 feature threatens any top-five priority, disable or postpone it.
