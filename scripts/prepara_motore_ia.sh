#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IA_DIR="$ROOT/motore_ia"
SRC_DIR="$IA_DIR/llama.cpp"
BIN_DIR="$IA_DIR/bin"
MODEL_DIR="$IA_DIR/modelli"
MODEL="$MODEL_DIR/qwen2.5-0.5b-instruct-q4_0.gguf"

mkdir -p "$BIN_DIR" "$MODEL_DIR"

if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "x86_64" ]; then
  echo "Questo preparatore e pensato per il Mac Intel di Jarvis."
  exit 1
fi

echo "=== Preparazione motore IA locale Jarvis ==="
echo "Sistema: macOS Intel"
echo "Motore: llama.cpp CPU"
echo "Modello: Qwen2.5 0.5B Instruct Q4_0 (~429 MB)"

if [ ! -d "$SRC_DIR/.git" ]; then
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$SRC_DIR"
fi

cd "$SRC_DIR"

git fetch --unshallow >/dev/null 2>&1 || true
if git cat-file -e 3420909^ 2>/dev/null; then
  git checkout --detach 3420909^
else
  echo "ERRORE: non riesco a recuperare il commit compatibile di llama.cpp."
  exit 3
fi

# Compatibilita con AppleClang 10 / macOS High Sierra.
# La versione storica di llama.cpp non dichiara un distruttore per
# common_params_sampling: il compilatore lo genera implicitamente.
# Su AppleClang 10, nel percorso di link di libcommon + llama-server,
# quel distruttore implicito puo produrre un riferimento non risolto.
#
# Rendiamo il distruttore esplicitamente INLINE nella struttura. In questo
# modo il simbolo viene emesso nel contesto in cui common_params_sampling
# viene usato, evitando la dipendenza da una definizione out-of-line nel
# singolo object file di sampling.cpp.
git checkout -- common/common.h common/sampling.cpp
python - <<'PY'
from pathlib import Path

header = Path("common/common.h")
text = header.read_text()
needle = "struct common_params_sampling {\n"
replacement = "struct common_params_sampling {\n    ~common_params_sampling() {}\n"
if needle not in text:
    raise SystemExit("ERRORE: struttura common_params_sampling non trovata")
if "~common_params_sampling()" not in text:
    text = text.replace(needle, replacement, 1)
    header.write_text(text)
PY

export MACOSX_DEPLOYMENT_TARGET=10.13
export CMAKE_OSX_DEPLOYMENT_TARGET=10.13
export CMAKE_OSX_ARCHITECTURES=x86_64

rm -rf build
cmake -S . -B build   -DCMAKE_BUILD_TYPE=Release   -DCMAKE_OSX_DEPLOYMENT_TARGET=10.13   -DCMAKE_OSX_ARCHITECTURES=x86_64   -DGGML_METAL=OFF   -DGGML_BLAS=OFF   -DLLAMA_BUILD_SERVER=ON   -DLLAMA_BUILD_TESTS=OFF

cmake --build build --config Release --target llama-server -j 2

SERVER=""
for candidate in   "$SRC_DIR/build/bin/llama-server"   "$SRC_DIR/build/bin/server"; do
  if [ -x "$candidate" ]; then
    SERVER="$candidate"
    break
  fi
done

if [ -z "$SERVER" ]; then
  echo "ERRORE: llama-server non trovato dopo la compilazione."
  exit 2
fi

cp "$SERVER" "$BIN_DIR/llama-server"
chmod +x "$BIN_DIR/llama-server"

if [ ! -f "$MODEL" ]; then
  echo "Scarico il modello Qwen2.5 0.5B..."
  curl -L --fail --progress-bar     -o "$MODEL"     "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf"
fi

echo ""
echo "Motore IA locale preparato."
echo "Binario: $BIN_DIR/llama-server"
echo "Modello: $MODEL"
echo "Jarvis lo avviera automaticamente quando servira."
