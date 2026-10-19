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


def statistiche_pcm16(audio):
    """Restituisce RMS, picco assoluto, campioni saturi e campioni totali."""
    campioni = array.array("h")
    campioni.frombytes(audio[: len(audio) - (len(audio) % 2)])
    if not campioni:
        return 0, 0, 0, 0
    rms = int((sum(valore * valore for valore in campioni) / len(campioni)) ** 0.5)
    picco = max(abs(valore) for valore in campioni)
    saturi = sum(1 for valore in campioni if abs(valore) >= 32760)
    return rms, picco, saturi, len(campioni)


def rms_pcm16(audio):
    """Compatibilità con gli script che usano la funzione RMS."""
    return statistiche_pcm16(audio)[0]


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
        print("Ingressi audio disponibili:")
        try:
            import sounddevice as sd
            for indice, dispositivo in enumerate(sd.query_devices()):
                if int(dispositivo.get("max_input_channels", 0) or 0) > 0:
                    print(
                        f"  {indice}: {dispositivo.get('name')} "
                        f"({dispositivo.get('max_input_channels')} canali in ingresso)"
                    )
        except Exception as errore:
            print(f"Impossibile elencare gli ingressi: {errore}")
        print("Per forzare un ingresso: JARVIS_AUDIO_DEVICE=0 python scripts/diagnostica_voce.py 30")
        return 1

    stato_microfono = ascoltatore.stato()
    print(
        "Ingresso audio attivo: "
        f"{stato_microfono.get('dispositivo_attivo')} "
        f"(richiesto: {stato_microfono.get('dispositivo_richiesto')})"
    )

    try:
        if not riconoscitore.avvia():
            print(f"ERRORE RICONOSCITORE: {riconoscitore.ultimo_errore}")
            return 1

        print(f"Riconoscitore attivo: {riconoscitore.backend_attivo}")
        print(f"Parla normalmente per {durata} secondi.")
        print("Prova: 'Ehi Jarvis, che ore sono?' e poi una frase più lunga.")
        print("Le trascrizioni compariranno appena il riconoscitore chiude una frase.")
        print("Non vengono salvati audio o trascrizioni in file.")
        inizio = time.monotonic()
        prossimo_livello = inizio
        livelli = []
        picco_massimo = 0
        campioni_saturi = 0
        campioni_totali = 0
        trascrizioni = 0

        while time.monotonic() - inizio < durata:
            audio = ascoltatore.ascolta(timeout=1)
            if not audio:
                continue

            livello, picco, saturi, totale = statistiche_pcm16(audio)
            livelli.append(livello)
            picco_massimo = max(picco_massimo, picco)
            campioni_saturi += saturi
            campioni_totali += totale
            adesso = time.monotonic()
            if adesso >= prossimo_livello:
                print(f"Audio RMS: {livello}; picco: {picco}; campioni saturi nel blocco: {saturi}/{totale}")
                prossimo_livello = adesso + 2

            testo = riconoscitore.riconosci(audio)
            if testo:
                trascrizioni += 1
                grezzo = riconoscitore.ultima_trascrizione_grezza
                normalizzato = riconoscitore.ultima_trascrizione_normalizzata
                confidenza = riconoscitore.ultima_confidenza_media
                parole = riconoscitore.ultime_parole_riconosciute
                print(f"TRASCRIZIONE GREZZA {trascrizioni}: {grezzo!r}")
                if normalizzato and normalizzato != grezzo:
                    print(f"TRASCRIZIONE NORMALIZZATA {trascrizioni}: {normalizzato!r}")
                if confidenza is not None:
                    print(f"Confidenza media parole Vosk (solo indicativa): {confidenza:.3f}")
                if parole:
                    print("Parole Vosk: " + ", ".join(parole))

        print("\n=== Risultato ===")
        massimo = max(livelli) if livelli else 0
        media = int(sum(livelli) / len(livelli)) if livelli else 0
        percentuale_satura = (
            100.0 * campioni_saturi / campioni_totali if campioni_totali else 0.0
        )
        print(f"Livello RMS medio: {media}; massimo RMS: {massimo}; picco assoluto: {picco_massimo}")
        print(f"Campioni prossimi alla saturazione: {percentuale_satura:.3f}%")
        print(f"Frasi riconosciute: {trascrizioni}")
        if percentuale_satura > 1.0:
            print("DIAGNOSI: possibile clipping. Abbassa il guadagno del microfono o allontanalo.")
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
