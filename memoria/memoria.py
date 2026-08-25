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
        self.profilo = ProfiloJarvis(logger)

    def avvia(self):
        self.attiva = True
        self.profilo.avvia()
        if self.logger:
            self.logger.info("Memoria Jarvis avviata.")
        return True

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
