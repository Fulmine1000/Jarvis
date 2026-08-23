"""J.A.R.V.I.S. — Entry point ufficiale.

Il processo principale mantiene il loop grafico dell'HUD; il kernel e i
comandi lavorano in un thread separato. Questo evita i problemi di Tkinter
su macOS, dove il loop grafico deve restare nel main thread.
"""

import signal
import sys
import threading
import time
import traceback

from core.kernel import KernelJarvis
from interfaccia.hud import HUDJarvis

kernel = None
hud = None
_worker = None
_chiusura_richiesta = threading.Event()


def ciclo_testuale():
    print()
    print("Modalità solo-testo attiva. Digita un comando.")
    print("Comandi: 'buongiorno', 'che ore sono', 'stato sistema', 'esci'.")
    print()
    while not _chiusura_richiesta.is_set():
        try:
            comando = input("\nTu: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not comando:
            continue
        if comando.lower() in ("esci", "chiudi", "stop"):
            break
        risposta = kernel.esegui_comando(comando)
        if risposta:
            print("\nJ.A.R.V.I.S.:", risposta)
            hud.registra_evento(f"Comando: {comando}")


def attesa_signal():
    try:
        signal.signal(signal.SIGINT, chiusura)
        signal.signal(signal.SIGTERM, chiusura)
    except (ValueError, OSError):
        pass
    while not _chiusura_richiesta.is_set():
        time.sleep(1)


def worker_jarvis():
    try:
        if kernel.voce_disponibile:
            print("Modalità vocale attiva. Pronuncia la wake word: Jarvis")
            attesa_signal()
        else:
            print("Modalità solo-testo (audio non disponibile).")
            ciclo_testuale()
    except Exception:
        traceback.print_exc()
    finally:
        _chiusura_richiesta.set()
        if hud:
            hud.ferma()


def chiusura(signum=None, frame=None):
    if _chiusura_richiesta.is_set():
        return
    _chiusura_richiesta.set()
    print("\nArresto Jarvis...")
    try:
        if hud:
            hud.ferma()
    except Exception:
        pass
    try:
        if kernel:
            kernel.arresta()
    except Exception as errore:
        print(f"Errore durante l'arresto: {errore}")


def main():
    global kernel, hud, _worker
    print("=" * 60)
    print("           J.A.R.V.I.S.")
    print("       Assistente Intelligente Personale")
    print("          Versione definitiva")
    print("=" * 60)
    print()
    try:
        kernel = KernelJarvis()
        kernel.avvia()
        hud = HUDJarvis(kernel=kernel, width=1500, height=900)
        hud.aggiorna_kernel()
        hud.collega_kernel(kernel)

        _worker = threading.Thread(target=worker_jarvis, name="JarvisCore", daemon=True)
        _worker.start()

        print("Avvio HUD J.A.R.V.I.S. animato...")
        # Tkinter resta nel main thread: è necessario soprattutto su macOS.
        hud.avvia()

        _chiusura_richiesta.set()
        if kernel:
            kernel.arresta()
    except KeyboardInterrupt:
        chiusura()
    except Exception:
        traceback.print_exc()
        chiusura()
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
