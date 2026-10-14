#!/usr/bin/env bash
set -euo pipefail

# Scarica il modello ufficiale italiano completo di Vosk senza sovrascrivere file.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/vosk-model-it-0.22"
URL="https://alphacephei.com/vosk/models/vosk-model-it-0.22.zip"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/jarvis-vosk-it.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

if [ -d "$DEST" ]; then
  echo "Il modello completo esiste già: $DEST"
  echo "Non scarico né sovrascrivo nulla."
  exit 0
fi

for comando in curl unzip; do
  if ! command -v "$comando" >/dev/null 2>&1; then
    echo "ERRORE: comando richiesto non trovato: $comando" >&2
    exit 1
  fi
done

echo "Scarico il modello Vosk italiano completo (download grande, circa 1,2 GB una volta installato)..."
curl -L --fail --retry 3 "$URL" -o "$TMP/modello.zip"

echo "Verifico l'archivio..."
unzip -tq "$TMP/modello.zip"

echo "Estraggo il modello..."
mkdir "$TMP/estratto"
unzip -q "$TMP/modello.zip" -d "$TMP/estratto"

SORGENTE="$TMP/estratto/vosk-model-it-0.22"
if [ ! -d "$SORGENTE" ]; then
  SORGENTE="$(find "$TMP/estratto" -type d -name 'vosk-model-it-0.22' -print -quit)"
fi

if [ -z "${SORGENTE:-}" ] || [ ! -d "$SORGENTE" ]; then
  echo "ERRORE: l'archivio non contiene la cartella attesa vosk-model-it-0.22." >&2
  exit 1
fi

if [ ! -d "$SORGENTE/am" ] || [ ! -d "$SORGENTE/conf" ]; then
  echo "ERRORE: il modello estratto non contiene le cartelle am e conf." >&2
  exit 1
fi

mv "$SORGENTE" "$DEST"
echo
echo "Modello installato: $DEST"
echo "Jarvis lo selezionerà automaticamente al prossimo avvio."
echo "Per tornare al modello leggero, rinomina la cartella completa oppure imposta"
echo '"modello_riconoscimento": "vosk-model-small-it-0.22" nella sezione voce di config/config.json.'
