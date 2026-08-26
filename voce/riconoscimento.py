from __future__ import annotations

import importlib.util
import json
import os
from typing import Any


class RiconoscitoreVoce:
    """Riconoscimento vocale Vosk con caricamento nativo ritardato e sicuro."""

    def __init__(self, config=None):
        self.nome = "Riconoscitore Vocale"
        self.config = config
        self.attivo = False
        self.modello = None
        self.riconoscitore = None
        self.lingua = "it"
        self.disponibile = self._vosk_disponibile()
        self.ultimo_errore = None
        self._Model = None
        self._KaldiRecognizer = None

        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.percorso_modello = os.path.join(base, "vosk-model-small-it-0.22")
        self.sample_rate = 16000

        if self.config:
            voce = self.config.sezione("voce")
            modello = voce.get("modello_riconoscimento", None)
            if modello:
                self.percorso_modello = os.path.join(base, modello)
            self.sample_rate = int(voce.get("sample_rate", 16000))

    @staticmethod
    def _vosk_disponibile():
        """Controlla la presenza del pacchetto senza caricare la libreria nativa."""
        try:
            return importlib.util.find_spec("vosk") is not None
        except (ImportError, OSError, ValueError):
            return False

    def _carica_vosk(self):
        """Carica Vosk solo quando serve realmente il riconoscimento."""
        if self._Model is not None and self._KaldiRecognizer is not None:
            return True
        try:
            from vosk import KaldiRecognizer, Model
        except (ImportError, OSError, RuntimeError) as errore:
            self.disponibile = False
            self.ultimo_errore = str(errore)
            return False
        self._Model = Model
        self._KaldiRecognizer = KaldiRecognizer
        self.disponibile = True
        return True

    def avvia(self):
        if self.attivo:
            return True
        if not self.disponibile or not self._vosk_disponibile():
            self.disponibile = False
            self.attivo = False
            self.ultimo_errore = "Vosk non disponibile"
            return False

        if not os.path.isdir(self.percorso_modello):
            self.attivo = False
            self.ultimo_errore = f"Modello Vosk non trovato: {self.percorso_modello}"
            return False

        try:
            if not self._carica_vosk():
                return False

            self.modello = self._Model(self.percorso_modello)
            self.riconoscitore = self._KaldiRecognizer(self.modello, self.sample_rate)
            self.attivo = True
            self.ultimo_errore = None
            return True
        except (OSError, RuntimeError, ValueError) as errore:
            self.modello = None
            self.riconoscitore = None
            self.attivo = False
            self.ultimo_errore = str(errore)
            return False

    def riconosci(self, audio):
        if not self.attivo or not audio or self.riconoscitore is None:
            return None
        try:
            if self.riconoscitore.AcceptWaveform(audio):
                risultato: dict[str, Any] = json.loads(self.riconoscitore.Result())
                return str(risultato.get("text", "")).strip() or None
        except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as errore:
            self.ultimo_errore = str(errore)
        return None

    def reset(self):
        if self.modello is not None and self._KaldiRecognizer is not None:
            try:
                self.riconoscitore = self._KaldiRecognizer(self.modello, self.sample_rate)
            except (OSError, RuntimeError, ValueError) as errore:
                self.ultimo_errore = str(errore)
                self.riconoscitore = None
                self.attivo = False

    def ferma(self):
        self.attivo = False
        self.modello = None
        self.riconoscitore = None
        return True

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "lingua": self.lingua,
            "modello": self.percorso_modello,
            "sample_rate": self.sample_rate,
            "disponibile": self.disponibile,
            "ultimo_errore": self.ultimo_errore,
        }
