"""Compatibilita storica per la gestione dei moduli.

Il kernel attuale utilizza i gestori ufficiali del progetto. Questo file
rimane disponibile per compatibilita con eventuali integrazioni precedenti.
"""

import importlib


class ModuloManager:
    def __init__(self, logger=None):
        self.logger = logger
        self.moduli = {}

    def registra(self, nome, percorso):
        self.moduli[nome] = {
            "percorso": percorso,
            "stato": "registrato",
            "oggetto": None,
        }
        if self.logger:
            self.logger.info(f"Modulo registrato: {nome}")

    def carica(self, nome):
        if nome not in self.moduli:
            return False
        try:
            modulo = importlib.import_module(self.moduli[nome]["percorso"])
            self.moduli[nome]["oggetto"] = modulo
            self.moduli[nome]["stato"] = "caricato"
            if self.logger:
                self.logger.info(f"Modulo caricato: {nome}")
            return True
        except Exception as errore:
            self.moduli[nome]["stato"] = "errore"
            if self.logger:
                metodo = getattr(self.logger, "errore", self.logger.info)
                metodo(f"Errore caricamento {nome}: {errore}")
            return False

    def avvia(self, nome):
        if nome not in self.moduli:
            return False
        modulo = self.moduli[nome]["oggetto"]
        if modulo is None:
            return False
        try:
            if hasattr(modulo, "avvia"):
                modulo.avvia()
            self.moduli[nome]["stato"] = "attivo"
            return True
        except Exception as errore:
            self.moduli[nome]["stato"] = "errore"
            if self.logger:
                metodo = getattr(self.logger, "errore", self.logger.info)
                metodo(str(errore))
            return False

    def elenco(self):
        return dict(self.moduli)


if __name__ == "__main__":
    manager = ModuloManager()
    manager.registra("test", "math")
    print(manager.carica("test"))
    print(manager.elenco())
