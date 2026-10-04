from __future__ import annotations

import datetime as dt

from .conoscenza import ConoscenzaJarvis


class CervelloJarvis:
    """Cervello cognitivo centrale di J.A.R.V.I.S.

    Coordina modello linguistico, memoria, contesto e conoscenza esterna.
    Le azioni del computer restano affidate ai moduli operativi autorizzati.
    """

    def __init__(self, kernel):
        self.kernel = kernel
        self.attivo = True
        self.richieste = 0
        self.ultima_richiesta = None
        self.conoscenza = ConoscenzaJarvis(getattr(kernel, "logger", None))

    def rispondi(self, testo: str):
        testo = (testo or "").strip()
        if not testo or not self.attivo:
            return None
        self.richieste += 1
        self.ultima_richiesta = dt.datetime.now().isoformat(timespec="seconds")
        dialogo = getattr(self.kernel, "dialogo", None)
        if not dialogo:
            return None
        # Per le domande normali inviamo al modello soprattutto la domanda
        # dell'utente. Il piccolo Qwen locale funziona molto meglio senza
        # un lungo dump di stato, cronologia e memoria dentro la richiesta.
        contesto_web = ""
        if self.conoscenza.necessita_web(testo):
            risultati = self.conoscenza.cerca_web(testo)
            if risultati:
                contesto_web = (
                    "\n\nDATI WEB RECENTI (solo se pertinenti):\n" + risultati
                )

        # Le regole comportamentali sono già nel system prompt del dialogo.
        # Evitiamo di duplicarle: meno token da elaborare e meno ambiguità.
        richiesta = testo + contesto_web

        return dialogo.rispondi(richiesta)

    def _contesto_reale(self) -> str:
        parti = []
        try:
            parti.append(f"Stato Jarvis: {self.kernel.stato}")
        except Exception:
            pass
        try:
            nome = self.kernel.preferenze.leggi("nome_utente")
            if nome:
                parti.append(f"Nome utente configurato: {nome}")
                parti.append("Appellativo da usare nelle risposte: Sir")
        except Exception:
            pass
        try:
            contesto = self.kernel.contesto.cronologia()[-6:]
            if contesto:
                parti.append(f"Ultimi scambi disponibili: {contesto}")
        except Exception:
            pass
        try:
            ricordi = self.kernel.memoria.elenco_ricordi()
            if isinstance(ricordi, dict):
                elementi = list(ricordi.items())[-10:]
                if elementi:
                    parti.append(f"Ricordi persistenti disponibili: {dict(elementi)}")
            elif ricordi:
                parti.append(f"Ricordi persistenti disponibili: {ricordi}")
        except Exception:
            pass
        return "\n".join(parti)

    def stato(self):
        dialogo = getattr(self.kernel, "dialogo", None)
        return {"attivo": self.attivo, "stato": "attivo" if self.attivo else "spento", "richieste": self.richieste, "ultima_richiesta": self.ultima_richiesta, "motore": dialogo.stato() if dialogo else {"attivo": False}, "conoscenza": self.conoscenza.stato()}

    def ferma(self):
        self.attivo = False
        return True

    def avvia(self):
        self.attivo = True
        return True
