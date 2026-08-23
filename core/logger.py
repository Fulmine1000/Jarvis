import os
from datetime import datetime


class LoggerJarvis:
    """Logger leggero, locale e senza dipendenze esterne."""

    def __init__(self, cartella="logs"):
        self.cartella = cartella
        os.makedirs(self.cartella, exist_ok=True)

    def scrivi(self, livello, messaggio):
        ora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        testo = f"[{ora}] [{livello}] {messaggio}"
        print(testo)
        file_log = os.path.join(self.cartella, "jarvis.log")
        try:
            with open(file_log, "a", encoding="utf-8") as log:
                log.write(testo + "\n")
        except OSError:
            pass

    def info(self, messaggio):
        self.scrivi("INFO", messaggio)

    def errore(self, messaggio):
        self.scrivi("ERRORE", messaggio)

    def warning(self, messaggio):
        self.scrivi("WARNING", messaggio)

    def debug(self, messaggio):
        self.scrivi("DEBUG", messaggio)

    error = errore
    warn = warning
