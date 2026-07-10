#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "$(dirname "$0")/common.sh"
activate_venv_if_exists

python -m uvicorn src.api:app --host 127.0.0.1 --port 7800
