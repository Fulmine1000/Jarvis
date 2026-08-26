#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/venv/bin/python"
PLIST_SOURCE="$ROOT/avvio/com.fulmine1000.jarvis.plist"
PLIST_TARGET="$HOME/Library/LaunchAgents/com.fulmine1000.jarvis.plist"
LOG_DIR="$ROOT/logs"

if [ ! -x "$PYTHON" ]; then
    echo "Errore: non trovo il Python del virtual environment: $PYTHON"
    echo "Assicurati che il progetto contenga venv/ prima di installare l'avvio automatico."
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

# Rimuove un'eventuale installazione precedente.
launchctl bootout "gui/$(id -u)" "$PLIST_TARGET" 2>/dev/null || true

sed \
    -e "s|__JARVIS_PYTHON__|$PYTHON|g" \
    -e "s|__JARVIS_ROOT__|$ROOT|g" \
    "$PLIST_SOURCE" > "$PLIST_TARGET"

chmod 644 "$PLIST_TARGET"

launchctl bootstrap "gui/$(id -u)" "$PLIST_TARGET"
launchctl enable "gui/$(id -u)/com.fulmine1000.jarvis"

# Avvia immediatamente Jarvis, senza aspettare il prossimo login.
launchctl kickstart -k "gui/$(id -u)/com.fulmine1000.jarvis"

echo "J.A.R.V.I.S. configurato per l'avvio automatico."
echo "Da ora verrà avviato automaticamente al login di macOS."
