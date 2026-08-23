from __future__ import annotations

import json
import os
import urllib.request


class DialogoJarvis:
    """Conversazione AI opzionale e locale tramite Ollama.

    Se Ollama o il modello non sono presenti, Jarvis continua normalmente con
    il router deterministico e non considera l'AI locale una dipendenza critica.
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.endpoint = os.getenv("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
        self.modello = os.getenv("JARVIS_OLLAMA_MODEL", "llama3.2:3b")
        self.attivo = True
        self.storia = []
        self.istruzioni = (
            "Sei J.A.R.V.I.S., assistente personale in italiano. "
            "Parla in modo elegante, calmo, sintetico e naturale. "
            "Non fingere di aver eseguito azioni che non hai realmente eseguito. "
            "Non inventare dati di sistema o dispositivi."
        )

    def rispondi(self, testo):
        if not testo or not self.attivo:
            return None
        messaggi = [{"role": "system", "content": self.istruzioni}]
        messaggi.extend(self.storia[-8:])
        messaggi.append({"role": "user", "content": testo})
        payload = json.dumps({
            "model": self.modello,
            "messages": messaggi,
            "stream": False,
            "options": {"temperature": 0.7},
        }).encode("utf-8")
        try:
            richiesta = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(richiesta, timeout=20) as risposta:
                dati = json.loads(risposta.read().decode("utf-8"))
            testo_risposta = (dati.get("message") or {}).get("content", "").strip()
            if not testo_risposta:
                return None
            self.storia.extend([
                {"role": "user", "content": testo},
                {"role": "assistant", "content": testo_risposta},
            ])
            return testo_risposta
        except Exception as errore:
            if self.logger:
                self.logger.debug(f"AI locale non disponibile: {errore}")
            return None

    def stato(self):
        return {
            "attivo": self.attivo,
            "motore": "Ollama locale",
            "modello": self.modello,
            "storia_messaggi": len(self.storia),
        }
