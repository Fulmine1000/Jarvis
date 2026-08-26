#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/venv/bin/python"
PLIST_SOURCE="$ROOT/avvio/com.fulmine1000.jarvis.plist"
PLIST_TARGET="$HOME/Library/LaunchAgents/com.fulmine1000.jarvis.plist"
LOG_DIR="$ROOT/logs"

if [ ! -x "$PYTHON" ]; then
    echo "Errore: non trovo il Python del virtual environment: $PYTHON"
    echo "Assicurati che il progetto contenga venv/ prima di installare il guardiano."
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"
launchctl bootout "gui/$(id -u)" "$PLIST_TARGET" 2>/dev/null || true

sed \
    -e "s|__JARVIS_PYTHON__|$PYTHON|g" \
    -e "s|__JARVIS_ROOT__|$ROOT|g" \
    "$PLIST_SOURCE" > "$PLIST_TARGET"

chmod 644 "$PLIST_TARGET"
launchctl bootstrap "gui/$(id -u)" "$PLIST_TARGET"
launchctl enable "gui/$(id -u)/com.fulmine1000.jarvis"
launchctl kickstart -k "gui/$(id -u)/com.fulmine1000.jarvis"

echo "Guardiano vocale J.A.R.V.I.S. attivato."
echo "Jarvis NON viene avviato all'accesso: resta in ascolto della wake word."
echo "Pronuncia: Jarvis, Hey Jarvis oppure Ehi Jarvis."
