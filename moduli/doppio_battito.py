"""Rilevamento opzionale del doppio battito di mani tramite microfono.

Attivazione esplicita con JARVIS_DOPPIO_BATTITO=1. Il listener usa il microfono
in esclusiva e può interferire con il riconoscimento vocale continuo: abilitarlo
solo su sistemi dove il backend audio supporta l'accesso condiviso.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Callable


class RilevatoreDoppioBattito:
    """Rileva due picchi audio ravvicinati senza registrare o salvare l'audio."""

    def __init__(
        self,
        callback: Callable[[], None],
        soglia_rms: float = 0.18,
        intervallo_minimo: float = 0.12,
        intervallo_massimo: float = 0.75,
        cooldown: float = 2.0,
        logger=None,
        samplerate: int = 16000,
        blocksize: int = 512,
    ):
        self.callback = callback
        self.soglia_rms = max(0.01, float(soglia_rms))
        self.intervallo_minimo = max(0.05, float(intervallo_minimo))
        self.intervallo_massimo = max(self.intervallo_minimo, float(intervallo_massimo))
        self.cooldown = max(0.1, float(cooldown))
        self.logger = logger
        self.samplerate = int(samplerate)
        self.blocksize = int(blocksize)
        self._stop = threading.Event()
        self._thread = None
        self._ultimo_battito = 0.0
        self._ultimo_trigger = 0.0
        self._sopra_soglia = False
        self._lock = threading.Lock()

    def _log(self, livello: str, testo: str) -> None:
        try:
            if self.logger and hasattr(self.logger, livello):
                getattr(self.logger, livello)(testo)
        except Exception:
            pass

    def processa_rms(self, rms: float, adesso: float | None = None) -> bool:
        """Punto di ingresso deterministico, testabile senza microfono."""
        adesso = time.monotonic() if adesso is None else float(adesso)
        picco = float(rms) >= self.soglia_rms
        with self._lock:
            if not picco:
                self._sopra_soglia = False
                return False
            if self._sopra_soglia:
                return False
            self._sopra_soglia = True
            if adesso - self._ultimo_trigger < self.cooldown:
                return False
            if self._ultimo_battito and self.intervallo_minimo <= adesso - self._ultimo_battito <= self.intervallo_massimo:
                self._ultimo_battito = 0.0
                self._ultimo_trigger = adesso
                trigger = True
            else:
                self._ultimo_battito = adesso
                trigger = False
        if trigger:
            self._log("info", "Doppio battito rilevato.")
            try:
                self.callback()
            except Exception as errore:
                self._log("warning", f"Callback doppio battito fallita: {errore}")
            return True
        return False

    def avvia(self) -> bool:
        """Avvia il listener audio in background; richiede sounddevice."""
        if self._thread and self._thread.is_alive():
            return True
        try:
            import sounddevice as sd
        except Exception as errore:
            self._log("warning", f"Rilevamento battito non disponibile: {errore}")
            return False

        self._stop.clear()

        def lavoro():
            import numpy as np

            def audio_callback(indata, frames, time_info, status):
                if status:
                    self._log("warning", f"Audio battito: {status}")
                samples = np.asarray(indata, dtype="float32")
                rms = float(np.sqrt(np.mean(np.square(samples)))) if samples.size else 0.0
                self.processa_rms(rms)

            try:
                with sd.InputStream(
                    samplerate=self.samplerate,
                    blocksize=self.blocksize,
                    channels=1,
                    dtype="float32",
                    callback=audio_callback,
                ):
                    while not self._stop.wait(0.1):
                        pass
            except Exception as errore:
                self._log("warning", f"Listener doppio battito arrestato: {errore}")

        self._thread = threading.Thread(target=lavoro, name="JarvisDoppioBattito", daemon=True)
        self._thread.start()
        self._log("info", "Rilevamento doppio battito attivato (microfono condiviso richiesto).")
        return True

    def ferma(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None


__all__ = ["RilevatoreDoppioBattito"]
