#!/usr/bin/env bash
set -euo pipefail

# Prepara whisper.cpp e un modello Whisper BASE multilingue.
# Il modello base riconosce molte lingue con rilevamento automatico; non è
# un modello per una singola lingua. Il download è di circa 150 MB.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/motore_ia/whisper.cpp"
MODEL_DIR="$DIR/models"
MODEL="$MODEL_DIR/ggml-base.bin"
REPO_URL="https://github.com/ggerganov/whisper.cpp.git"
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"

mkdir -p "$ROOT/motore_ia"

# Non creare MODEL_DIR prima del clone: farlo crea una cartella whisper.cpp
# non vuota e git clone fallisce. Se un'esecuzione precedente ha lasciato
# soltanto models/, conserva gli eventuali file e libera la cartella.
if [ ! -d "$DIR/.git" ]; then
  if [ -d "$DIR" ]; then
    EXTRA="$(find "$DIR" -mindepth 1 -maxdepth 1 ! -name models -print | wc -l | tr -d ' ')"
    if [ "$EXTRA" != "0" ]; then
      echo "ERRORE: $DIR esiste ma non è un repository Git riconoscibile." >&2
      echo "Non lo modifico per non cancellare file esistenti. Rinomina la cartella e riprova." >&2
      exit 1
    fi
    if [ -d "$MODEL_DIR" ]; then
      PRESERVE="$ROOT/motore_ia/.whisper-models-preserve"
      if [ -e "$PRESERVE" ]; then
        echo "ERRORE: esiste già $PRESERVE; non sovrascrivo file." >&2
        exit 1
      fi
      mv "$MODEL_DIR" "$PRESERVE"
      rmdir "$DIR"
      if ! git clone --depth 1 --branch v1.5.5 "$REPO_URL" "$DIR"; then
        mkdir -p "$DIR"
        mv "$PRESERVE" "$MODEL_DIR"
        exit 1
      fi
      mkdir -p "$MODEL_DIR"
      cp -R "$PRESERVE/." "$MODEL_DIR/"
      rm -rf "$PRESERVE"
    else
      rmdir "$DIR"
      git clone --depth 1 --branch v1.5.5 "$REPO_URL" "$DIR"
    fi
  else
    git clone --depth 1 --branch v1.5.5 "$REPO_URL" "$DIR"
  fi
fi

mkdir -p "$MODEL_DIR"

if [ ! -x "$DIR/main" ] && [ ! -x "$DIR/build/bin/main" ] && [ ! -x "$DIR/build/bin/whisper-cli" ]; then
  echo "Compilo whisper.cpp per il Mac in uso..."
  if command -v cmake >/dev/null 2>&1; then
    cmake -S "$DIR" -B "$DIR/build" -DCMAKE_BUILD_TYPE=Release
    cmake --build "$DIR/build" --config Release -j2
  else
    make -C "$DIR" -j2
  fi
fi

if [ ! -f "$MODEL" ]; then
  echo "Scarico il modello Whisper BASE multilingue (circa 150 MB)..."
  if command -v curl >/dev/null 2>&1; then
    curl -L --fail --retry 3 "$MODEL_URL" -o "$MODEL"
  else
    echo "ERRORE: serve curl per scaricare il modello." >&2
    exit 1
  fi
fi

if [ ! -s "$MODEL" ]; then
  echo "ERRORE: il modello scaricato è vuoto." >&2
  exit 1
fi

echo
echo "Preparazione completata."
echo "Modello: $MODEL"
if [ -x "$DIR/build/bin/whisper-cli" ]; then
  echo "Eseguibile: $DIR/build/bin/whisper-cli"
elif [ -x "$DIR/build/bin/main" ]; then
  echo "Eseguibile: $DIR/build/bin/main"
elif [ -x "$DIR/main" ]; then
  echo "Eseguibile: $DIR/main"
fi
echo "Riavvia Jarvis: python jarvis.py"
