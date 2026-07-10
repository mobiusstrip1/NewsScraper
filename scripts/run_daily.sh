#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "$(dirname "$0")/common.sh"
activate_venv_if_exists

mkdir -p logs digest data
python src/main.py >> logs/run.log 2>&1
