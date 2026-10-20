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
        """Mantiene il profilo personale sui tre dati autorizzati.

        I vecchi ricordi personali vengono ripuliti una sola volta. In seguito
        la memoria generale di Jarvis continua a funzionare normalmente.
        """
        impostazioni = self.database.dati.setdefault("impostazioni", {})
        inizializzato = impostazioni.get(
            "profilo_personale_simone_inizializzato", {}
        )
        if not (isinstance(inizializzato, dict) and inizializzato.get("valore")):
            # Rimuove solo le vecchie chiavi personali note, senza cancellare
            # appunti o memoria generale di Jarvis.
            ricordi = self.database.dati.get("ricordi", {})
            if isinstance(ricordi, dict):
                chiavi_personali = {
                    "nome", "nome_utente", "il mio nome",
                    "animale_preferito", "animale preferito",
                    "colore_preferito", "colore preferito",
                    "cane", "animale",
                }
                for chiave in list(ricordi):
                    normalizzata = str(chiave).strip().lower().replace("-", "_")
                    if normalizzata in chiavi_personali:
                        ricordi.pop(chiave, None)
                if not ricordi:
                    self.database.dati.pop("ricordi", None)
            self.database.aggiungi(
                "impostazioni",
                "profilo_personale_simone_inizializzato",
                True,
            )

        profilo = self.database.dati.setdefault("profilo", {})
        profilo.clear()
        for chiave, valore in (
            ("nome_utente", "Simone"),
            ("animale_preferito", "lupo"),
            ("colore_preferito", "blu"),
        ):
            self.database.aggiungi("profilo", chiave, valore)
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
