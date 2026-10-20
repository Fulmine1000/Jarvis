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

from core.istanza import IstanzaUnicaJarvis
from core.kernel import KernelJarvis
from dispositivi.telefono import TelefonoJarvis
from interfaccia.hud import HUDJarvis
from interfaccia.gesti import ControlloGesti


class JarvisOS:
    """Gestisce una sessione completa di J.A.R.V.I.S."""

    def __init__(self):
        self.kernel: KernelJarvis | None = None
        self.hud: HUDJarvis | None = None
        self.telefono: TelefonoJarvis | None = None
        self.gesti: ControlloGesti | None = None
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
            # Se Qt non e disponibile, Jarvis resta comunque operativo in
            # modalita voce/testo invece di terminare l'intera sessione.
            try:
                self.hud = HUDJarvis(kernel=self.kernel, width=1200, height=680)
                self.kernel.hud = self.hud
                self.hud.collega_kernel(self.kernel)
                self.hud.aggiorna_kernel()
            except Exception as errore:
                self.hud = None
                self.kernel.hud = None
                self.kernel.logger.warning(f"HUD non disponibile: {errore}")
                print(f"Avviso: HUD non disponibile, Jarvis continua senza interfaccia grafica: {errore}")

            # La camera è opzionale e si attiva solo con consenso esplicito.
            if os.environ.get("JARVIS_GESTI") == "1":
                try:
                    self.gesti = ControlloGesti(
                        callback=self._gesto_rilevato,
                        logger=self.kernel.logger,
                    )
                    if not self.gesti.avvia():
                        self.gesti = None
                        print("Controllo gestuale non disponibile; Jarvis continua normalmente.")
                except Exception as errore:
                    self.gesti = None
                    self.kernel.logger.warning(f"Controllo gestuale non avviato: {errore}")

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
            if self.hud:
                self.hud._run_qt()
            else:
                self._attesa_sessione()

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

    def _gesto_rilevato(self, gesto: str) -> None:
        """Mostra nell'HUD gli eventi gestuali senza simulare azioni di sistema."""
        descrizioni = {
            "mano_aperta": "Mano aperta rilevata",
            "pizzico": "Pizzico: selezione/afferra",
            "scorri_destra": "Gesto: scorri a destra",
            "scorri_sinistra": "Gesto: scorri a sinistra",
            "zoom_avanti": "Gesto: zoom avanti",
            "zoom_indietro": "Gesto: zoom indietro",
        }
        messaggio = descrizioni.get(gesto, f"Gesto rilevato: {gesto}")
        if self.hud:
            self.hud.registra_evento(messaggio)
        if self.kernel and getattr(self.kernel, "logger", None):
            self.kernel.logger.info(messaggio)

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

        if self.gesti:
            try:
                self.gesti.ferma()
            except Exception:
                pass
            self.gesti = None

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
    # Una sola istanza globale: se una seconda esecuzione viene avviata
    # accidentalmente dalla wake word o dal terminale, non crea un altro
    # HUD/microfono/server ma termina in modo innocuo.
    istanza = IstanzaUnicaJarvis()
    if not istanza.acquisisci():
        print("J.A.R.V.I.S. è già in esecuzione: nessuna seconda istanza avviata.")
        return 0

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
    finally:
        istanza.rilascia()


if __name__ == "__main__":
    raise SystemExit(main())
