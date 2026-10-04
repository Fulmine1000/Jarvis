from __future__ import annotations

import html
import json
import os
import re
import unicodedata
import urllib.parse
import urllib.request


class ConoscenzaJarvis:
    """Conoscenza locale + dati Web aggiornati per il cervello di Jarvis.

    La base locale viene consultata prima del Web e contiene solo i passaggi
    piu pertinenti alla domanda, cosi il modello non riceve un enorme dump.
    """

    BASE_JARVIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILE_BASE_LOCALE = os.path.join(BASE_JARVIS, "conoscenza", "base.json")

    def __init__(self, logger=None):
        self.logger = logger
        self.attivo = True
        self.locale_attivo = True
        self.voci = []
        self._carica_base_locale()

    @staticmethod
    def _normalizza(testo: str) -> str:
        testo = unicodedata.normalize("NFKD", str(testo or "").lower())
        return "".join(c for c in testo if not unicodedata.combining(c))

    @classmethod
    def _tokenizza(cls, testo: str):
        normalizzato = cls._normalizza(testo)
        return set(re.findall(r"[a-z0-9àèéìòù]+", normalizzato))

    def _carica_base_locale(self):
        try:
            with open(self.FILE_BASE_LOCALE, "r", encoding="utf-8") as file:
                dati = json.load(file)
            voci = dati.get("voci", []) if isinstance(dati, dict) else []
            self.voci = [voce for voce in voci if isinstance(voce, dict) and voce.get("testo")]
        except (OSError, ValueError, TypeError) as errore:
            self.voci = []
            self._log_debug(f"Base conoscenza locale non disponibile: {errore}")

    def _log_debug(self, messaggio):
        if self.logger and hasattr(self.logger, "debug"):
            self.logger.debug(messaggio)

    def cerca_locale(self, query: str, massimo: int = 3, caratteri_massimi: int = 1800) -> str:
        """Recupera solo le voci locali piu pertinenti alla domanda."""
        query = (query or "").strip()
        if not query or not self.attivo or not self.locale_attivo or not self.voci:
            return ""

        query_norm = self._normalizza(query)
        query_tokens = self._tokenizza(query)
        candidati = []

        for voce in self.voci:
            titolo = str(voce.get("titolo", ""))
            testo = str(voce.get("testo", ""))
            chiavi = [str(x) for x in voce.get("parole_chiave", [])]
            argomenti = [str(x) for x in voce.get("argomenti", [])]
            score = 0

            titolo_norm = self._normalizza(titolo)
            if titolo_norm and titolo_norm in query_norm:
                score += 8

            for chiave in chiavi:
                chiave_norm = self._normalizza(chiave)
                if chiave_norm and chiave_norm in query_norm:
                    score += 5
                score += min(2, len(self._tokenizza(chiave) & query_tokens))

            score += min(4, len(self._tokenizza(titolo) & query_tokens) * 2)
            score += min(2, len(self._tokenizza(" ".join(argomenti)) & query_tokens))

            if score > 0:
                candidati.append((score, titolo, testo))

        candidati.sort(key=lambda item: (-item[0], item[1]))
        risultati = []
        totale = 0
        for score, titolo, testo in candidati[:massimo]:
            blocco = f"- {titolo}: {testo}"
            if totale + len(blocco) > caratteri_massimi:
                break
            risultati.append(blocco)
            totale += len(blocco)

        return "\n".join(risultati)

    def risposta_rapida(self, query: str):
        """Restituisce subito una risposta naturale per domande definitorie note."""
        query = (query or "").strip()
        if not query or not self.attivo or not self.locale_attivo or not self.voci:
            return None

        normalizzato = self._normalizza(query)
        definitoria = (
            normalizzato.startswith("cos'e ")
            or normalizzato.startswith("che cos'e ")
            or normalizzato.startswith("cosa e ")
            or normalizzato.startswith("spiegami ")
            or normalizzato.startswith("cosa significa ")
            or normalizzato.startswith("che significa ")
        )
        if not definitoria:
            return None

        query_tokens = self._tokenizza(query)
        migliore = None
        for voce in self.voci:
            titolo = str(voce.get("titolo", ""))
            testo = str(voce.get("testo", "")).strip()
            if not testo:
                continue
            score = 0
            titolo_norm = self._normalizza(titolo)
            if titolo_norm and titolo_norm in normalizzato:
                score += 8
            for chiave in voce.get("parole_chiave", []):
                chiave_norm = self._normalizza(str(chiave))
                if chiave_norm and chiave_norm in normalizzato:
                    score += 5
                score += min(2, len(self._tokenizza(str(chiave)) & query_tokens))
            score += min(4, len(self._tokenizza(titolo) & query_tokens) * 2)
            if score >= 8 and (migliore is None or score > migliore[0]):
                migliore = (score, testo)

        if not migliore:
            return None

        testo = migliore[1]
        # Una breve apertura rende la risposta piu naturale senza chiedere
        # al modello di generarla, evitando diversi secondi di attesa.
        if testo:
            testo = testo[0].lower() + testo[1:]
        return "In breve, " + testo

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
            self._log_debug(f"Ricerca Web non disponibile: {errore}")
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
        return {
            "attivo": self.attivo,
            "funzione": "conoscenza locale + Web",
            "voci_locali": len(self.voci),
        }
