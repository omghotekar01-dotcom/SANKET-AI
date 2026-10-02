#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON_BIN:-python3}"
[[ -x .venv/bin/python ]] && PY=.venv/bin/python
"$PY" -m ml.training.train_template
"$PY" -m ml.evaluation.report
