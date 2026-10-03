"""
Memoria conversazionale di Jarvis.

Adattamento del componente jarvis/ai/memory.py alla struttura reale della
repository. Gestisce il contesto temporaneo separatamente dalla memoria
persistente presente in memoria/memoria.py.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional


class Memory:
    """Gestisce cronologia, profilo temporaneo e contesto conversazionale."""

    def __init__(self, max_turns: int = 20, context_history_limit: int = 10):
        self.max_turns = max(1, int(max_turns))
        self.context_history_limit = max(1, int(context_history_limit))
        self.conversation_history: List[Dict[str, Any]] = []
        self.user_profile: Dict[str, Any] = {}
        self.context: Dict[str, Any] = {}

    def add_user_input(self, text: str) -> None:
        """Aggiunge un messaggio dell'utente."""
        self._add_message("user", text)

    def add_response(self, text: str) -> None:
        """Aggiunge una risposta di Jarvis."""
        self._add_message("assistant", text)

    def add_message(self, message_type: str, content: str) -> None:
        """Aggiunge un messaggio con un tipo personalizzato."""
        self._add_message(message_type, content)

    def _add_message(self, message_type: str, content: str) -> None:
        tipo = str(message_type or "").strip().lower()
        testo = self._normalizza_testo(content)
        if not tipo or not testo:
            return
        self.conversation_history.append({
            "type": tipo,
            "content": testo,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })
        self._trim_history()

    def get_context(self) -> Dict[str, Any]:
        """Restituisce una copia sicura del contesto corrente."""
        return {
            "history": self.get_history(self.context_history_limit),
            "profile": deepcopy(self.user_profile),
            "context": deepcopy(self.context),
        }

    def update_profile(self, key: str, value: Any) -> None:
        """Aggiorna un'informazione del profilo temporaneo."""
        chiave = str(key or "").strip()
        if chiave:
            self.user_profile[chiave] = value

    def get_profile(self, key: Optional[str] = None, default: Any = None) -> Any:
        """Legge un'informazione o l'intero profilo."""
        if key is None:
            return deepcopy(self.user_profile)
        return self.user_profile.get(str(key), default)

    def remove_profile(self, key: str) -> bool:
        """Rimuove un'informazione dal profilo."""
        chiave = str(key or "").strip()
        if chiave in self.user_profile:
            del self.user_profile[chiave]
            return True
        return False

    def update_context(self, key: str, value: Any) -> None:
        """Aggiorna un valore del contesto."""
        chiave = str(key or "").strip()
        if chiave:
            self.context[chiave] = value

    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Legge un valore del contesto."""
        return self.context.get(str(key), default)

    def remove_context(self, key: str) -> bool:
        """Rimuove un valore dal contesto."""
        chiave = str(key or "").strip()
        if chiave in self.context:
            del self.context[chiave]
            return True
        return False

    def get_history(self, limit: Optional[int] = 10) -> List[Dict[str, Any]]:
        """Restituisce gli ultimi messaggi come copia indipendente."""
        if limit is None:
            elementi = self.conversation_history
        else:
            limite = max(0, int(limit))
            elementi = self.conversation_history[-limite:] if limite else []
        return deepcopy(elementi)

    def clear_history(self) -> None:
        """Cancella soltanto la cronologia."""
        self.conversation_history.clear()

    def clear_context(self) -> None:
        """Cancella soltanto il contesto temporaneo."""
        self.context.clear()

    def clear_profile(self) -> None:
        """Cancella soltanto il profilo temporaneo."""
        self.user_profile.clear()

    def clear(self) -> None:
        """Cancella tutta la memoria temporanea."""
        self.conversation_history.clear()
        self.user_profile.clear()
        self.context.clear()

    def set_max_turns(self, max_turns: int) -> None:
        """Imposta il limite della cronologia e lo applica subito."""
        self.max_turns = max(1, int(max_turns))
        self._trim_history()

    def count(self) -> int:
        """Restituisce il numero di messaggi in cronologia."""
        return len(self.conversation_history)

    def ultimo_messaggio(self, message_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Restituisce l'ultimo messaggio, eventualmente filtrato per tipo."""
        if message_type is None:
            return deepcopy(self.conversation_history[-1]) if self.conversation_history else None

        tipo = str(message_type).strip().lower()
        for messaggio in reversed(self.conversation_history):
            if messaggio.get("type") == tipo:
                return deepcopy(messaggio)
        return None

    def stato(self) -> Dict[str, Any]:
        """Restituisce lo stato della memoria conversazionale."""
        return {
            "messaggi": len(self.conversation_history),
            "max_turns": self.max_turns,
            "limite_contesto": self.context_history_limit,
            "profilo_informazioni": len(self.user_profile),
            "valori_contesto": len(self.context),
        }

    def _trim_history(self) -> None:
        """Mantiene la cronologia entro il limite configurato."""
        if len(self.conversation_history) > self.max_turns:
            self.conversation_history = self.conversation_history[-self.max_turns:]

    @staticmethod
    def _normalizza_testo(text: Any) -> str:
        """Normalizza gli spazi del contenuto."""
        return " ".join(str(text or "").strip().split())


__all__ = ["Memory"]
