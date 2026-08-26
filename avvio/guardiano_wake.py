"""Guardiano vocale di J.A.R.V.I.S.

Rimane in background e ascolta esclusivamente la wake word. Quando riconosce
"Jarvis", "Hey Jarvis" o "Ehi Jarvis", libera il microfono e avvia jarvis.py
in modalita interattiva grafica. Se nella stessa frase e presente un comando,
lo passa direttamente alla nuova sessione di Jarvis.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce
from voce.wake_word import WakeWordJarvis


class GuardianoWake:
    """Listener leggero che attiva Jarvis con la voce."""

    PAROLE = {"jarvis", "hey jarvis", "ehi jarvis"}

    def __init__(self) -> None:
        self.root = ROOT
        self.python = sys.executable
        self.ascoltatore = AscoltatoreVoce()
        self.riconoscitore = RiconoscitoreVoce()
        self.wake_word = WakeWordJarvis()
        self.jarvis_process: subprocess.Popen | None = None
        self.attivo = True

    def _log(self, messaggio: str) -> None:
        try:
            log_dir = os.path.join(self.root, "logs")
            os.makedirs(log_dir, exist_ok=True)
            percorso = os.path.join(log_dir, "guardiano_wake.log")
            with open(percorso, "a", encoding="utf-8") as file:
                file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {messaggio}\n")
        except OSError:
            pass

    def _estrai_comando_wake(self, testo: str) -> str:
        """Restituisce il testo dopo la wake word, se presente."""
        testo = self.wake_word.pulisci_testo(testo)
        for parola in sorted(self.PAROLE, key=len, reverse=True):
            if testo == parola:
                return ""
            prefisso = parola + " "
            if testo.startswith(prefisso):
                return testo[len(prefisso):].strip()
        return ""

    def _e_wake_word(self, testo: str) -> bool:
        testo = self.wake_word.pulisci_testo(testo)
        return testo in self.PAROLE or any(
            testo.startswith(parola + " ") for parola in self.PAROLE
        )

    def _avvia_jarvis(self, comando_iniziale: str = "") -> None:
        self._log("Wake word riconosciuta: avvio della sessione grafica di Jarvis.")
        self.ascoltatore.ferma()
        self.riconoscitore.ferma()

        jarvis = os.path.join(self.root, "jarvis.py")
        ambiente = os.environ.copy()
        ambiente["JARVIS_ATTIVATO_DA_WAKE"] = "1"
        if comando_iniziale:
            ambiente["JARVIS_COMANDO_INIZIALE"] = comando_iniziale
            self._log(f"Comando iniziale passato a Jarvis: {comando_iniziale}")
        else:
            ambiente.pop("JARVIS_COMANDO_INIZIALE", None)

        try:
            self.jarvis_process = subprocess.Popen(
                [self.python, jarvis],
                cwd=self.root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                env=ambiente,
            )
            self._log(f"Jarvis avviato dalla wake word, PID {self.jarvis_process.pid}.")
        except (OSError, ValueError) as errore:
            self._log(f"Errore avvio Jarvis: {errore}")
            self.jarvis_process = None
            return

        while self.attivo and self.jarvis_process.poll() is None:
            time.sleep(0.5)

        if self.jarvis_process is not None:
            self._log("Sessione Jarvis terminata: riprendo ascolto della wake word.")
        self.jarvis_process = None

    def _prepara_ascolto(self) -> bool:
        if not self.ascoltatore.avvia():
            self._log(f"Microfono non disponibile: {self.ascoltatore.ultimo_errore}")
            return False
        if not self.riconoscitore.avvia():
            self._log(f"Riconoscimento vocale non disponibile: {self.riconoscitore.ultimo_errore}")
            self.ascoltatore.ferma()
            return False
        self._log("Ascolto wake word attivo.")
        return True

    def ciclo(self) -> int:
        self._log("Guardiano vocale avviato.")
        while self.attivo:
            if not self._prepara_ascolto():
                time.sleep(3)
                continue
            try:
                while self.attivo and self.jarvis_process is None:
                    audio = self.ascoltatore.ascolta(timeout=1)
                    if not audio:
                        continue
                    testo = self.riconoscitore.riconosci(audio)
                    if testo and self._e_wake_word(testo):
                        comando = self._estrai_comando_wake(testo)
                        self._avvia_jarvis(comando)
                        break
            except (KeyboardInterrupt, SystemExit):
                self.attivo = False
                break
            except Exception as errore:
                self._log(f"Errore nel ciclo di ascolto: {errore}")
                time.sleep(1)
            finally:
                self.ascoltatore.ferma()
                self.riconoscitore.ferma()
        self._log("Guardiano vocale terminato.")
        return 0

    def ferma(self) -> None:
        self.attivo = False
        self.ascoltatore.ferma()
        self.riconoscitore.ferma()


def main() -> int:
    guardiano = GuardianoWake()
    try:
        return guardiano.ciclo()
    finally:
        guardiano.ferma()


if __name__ == "__main__":
    raise SystemExit(main())
