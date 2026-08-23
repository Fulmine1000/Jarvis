"""J.A.R.V.I.S. — Entry point ufficiale.

Avvia il kernel e, in base alla disponibilità del modulo voce, entra in:
  - modalità vocale (microfono + Vosk + wake word "Jarvis"), oppure
  - modalità solo-testo (comandi da terminale).

Entrambe le modalità integrano l'HUD testuale.
"""

import signal
import sys
import time
import traceback

from core.kernel import KernelJarvis
from interfaccia.hud import HUDJarvis


kernel = None
hud = None


def mostra_hud():
    """Aggiorna e stampa l'HUD se disponibile."""
    if hud and kernel:
        try:
            hud.aggiorna_kernel()
            hud.mostra()
        except Exception:
            pass


def ciclo_testuale():
    """Loop dei comandi da terminale."""
    print()
    print("Modalità solo-testo attiva. Digita un comando.")
    print("Comandi: 'buongiorno', 'che ore sono', 'stato sistema',")
    print("'stato dispositivi', 'accendi luce soggiorno', 'esci'.")
    print()

    while True:
        try:
            comando = input("\nTu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not comando:
            continue
        if comando.lower() in ("esci", "chiudi", "stop"):
            break

        risposta = kernel.esegui_comando(comando)
        if risposta:
            print("\nJ.A.R.V.I.S.:", risposta)


def attesa_signal():
    """Mantiene attivo Jarvis in modalità vocale."""
    try:
        signal.signal(signal.SIGINT, chiusura)
        signal.signal(signal.SIGTERM, chiusura)
    except (ValueError, OSError):
        pass

    try:
        while True:
            signal.pause()
    except AttributeError:
        while True:
            time.sleep(1)


def chiusura(signum=None, frame=None):
    global kernel
    print("\nArresto Jarvis...")

    try:
        if kernel:
            kernel.arresta()
    except Exception as errore:
        print(f"Errore durante l'arresto: {errore}")

    raise SystemExit(0)


def main():
    global kernel, hud

    print("=" * 60)
    print("           J.A.R.V.I.S.")
    print("       Assistente Intelligente Personale")
    print("          Versione definitiva")
    print("=" * 60)
    print()

    try:
        kernel = KernelJarvis()
        kernel.avvia()

        hud = HUDJarvis()
        hud.avvia()
        hud.collega_kernel(kernel)
        mostra_hud()

        print()
        print("Jarvis è operativo.")

        if kernel.voce_disponibile:
            print("Modalità vocale attiva. Pronuncia la wake word: Jarvis")
            print("Premi CTRL+C per uscire.")
            attesa_signal()
        else:
            print("Modalità solo-testo (audio non disponibile).")
            print("Premi CTRL+C per uscire.")
            ciclo_testuale()

        chiusura()

    except KeyboardInterrupt:
        chiusura()
    except Exception:
        traceback.print_exc()
        chiusura()


if __name__ == "__main__":
    main()
