#!/usr/bin/env python3
"""Scarica il modello vocale italiano maschile Riccardo per Jarvis."""

import hashlib
import os
import sys
import subprocess
import urllib.request
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE, "voce", "modelli")

MODEL_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
    "it/it_IT/riccardo/x_low/it_IT-riccardo-x_low.onnx"
)
CONFIG_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
    "it/it_IT/riccardo/x_low/it_IT-riccardo-x_low.onnx.json"
)

MODEL_PATH = os.path.join(MODEL_DIR, "it_IT-riccardo-x_low.onnx")
CONFIG_PATH = os.path.join(MODEL_DIR, "it_IT-riccardo-x_low.onnx.json")
MODEL_SHA256 = "1368de15f123275a7ef951c9e5e30be0f58a032daa14a0da44037443c1d1d21b"


def scarica(url, destinazione):
    """Scarica il modello usando curl su macOS e urllib come fallback."""
    print(f"Download: {os.path.basename(destinazione)}")

    # Su macOS High Sierra il Python 3.11 installato può non avere
    # una catena CA aggiornata. curl usa invece il trust store di macOS.
    curl = shutil.which("curl") if "shutil" in globals() else None
    if curl:
        risultato = subprocess.run(
            [
                curl,
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--output",
                destinazione,
                url,
            ],
            check=False,
        )
        if risultato.returncode == 0:
            return

    try:
        urllib.request.urlretrieve(url, destinazione)
    except Exception:
        try:
            if os.path.exists(destinazione):
                os.remove(destinazione)
        except OSError:
            pass
        raise


def verifica_modello():
    if not os.path.isfile(MODEL_PATH):
        return False

    sha256 = hashlib.sha256()
    with open(MODEL_PATH, "rb") as file:
        for blocco in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(blocco)

    return sha256.hexdigest() == MODEL_SHA256


def installa_piper():
    """Installa Piper nel virtualenv se il comando non è già disponibile."""
    if shutil.which("piper"):
        print("Piper TTS già disponibile.")
        return True

    pip = os.path.join(sys.prefix, "bin", "pip")
    if not os.path.isfile(pip):
        pip = shutil.which("pip")

    if not pip:
        print("AVVISO: pip non trovato nel virtualenv; Piper non può essere installato automaticamente.")
        return False

    print("Piper TTS non trovato: installazione di piper-tts==1.3.0...")
    risultato = subprocess.run(
        [pip, "install", "--only-binary=:all:", "piper-tts==1.3.0"],
        check=False,
    )

    if risultato.returncode != 0:
        print("AVVISO: installazione di Piper non riuscita.")
        print("Il modello Riccardo è stato comunque preparato.")
        return False

    return shutil.which("piper") is not None

def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    if not verifica_modello():
        scarica(MODEL_URL, MODEL_PATH)

    if not verifica_modello():
        print("ERRORE: checksum del modello non valido.")
        try:
            os.remove(MODEL_PATH)
        except OSError:
            pass
        return 1

    if not os.path.isfile(CONFIG_PATH):
        scarica(CONFIG_URL, CONFIG_PATH)

    piper_ok = installa_piper()

    print("Voce italiana maschile Riccardo installata.")
    print(f"Modello: {MODEL_PATH}")
    if piper_ok:
        print("Motore Piper TTS: disponibile.")
    else:
        print("Motore Piper TTS: NON disponibile; Jarvis userà temporaneamente la voce di sistema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
