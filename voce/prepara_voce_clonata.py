#!/usr/bin/env python3
"""Prepara il motore locale XTTS v2 per Jarvis su Mac Intel / High Sierra.

Il preparatore forza:
- macOS deployment target 10.13
- architettura x86_64
- versioni native con wheel compatibili
- constraints anche per le dipendenze transitive di TTS

In questo modo pip non può sostituire grpcio/llvmlite con release moderne
che richiedono macOS 11+ o una compilazione locale.
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
    # Il Mac dell'utente è High Sierra 10.13.6.
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

    # Coqui TTS 0.22 appartiene a un ecosistema di dipendenze datato.
    # Manteniamo pip sotto 25 e installiamo prima i binari nativi.
    run("install", "--upgrade", "pip<25")

    run(
        "install",
        "--only-binary=grpcio,llvmlite,soxr",
        "grpcio==1.59.0",
        "llvmlite==0.41.1",
        "soxr==0.3.6",
    )

    # PIP_CONSTRAINT impedisce a TTS e alle sue dipendenze transitive di
    # rimpiazzare i pin con release moderne incompatibili con High Sierra.
    run(
        "install",
        "--only-binary=grpcio,llvmlite,soxr",
        "torch==2.0.1",
        "torchaudio==2.0.2",
        "TTS==0.22.0",
    )

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
