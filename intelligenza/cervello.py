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
        parti = ["Contesto reale del sistema:", self._contesto_reale() or "nessun dato aggiuntivo"]
        if self.conoscenza.necessita_web(testo):
            risultati = self.conoscenza.cerca_web(testo)
            if risultati:
                parti.extend(["\nInformazioni Web recenti (usale come contesto, non inventare fatti):", risultati])
        parti.extend(["\nRichiesta dell'utente:", testo])
        return dialogo.rispondi("\n".join(parti))

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
        except Exception:
            pass
        try:
            contesto = self.kernel.contesto.cronologia()[-6:]
            if contesto:
                parti.append(f"Ultimi scambi disponibili: {contesto}")
        except Exception:
            pass
        try:
            ricordi = self.kernel.memoria.elenco_ricordi()[-10:]
            if ricordi:
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
