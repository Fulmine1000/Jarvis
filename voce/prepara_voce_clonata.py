#!/usr/bin/env python3
"""Prepara il motore locale di clonazione vocale Jarvis.

Profilo mirato: Mac Intel / macOS High Sierra / Python 3.11.
Evita build da sorgente delle dipendenze native usando versioni con wheel
compatibili quando disponibili.
"""
from __future__ import annotations

import platform
import subprocess
import sys


def run(*args: str) -> None:
    print(">>>", " ".join(args))
    subprocess.check_call([sys.executable, "-m", "pip", *args])


def main() -> int:
    if platform.system() != "Darwin":
        print("Questo preparatore e pensato per macOS.")
        return 1

    machine = platform.machine().lower()
    if machine not in {"x86_64", "amd64"}:
        print(f"Architettura rilevata: {machine}. Questo profilo e per Mac Intel.")
        return 1

    version = sys.version_info
    if version[:2] != (3, 11):
        print(f"Python rilevato: {version.major}.{version.minor}. Usa Python 3.11.")
        return 1

    # Manteniamo pip sotto 25 per evitare incompatibilita con il vecchio
    # ecosistema di Coqui TTS 0.22.
    run("install", "--upgrade", "pip<25")

    # PyTorch 2.0.1 / torchaudio 2.0.2 sono il profilo previsto da TTS 0.22.
    run("install", "torch==2.0.1", "torchaudio==2.0.2")

    # Queste versioni dispongono di wheel CPython 3.11 macOS Intel:
    # - grpcio 1.59.0: macOS 10.10+ universal2
    # - llvmlite 0.41.1: macOS 10.9+ x86_64
    # - soxr 0.3.6: macOS 10.9+ x86_64
    #
    # --only-binary impedisce a pip di ricadere in compilazioni locali
    # che su High Sierra possono fallire per assenza di Python.h/toolchain.
    run(
        "install",
        "--only-binary=grpcio,llvmlite,soxr",
        "grpcio==1.59.0",
        "llvmlite==0.41.1",
        "soxr==0.3.6",
    )

    run("install", "TTS==0.22.0")

    print()
    print("Motore XTTS v2 installato.")
    print("Avvia Jarvis e controlla che compaia:")
    print("  Caricamento voce locale Jarvis (XTTS v2)...")
    print("  Motore vocale XTTS v2 pronto")
    print()
    print("Il campione viene cercato automaticamente sul Desktop:")
    print("  jarvis-are-you-there-at-your-service-sir.wav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
