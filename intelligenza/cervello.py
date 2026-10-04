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
        # Le domande definitorie gia presenti nella base locale possono avere
        # una risposta immediata e naturale, evitando di attendere Qwen.
        if not self.conoscenza.necessita_web(testo):
            risposta_rapida = self.conoscenza.risposta_rapida(testo)
            if risposta_rapida:
                return risposta_rapida

        # Per le altre domande inviamo al modello soprattutto la richiesta
        # dell'utente. Qwen riceve solo il contesto utile, non uno stato enorme.
        contesto = ""
        locale = self.conoscenza.cerca_locale(testo, massimo=2, caratteri_massimi=1200)
        if locale:
            contesto += (
                "\n\nCONOSCENZA LOCALE PERTINENTE (usala come riferimento):\n"
                + locale
            )

        if self.conoscenza.necessita_web(testo):
            risultati = self.conoscenza.cerca_web(testo)
            if risultati:
                contesto += (
                    "\n\nDATI WEB RECENTI (solo se pertinenti e distinguendoli "
                    "dalla conoscenza locale):\n" + risultati
                )

        # Il contesto viene recuperato solo quando esiste una corrispondenza.
        # In questo modo le domande normali restano rapide e il modello riceve
        # informazioni aggiuntive solo quando possono migliorare la precisione.
        richiesta = testo + contesto

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
