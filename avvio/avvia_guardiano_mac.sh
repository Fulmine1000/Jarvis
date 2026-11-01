#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/venv/bin/python"
ENV_FILE="$HOME/.config/jarvis/gateway.env"

if [ ! -x "$PYTHON" ]; then
    echo "Python del virtual environment non trovato: $PYTHON" >&2
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Configurazione gateway assente: $ENV_FILE" >&2
    echo "Eseguire prima avvio/installa_avvio_mac.sh." >&2
    exit 1
fi

# File locale creato dall'installer, leggibile soltanto dall'utente.
if [ "$(stat -f '%Lp' "$ENV_FILE" 2>/dev/null || stat -c '%a' "$ENV_FILE")" != "600" ]; then
    chmod 600 "$ENV_FILE"
fi

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

exec "$PYTHON" "$ROOT/avvio/guardiano_wake.py"
