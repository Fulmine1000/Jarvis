#!/usr/bin/env python3
"""Prepara XTTS v2 per Jarvis su Mac Intel / High Sierra.

Il profilo blocca le dipendenze note per TTS 0.22/XTTS v2:
- macOS deployment target 10.13
- architettura x86_64
- torch/torchaudio 2.1.0
- transformers 4.36.2
- tokenizers 0.15.2
- numpy 1.26.4
- wheel native compatibili con High Sierra

Il post-processing della voce viene gestito da voce/tts.py.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONSTRAINTS = ROOT / "requirements-voce-clonata.txt"


def run(*args: str) -> None:
    env = os.environ.copy()
    env["MACOSX_DEPLOYMENT_TARGET"] = "10.13"
    env["ARCHFLAGS"] = "-arch x86_64"
    env["PIP_CONSTRAINT"] = str(CONSTRAINTS)
    print(">>>", " ".join(args))
    subprocess.check_call([sys.executable, "-m", "pip", *args], env=env)


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

    if not CONSTRAINTS.is_file():
        print(f"File constraints non trovato: {CONSTRAINTS}")
        return 1

    run("install", "--upgrade", "pip<25")

    run(
        "install",
        "--only-binary=grpcio,llvmlite,soxr",
        "grpcio==1.59.0",
        "llvmlite==0.41.1",
        "soxr==0.3.6",
    )

    run(
        "install",
        "--only-binary=grpcio,llvmlite,soxr",
        "torch==2.1.0",
        "torchaudio==2.1.0",
        "TTS==0.22.0",
        "transformers==4.36.2",
        "tokenizers==0.15.2",
        "numpy==1.26.4",
    )

    print()
    print("Motore XTTS v2 e profilo vocale cinematografico installati.")
    print("Il campione viene cercato automaticamente sul Desktop:")
    print("  jarvis-are-you-there-at-your-service-sir.wav")
    print()
    print("Il profilo cinematografico modifica leggermente pitch e ritmo")
    print("della voce generata; non richiede servizi cloud.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
