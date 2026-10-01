# SANKET AI — Deployment, Operations and Offline Guide

## 1. Development topology

Default hackathon:
- frontend: localhost Vite/React;
- backend: localhost FastAPI;
- model: local file;
- database: local SQLite;
- sign clips: local assets.

Core interpretation must not require internet.

## 2. One-command startup

Windows:
`run_dev.bat`

Linux/macOS:
`./run_dev.sh`

Scripts should:
- check Python;
- check Node;
- create/install environment when safe;
- verify model artifact;
- start backend;
- start frontend;
- print URLs;
- preserve readable logs.

## 3. Production-like local build

Provide:
- frontend production build;
- FastAPI static serving or reverse proxy option;
- environment config;
- deterministic model path.

## 4. Environment variables

Examples:
- APP_ENV
- API_HOST
- API_PORT
- WEB_ORIGIN
- MODEL_PATH
- DB_PATH
- ENABLE_RAW_VIDEO_CAPTURE=false
- ENABLE_EXPERIMENTAL_CALLING=true/false

No required secret should exist for core demo.

## 5. Offline assets

Bundle:
- UI assets;
- fonts if licensing allows;
- model;
- label map;
- feature schema;
- reverse sign clips required for demo;
- demo videos.

Do not depend on CDN fonts/icons during judging.

## 6. Offline validation

Before event:
- disconnect Wi-Fi;
- reboot;
- start from scratch;
- run entire P0 demo;
- verify reverse clips;
- verify TTS behavior;
- verify demo replay.

## 7. Logging

Use separate logs:
- backend runtime;
- recognition metrics;
- errors.

Cap file size or use rotating logs.

## 8. Health checks

`/api/health` should return:
- API status;
- model loaded;
- model version;
- DB status;
- feature schema;
- optional inference self-test.

## 9. Readiness check

Before user can start:
- camera available or demo mode selected;
- model loaded;
- label map matches;
- backend connected.

## 10. Packaging

Possible hackathon packaging:
- repository + setup scripts;
- prebuilt frontend;
- zipped portable environment only if allowed;
- optional Docker for judges, but do not make Docker mandatory if it complicates webcam access.

## 11. Docker

Use only if stable.

Challenges:
- camera passthrough;
- GPU runtime;
- Windows setup.

Prefer native startup for the live demo if Docker creates risk.

## 12. Crash recovery

Backend:
- startup should be idempotent;
- DB migrations safe;
- model load failure clear.

Frontend:
- reconnect websocket;
- preserve local settings;
- allow restart interpretation.

## 13. Version display

Diagnostics:
- app version;
- git commit short SHA if available;
- model version;
- feature schema.

This helps debug mismatched laptops.

## 14. Release archive

Before hackathon final:
- tag release;
- create backup zip;
- export model;
- copy demo assets;
- keep offline dependency caches where allowed.

## 15. Post-hackathon deployment path

Potential:
- web PWA with browser inference;
- desktop app;
- Android app;
- institution kiosk;
- SDK.

Choose after validating actual user needs.
