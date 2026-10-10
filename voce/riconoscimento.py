from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
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
        self.multilingue = None
        self.backend_attivo = "vosk"
        self.usa_multilingue = False

        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.percorso_modello = os.path.join(base, "vosk-model-small-it-0.22")
        self.sample_rate = 16000

        if self.config:
            voce = self.config.sezione("voce")
            modello = voce.get("modello_riconoscimento", None)
            if modello:
                self.percorso_modello = os.path.join(base, modello)
            self.sample_rate = int(voce.get("sample_rate", 16000))
            self.usa_multilingue = bool(voce.get("riconoscimento_multilingue", False))
            if self.usa_multilingue:
                try:
                    from voce.whisper_multilingue import WhisperMultilingue
                    modello_multi = voce.get("modello_multilingue", "motore_ia/whisper.cpp/models/ggml-base.bin")
                    eseguibile_multi = voce.get("eseguibile_multilingue", "")
                    self.multilingue = WhisperMultilingue(
                        modello=os.path.join(base, modello_multi) if not os.path.isabs(modello_multi) else modello_multi,
                        eseguibile=eseguibile_multi,
                        sample_rate=self.sample_rate,
                        timeout=voce.get("timeout_multilingue", 90),
                    )
                except (ImportError, OSError, ValueError, TypeError) as errore:
                    self.ultimo_errore = str(errore)

    @staticmethod
    def _vosk_disponibile():
        """Verifica Vosk rispettando anche i test che bloccano il modulo."""
        if "vosk" in sys.modules and sys.modules["vosk"] is None:
            return False
        try:
            return importlib.util.find_spec("vosk") is not None
        except (ImportError, ModuleNotFoundError, OSError, ValueError):
            return False

    @staticmethod
    def normalizza_comando_riconosciuto(testo):
        """Corregge trascrizioni Vosk note, anche se precedute dalla wake word.

        Le correzioni sono volutamente limitate a frasi osservate nell'uso
        reale, per non alterare arbitrariamente altri comandi dell'utente.
        """
        originale = str(testo or "").strip()
        confronto = re.sub(r"\s+", " ", originale.lower()).strip()
        confronto = re.sub(r"[.,!?;:]+$", "", confronto).strip()

        # Vosk può restituire l'intera frase, wake word compresa. In quel caso
        # normalizziamo solo il comando e manteniamo il prefisso originale.
        prefisso = ""
        for wake in ("hey jarvis ", "ehi jarvis ", "jarvis ", "giardino "):
            if confronto.startswith(wake):
                # "giardino" è una trascrizione Vosk già osservata al posto
                # della wake word: la correzione produce un comando valido
                # solo se il testo successivo coincide con un alias noto.
                prefisso = "jarvis " if wake == "giardino " else wake
                confronto = confronto[len(wake):].strip()
                break

        alias = (
            # Variante fonetica riportata nei log reali di Vosk.
            (r"(?:stato\s+)?sei\s+bersi\s+giur(?:\s+it)?", "stato cybersecurity"),
            (r"stato\s+sai\s+per\s+giur(?:\s+it)?", "stato cybersecurity"),
            (r"stato\s+sarebb(?:e|ero)\s+(?:security|servizi|service|giur(?:\s+it)?)", "stato cybersecurity"),
            (r"stato\s+sarebbe\s+security", "stato cybersecurity"),
            (r"(?:controlla|controllare|controllo)\s+(?:la\s+)?sicurezza", "stato cybersecurity"),
            (r"(?:stato\s+)?(?:sai\s+per\s+security|cyber\s*security|cybersecurity)", "stato cybersecurity"),
            (r"stato\s+sai\s+bersi\s+uniti", "stato cybersecurity"),
            (r"sai\s+bersi\s+uniti", "cybersecurity"),
            (r"analizzano\s+(?:il|la)\s+mia\s+rete", "analizza la mia rete"),
            (r"analizza\s+il\s+mia\s+rete", "analizza la mia rete"),
        )
        for pattern, canonico in alias:
            if re.fullmatch(pattern, confronto):
                return (prefisso + canonico).strip()
        return originale

    def _carica_vosk(self):
        """Carica Vosk solo quando serve realmente il riconoscimento."""
        if self._Model is not None and self._KaldiRecognizer is not None:
            return True
        if not self._vosk_disponibile():
            self.disponibile = False
            self.ultimo_errore = "Vosk non disponibile"
            return False
        try:
            from vosk import KaldiRecognizer, Model
        except (ImportError, ModuleNotFoundError, OSError, RuntimeError) as errore:
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

        # Preferisci Whisper multilingue se richiesto e preparato; altrimenti usa Vosk.
        if self.usa_multilingue and self.multilingue is not None:
            if self.multilingue.avvia():
                self.backend_attivo = "whisper"
                self.lingua = "auto"
                self.attivo = True
                self.ultimo_errore = None
                return True
            self.ultimo_errore = self.multilingue.ultimo_errore

        if not self.disponibile or not self._vosk_disponibile():
            self.disponibile = False
            self.attivo = False
            if not self.ultimo_errore:
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
            self.backend_attivo = "vosk"
            self.lingua = "it"
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
        if not self.attivo or not audio:
            return None
        if self.backend_attivo == "whisper" and self.multilingue is not None:
            testo = self.multilingue.riconosci(audio)
            if testo:
                return self.normalizza_comando_riconosciuto(testo) or None
            return None
        if self.riconoscitore is None:
            return None
        try:
            if self.riconoscitore.AcceptWaveform(audio):
                risultato: dict[str, Any] = json.loads(self.riconoscitore.Result())
                testo = str(risultato.get("text", "")).strip()
                return self.normalizza_comando_riconosciuto(testo) or None
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
        if self.multilingue is not None:
            self.multilingue.ferma()
        self.backend_attivo = "vosk"
        return True

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "lingua": self.lingua,
            "backend": self.backend_attivo,
            "multilingue_configurato": self.usa_multilingue,
            "stato_multilingue": self.multilingue.stato() if self.multilingue else None,
            "modello": self.percorso_modello,
            "sample_rate": self.sample_rate,
            "disponibile": self.disponibile,
            "ultimo_errore": self.ultimo_errore,
        }
