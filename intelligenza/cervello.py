from __future__ import annotations

import datetime as dt


class CervelloJarvis:
    """Strato cognitivo di J.A.R.V.I.S.

    Coordina conversazione, contesto e memoria senza sostituire il router
    deterministico dei comandi. Il modello AI viene usato per comprendere e
    conversare quando una richiesta non corrisponde a un'azione locale nota.
    """

    def __init__(self, kernel):
        self.kernel = kernel
        self.attivo = True
        self.richieste = 0
        self.ultima_richiesta = None

    def rispondi(self, testo: str):
        testo = (testo or "").strip()
        if not testo or not self.attivo:
            return None

        self.richieste += 1
        self.ultima_richiesta = dt.datetime.now().isoformat(timespec="seconds")

        dialogo = getattr(self.kernel, "dialogo", None)
        if not dialogo:
            return None

        # Il dialogo mantiene la cronologia; qui aggiungiamo solo contesto
        # reale disponibile, evitando di inventare informazioni.
        contesto = self._contesto_reale()
        richiesta = testo
        if contesto:
            richiesta = f"Contesto reale del sistema:\n{contesto}\n\nRichiesta dell'utente:\n{testo}"

        return dialogo.rispondi(richiesta)

    def _contesto_reale(self) -> str:
        parti = []
        try:
            stato = self.kernel.stato
            parti.append(f"Stato Jarvis: {stato}")
        except Exception:
            pass

        try:
            nome = self.kernel.preferenze.leggi("nome_utente")
            if nome:
                parti.append(f"Nome utente configurato: {nome}")
        except Exception:
            pass

        try:
            contesto = self.kernel.contesto.stato()
            if contesto:
                parti.append(f"Contesto conversazionale disponibile: {contesto}")
        except Exception:
            pass

        return "\n".join(parti)

    def stato(self):
        dialogo = getattr(self.kernel, "dialogo", None)
        return {
            "attivo": self.attivo,
            "stato": "attivo" if self.attivo else "spento",
            "richieste": self.richieste,
            "ultima_richiesta": self.ultima_richiesta,
            "motore": dialogo.stato() if dialogo else {"attivo": False},
        }

    def ferma(self):
        self.attivo = False
        return True

    def avvia(self):
        self.attivo = True
        return True
