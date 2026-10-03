"""
Motore di conversazione locale di Jarvis.

Adattamento di jarvis/ai/conversation.py alla struttura reale della
repository. Fornisce risposte di base per conversazioni comuni, lasciando
al CervelloJarvis e al motore DialogoJarvis la gestione delle richieste
più avanzate.
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Dict, Optional


class ConversationEngine:
    """Motore conversazionale locale di base in italiano."""

    def __init__(self, language: str = "it_IT"):
        self.language = str(language or "it_IT").strip()
        self.responses = self._load_responses()
        self.context_history = []

    def generate_response(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Genera una risposta in base alla richiesta dell'utente."""
        testo = " ".join(str(user_input or "").strip().split())
        if not testo:
            return "Mi dica pure, Sir."

        self.context_history.append({
            "user": testo,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })
        self.context_history = self.context_history[-20:]

        input_lower = testo.casefold()

        if self._contiene_una_delle(input_lower, ("ciao", "salve", "buongiorno", "buonasera", "buonanotte")):
            return self._get_greeting()

        if self._contiene_una_delle(input_lower, ("chi sei", "cosa sei", "presentati")):
            return (
                "Sono Jarvis, il suo assistente personale. "
                "Tutti i sistemi sono pronti. Come posso assisterla, Sir?"
            )

        if "come ti chiami" in input_lower:
            return "Il mio nome è Jarvis, Sir."

        if "come stai" in input_lower:
            return self._get_mood_response()

        if self._richiede_ora(input_lower):
            return self._get_time_response()

        if "data" in input_lower or "che giorno" in input_lower or "oggi che giorno" in input_lower:
            return self._get_date_response()

        if "barzelletta" in input_lower or "fammi ridere" in input_lower or "scherzo" in input_lower:
            return self._get_joke()

        if "aiuto" in input_lower or "cosa puoi fare" in input_lower or "che cosa puoi fare" in input_lower:
            return self._get_help()

        return self._generate_default_response(testo, context)

    def _get_greeting(self) -> str:
        """Restituisce un saluto coerente con l'orario."""
        ora = datetime.now().hour
        if 5 <= ora < 12:
            saluti = (
                "Buongiorno, Sir. Come posso assisterla?",
                "Buongiorno, Simone. Tutti i sistemi sono pronti.",
            )
        elif 12 <= ora < 18:
            saluti = (
                "Buon pomeriggio, Sir. Come posso assisterla?",
                "Salve, Sir. Jarvis operativo.",
            )
        elif 18 <= ora < 23:
            saluti = (
                "Buonasera, Sir. Come posso assisterla?",
                "Buonasera, Simone. Tutti i sistemi sono pronti.",
            )
        else:
            saluti = (
                "Buonanotte, Sir. Come posso assisterla?",
                "Jarvis operativo, Sir.",
            )
        return random.choice(saluti)

    def _get_time_response(self) -> str:
        """Restituisce l'ora locale del computer."""
        now = datetime.now()
        periodo = self._periodo_giornata(now.hour)
        return f"Sono le {now.hour:02d}:{now.minute:02d}, Sir. È {periodo}."

    def _get_date_response(self) -> str:
        """Restituisce la data locale in italiano."""
        now = datetime.now()
        mesi = (
            "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
            "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
        )
        giorni = (
            "lunedì", "martedì", "mercoledì", "giovedì",
            "venerdì", "sabato", "domenica",
        )
        return f"Oggi è {giorni[now.weekday()]}, {now.day} {mesi[now.month - 1]} {now.year}."

    def _get_mood_response(self) -> str:
        """Restituisce una risposta sullo stato operativo di Jarvis."""
        return random.choice((
            "Funziono perfettamente, grazie per aver chiesto.",
            "Tutti i sistemi sono operativi. Pronto ad assisterla.",
            "Sistemi nominali. Come posso esserle utile, Sir?",
        ))

    def _get_joke(self) -> str:
        """Restituisce una battuta casuale."""
        return random.choice((
            "Perché l'intelligenza artificiale non va al mare? Perché teme i virus.",
            "Quanti robot servono per cambiare una lampadina? Uno solo, ma prima deve aggiornare il firmware.",
            "Ho chiesto a un computer se aveva fame. Mi ha risposto: byte.",
        ))

    def _get_help(self) -> str:
        """Descrive sinteticamente le capacità disponibili."""
        return (
            "Posso assisterla con conversazioni, informazioni su ora e data, "
            "memoria, comandi vocali, dispositivi e automazioni. "
            "Le capacità effettivamente disponibili dipendono dai moduli attivi."
        )

    def _generate_default_response(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Risposta locale di fallback quando non esiste un pattern dedicato."""
        if context:
            return random.choice((
                "Ho ricevuto la richiesta. Mi fornisca pure ulteriori dettagli.",
                "Comprendo. Posso elaborare meglio la richiesta se mi indica cosa desidera ottenere.",
                "Ricevuto, Sir. Specifiche ulteriori mi permetteranno di procedere.",
            ))

        return random.choice((
            f"Ho ricevuto: «{user_input}». Come posso procedere?",
            "Comprendo. Può fornirmi qualche dettaglio in più?",
            "Ricevuto, Sir. Cosa desidera che faccia?",
        ))

    def get_history(self, limit: int = 10):
        """Restituisce gli ultimi elementi del contesto conversazionale."""
        limite = max(0, int(limit))
        if limite == 0:
            return []
        return list(self.context_history[-limite:])

    def clear_history(self) -> None:
        """Cancella il contesto temporaneo del motore."""
        self.context_history.clear()

    def stato(self) -> Dict[str, Any]:
        """Restituisce lo stato del motore conversazionale."""
        return {
            "lingua": self.language,
            "messaggi_contesto": len(self.context_history),
            "motore": "conversation-engine-locale",
        }

    def _load_responses(self) -> Dict[str, Any]:
        """Predisposizione per pattern esterni senza dipendenze obbligatorie."""
        return {}

    @staticmethod
    def _contiene_una_delle(testo: str, parole) -> bool:
        return any(parola in testo for parola in parole)

    @staticmethod
    def _richiede_ora(testo: str) -> bool:
        return (
            "che ore sono" in testo
            or "che ora è" in testo
            or "che ora e" in testo
            or testo.strip() == "ora"
        )

    @staticmethod
    def _periodo_giornata(ora: int) -> str:
        if 5 <= ora < 12:
            return "mattina"
        if 12 <= ora < 17:
            return "pomeriggio"
        if 17 <= ora < 21:
            return "sera"
        return "notte"


__all__ = ["ConversationEngine"]
