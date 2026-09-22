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

    print("Voce italiana maschile Riccardo installata.")
    print(f"Modello: {MODEL_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
