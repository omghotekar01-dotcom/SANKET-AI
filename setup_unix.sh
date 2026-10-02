#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r apps/api/requirements-dev.txt
pip install -r apps/api/requirements-vision.txt
(cd apps/web && npm install)
python -m pytest apps/api/tests -q
echo "Setup complete. Run ./run_dev.sh"
