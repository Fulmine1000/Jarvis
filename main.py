"""Jarvis 3.0 — Entry point ufficiale.

Avvia il kernel e, in base alla disponibilità del modulo voce, entra in:
  - modalità vocale (microfono + Vosk + wake word "Jarvis"), oppure
  - modalità solo-testo (comandi da terminale).

Entrambe le modalità integrano l'HUD testuale.
"""

import sys
import signal
import time
import traceback

from core.kernel import KernelJarvis
from interfaccia.hud import HUDJarvis


kernel = None
hud = None


def mostra_hud():
    """Aggiorna e stampa l'HUD se disponibile."""

    global hud

    if hud and kernel:

        try:

            hud.aggiorna_kernel()
            hud.mostra()

        except Exception:

            pass


def ciclo_testuale():
    """Loop comandi da terminale (modalità solo-testo)."""

    global hud

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
    """Attende segnali di interruzione (vocale) o EOF."""

    try:

        signal.signal(signal.SIGINT, chiusura)
        signal.signal(signal.SIGTERM, chiusura)

    except (ValueError, OSError):

        # Signal handlers possono essere impostati solo nel thread principale.
        pass

    try:

        # signal.pause() esiste solo su Unix (macOS/Linux).
        while True:
            signal.pause()

    except AttributeError:

        # Windows: fallback a un loop attivo.
        while True:
            time.sleep(1)


def chiusura(signum=None, frame=None):

    global kernel

    print("\n")
    print("Arresto Jarvis...")

    try:

        if kernel:
            kernel.arresta()

    except Exception as errore:

        print(f"Errore durante l'arresto: {errore}")

    sys.exit(0)


def main():

    global kernel, hud

    print("=" * 60)
    print("           JARVIS 3.0")
    print(" Assistente Intelligente Personale")
    print("=" * 60)
    print()

    try:

        kernel = KernelJarvis()

        kernel.avvia()

        # HUD
        hud = HUDJarvis()
        hud.avvia()
        hud.collega_kernel(kernel)

        mostra_hud()

        print()
        print("Jarvis è operativo.")

        if kernel.voce_disponibile:

            print("Modalità vocale attiva. Pronuncia la wake word: Jarvis")
            print("Premi CTRL+C per uscire.")
            print()

            attesa_signal()

        else:

            print("Modalità solo-testo (audio non disponibile).")
            print("Premi CTRL+C per uscire.")
            print()

            ciclo_testuale()

        chiusura()

    except KeyboardInterrupt:

        chiusura()

    except Exception:

        traceback.print_exc()

        chiusura()


if __name__ == "__main__":
    main()
