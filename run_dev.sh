#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" scripts/check_env.py || true
exec "$PYTHON_BIN" scripts/run_dev.py
