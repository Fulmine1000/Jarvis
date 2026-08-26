import datetime


class GestoreDispositivi:
    """Gestore centrale dei dispositivi di J.A.R.V.I.S.

    Mantiene una vista uniforme dei dispositivi, espone capacità disponibili,
    ricerca tollerante dei nomi e permette operazioni mirate senza assumere
    che ogni dispositivo implementi le stesse funzioni.
    """

    ALIAS = {
        "mac": "computer",
        "macbook": "computer",
        "pc": "computer",
        "telefono principale": "telefono",
        "smartphone": "telefono",
        "cellulare": "telefono",
        "android": "telefono",
        "tv": "tv",
        "televisione": "tv",
        "televisore": "tv",
        "casa": "smart_home",
        "domotica": "smart_home",
        "wifi": "rete",
    }

    def __init__(self, logger=None):
        self.nome = "Gestore Dispositivi"
        self.logger = logger
        self.dispositivi = {}
        self.connessione = None
        self.base = None

    def collega_connessione(self, connessione):
        self.connessione = connessione
        return "Connessione dispositivi collegata."

    def registra(self, nome, dispositivo):
        nome = str(nome).strip().lower()
        self.dispositivi[nome] = dispositivo
        if getattr(dispositivo, "base", False):
            self.base = nome
        if self.connessione:
            self.connessione.registra(nome, dispositivo)
        if self.logger:
            self.logger.info(f"Dispositivo registrato: {nome}")
        return f"{nome} registrato."

    def rimuovi(self, nome):
        nome = self.risolvi_nome(nome)
        if nome in self.dispositivi:
            del self.dispositivi[nome]
            if self.base == nome:
                self.base = None
            return f"{nome} rimosso."
        return "Dispositivo non trovato."

    def risolvi_nome(self, nome):
        """Normalizza un nome o alias e trova anche corrispondenze parziali."""
        valore = str(nome or "").strip().lower()
        if valore in self.ALIAS:
            valore = self.ALIAS[valore]
        if valore in self.dispositivi:
            return valore
        for candidato in self.dispositivi:
            if valore and (valore in candidato or candidato in valore):
                return candidato
        return valore

    def cerca(self, nome):
        return self.dispositivi.get(self.risolvi_nome(nome))

    def cerca_base(self):
        return self.dispositivi.get(self.base) if self.base else None

    def elenco(self):
        return list(self.dispositivi.keys())

    def capacita_dispositivo(self, nome):
        """Restituisce le funzioni pubbliche realmente esposte dal dispositivo."""
        dispositivo = self.cerca(nome)
        if not dispositivo:
            return []
        escluse = {"stato", "base", "logger", "nome", "modello"}
        return sorted(
            nome_funzione
            for nome_funzione in dir(dispositivo)
            if not nome_funzione.startswith("_")
            and nome_funzione not in escluse
            and callable(getattr(dispositivo, nome_funzione, None))
        )

    def stato_tutti(self):
        risultato = {}
        for nome, dispositivo in self.dispositivi.items():
            try:
                stato = dispositivo.stato() if hasattr(dispositivo, "stato") else {"stato": "disponibile"}
                risultato[nome] = {
                    "stato": stato,
                    "capacita": self.capacita_dispositivo(nome),
                }
            except Exception as errore:
                risultato[nome] = {"errore": str(errore), "capacita": self.capacita_dispositivo(nome)}
        return risultato

    def connetti(self, nome):
        nome = self.risolvi_nome(nome)
        if self.connessione:
            return self.connessione.connetti(nome)
        dispositivo = self.cerca(nome)
        if dispositivo and hasattr(dispositivo, "connetti"):
            return dispositivo.connetti()
        return "Dispositivo non disponibile."

    def disconnetti(self, nome):
        nome = self.risolvi_nome(nome)
        if self.connessione:
            return self.connessione.disconnetti(nome)
        dispositivo = self.cerca(nome)
        if dispositivo and hasattr(dispositivo, "disconnetti"):
            return dispositivo.disconnetti()
        return "Dispositivo non disponibile."

    def sincronizza(self, nome):
        nome = self.risolvi_nome(nome)
        if self.connessione:
            return self.connessione.sincronizza(nome)
        dispositivo = self.cerca(nome)
        if dispositivo and hasattr(dispositivo, "sincronizza"):
            return dispositivo.sincronizza()
        return "Sincronizzazione non disponibile."

    def sincronizza_base(self):
        if not self.base:
            return "Base non trovata."
        return self.sincronizza(self.base)

    def esegui(self, nome, azione, *args, **kwargs):
        """Esegue una capacità esplicita su un dispositivo registrato."""
        dispositivo = self.cerca(nome)
        if not dispositivo:
            return "Dispositivo non trovato."
        funzione = getattr(dispositivo, str(azione), None)
        if not callable(funzione):
            return f"Il dispositivo non supporta l'azione {azione}."
        try:
            return funzione(*args, **kwargs)
        except Exception as errore:
            if self.logger:
                self.logger.error(f"Errore su dispositivo {nome}, azione {azione}: {errore}")
            return f"Non riesco a eseguire {azione} su {nome}."

    def rapporto(self):
        return {
            "nome": self.nome,
            "ora": datetime.datetime.now().strftime("%H:%M:%S"),
            "base": self.base,
            "numero_dispositivi": len(self.dispositivi),
            "dispositivi": self.elenco(),
        }

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo",
            "base": self.base,
            "numero_dispositivi": len(self.dispositivi),
            "dispositivi": self.elenco(),
        }
