"""Guardiano vocale di J.A.R.V.I.S.

Rimane in background e ascolta esclusivamente la wake word. Quando riconosce
"Jarvis", "Hey Jarvis" o "Ehi Jarvis", libera il microfono e avvia jarvis.py.
Quando Jarvis viene chiuso, il guardiano riprende automaticamente l'ascolto.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce
from voce.wake_word import WakeWordJarvis


class GuardianoWake:
    """Listener leggero e invisibile che attiva Jarvis con la voce."""

    PAROLE = {"jarvis", "hey jarvis", "ehi jarvis"}

    def __init__(self) -> None:
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.python = sys.executable
        self.ascoltatore = AscoltatoreVoce()
        self.riconoscitore = RiconoscitoreVoce()
        self.wake_word = WakeWordJarvis()
        self.jarvis_process: subprocess.Popen | None = None
        self.attivo = True

    @staticmethod
    def _normalizza(testo: str | None) -> str:
        return " ".join(str(testo or "").lower().strip().split())

    def _e_wake_word(self, testo: str) -> bool:
        testo = self.wake_word.pulisci_testo(testo)
        if testo in self.PAROLE:
            return True
        # Accetta anche eventuali parole di riempimento riconosciute insieme
        # alla wake word, ma non avvia Jarvis per una frase completamente diversa.
        return any(
            testo.startswith(parola + " ")
            for parola in self.PAROLE
        )

    def _avvia_jarvis(self) -> None:
        self.ascoltatore.ferma()
        self.riconoscitore.ferma()

        jarvis = os.path.join(self.root, "jarvis.py")
        self.jarvis_process = subprocess.Popen(
            [self.python, jarvis],
            cwd=self.root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # Il guardiano resta vivo ma non tocca il microfono mentre Jarvis è attivo.
        while self.attivo and self.jarvis_process.poll() is None:
            time.sleep(0.5)

        self.jarvis_process = None

    def _prepara_ascolto(self) -> bool:
        if not self.ascoltatore.avvia():
            return False
        if not self.riconoscitore.avvia():
            self.ascoltatore.ferma()
            return False
        return True

    def ciclo(self) -> int:
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
                        self._avvia_jarvis()
                        break
            except (KeyboardInterrupt, SystemExit):
                self.attivo = False
                break
            except Exception:
                time.sleep(1)
            finally:
                self.ascoltatore.ferma()
                self.riconoscitore.ferma()

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
