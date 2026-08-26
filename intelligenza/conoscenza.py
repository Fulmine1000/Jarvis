from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request


class ConoscenzaJarvis:
    """Livello di conoscenza esterna per il cervello di Jarvis.

    Il modello locale resta il motore principale. Questo modulo fornisce
    contesto verificabile dal Web quando una domanda può richiedere dati
    aggiornati o quando il modello ha bisogno di fonti esterne.
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.attivo = True

    def cerca_web(self, query: str, massimo: int = 5) -> str:
        query = (query or "").strip()
        if not query or not self.attivo:
            return ""
        try:
            url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
            richiesta = urllib.request.Request(
                url,
                headers={"User-Agent": "JARVIS/2.0 (+local assistant)"},
            )
            with urllib.request.urlopen(richiesta, timeout=8) as risposta:
                testo = risposta.read().decode("utf-8", errors="replace")

            risultati = []
            blocchi = re.findall(r'<a[^>]+class="result__a"[^>]*>(.*?)</a>', testo, re.S)
            snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', testo, re.S)
            for indice, titolo in enumerate(blocchi[:massimo]):
                titolo = re.sub(r"<.*?>", "", html.unescape(titolo)).strip()
                descrizione = ""
                if indice < len(snippets):
                    descrizione = re.sub(r"<.*?>", "", html.unescape(snippets[indice])).strip()
                if titolo:
                    risultati.append(f"- {titolo}: {descrizione}" if descrizione else f"- {titolo}")
            return "\n".join(risultati)
        except Exception as errore:
            if self.logger and hasattr(self.logger, "debug"):
                self.logger.debug(f"Ricerca Web non disponibile: {errore}")
            return ""

    def necessita_web(self, testo: str) -> bool:
        parole = (
            "oggi", "adesso", "attuale", "attualmente", "ultima", "ultime",
            "ultimo", "ultimi", "recentemente", "notizie", "news", "prezzo",
            "quanto costa", "meteo", "tempo", "chi è il presidente", "risultato",
            "classifica", "quando esce", "uscito", "uscita", "aggiornamento",
        )
        normalizzato = (testo or "").lower()
        return any(parola in normalizzato for parola in parole)

    def stato(self):
        return {"attivo": self.attivo, "funzione": "conoscenza Web"}
