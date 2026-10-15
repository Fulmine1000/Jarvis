#!/usr/bin/env python3
"""Diagnostica il microfono usato da Jarvis senza avviare HUD o Vosk.

Eseguire dalla cartella principale:
    python scripts/diagnostica_microfono.py

Il programma mostra i dispositivi d'ingresso e misura per 8 secondi il livello
audio del microfono selezionato. Non salva né riproduce registrazioni.
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
import time
from collections import deque


def rms_pcm16(audio: bytes) -> int:
    campioni = len(audio) // 2
    if campioni <= 0:
        return 0
    valori = struct.unpack("<" + "h" * campioni, audio[: campioni * 2])
    return int(math.sqrt(sum(valore * valore for valore in valori) / campioni))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", type=int, default=None, help="indice del microfono da provare")
    parser.add_argument("--secondi", type=int, default=8, help="durata del test (default: 8)")
    args = parser.parse_args()

    try:
        import sounddevice as sd
    except (ImportError, OSError) as errore:
        print(f"ERRORE: sounddevice/PortAudio non disponibile: {errore}")
        return 2

    try:
        dispositivi = sd.query_devices()
    except Exception as errore:
        print(f"ERRORE: impossibile elencare i dispositivi audio: {errore}")
        return 2

    print("\n=== DISPOSITIVI AUDIO CON INGRESSO ===")
    ingressi = []
    for indice, dispositivo in enumerate(dispositivi):
        if int(dispositivo.get("max_input_channels", 0)) > 0:
            ingressi.append(indice)
            print(
                f"[{indice}] {dispositivo.get('name', 'dispositivo senza nome')} "
                f"(canali={dispositivo.get('max_input_channels')}, "
                f"frequenza_predefinita={dispositivo.get('default_samplerate')})"
            )

    if not ingressi:
        print("ERRORE: PortAudio non rileva alcun dispositivo con ingresso.")
        return 2

    if args.device is not None:
        device = args.device
    else:
        try:
            device = sd.default.device[0]
        except Exception:
            device = None

    if device is None or int(device) < 0 or int(device) not in ingressi:
        print("\nERRORE: non è selezionato un microfono predefinito valido.")
        print("Riprova indicando l'indice mostrato sopra, per esempio:")
        print("python scripts/diagnostica_microfono.py --device 1")
        return 2

    print(f"\nMicrofono scelto: [{device}] {dispositivi[int(device)]['name']}")
    print("Test in corso. Parla normalmente per alcuni secondi quando richiesto.")
    livelli = deque(maxlen=10)

    def callback(indata, frames, tempo_audio, stato):
        if stato:
            print(f"AVVISO AUDIO: {stato}", file=sys.stderr)
        livelli.append(rms_pcm16(bytes(indata)))

    try:
        with sd.RawInputStream(
            device=int(device),
            samplerate=16000,
            blocksize=1600,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            durata = max(3, min(30, int(args.secondi)))
            for secondo in range(durata):
                time.sleep(1)
                valori = list(livelli)
                media = int(sum(valori) / len(valori)) if valori else 0
                picco = max(valori) if valori else 0
                print(f"{secondo + 1:02d}s  RMS medio={media:5d}  RMS massimo={picco:5d}")

    except (OSError, RuntimeError, ValueError) as errore:
        print(f"ERRORE APERTURA/LETTURA MICROFONO: {errore}")
        print("Controlla il microfono selezionato e i permessi di macOS per Terminale.")
        return 2

    valori = list(livelli)
    if not valori or max(valori) < 20:
        print("\nESITO: il segnale è assente o quasi nullo.")
        print("Controlla Preferenze di Sistema > Sicurezza e Privacy > Privacy > Microfono,")
        print("autorizza Terminale, poi verifica il microfono d'ingresso nelle impostazioni Suono.")
        return 1

    if max(valori) < 150:
        print("\nESITO: il microfono riceve un segnale molto debole.")
        print("Avvicinati al microfono o prova un altro dispositivo d'ingresso.")
        return 1

    print("\nESITO: il microfono riceve audio. Se Jarvis non trascrive, il problema è a valle")
    print("(filtro, segmentazione audio o riconoscimento Vosk), non l'assenza del segnale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
