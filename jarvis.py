"""J.A.R.V.I.S. — punto di ingresso ufficiale.

Avvia kernel, voce, HUD Qt Quick/QML e server telefono locale.
L'interfaccia grafica vive nel Main Thread; voce e supervisione restano in background.
"""

from __future__ import annotations

import os
import signal
import threading
import time
import traceback

from core.kernel import KernelJarvis
from dispositivi.telefono import TelefonoJarvis
from interfaccia.hud import HUDJarvis


class JarvisOS:
    """Gestisce una sessione completa di J.A.R.V.I.S."""

    def __init__(self):
        self.kernel: KernelJarvis | None = None
        self.hud: HUDJarvis | None = None
        self.telefono: TelefonoJarvis | None = None
        self.indirizzo_telefono: str | None = None
        self._worker: threading.Thread | None = None
        self._chiusura = threading.Event()

    def avvia(self) -> bool:
        """Avvia kernel, voce, server telefono e HUD Qt Quick."""
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

            try:
                self.telefono = TelefonoJarvis(
                    "Telefono remoto",
                    "Client web Jarvis",
                    logger=self.kernel.logger,
                    gestore_comandi=self.kernel.esegui_comando,
                )
                self.indirizzo_telefono = self.telefono.avvia_server(
                    gestore_comandi=self.kernel.esegui_comando,
                    porta=8765,
                )
                print(f"Server telefono Jarvis attivo: {self.indirizzo_telefono}")
                self.kernel.logger.info(
                    f"Server telefono attivo: {self.indirizzo_telefono}"
                )
            except Exception as errore:
                self.telefono = None
                self.indirizzo_telefono = None
                self.kernel.logger.error(
                    f"Server telefono non disponibile: {errore}"
                )
                print(f"Avviso: server telefono non disponibile: {errore}")

            # HUD Qt Quick/QML: niente Tkinter e niente Canvas.
            self.hud = HUDJarvis(kernel=self.kernel, width=1050, height=650)
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

            if self.indirizzo_telefono:
                print(f"Collega un telefono alla stessa Wi-Fi e apri: {self.indirizzo_telefono}")

            print("Avvio HUD J.A.R.V.I.S. Qt Quick...")

            attivato_da_wake = os.environ.get("JARVIS_ATTIVATO_DA_WAKE") == "1"
            comando_iniziale = os.environ.get("JARVIS_COMANDO_INIZIALE", "").strip()
            if attivato_da_wake and comando_iniziale:
                try:
                    self.hud.registra_evento(
                        f"Comando iniziale: {comando_iniziale}"
                    )
                    self.kernel.esegui_comando(comando_iniziale)
                except Exception as errore:
                    self.kernel.logger.error(
                        f"Errore comando iniziale: {errore}"
                    )

            # Qt su macOS deve essere gestito dal thread principale.
            self.hud._run_qt()

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
                    if self.hud and self.hud.attivo:
                        self.hud.ferma()
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

    def arresta(self) -> bool:
        """Arresta ordinatamente server telefono, HUD, voce e kernel."""
        self._chiusura.set()

        if self.telefono:
            try:
                self.telefono.ferma_server()
            except Exception:
                pass

        if self.hud and self.hud.attivo:
            try:
                self.hud.ferma()
            except Exception:
                pass

        if self.kernel:
            try:
                self.kernel.richiedi_arresto()
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
