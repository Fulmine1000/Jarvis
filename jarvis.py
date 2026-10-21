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
from moduli.doppio_battito import RilevatoreDoppioBattito


class JarvisOS:
    """Gestisce una sessione completa di J.A.R.V.I.S."""

    def __init__(self):
        self.kernel: KernelJarvis | None = None
        self.hud: HUDJarvis | None = None
        self.telefono: TelefonoJarvis | None = None
        self.gesti: ControlloGesti | None = None
        self.battito: RilevatoreDoppioBattito | None = None
        self.indirizzo_telefono: str | None = None
        self._worker: threading.Thread | None = None
        self._chiusura = threading.Event()

    def avvia(self) -> bool:
        """Avvia kernel, voce, server telefono, rilevatori opzionali e HUD."""
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
                self.kernel.logger.info(f"Server telefono attivo: {self.indirizzo_telefono}")
            except Exception as errore:
                self.telefono = None
                self.indirizzo_telefono = None
                self.kernel.logger.error(f"Server telefono non disponibile: {errore}")
                print(f"Avviso: server telefono non disponibile: {errore}")

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
                    self.gesti = ControlloGesti(callback=self._gesto_rilevato, logger=self.kernel.logger)
                    if not self.gesti.avvia():
                        self.gesti = None
                        print("Controllo gestuale non disponibile; Jarvis continua normalmente.")
                except Exception as errore:
                    self.gesti = None
                    self.kernel.logger.warning(f"Controllo gestuale non avviato: {errore}")

            # Il doppio battito è opt-in perché apre un secondo stream audio.
            # Se il driver non consente l'accesso condiviso, disattivarlo e
            # usare la wake word normale: JARVIS_DOPPIO_BATTITO=0.
            if os.environ.get("JARVIS_DOPPIO_BATTITO") == "1":
                try:
                    soglia = float(os.environ.get("JARVIS_BATTITO_SOGLIA_RMS", "0.18"))
                    self.battito = RilevatoreDoppioBattito(
                        callback=self._doppio_battito_async,
                        soglia_rms=soglia,
                        logger=self.kernel.logger,
                    )
                    if not self.battito.avvia():
                        self.battito = None
                        print("Doppio battito non disponibile; la wake word resta attiva.")
                except (TypeError, ValueError, Exception) as errore:
                    self.battito = None
                    self.kernel.logger.warning(f"Doppio battito non avviato: {errore}")

            self._worker = threading.Thread(target=self._attesa_sessione, name="JarvisCore", daemon=True)
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
                    if self.hud:
                        self.hud.registra_evento(f"Comando iniziale: {comando_iniziale}")
                    self.kernel.esegui_comando(comando_iniziale)
                except Exception as errore:
                    self.kernel.logger.error(f"Errore comando iniziale: {errore}")

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
        try:
            from interfaccia.ologramma_3d_server import aggiorna_gesto
            aggiorna_gesto(gesto)
        except Exception:
            pass
        if self.hud:
            self.hud.applica_gesto(gesto)
            self.hud.registra_evento(messaggio)
        if self.kernel and getattr(self.kernel, "logger", None):
            self.kernel.logger.info(messaggio)

    def _doppio_battito_async(self) -> None:
        """Sposta TTS e apertura app fuori dal callback audio in tempo reale."""
        threading.Thread(
            target=self._doppio_battito_rilevato,
            name="JarvisBattitoAzione",
            daemon=True,
        ).start()

    def _doppio_battito_rilevato(self) -> None:
        """Saluta e apre soltanto app/URL esplicitamente configurati dall'utente."""
        if not self.kernel or self._chiusura.is_set():
            return
        messaggio = "Bentornato Simone. Tutti i sistemi sono pronti."
        if self.hud:
            self.hud.registra_evento("Doppio battito: Jarvis attivato")
        self.kernel.logger.info("Attivazione tramite doppio battito.")
        try:
            self.kernel.parla(messaggio)
        except Exception as errore:
            self.kernel.logger.warning(f"Saluto dopo doppio battito non riuscito: {errore}")

        app = getattr(self.kernel, "capacita", None)
        if not app:
            return
        for nome in filter(None, (x.strip() for x in os.environ.get("JARVIS_BATTITO_APPS", "").split(","))):
            try:
                risposta = app.apri_app(nome)
                self.kernel.logger.info(f"Doppio battito: {risposta}")
            except Exception as errore:
                self.kernel.logger.warning(f"Avvio app configurata non riuscito: {errore}")
        for url in filter(None, (x.strip() for x in os.environ.get("JARVIS_BATTITO_URLS", "").split(","))):
            if not url.startswith(("https://", "http://")):
                self.kernel.logger.warning("URL battito ignorato: usare solo URL http/https.")
                continue
            try:
                risposta = app.apri_url(url)
                self.kernel.logger.info(f"Doppio battito: {risposta}")
            except Exception as errore:
                self.kernel.logger.warning(f"Apertura URL configurato non riuscita: {errore}")

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
        if self._chiusura.is_set() or (self.kernel and self.kernel.arresto_richiesto):
            if self.hud and self.hud.attivo:
                self.hud.ferma()

    def arresta(self) -> bool:
        """Arresta ordinatamente rilevatori, server telefono, HUD, voce e kernel."""
        self._chiusura.set()
        for nome in ("battito", "gesti"):
            modulo = getattr(self, nome, None)
            if modulo:
                try:
                    modulo.ferma()
                except Exception:
                    pass
                setattr(self, nome, None)

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
    main()
