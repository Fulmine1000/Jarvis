"""J.A.R.V.I.S. — punto di ingresso ufficiale.

``python jarvis.py`` avvia l'intero sistema: kernel, voce e HUD.
La gestione dell'ascolto vocale resta nel ModuloVoce/MotoreAscolto; questo
launcher non crea un secondo ciclo input che possa competere con il microfono.

Il codice grafico Tkinter viene eseguito esclusivamente nel Main Thread,
come richiesto da macOS/AppKit. L'ascolto vocale e la supervisione del kernel
restano invece in background.
"""

from __future__ import annotations

import signal
import threading
import time
import traceback

from core.kernel import KernelJarvis
from interfaccia.hud import HUDJarvis


class JarvisOS:
    """Gestisce una sessione completa di J.A.R.V.I.S."""

    def __init__(self):
        self.kernel: KernelJarvis | None = None
        self.hud: HUDJarvis | None = None
        self._worker: threading.Thread | None = None
        self._chiusura = threading.Event()

    def avvia(self) -> bool:
        """Avvia kernel, voce e HUD nel corretto contesto di esecuzione."""
        print("=" * 64)
        print("                    J.A.R.V.I.S.")
        print("             Assistente Intelligente Personale")
        print("                  VERSIONE DEFINITIVA")
        print("=" * 64)

        try:
            self.kernel = KernelJarvis()
            if not self.kernel.avvia():
                print("Errore durante l'avvio del kernel.")
                return False

            self.hud = HUDJarvis(kernel=self.kernel, width=1500, height=900)
            self.kernel.hud = self.hud
            self.hud.collega_kernel(self.kernel)
            self.hud.aggiorna_kernel()

            self._worker = threading.Thread(
                target=self._attesa_sessione,
                name="JarvisCore",
                daemon=True,
            )
            self._worker.start()

            if self.kernel.voce_disponibile:
                print("Modalità vocale attiva. Pronuncia 'Jarvis', 'Hey Jarvis' o 'Ehi Jarvis'.")
            else:
                print("Modalità solo-testo attiva. Digita un comando nella console.")

            print("Avvio HUD J.A.R.V.I.S. animato...")

            # Tkinter/AppKit deve essere creato e gestito dal Main Thread su macOS.
            self.hud._run_tk()

            self._chiusura.set()
            if self.kernel and not self.kernel.arresto_richiesto:
                self.kernel.richiedi_arresto()

            return True

        except KeyboardInterrupt:
            self.arresta()
            return True
        except Exception:
            traceback.print_exc()
            self.arresta()
            return False

    def _attesa_sessione(self) -> None:
        """Mantiene viva la sessione; l'ascolto è gestito dal ModuloVoce."""
        try:
            while not self._chiusura.is_set():
                if self.kernel and self.kernel.arresto_richiesto:
                    # Il thread non modifica direttamente Tk: accoda la chiusura
                    # al Main Thread tramite after().
                    if self.hud and self.hud.finestra:
                        try:
                            self.hud.finestra.after(0, self.hud.ferma)
                        except Exception:
                            pass
                    break
                time.sleep(0.25)
        finally:
            self._chiusura.set()

    def _controlla_chiusura(self) -> None:
        """Compatibilità con il precedente launcher."""
        if self._chiusura.is_set() or (
            self.kernel and self.kernel.arresto_richiesto
        ):
            if self.hud and self.hud.attivo:
                self.hud.ferma()
            return

        if self.hud and self.hud.finestra:
            try:
                self.hud.finestra.after(100, self._controlla_chiusura)
            except Exception:
                pass

    def arresta(self) -> bool:
        """Arresta ordinatamente HUD, voce e kernel."""
        self._chiusura.set()

        if self.kernel:
            try:
                self.kernel.richiedi_arresto()
            except Exception:
                pass

        if self.hud and self.hud.attivo:
            try:
                self.hud.ferma()
            except Exception:
                pass

        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=1.5)

        if self.kernel:
            try:
                self.kernel.arresta()
            except Exception as errore:
                print(f"Errore durante l'arresto: {errore}")

        return True

    def esegui(self) -> bool:
        """Alias storico: l'esecuzione principale è già gestita da avvia()."""
        if self.kernel and self.kernel.stato == "Operativo":
            self._attesa_sessione()
            return True
        return False


def main() -> int:
    jarvis = JarvisOS()

    def chiusura(signum=None, frame=None):
        jarvis.arresta()

    try:
        signal.signal(signal.SIGINT, chiusura)
        signal.signal(signal.SIGTERM, chiusura)
    except (ValueError, OSError):
        pass

    try:
        jarvis.avvia()
        return 0
    except KeyboardInterrupt:
        jarvis.arresta()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
