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
    curl = shutil.which("curl")
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
    """Installa il binario Piper macOS x86_64 senza dipendere da onnxruntime."""
    destinazione = os.path.join(BASE, "voce", "bin")
    piper_path = os.path.join(destinazione, "piper")

    if os.path.isfile(piper_path) and os.access(piper_path, os.X_OK):
        print("Piper TTS già disponibile.")
        return True

    if sys.platform != "darwin" or os.uname().machine not in ("x86_64", "amd64"):
        print("AVVISO: installazione automatica del binario Piper prevista per macOS Intel.")
        return False

    url = (
        "https://github.com/rhasspy/piper/releases/download/"
        "2023.11.14-2/piper_macos_x64.tar.gz"
    )
    phonemize_url = (
        "https://github.com/rhasspy/piper-phonemize/releases/download/"
        "2023.11.14-4/piper-phonemize_macos_x64.tar.gz"
    )
    archivio = os.path.join(MODEL_DIR, "piper_macos_x64.tar.gz")
    archivio_phonemize = os.path.join(
        MODEL_DIR, "piper-phonemize_macos_x64.tar.gz"
    )
    temporanea = os.path.join(MODEL_DIR, "_piper_extract")
    lib_destinazione = os.path.join(destinazione, "piper-phonemize", "lib")

    print("Piper Python non è installabile su High Sierra perché manca una wheel compatibile di onnxruntime.")
    print("Scarico invece il binario Piper macOS Intel ufficiale e le librerie runtime...")

    try:
        scarica(url, archivio)
        scarica(phonemize_url, archivio_phonemize)

        if os.path.isdir(temporanea):
            subprocess.run(["rm", "-rf", temporanea], check=False)
        os.makedirs(temporanea, exist_ok=True)

        risultato = subprocess.run(
            ["tar", "-xzf", archivio, "-C", temporanea],
            check=False,
        )
        if risultato.returncode != 0:
            raise RuntimeError("estrazione del binario Piper fallita")

        risultato = subprocess.run(
            ["tar", "-xzf", archivio_phonemize, "-C", temporanea],
            check=False,
        )
        if risultato.returncode != 0:
            raise RuntimeError("estrazione delle librerie Piper fallita")

        trovato = None
        for radice, _, file in os.walk(temporanea):
            candidato = os.path.join(radice, "piper")
            if os.path.isfile(candidato):
                trovato = candidato
                break

        if not trovato:
            raise RuntimeError("binario Piper non trovato negli archivi")

        lib_origine = None
        for radice, directory, _ in os.walk(temporanea):
            if os.path.basename(radice) == "lib" and os.path.basename(os.path.dirname(radice)) == "piper-phonemize":
                lib_origine = radice
                break

        if not lib_origine:
            raise RuntimeError("librerie piper-phonemize non trovate nell'archivio")

        os.makedirs(destinazione, exist_ok=True)
        os.makedirs(lib_destinazione, exist_ok=True)

        shutil.copy2(trovato, piper_path)
        os.chmod(piper_path, 0o755)

        for nome in os.listdir(lib_origine):
            origine = os.path.join(lib_origine, nome)
            destinazione_lib = os.path.join(lib_destinazione, nome)
            if os.path.isfile(origine):
                shutil.copy2(origine, destinazione_lib)

        # Il binario ufficiale usa @rpath per le dylib. Aggiungiamo una
        # rpath relativa al binario, così Jarvis resta portabile e non
        # dipende dal percorso assoluto dell'utente.
        install_name_tool = shutil.which("install_name_tool")
        if install_name_tool:
            risultato = subprocess.run(
                [
                    install_name_tool,
                    "-add_rpath",
                    "@executable_path/piper-phonemize/lib",
                    piper_path,
                ],
                check=False,
            )
            if risultato.returncode != 0:
                raise RuntimeError("configurazione della rpath di Piper fallita")
        else:
            raise RuntimeError("install_name_tool non disponibile")

        # Controllo reale: non basta che il file esista; Piper deve poter
        # essere avviato sul Mac prima di dichiararlo disponibile.
        controllo = subprocess.run(
            [piper_path, "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        if controllo.returncode != 0:
            errore = controllo.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                "Piper installato ma non avviabile"
                + (f": {errore}" if errore else "")
            )

        print(f"Piper installato: {piper_path}")
        return True
    except Exception as errore:
        print(f"AVVISO: installazione del binario Piper non riuscita: {errore}")
        return False
    finally:
        try:
            if os.path.isdir(temporanea):
                subprocess.run(["rm", "-rf", temporanea], check=False)
            for file_temporaneo in (archivio, archivio_phonemize):
                if os.path.isfile(file_temporaneo):
                    os.remove(file_temporaneo)
        except OSError:
            pass


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
