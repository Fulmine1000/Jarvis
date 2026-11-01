#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/venv/bin/python"
PLIST_SOURCE="$ROOT/avvio/com.fulmine1000.jarvis.plist"
PLIST_TARGET="$HOME/Library/LaunchAgents/com.fulmine1000.jarvis.plist"
LOG_DIR="$ROOT/logs"
CONFIG_DIR="$HOME/.config/jarvis"
GATEWAY_ENV="$CONFIG_DIR/gateway.env"

if [ ! -x "$PYTHON" ]; then
    echo "Errore: non trovo il Python del virtual environment: $PYTHON"
    echo "Assicurati che il progetto contenga venv/ prima di installare il guardiano."
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR" "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"

if [ ! -f "$GATEWAY_ENV" ]; then
    if ! command -v openssl >/dev/null 2>&1; then
        echo "Errore: openssl è necessario per generare il token gateway."
        exit 1
    fi
    TOKEN="$(openssl rand -hex 32)"
    umask 077
    {
        echo "JARVIS_GATEWAY_ENABLED=1"
        printf 'JARVIS_GATEWAY_TOKEN=%s\n' "$TOKEN"
        echo "JARVIS_GATEWAY_HOST=127.0.0.1"
        echo "JARVIS_GATEWAY_PORT=8767"
    } > "$GATEWAY_ENV"
    chmod 600 "$GATEWAY_ENV"
    unset TOKEN
    echo "Creato token gateway in $GATEWAY_ENV (permessi 600)."
else
    chmod 600 "$GATEWAY_ENV"
    if ! grep -q '^JARVIS_GATEWAY_ENABLED=1$' "$GATEWAY_ENV" || ! grep -q '^JARVIS_GATEWAY_TOKEN=.' "$GATEWAY_ENV"; then
        echo "Errore: $GATEWAY_ENV esiste ma non contiene le impostazioni gateway richieste."
        echo "Correggere il file manualmente; non viene sovrascritto per proteggere i segreti."
        exit 1
    fi
fi

launchctl bootout "gui/$(id -u)" "$PLIST_TARGET" 2>/dev/null || true
sed -e "s|__JARVIS_ROOT__|$ROOT|g" "$PLIST_SOURCE" > "$PLIST_TARGET"
chmod 644 "$PLIST_TARGET"
chmod +x "$ROOT/avvio/avvia_guardiano_mac.sh"
launchctl bootstrap "gui/$(id -u)" "$PLIST_TARGET"
launchctl enable "gui/$(id -u)/com.fulmine1000.jarvis"
launchctl kickstart -k "gui/$(id -u)/com.fulmine1000.jarvis"

echo "Guardiano vocale J.A.R.V.I.S. attivato."
echo "Gateway locale autenticato abilitato su 127.0.0.1:8767."
echo "Token conservato fuori dal repository: $GATEWAY_ENV"
echo "Per leggere il token e configurarlo in AWS, usare il password manager o leggere il file localmente; non inviarlo in chat."
