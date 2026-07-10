#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "$(dirname "$0")/common.sh"

PYTHON="$(resolve_python)"
echo "Using ${PYTHON} to create virtual environment..."

if ! "$PYTHON" -m venv .venv; then
  echo "Failed to create .venv with ${PYTHON}." >&2
  echo "Try manually: python -m venv .venv" >&2
  exit 1
fi

activate_venv_if_exists
pip install -r requirements.txt

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if [[ -f ".venv/Scripts/activate" ]]; then
  echo "Done. Activate with: source .venv/Scripts/activate"
else
  echo "Done. Activate with: source .venv/bin/activate"
fi
