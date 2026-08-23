class ModuleManager:
    """Gestisce registrazione, avvio, arresto e stato dei moduli Jarvis."""

    def __init__(self, logger):
        self.logger = logger
        self.moduli = {}

    def registra(self, nome, modulo):
        self.moduli[nome] = modulo
        self.logger.info(f"Modulo registrato: {nome}")

    def avvia(self, nome):
        modulo = self.moduli.get(nome)
        if modulo is None:
            self.logger.warning(f"Modulo non trovato: {nome}")
            return False

        try:
            risultato = modulo.avvia()
            if risultato:
                self.logger.info(f"Modulo avviato: {nome}")
            else:
                self.logger.warning(f"Modulo non avviato: {nome}")
            return bool(risultato)
        except Exception as errore:
            self.logger.errore(f"Errore avvio {nome}: {errore}")
            return False

    def ferma(self, nome):
        modulo = self.moduli.get(nome)
        if modulo is None:
            return False

        ferma = getattr(modulo, "ferma", None)
        if not callable(ferma):
            return True

        try:
            risultato = ferma()
            self.logger.info(f"Modulo arrestato: {nome}")
            return risultato is not False
        except Exception as errore:
            self.logger.warning(f"Errore arresto {nome}: {errore}")
            return False

    def ferma_tutti(self):
        """Arresta tutti i moduli in ordine inverso di registrazione."""
        risultati = {}
        for nome in reversed(list(self.moduli)):
            risultati[nome] = self.ferma(nome)
        return risultati

    def stato(self):
        risultato = {}
        for nome, modulo in self.moduli.items():
            try:
                stato = getattr(modulo, "stato", None)
                risultato[nome] = stato() if callable(stato) else "attivo"
            except Exception as errore:
                self.logger.warning(f"Errore stato {nome}: {errore}")
                risultato[nome] = "errore"
        return risultato
