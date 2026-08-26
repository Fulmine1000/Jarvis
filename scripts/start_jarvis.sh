#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

if [ -f "venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "venv/bin/activate"
fi

exec python3 jarvis.py
