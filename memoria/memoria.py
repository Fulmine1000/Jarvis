from datetime import datetime

from .database import DatabaseMemoria
from .profilo import ProfiloJarvis


class MemoriaJarvis:
    """Sistema centrale di memoria persistente di Jarvis."""

    def __init__(self, logger=None):
        self.nome = "Memoria Jarvis"
        self.attiva = False
        self.logger = logger
        self.database = DatabaseMemoria()
        self.profilo = ProfiloJarvis(logger, database=self.database)

    def avvia(self):
        self.attiva = True
        self._sincronizza_profilo_personale()
        self.profilo.avvia()
        if self.logger:
            self.logger.info("Memoria Jarvis avviata.")
        return True

    def _sincronizza_profilo_personale(self):
        """Mantiene nel profilo personale soltanto i tre dati autorizzati."""
        profilo = self.database.dati.setdefault("profilo", {})
        profilo.clear()
        for chiave, valore in (
            ("nome_utente", "Simone"),
            ("animale_preferito", "lupo"),
            ("colore_preferito", "blu"),
        ):
            self.database.aggiungi("profilo", chiave, valore)

        # I ricordi liberi possono contenere altre informazioni personali:
        # si azzerano per rispettare la richiesta di conservare solo questi dati.
        self.database.dati.pop("ricordi", None)
        self.database.salva()

    def ferma(self):
        self.attiva = False
        return True

    def ricorda(self, chiave, valore):
        """Salva un ricordo senza annidare inutilmente il campo valore."""
        if not str(chiave).strip():
            return "La chiave del ricordo non può essere vuota."
        self.database.aggiungi("ricordi", chiave, valore)
        return f"Ricorderò: {chiave}"

    def cerca(self, chiave):
        dato = self.database.leggi("ricordi", chiave)
        if not dato:
            return None
        return dato.get("valore") if isinstance(dato, dict) else dato

    def elenco_ricordi(self):
        return self.database.lista("ricordi")

    def dimentica(self, chiave):
        if self.database.elimina("ricordi", chiave):
            return "Ricordo eliminato."
        return "Ricordo non trovato."

    def conta_ricordi(self):
        return self.database.numero_ricordi()

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attiva" if self.attiva else "spenta",
            "ricordi": self.conta_ricordi(),
            "profilo": self.profilo.stato(),
        }
