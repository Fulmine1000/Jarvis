"""J.A.R.V.I.S. — punto di ingresso definitivo.

Il kernel viene avviato prima dell'interfaccia; l'HUD gestisce il proprio
ciclo Tkinter in un thread dedicato, mentre il worker principale gestisce
comandi e voce senza bloccare l'interfaccia.
"""

from __future__ import annotations

import signal
import threading
import time
import traceback

from core.kernel import KernelJarvis
from interfaccia.hud import HUDJarvis

kernel: KernelJarvis | None = None
hud: HUDJarvis | None = None
_worker: threading.Thread | None = None
_chiusura_richiesta = threading.Event()


def ciclo_testuale() -> None:
    print()
    print("Modalità solo-testo attiva. Digita un comando.")
    print("Scrivi 'aiuto' per le capacità disponibili o 'esci' per chiudere.")
    print()
    while not _chiusura_richiesta.is_set():
        try:
            comando = input("\nTu: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not comando:
            continue
        if comando.lower() in ("esci", "chiudi", "stop", "spegni jarvis"):
            if kernel:
                kernel.richiedi_arresto()
            break
        try:
            risposta = kernel.esegui_comando(comando) if kernel else None
            # KernelJarvis è l'unico proprietario della risposta vocale/testuale.
            # In modalità solo-testo SintesiVocale mostra già il fallback [JARVIS].
            if risposta and hud:
                hud.registra_evento(f"Comando: {comando}")
        except Exception as errore:
            print(f"Errore comando: {errore}")


def attesa_signal() -> None:
    try:
        signal.signal(signal.SIGINT, chiusura)
        signal.signal(signal.SIGTERM, chiusura)
    except (ValueError, OSError):
        pass
    while not _chiusura_richiesta.is_set():
        time.sleep(0.25)


def worker_jarvis() -> None:
    try:
        if kernel and kernel.voce_disponibile:
            print("Modalità vocale attiva. Pronuncia: Jarvis")
            attesa_signal()
        else:
            ciclo_testuale()
    except Exception:
        traceback.print_exc()
    finally:
        _chiusura_richiesta.set()


def chiusura(signum=None, frame=None) -> None:
    _chiusura_richiesta.set()
    if kernel:
        kernel.richiedi_arresto()


def controlla_chiusura() -> None:
    if _chiusura_richiesta.is_set() or (kernel and kernel.arresto_richiesto):
        if hud and hud.attivo:
            hud.ferma()
        return
    if hud and hud.finestra:
        try:
            hud.finestra.after(100, controlla_chiusura)
        except Exception:
            pass


def main() -> int:
    global kernel, hud, _worker
    print("=" * 64)
    print("                    J.A.R.V.I.S.")
    print("             Assistente Intelligente Personale")
    print("                  Definitive Edition")
    print("=" * 64)

    try:
        kernel = KernelJarvis()
        if not kernel.avvia():
            raise RuntimeError("Il kernel non è riuscito ad avviarsi.")

        hud = HUDJarvis(kernel=kernel, width=1500, height=900)
        kernel.hud = hud
        hud.collega_kernel(kernel)
        hud.aggiorna_kernel()

        _worker = threading.Thread(target=worker_jarvis, name="JarvisCore", daemon=True)
        _worker.start()

        print("Avvio HUD J.A.R.V.I.S. animato...")
        hud.avvia()
        if hud.finestra:
            hud.finestra.after(100, controlla_chiusura)
            # HUDJarvis possiede già il mainloop del proprio thread Tkinter.
            while hud.attivo and not _chiusura_richiesta.is_set():
                time.sleep(0.1)

    except KeyboardInterrupt:
        chiusura()
    except Exception:
        traceback.print_exc()
        chiusura()
    finally:
        _chiusura_richiesta.set()
        if hud and hud.attivo:
            hud.ferma()
        if _worker and _worker.is_alive():
            _worker.join(timeout=1.5)
        if kernel:
            try:
                kernel.arresta()
            except Exception as errore:
                print(f"Errore durante l'arresto: {errore}")
        hud = None
        kernel = None

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
