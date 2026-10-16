#!/usr/bin/env python3
"""Diagnostica live del microfono e di Vosk, senza salvare audio su disco.

Eseguire con Jarvis chiuso per evitare che due processi usino contemporaneamente
il microfono. Il programma mostra il testo grezzo e quello normalizzato da Vosk.
"""
from __future__ import annotations

import time
import sys
from pathlib import Path

# Quando lo script viene eseguito come:
#   python scripts/diagnostica_microfono_live.py
# Python mette "scripts/" in sys.path, non necessariamente la root del repo.
# Aggiungiamo quindi la root del progetto per rendere importabili i moduli Jarvis.
ROOT_PROGETTO = Path(__file__).resolve().parents[1]
if str(ROOT_PROGETTO) not in sys.path:
    sys.path.insert(0, str(ROOT_PROGETTO))


def main() -> int:
    try:
        import sounddevice as sd
    except (ImportError, OSError) as errore:
        print(f"ERRORE: sounddevice non disponibile: {errore}")
        return 1

    print("=== Dispositivi audio di ingresso ===")
    try:
        print(f"Dispositivo predefinito (ingresso, uscita): {sd.default.device}")
        dispositivi = sd.query_devices()
    except Exception as errore:
        print(f"ERRORE interrogando Core Audio: {errore}")
        return 1

    ingressi = []
    for indice, dispositivo in enumerate(dispositivi):
        if int(dispositivo.get("max_input_channels", 0)) > 0:
            ingressi.append((indice, dispositivo))
            print(
                f"[{indice}] {dispositivo.get('name', 'sconosciuto')} | "
                f"canali={dispositivo.get('max_input_channels')} | "
                f"frequenza_predefinita={dispositivo.get('default_samplerate')}"
            )

    if not ingressi:
        print("ERRORE: Core Audio non espone alcun microfono.")
        return 1

    from voce.ascoltatore import AscoltatoreVoce
    from voce.riconoscimento import RiconoscitoreVoce
    from voce.wake_word import WakeWordJarvis

    riconoscitore = RiconoscitoreVoce()
    # Verifica anche la logica wake-word -> comando, ma non esegue comandi
    # né attiva la sintesi vocale: la diagnostica resta sicura e non invasiva.
    wake_word = WakeWordJarvis(timeout=10)
    comandi_rilevati = []
    print(f"\nModello Vosk: {riconoscitore.percorso_modello}")
    print("Caricamento del modello...")
    if not riconoscitore.avvia():
        print(f"ERRORE avvio Vosk: {riconoscitore.ultimo_errore}")
        return 1

    ascoltatore = AscoltatoreVoce(
        frequenza=riconoscitore.sample_rate,
        blocksize=1600,
        filtro_rumore=True,
        livello_filtro=1,
    )
    if not ascoltatore.avvia():
        print(f"ERRORE apertura microfono predefinito: {ascoltatore.ultimo_errore}")
        riconoscitore.ferma()
        return 1

    print("\n=== Prova live (15 secondi) ===")
    print("Parla normalmente vicino al Mac. Prova: «Jarvis», pausa, «che ore sono».")
    print("Non viene creato né salvato alcun file audio. Premi Ctrl+C per terminare.")
    inizio = time.monotonic()
    prossima_diagnostica = inizio
    ultima_rilevazione = None
    try:
        while time.monotonic() - inizio < 15:
            audio = ascoltatore.ascolta(timeout=0.4)
            if audio:
                testo = riconoscitore.riconosci(audio)
                if testo:
                    ultima_rilevazione = testo
                    grezzo = riconoscitore.ultima_trascrizione_grezza
                    normalizzato = riconoscitore.ultima_trascrizione_normalizzata
                    confidenza = riconoscitore.ultima_confidenza_media
                    parole = riconoscitore.ultime_parole_riconosciute
                    esito = wake_word.controlla(normalizzato)
                    comando = str(esito.get("comando", "")).strip()
                    if comando:
                        comandi_rilevati.append(comando)
                    print(
                        f"TRASCRIZIONE grezza={grezzo!r} | "
                        f"normalizzata={normalizzato!r} | "
                        f"confidenza={confidenza!r} | parole={parole!r}"
                    )
                    print(
                        "WAKE_WORD "
                        f"attivato={esito.get('attivato', False)} | "
                        f"comando={comando!r} | "
                        f"parziale={esito.get('parziale', False)}"
                    )

            adesso = time.monotonic()
            if adesso >= prossima_diagnostica:
                stato = ascoltatore.stato()
                print(
                    f"AUDIO rms_ingresso={stato['rms_ingresso']} "
                    f"rms_filtrato={stato['rms_filtrato']} "
                    f"buffer={stato['buffer']} "
                    f"filtro={stato['filtro_rumore'].get('modalita', 'n/d')}"
                )
                prossima_diagnostica = adesso + 2

    except KeyboardInterrupt:
        print("\nProva interrotta dall'utente.")
    finally:
        ascoltatore.ferma()
        riconoscitore.ferma()

    if ultima_rilevazione is None:
        print("\nESITO: Vosk non ha restituito trascrizioni durante la prova.")
        print("Controllare RMS, dispositivo predefinito e permesso Microfono di macOS.")
        return 2

    print("\nESITO: microfono e Vosk hanno prodotto almeno una trascrizione.")
    if comandi_rilevati:
        print("Comandi riconosciuti dalla logica wake word (non eseguiti):")
        for comando in comandi_rilevati:
            print(f"  - {comando}")
    else:
        print("La logica wake word non ha estratto comandi completi durante questa prova.")
        print("Ripetere: «Jarvis», pausa breve, poi «che ore sono».")
    print("Questa prova non esegue comandi e non salva audio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
