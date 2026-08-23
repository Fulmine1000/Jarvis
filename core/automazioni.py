from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


@dataclass
class Automazione:
    nome: str
    azione: Callable[[], object]
    intervallo: float | None = None
    attiva: bool = True
    esecuzioni: int = 0
    ultima_esecuzione: str | None = None
    thread: threading.Thread | None = field(default=None, repr=False)


class AutomazioniJarvis:
    """Motore per automazioni periodiche locali."""

    def __init__(self, logger=None):
        self.logger = logger
        self.automazioni: dict[str, Automazione] = {}
        self._stop = threading.Event()
        self._lock = threading.RLock()

    def avvia(self):
        with self._lock:
            self._stop.clear()
            for auto in self.automazioni.values():
                auto.attiva = True
                if auto.intervallo and (not auto.thread or not auto.thread.is_alive()):
                    auto.thread = threading.Thread(
                        target=self._loop,
                        args=(auto,),
                        daemon=True,
                        name=f"JarvisAuto-{auto.nome}",
                    )
                    auto.thread.start()
        return True

    def registra(self, nome, azione, intervallo=None):
        nome = str(nome).strip().lower()
        if not nome or not callable(azione):
            raise ValueError("Automazione non valida")
        auto = Automazione(nome, azione, float(intervallo) if intervallo else None)
        with self._lock:
            self.automazioni[nome] = auto
            if auto.intervallo and not self._stop.is_set():
                auto.thread = threading.Thread(target=self._loop, args=(auto,), daemon=True, name=f"JarvisAuto-{nome}")
                auto.thread.start()
        return f"Automazione '{nome}' registrata."

    def _loop(self, auto):
        while not self._stop.wait(auto.intervallo or 1):
            if auto.attiva:
                self.esegui(auto.nome)

    def esegui(self, nome):
        auto = self.automazioni.get(str(nome).strip().lower())
        if not auto or not auto.attiva:
            return False
        try:
            auto.azione()
            auto.esecuzioni += 1
            auto.ultima_esecuzione = datetime.now().isoformat(timespec="seconds")
            return True
        except Exception as errore:
            if self.logger:
                self.logger.error(f"Automazione {auto.nome}: {errore}")
            return False

    def attiva(self, nome):
        auto = self.automazioni.get(str(nome).strip().lower())
        if not auto:
            return False
        auto.attiva = True
        return True

    def disattiva(self, nome):
        auto = self.automazioni.get(str(nome).strip().lower())
        if not auto:
            return False
        auto.attiva = False
        return True

    def elimina(self, nome):
        return self.automazioni.pop(str(nome).strip().lower(), None) is not None

    def ferma(self):
        self._stop.set()
        for auto in self.automazioni.values():
            auto.attiva = False
        for auto in self.automazioni.values():
            if auto.thread and auto.thread.is_alive():
                auto.thread.join(timeout=1)
        return True

    def stato(self):
        return {
            "stato": "attivo" if not self._stop.is_set() else "spento",
            "numero": len(self.automazioni),
            "automazioni": {
                nome: {
                    "attiva": a.attiva,
                    "intervallo": a.intervallo,
                    "esecuzioni": a.esecuzioni,
                    "ultima_esecuzione": a.ultima_esecuzione,
                }
                for nome, a in self.automazioni.items()
            },
        }


class PianificatoreJarvis:
    """Scheduler per attività ritardate."""

    def __init__(self, logger=None):
        self.logger = logger
        self._timers = {}
        self._lock = threading.RLock()
        self._attivo = True

    def pianifica(self, nome, secondi, azione):
        if not callable(azione) or secondi < 0:
            raise ValueError("Pianificazione non valida")
        self.annulla(nome)
        with self._lock:
            timer = threading.Timer(secondi, self._esegui, args=(nome, azione))
            timer.daemon = True
            self._timers[nome] = timer
            timer.start()
        return f"Attività '{nome}' pianificata tra {secondi} secondi."

    def _esegui(self, nome, azione):
        with self._lock:
            self._timers.pop(nome, None)
            attivo = self._attivo
        if not attivo:
            return
        try:
            azione()
        except Exception as errore:
            if self.logger:
                self.logger.error(f"Attività pianificata {nome}: {errore}")

    def annulla(self, nome):
        with self._lock:
            timer = self._timers.pop(nome, None)
        if timer:
            timer.cancel()
            return True
        return False

    def ferma(self):
        self._attivo = False
        for nome in list(self._timers):
            self.annulla(nome)
        return True

    def avvia(self):
        self._attivo = True
        return True

    def stato(self):
        return {"attivo": self._attivo, "attivita_pianificate": list(self._timers)}
