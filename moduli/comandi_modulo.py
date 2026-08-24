from comandi.gestore import GestoreComandi


class ModuloComandi:
    """Coordina il gestore dei comandi con il kernel Jarvis."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.nome = "Comandi"
        self.attivo = False
        self.gestore = None

    def avvia(self):
        if self.attivo:
            return True
        dispositivi = getattr(self.kernel.modulo_dispositivi, "gestore", None)
        self.gestore = GestoreComandi(
            memoria=self.kernel.memoria,
            personalita=getattr(self.kernel, "personalita", None),
            dispositivi=dispositivi,
            kernel=self.kernel,
            logger=self.kernel.logger,
        )
        self.attivo = bool(self.gestore.avvia())
        self.kernel.logger.info("Modulo comandi attivo.")
        return self.attivo

    def esegui(self, comando):
        if not self.gestore:
            return "Gestore comandi non avviato."
        return self.gestore.esegui(comando)

    def ferma(self):
        if self.gestore:
            self.gestore.ferma()
        self.attivo = False
        return True

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "gestore": self.gestore.stato() if self.gestore else {},
        }
