#!/usr/bin/env bash

is_windows_shell() {
  [[ "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* || -n "${MINGW_PREFIX:-}" ]]
}

resolve_python() {
  # Git Bash on Windows: `python3` is often a broken alias (exit code 49).
  if is_windows_shell; then
    if command -v python >/dev/null 2>&1; then
      echo python
      return 0
    fi
  fi

  if command -v python3 >/dev/null 2>&1; then
    echo python3
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    echo python
    return 0
  fi

  echo "Python not found. Install Python 3.10+ first." >&2
  return 1
}

activate_venv_if_exists() {
  if [[ -f ".venv/Scripts/activate" ]]; then
    # Windows (Git Bash / CMD venv)
    # shellcheck disable=SC1091
    source ".venv/Scripts/activate"
  elif [[ -f ".venv/bin/activate" ]]; then
    # macOS / Linux
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
  else
    echo "Virtual environment not found. Run setup_venv first." >&2
    return 1
  fi
}
