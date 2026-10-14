#!/usr/bin/env python3
"""Diagnostica il microfono e il riconoscimento Vosk senza avviare tutta la GUI."""

from __future__ import annotations

import array
import json
import os
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce


class ConfigDiagnostica:
    def __init__(self, dati):
        self.dati = dati

    def sezione(self, nome):
        valore = self.dati.get(nome, {})
        return valore if isinstance(valore, dict) else {}


def rms_pcm16(audio):
    campioni = array.array("h")
    campioni.frombytes(audio[: len(audio) - (len(audio) % 2)])
    if not campioni:
        return 0
    return int((sum(valore * valore for valore in campioni) / len(campioni)) ** 0.5)


def main():
    durata = 20
    if len(sys.argv) > 1:
        try:
            durata = max(5, min(120, int(sys.argv[1])))
        except ValueError:
            print("Uso: python scripts/diagnostica_voce.py [secondi: 5-120]")
            return 2

    percorso_config = os.path.join(ROOT, "config", "config.json")
    try:
        with open(percorso_config, "r", encoding="utf-8") as file:
            dati = json.load(file)
    except (OSError, ValueError) as errore:
        print(f"Impossibile leggere {percorso_config}: {errore}")
        return 2

    config = ConfigDiagnostica(dati)
    riconoscitore = RiconoscitoreVoce(config)
    ascoltatore = AscoltatoreVoce(frequenza=riconoscitore.sample_rate)

    print("=== Diagnostica vocale Jarvis ===")
    print("La prova registra solo in memoria e non salva l'audio su disco.")
    print(f"Backend richiesto: {'Whisper' if riconoscitore.usa_multilingue else 'Vosk'}")
    print(f"Modello Vosk selezionato/fallback: {riconoscitore.percorso_modello}")
    print(f"Frequenza prevista: {riconoscitore.sample_rate} Hz")
    if not ascoltatore.avvia():
        print(f"ERRORE MICROFONO: {ascoltatore.ultimo_errore}")
        return 1

    try:
        if not riconoscitore.avvia():
            print(f"ERRORE RICONOSCITORE: {riconoscitore.ultimo_errore}")
            return 1

        print(f"Riconoscitore attivo: {riconoscitore.backend_attivo}")
        print(f"Parla normalmente per {durata} secondi.")
        print("Prova: 'Ehi Jarvis, che ore sono?' e poi una frase più lunga.")
        print("Le trascrizioni compariranno appena il riconoscitore chiude una frase.")
        inizio = time.monotonic()
        prossimo_livello = inizio
        livelli = []
        trascrizioni = 0

        while time.monotonic() - inizio < durata:
            audio = ascoltatore.ascolta(timeout=1)
            if not audio:
                continue

            livello = rms_pcm16(audio)
            livelli.append(livello)
            adesso = time.monotonic()
            if adesso >= prossimo_livello:
                print(f"Livello microfono RMS: {livello}")
                prossimo_livello = adesso + 2

            testo = riconoscitore.riconosci(audio)
            if testo:
                trascrizioni += 1
                print(f"TRASCRIZIONE {trascrizioni}: {testo!r}")

        print("\n=== Risultato ===")
        massimo = max(livelli) if livelli else 0
        media = int(sum(livelli) / len(livelli)) if livelli else 0
        print(f"Livello RMS medio: {media}; massimo: {massimo}")
        print(f"Frasi riconosciute: {trascrizioni}")
        if massimo < 150:
            print("DIAGNOSI: il segnale è quasi assente. Controlla ingresso microfono e permessi macOS.")
        elif trascrizioni == 0:
            print("DIAGNOSI: arriva audio, ma non si è chiusa alcuna frase riconosciuta.")
            print("Prova a parlare più vicino al microfono e fai una pausa di circa un secondo.")
        else:
            print("Confronta le righe TRASCRIZIONE con le parole che hai pronunciato.")
        if riconoscitore.ultimo_errore:
            print(f"Ultimo errore del riconoscitore: {riconoscitore.ultimo_errore}")
        return 0
    except KeyboardInterrupt:
        print("\nProva interrotta.")
        return 130
    finally:
        ascoltatore.ferma()
        riconoscitore.ferma()


if __name__ == "__main__":
    raise SystemExit(main())
