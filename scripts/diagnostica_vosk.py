#!/usr/bin/env python3
"""Confronta Vosk sul microfono con audio grezzo e filtrato, senza salvare registrazioni.

Dalla cartella principale, con il virtualenv attivo:
    python scripts/diagnostica_vosk.py
Facoltativi:
    python scripts/diagnostica_vosk.py --secondi 20
    python scripts/diagnostica_vosk.py --device 1

Durante il test pronuncia più volte, con una pausa breve fra le frasi:
    "Jarvis"
    "Jarvis, che ore sono?"

L'audio resta in memoria e non viene scritto su disco.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from voce.filtro_rumore import FiltroRumore
from voce.riconoscimento import RiconoscitoreVoce


def rms_pcm16(audio: bytes) -> int:
    count = len(audio) // 2
    if count <= 0:
        return 0
    values = struct.unpack("<" + "h" * count, audio[: count * 2])
    return int(math.sqrt(sum(value * value for value in values) / count))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", type=int, default=None, help="indice del microfono")
    parser.add_argument("--secondi", type=int, default=15, help="durata del test (default: 15)")
    args = parser.parse_args()

    try:
        import sounddevice as sd
        from vosk import KaldiRecognizer, Model
    except (ImportError, OSError) as errore:
        print(f"ERRORE: dipendenza audio/Vosk non disponibile: {errore}")
        return 2

    modello_path = RiconoscitoreVoce._modello_italiano_predefinito(BASE)
    if not os.path.isdir(modello_path):
        print(f"ERRORE: modello Vosk non trovato: {modello_path}")
        return 2

    try:
        dispositivi = sd.query_devices()
        ingressi = [
            i for i, device in enumerate(dispositivi)
            if int(device.get("max_input_channels", 0)) > 0
        ]
    except Exception as errore:
        print(f"ERRORE: impossibile elencare i microfoni: {errore}")
        return 2

    device = args.device
    if device is None:
        try:
            device = int(sd.default.device[0])
        except (TypeError, ValueError):
            device = -1
    if device not in ingressi:
        print("ERRORE: nessun microfono predefinito valido.")
        print("Dispositivi con ingresso:")
        for index in ingressi:
            print(f"  [{index}] {dispositivi[index]['name']}")
        print("Riprova con --device INDICE.")
        return 2

    print("=== DIAGNOSTICA VOSK: AUDIO GREZZO VS FILTRATO ===")
    print(f"Microfono: [{device}] {dispositivi[device]['name']}")
    print(f"Modello: {modello_path}")
    print("Non vengono salvati file audio.")
    print("Pronuncia più volte: 'Jarvis', pausa, 'Jarvis, che ore sono?'")
    print("Il confronto è indicativo: due riconoscitori ricevono lo stesso audio,")
    print("uno grezzo e uno filtrato.")

    try:
        model = Model(modello_path)
        raw_rec = KaldiRecognizer(model, 16000)
        filtered_rec = KaldiRecognizer(model, 16000)
        for rec in (raw_rec, filtered_rec):
            set_words = getattr(rec, "SetWords", None)
            if callable(set_words):
                set_words(True)
        filtro = FiltroRumore(frequenza=16000, livello=2)
        filtro.avvia()
        print(f"Filtro: {filtro.stato().get('modalita')}")

        duration = max(5, min(60, int(args.secondi)))
        last_report = time.monotonic()
        count = 0
        raw_rms_sum = 0
        filtered_rms_sum = 0
        with sd.RawInputStream(
            device=device,
            samplerate=16000,
            blocksize=1600,
            dtype="int16",
            channels=1,
        ) as stream:
            started = time.monotonic()
            while time.monotonic() - started < duration:
                block, overflowed = stream.read(1600)
                raw = bytes(block)
                filtered = filtro.processa(raw)
                count += 1
                raw_rms_sum += rms_pcm16(raw)
                filtered_rms_sum += rms_pcm16(filtered)

                raw_done = raw_rec.AcceptWaveform(raw)
                filtered_done = filtered_rec.AcceptWaveform(filtered)
                if raw_done:
                    result = json.loads(raw_rec.Result())
                    print(f"GREZZO    finale: {result.get('text', '') or '(vuoto)'}")
                if filtered_done:
                    result = json.loads(filtered_rec.Result())
                    print(f"FILTRATO  finale: {result.get('text', '') or '(vuoto)'}")

                now = time.monotonic()
                if now - last_report >= 3.0:
                    raw_partial = json.loads(raw_rec.PartialResult()).get("partial", "")
                    filtered_partial = json.loads(filtered_rec.PartialResult()).get("partial", "")
                    print(
                        f"[{int(now - started):02d}s] "
                        f"RMS grezzo={rms_pcm16(raw):4d}, "
                        f"filtrato={rms_pcm16(filtered):4d}, "
                        f"parziale grezzo={raw_partial!r}, "
                        f"parziale filtrato={filtered_partial!r}"
                    )
                    if overflowed:
                        print("AVVISO: il flusso audio ha segnalato un overflow.")
                    last_report = now

        raw_final = json.loads(raw_rec.FinalResult()).get("text", "")
        filtered_final = json.loads(filtered_rec.FinalResult()).get("text", "")
        print("\n=== RIEPILOGO ===")
        print(f"Blocchi analizzati: {count}")
        print(f"RMS medio grezzo: {raw_rms_sum // max(count, 1)}")
        print(f"RMS medio filtrato: {filtered_rms_sum // max(count, 1)}")
        print(f"Finale grezzo: {raw_final!r}")
        print(f"Finale filtrato: {filtered_final!r}")
        print("\nConfronta soprattutto se 'Jarvis' appare nel grezzo ma scompare nel filtrato.")
        return 0
    except (OSError, RuntimeError, ValueError, TypeError) as errore:
        print(f"ERRORE DURANTE LA DIAGNOSTICA: {type(errore).__name__}: {errore}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
