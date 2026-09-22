"""Compatibilità del modulo voce storico di Jarvis.

Il sistema ufficiale usa il modulo moduli.voce_modulo; questa classe mantiene
l'API precedente senza riferimenti a versioni legacy e senza avviare thread
alla semplice importazione.
"""

import os
import platform
import queue
import re
import shlex
import subprocess
import threading


class VoceJarvis:
    def __init__(self):
        self.sistema = platform.system()
        self.voce = "Alice"
        self.velocita = 170
        self.volume = 1.0
        self.silenzioso = False
        self.parlando = False
        self._attivo = False
        self._thread = None
        self.coda = queue.Queue()

    def avvia(self):
        if self._attivo:
            return True
        self._attivo = True
        self._thread = threading.Thread(target=self.gestore_voce, daemon=True)
        self._thread.start()
        return True

    def ferma(self):
        self._attivo = False
        return True

    def gestore_voce(self):
        while self._attivo:
            try:
                testo = self.coda.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self.esegui(testo)
            finally:
                self.coda.task_done()

    def parla(self, testo):
        if not self.silenzioso and testo:
            if not self._attivo:
                self.avvia()
            self.coda.put(str(testo))
        return True

    def _testo_per_voce(self, testo):
        """Prepara il testo per il TTS senza modificare ciò che Jarvis mostra.

        L'appellativo resta scritto "Sir" in memoria, interfaccia e testo
        visualizzato. Sul Mac la singola parola viene affidata alla voce
        inglese britannica Daniel, per ottenere la pronuncia /sɜːr/. Subito
        dopo viene ripristinata la voce italiana configurata.
        """
        testo = str(testo)

        if self.sistema != "Darwin":
            return testo

        voce = self.voce.replace("]", "")
        sostituzione = (
            f"[[voice:Daniel]]Sir[[voice:{voce}]]"
        )

        return re.sub(
            r"(?<!\w)Sir(?!\w)",
            sostituzione,
            testo,
        )

    def esegui(self, testo):
        self.parlando = True
        try:
            print("JARVIS:", testo)
            testo_voce = self._testo_per_voce(testo)

            if self.sistema == "Darwin":
                subprocess.run(
                    ["say", "-v", self.voce, "-r", str(self.velocita), testo_voce],
                    check=False,
                )
            elif self.sistema == "Linux":
                subprocess.run(["espeak", testo_voce], check=False)
            elif self.sistema == "Windows":
                return False
            return True
        finally:
            self.parlando = False

    def elenco_voci(self):
        if self.sistema == "Darwin":
            subprocess.run(["say", "-v", "?"], check=False)
            return "Lista voci mostrata."
        return "Funzione non disponibile su questo sistema."

    def cambia_voce(self, nome):
        self.voce = str(nome)
        return f"Voce impostata: {self.voce}"

    def cambia_velocita(self, valore):
        self.velocita = int(valore)
        return f"Velocità impostata: {self.velocita}"

    def stato(self):
        return {
            "voce": self.voce,
            "velocita": self.velocita,
            "parlando": self.parlando,
            "silenzioso": self.silenzioso,
            "attivo": self._attivo,
        }
