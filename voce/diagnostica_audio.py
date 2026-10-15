"""Diagnostica reale di microfono e altoparlanti per Jarvis.

Eseguire dal Mac con:
    python -m voce.diagnostica_audio

Registra solo in memoria per pochi secondi per misurare il livello audio;
non salva né invia registrazioni.
"""
from __future__ import annotations

import math
import sys


def prova_microfono(secondi: float = 4.0) -> bool:
    try:
        import sounddevice as sd
    except Exception as errore:
        print(f"ERRORE MICROFONO: sounddevice non caricabile: {errore}")
        return False

    try:
        dispositivi = sd.query_devices()
        print("\n=== DISPOSITIVI AUDIO ===")
        for indice, dispositivo in enumerate(dispositivi):
            ingressi = int(dispositivo.get("max_input_channels", 0))
            uscite = int(dispositivo.get("max_output_channels", 0))
            if ingressi or uscite:
                marcatori = []
                if ingressi:
                    marcatori.append(f"ingressi={ingressi}")
                if uscite:
                    marcatori.append(f"uscite={uscite}")
                print(f"[{indice}] {dispositivo.get('name', 'dispositivo')} ({', '.join(marcatori)})")
        print(f"Dispositivo predefinito: {sd.default.device}")
        ingresso = sd.query_devices(kind="input")
        print(f"Microfono predefinito: {ingresso.get('name', 'sconosciuto')}")
        frequenza = 16000
        print(f"Parla normalmente per {secondi:.0f} secondi...")
        audio = sd.rec(
            int(secondi * frequenza),
            samplerate=frequenza,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        campioni = audio.reshape(-1)
        if len(campioni) == 0:
            print("ERRORE MICROFONO: nessun campione audio ricevuto.")
            return False
        somma = sum(int(campione) * int(campione) for campione in campioni)
        rms = math.sqrt(somma / len(campioni))
        picco = max(abs(int(campione)) for campione in campioni)
        print(f"Livello microfono: RMS={rms:.1f}, picco={picco}")
        if rms < 25 or picco < 100:
            print("ESITO MICROFONO: segnale quasi assente. Controlla ingresso e permessi.")
            return False
        print("ESITO MICROFONO: segnale rilevato.")
        return True
    except Exception as errore:
        print(f"ERRORE MICROFONO: {type(errore).__name__}: {errore}")
        print("Controlla il dispositivo d'ingresso e i permessi microfono di Terminale.")
        return False


def prova_sintesi() -> bool:
    print("\n=== PROVA VOCALE ===")
    try:
        from voce.sintesi import SintesiVocale

        sintesi = SintesiVocale()
        stato = sintesi.stato()
        print(
            f"Motore={stato.get('motore')}, "
            f"voce macOS={stato.get('voce_sistema') or 'predefinita'}, "
            f"campione={stato.get('campione_voce_locale')}"
        )
        risultato = sintesi.parla("Prova audio di Jarvis. Se senti questa frase, l'uscita audio funziona.")
        if risultato:
            print("ESITO SINTESI: il motore ha completato la riproduzione senza errori.")
            return True
        print("ESITO SINTESI: nessun motore ha confermato la riproduzione.")
        return False
    except Exception as errore:
        print(f"ERRORE SINTESI: {type(errore).__name__}: {errore}")
        return False


def main() -> int:
    print("Diagnostica audio Jarvis — nessun audio viene salvato.")
    microfono_ok = prova_microfono()
    sintesi_ok = prova_sintesi()
    print("\n=== RIEPILOGO ===")
    print(f"Microfono: {'OK' if microfono_ok else 'ERRORE'}")
    print(f"Voce in uscita: {'OK' if sintesi_ok else 'ERRORE'}")
    return 0 if microfono_ok and sintesi_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
